"""
Módulo de Memória Cognitiva para o ROKO.

Este módulo contém a classe CognitiveMemory, responsável pela persistência
de longo prazo das interações. Utiliza uma base de dados SQLite para
metadados e um índice vetorial FAISS para busca semântica eficiente.
O índice FAISS também é persistido em disco para performance.
"""

import os
import re
import sqlite3
import numpy as np
import faiss
import logging
import time
import threading
from typing import Dict, List, Any, Optional
from .embedding_cache import EmbeddingCache
from .contextual_reranker import ContextualReranker

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

class CognitiveMemory:
    """
    Sistema de memória de longo prazo com recuperação semântica e persistência.
    """
    def __init__(self, db_path: str = "roko_nexus.db", index_path: str = "faiss_index.bin", faiss_dim: int = 3072):
        self.db_path = db_path
        self.index_path = index_path
        self.faiss_dim = faiss_dim
        self.index = None
        self.last_indexed_id = 0

        # Thread-local storage para conexões SQLite
        self._local = threading.local()
        self._db_lock = threading.RLock()

        # Inicializar cache e re-ranker
        self.embedding_cache = EmbeddingCache()
        self.reranker = ContextualReranker(db_path)

        self._init_db()
        self._load_or_create_index()

    def _workspace_base_dir(self) -> str:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace_projects'))
        os.makedirs(base, exist_ok=True)
        return base

    @staticmethod
    def _slugify(value: Optional[str]) -> str:
        if not value:
            return ''
        value = value.lower()
        value = re.sub(r'[^a-z0-9]+', '-', value)
        value = value.strip('-')
        return value

    def _build_workspace_dirname(self, user_id: int, username: Optional[str]) -> str:
        slug = self._slugify(username)
        if not slug:
            slug = f'user-{user_id}'
        return f"{slug}-{user_id}"

    def _get_connection(self):
        """Retorna uma conexão thread-safe para o banco de dados."""
        # Usar thread-local storage para garantir uma conexão por thread
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            with self._db_lock:
                self._local.conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,  # Permitir uso entre threads com cuidado
                    timeout=10.0  # Timeout maior para operações concorrentes
                )
                # Configurações otimizadas para concorrência
                self._local.conn.execute("PRAGMA busy_timeout = 10000;")
                self._local.conn.execute("PRAGMA journal_mode = WAL;")
                self._local.conn.execute("PRAGMA synchronous = NORMAL;")
                self._local.conn.execute("PRAGMA cache_size = 10000;")
                self._local.conn.execute("PRAGMA temp_store = memory;")

        return self._local.conn

    def _init_db(self):
        """Inicializa o banco de dados com thread safety."""
        with self._db_lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()

                # Tabela de usuários
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        last_login REAL,
                        is_active INTEGER DEFAULT 1,
                        workspace_root TEXT,
                        avatar TEXT
                    )
                ''')

                cursor.execute("PRAGMA table_info(users)")
                user_columns = [column[1] for column in cursor.fetchall()]

                if 'workspace_root' not in user_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN workspace_root TEXT")
                    logging.info("Migração: Coluna 'workspace_root' adicionada à tabela users")

                if 'avatar' not in user_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
                    logging.info("Migração: Coluna 'avatar' adicionada à tabela users")


                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        timestamp REAL DEFAULT CURRENT_TIMESTAMP,
                        interaction_type TEXT NOT NULL,
                        user_prompt TEXT NOT NULL,
                        agent_thoughts TEXT,
                        agent_response TEXT,
                        embedding BLOB NOT NULL,
                        tags TEXT,
                        category TEXT,
                        importance_score INTEGER DEFAULT 5,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')

            # Migration: Add missing columns if they don't exist
                cursor.execute("PRAGMA table_info(interactions)")
                columns = [column[1] for column in cursor.fetchall()]

                if 'tags' not in columns:
                    cursor.execute("ALTER TABLE interactions ADD COLUMN tags TEXT")
                    logging.info("Migração: Coluna 'tags' adicionada à tabela interactions")

                if 'category' not in columns:
                    cursor.execute("ALTER TABLE interactions ADD COLUMN category TEXT")
                    logging.info("Migração: Coluna 'category' adicionada à tabela interactions")

                if 'importance_score' not in columns:
                    cursor.execute("ALTER TABLE interactions ADD COLUMN importance_score INTEGER DEFAULT 5")
                    logging.info("Migração: Coluna 'importance_score' adicionada à tabela interactions")

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value INTEGER
                    )
                ''')
                cursor.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('last_indexed_id', 0)")

                conn.commit()
                logging.info("✅ Base de dados inicializada com sucesso")

            except Exception as e:
                conn.rollback()
                logging.error(f"Erro na inicialização da base de dados: {e}")
                raise

    def _load_or_create_index(self):
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM metadata WHERE key = 'last_indexed_id'")
                    result = cursor.fetchone()
                    self.last_indexed_id = result[0] if result else 0
                logging.info(f"Índice FAISS carregado de '{self.index_path}' com {self.index.ntotal} vetores.")
            else:
                # Usar IndexHNSW para melhor performance
                if self.faiss_dim == 3072:
                    # HNSW com parâmetros otimizados para embeddings OpenAI
                    base_index = faiss.IndexHNSWFlat(self.faiss_dim, 32)  # M=32 para boa qualidade/speed
                    base_index.hnsw.efConstruction = 200  # Melhor construção
                    base_index.hnsw.efSearch = 128        # Busca mais rápida
                    self.index = faiss.IndexIDMap(base_index)
                else:
                    # Fallback para IndexFlatL2
                    self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.faiss_dim))

                logging.info("Nenhum índice FAISS encontrado. Criando novo com IndexHNSW otimizado.")
                # Forçar salvamento inicial do índice vazio
                self._save_index()
        except Exception as e:
            logging.warning(f"Erro ao carregar/criar índice FAISS: {e}. Criando fallback.")
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.faiss_dim))
            self.last_indexed_id = 0
            # Tentar salvar o índice recém-criado
            try:
                self._save_index()
            except Exception as save_error:
                logging.error(f"Falha ao salvar índice inicial: {save_error}")

    def _save_index(self):
        try:
            # Verificar se o índice é válido (permitir índices vazios para inicialização)
            if self.index is None:
                logging.error("Índice FAISS é None - criando novo")
                self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.faiss_dim))

            # Permitir salvar índices vazios para persistência inicial
            if self.index.ntotal == 0:
                logging.info("Salvando índice vazio para inicialização")

            # Criar backup antes de salvar
            backup_path = f"{self.index_path}.backup"
            if os.path.exists(self.index_path):
                import shutil
                shutil.copy2(self.index_path, backup_path)

            # Salvar índice
            faiss.write_index(self.index, self.index_path)

            # Verificar se foi salvo corretamente
            if not os.path.exists(self.index_path):
                raise Exception("Arquivo de índice não foi criado")

            # Testar se pode ser carregado
            test_index = faiss.read_index(self.index_path)
            if test_index.ntotal != self.index.ntotal:
                raise Exception("Índice salvo não corresponde ao original")

            # Atualizar metadata
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE metadata SET value = ? WHERE key = 'last_indexed_id'", (self.last_indexed_id,))
                conn.commit()

            # Remover backup se tudo correu bem
            if os.path.exists(backup_path):
                os.remove(backup_path)

            logging.info(f"Índice FAISS com {self.index.ntotal} vetores salvo em '{self.index_path}'.")
            return True

        except Exception as e:
            logging.error(f"Falha ao salvar o índice FAISS: {e}")

            # Restaurar backup se existir
            backup_path = f"{self.index_path}.backup"
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, self.index_path)
                logging.info("Backup do índice restaurado")

            return False

    def _sync_index(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, embedding FROM interactions WHERE id > ? AND embedding IS NOT NULL", (self.last_indexed_id,))
                new_rows = cursor.fetchall()

                if not new_rows:
                    return True

                logging.info(f"Sincronizando índice FAISS com {len(new_rows)} novas interações.")

                # Validar embeddings
                valid_rows = []
                for row in new_rows:
                    try:
                        embedding = np.frombuffer(row[1], dtype=np.float32)
                        if embedding.shape[0] == self.faiss_dim:
                            valid_rows.append((row[0], embedding))
                        else:
                            logging.warning(f"Embedding com dimensão incorreta: {embedding.shape[0]} (esperado: {self.faiss_dim})")
                    except Exception as e:
                        logging.warning(f"Erro ao processar embedding da interação {row[0]}: {e}")

                if not valid_rows:
                    logging.warning("Nenhum embedding válido para sincronizar")
                    return False

                # Preparar arrays
                new_embeddings = np.array([row[1] for row in valid_rows])
                new_ids = np.array([row[0] for row in valid_rows])

                # Adicionar ao índice
                self.index.add_with_ids(new_embeddings, new_ids)
                self.last_indexed_id = int(new_ids[-1])

                # Salvar índice
                success = self._save_index()
                if success:
                    logging.info(f"Índice sincronizado com sucesso. Total de vetores: {self.index.ntotal}")

                return success

        except Exception as e:
            logging.error(f"Erro na sincronização do índice: {e}")
            return False

    def create_user(self, username: str, email: str, password_hash: str) -> int:
        """Cria um novo usuário no sistema com thread safety."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, time.time()))
                conn.commit()
                user_id = cursor.lastrowid

                workspace_dirname = self._build_workspace_dirname(user_id, username)
                workspace_base = self._workspace_base_dir()
                workspace_path = os.path.join(workspace_base, workspace_dirname)

                try:
                    os.makedirs(workspace_path, exist_ok=True)
                except Exception as dir_error:
                    logging.error(f"Erro ao criar diretório de workspace {workspace_path}: {dir_error}")
                    raise

                cursor.execute(
                    "UPDATE users SET workspace_root = ? WHERE id = ?",
                    (workspace_dirname, user_id)
                )
                conn.commit()

                logging.info(f"👤 Usuário criado: {username} (ID: {user_id}) com workspace '{workspace_dirname}'")
                return user_id
            except sqlite3.IntegrityError as e:
                conn.rollback()
                if "username" in str(e):
                    raise ValueError("Nome de usuário já existe")
                elif "email" in str(e):
                    raise ValueError("Email já cadastrado")
                else:
                    raise ValueError("Erro de integridade dos dados")
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao criar usuário: {e}")
                raise

    def get_user_by_username(self, username: str) -> Dict:
        """Busca usuário por nome de usuário."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT id, username, email, password_hash, created_at, last_login, is_active, workspace_root, avatar
                    FROM users WHERE username = ?
                """, (username,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'username': row[1],
                        'email': row[2],
                        'password_hash': row[3],
                        'created_at': row[4],
                        'last_login': row[5],
                        'is_active': bool(row[6]),
                        'workspace_root': row[7],
                        'avatar': row[8]
                    }
                return None
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao buscar usuário: {e}")
                return None

    def get_user_by_email(self, email: str) -> Dict:
        """Busca usuário por email."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT id, username, email, password_hash, created_at, last_login, is_active, workspace_root, avatar
                    FROM users WHERE email = ?
                """, (email,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'username': row[1],
                        'email': row[2],
                        'password_hash': row[3],
                        'created_at': row[4],
                        'last_login': row[5],
                        'is_active': bool(row[6]),
                        'workspace_root': row[7],
                        'avatar': row[8]
                    }
                return None
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao buscar usuário por email: {e}")
                return None

    def update_last_login(self, user_id: int):
        """Atualiza o último login do usuário."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE users SET last_login = ?
                    WHERE id = ?
                """, (time.time(), user_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao atualizar último login: {e}")
                raise

    def update_user_avatar(self, user_id: int, avatar_data: str) -> bool:
        """Atualiza o avatar do usuário."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'UPDATE users SET avatar = ? WHERE id = ?',
                    (avatar_data, user_id)
                )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao atualizar avatar do usuário: {e}")
                return False

    def get_user_avatar(self, user_id: int) -> str:
        """Obtém o avatar do usuário."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT avatar FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao obter avatar do usuário: {e}")
                return None

    def get_user_email(self, user_id: int) -> str:
        """Obtém o email do usuário."""
        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao obter email do usuário: {e}")
                return None

    def ensure_user_workspace(self, user_id: int, workspace_root: Optional[str], username: Optional[str] = None) -> str:
        """Garante que o usuário possua um workspace dedicado e retorna o diretório relativo."""
        workspace_base = self._workspace_base_dir()

        if username is None:
            with self._db_lock:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                row = cur.fetchone()
                username = row[0] if row else None

        target_dir = self._build_workspace_dirname(user_id, username)

        current_dir = None
        if workspace_root:
            candidate = str(workspace_root).strip().replace('..', '').strip('\/')
            if candidate:
                current_dir = candidate

        if current_dir and current_dir != target_dir:
            old_path = os.path.join(workspace_base, current_dir)
            new_path = os.path.join(workspace_base, target_dir)
            try:
                if os.path.exists(old_path):
                    if os.path.exists(new_path):
                        logging.warning(f"Workspace alvo {new_path} já existe. Mantendo diretório anterior {old_path}.")
                        target_dir = current_dir
                    else:
                        os.replace(old_path, new_path)
                        logging.info(f"Workspace do usuário {user_id} renomeado para {target_dir}")
            except OSError as err:
                logging.warning(f"Não foi possível renomear workspace {old_path}: {err}")
                target_dir = current_dir or target_dir

        workspace_path = os.path.join(workspace_base, target_dir)
        os.makedirs(workspace_path, exist_ok=True)

        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE users SET workspace_root = ? WHERE id = ?",
                    (target_dir, user_id)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao atualizar workspace do usuário {user_id}: {e}")
                raise

        return target_dir

    def save_interaction(self, **kwargs):
        """Salva interação com thread safety."""
        kwargs['embedding'] = kwargs['embedding'].astype(np.float32).tobytes()

        # Validar importance_score como integer
        if 'importance_score' in kwargs:
            kwargs['importance_score'] = int(kwargs['importance_score'])

        # Garantir que user_id está presente
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 1  # Usuário padrão para compatibilidade

        with self._db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cols = ', '.join(kwargs.keys())
                placeholders = ', '.join('?' for _ in kwargs)
                query = f"INSERT INTO interactions ({cols}) VALUES ({placeholders})"
                cursor.execute(query, tuple(kwargs.values()))
                conn.commit()
                logging.info(f"Interação do tipo '{kwargs.get('interaction_type')}' guardada para usuário {kwargs.get('user_id')}.")
            except Exception as e:
                conn.rollback()
                logging.error(f"Erro ao salvar interação: {e}")
                raise

    def retrieve_context(self, query_embedding: np.ndarray, top_k: int = 5,
                        query_context: Dict[str, Any] = None,
                        session_context: List[str] = None,
                        use_reranking: bool = True,
                        user_id: int = None) -> List[Dict]:
        self._sync_index()
        if self.index.ntotal == 0:
            return []

        # Buscar mais resultados iniciais para re-ranking
        search_k = min(top_k * 3, self.index.ntotal) if use_reranking else top_k

        query_embedding_np = np.expand_dims(query_embedding, axis=0).astype('float32')
        distances, ids = self.index.search(query_embedding_np, search_k)

        if ids.size == 0 or ids[0][0] == -1:
            return []

        # Recuperar dados completos incluindo metadados para re-ranking
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in ids[0])

            # Filtrar por usuário se especificado
            if user_id:
                query = f"""
                    SELECT id, user_prompt, agent_thoughts, agent_response,
                           timestamp, category, tags, importance_score
                    FROM interactions
                    WHERE id IN ({placeholders}) AND user_id = ?
                """
                cursor.execute(query, tuple(int(i) for i in ids[0]) + (user_id,))
            else:
                query = f"""
                    SELECT id, user_prompt, agent_thoughts, agent_response,
                           timestamp, category, tags, importance_score
                    FROM interactions
                    WHERE id IN ({placeholders})
                """
                cursor.execute(query, tuple(int(i) for i in ids[0]))
            rows = cursor.fetchall()

        # Mapear resultados com metadados
        results_with_metadata = []
        for i, row in enumerate(rows):
            if row[0] in ids[0]:
                result = {
                    "id": row[0],
                    "user_prompt": row[1],
                    "agent_thoughts": row[2],
                    "agent_response": row[3],
                    "timestamp": row[4],
                    "category": row[5],
                    "tags": row[6],
                    "importance_score": row[7],
                    "faiss_distance": float(distances[0][list(ids[0]).index(row[0])]),
                    "faiss_rank": list(ids[0]).index(row[0])
                }
                results_with_metadata.append(result)

        # Aplicar re-ranking se habilitado
        if use_reranking and results_with_metadata:
            results_with_metadata = self.reranker.rerank_results(
                results_with_metadata, query_context, session_context
            )

            # Log de acessos para frequência
            for result in results_with_metadata[:top_k]:
                self.reranker.log_interaction_access(result['id'])

        # Retornar apenas top_k resultados finais
        final_results = results_with_metadata[:top_k]

        logging.info(f"Recuperação contextual: {len(final_results)} resultados "
                    f"{'com re-ranking' if use_reranking else 'sem re-ranking'}")

        return final_results

    def close_connections(self):
        """Fecha todas as conexões thread-local de forma segura."""
        with self._db_lock:
            if hasattr(self._local, 'conn') and self._local.conn:
                try:
                    self._local.conn.close()
                    self._local.conn = None
                    logging.info("🔒 Conexão thread-local fechada")
                except Exception as e:
                    logging.warning(f"Erro ao fechar conexão: {e}")

    def get_last_chats(self, limit: int = 3, user_id: int = None) -> List[Dict]:
        """
        Recupera os últimos N chats para contexto.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if user_id:
                cursor.execute("""
                    SELECT user_prompt, agent_response, timestamp, id
                    FROM interactions
                    WHERE interaction_type = 'pipeline_execution'
                    AND user_id = ?
                    AND user_prompt IS NOT NULL
                    AND agent_response IS NOT NULL
                    AND LENGTH(TRIM(user_prompt)) > 0
                    AND LENGTH(TRIM(agent_response)) > 0
                    ORDER BY id DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT user_prompt, agent_response, timestamp, id
                    FROM interactions
                    WHERE interaction_type = 'pipeline_execution'
                    AND user_prompt IS NOT NULL
                    AND agent_response IS NOT NULL
                    AND LENGTH(TRIM(user_prompt)) > 0
                    AND LENGTH(TRIM(agent_response)) > 0
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()

        # Retorna em ordem cronológica (mais antigo primeiro)
        chats = []
        for row in reversed(rows):
            if row[0] and row[1] and str(row[0]).strip() and str(row[1]).strip():
                chats.append({
                    "user_prompt": str(row[0]).strip(),
                    "agent_response": str(row[1]).strip(),
                    "timestamp": row[2],
                    "interaction_id": row[3]
                })

        logging.info(f"💭 Recuperados {len(chats)} chats recentes para contexto de {limit} solicitados")

        # Debug: mostrar se há dados na tabela
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE interaction_type = 'pipeline_execution'")
        total_interactions = cursor.fetchone()[0]
        logging.info(f"🗃️ Total de interações na base: {total_interactions}")

        return chats

    def search_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Busca interações por categoria.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_prompt, agent_response, timestamp, tags
                FROM interactions
                WHERE category = ?
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            """, (category, limit))
            rows = cursor.fetchall()

        return [
            {
                "user_prompt": row[0],
                "agent_response": row[1],
                "timestamp": row[2],
                "tags": row[3]
            }
            for row in rows
        ]

    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict]:
        """
        Busca interações por tags.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            tag_params = [f"%{tag}%" for tag in tags]

            cursor.execute(f"""
                SELECT user_prompt, agent_response, timestamp, tags, category
                FROM interactions
                WHERE {tag_conditions}
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            """, tag_params + [limit])
            rows = cursor.fetchall()

        return [
            {
                "user_prompt": row[0],
                "agent_response": row[1],
                "timestamp": row[2],
                "tags": row[3],
                "category": row[4]
            }
            for row in rows
        ]

    def cleanup_old_memories(self, days_old: int = 30, keep_important: bool = True):
        """
        Remove interações antigas para otimizar a base de dados.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if keep_important:
                # Mantém interações importantes (score > 7)
                cursor.execute("""
                    DELETE FROM interactions
                    WHERE datetime(timestamp) < datetime('now', '-{} days')
                    AND (importance_score <= 7 OR importance_score IS NULL)
                """.format(days_old))
            else:
                cursor.execute("""
                    DELETE FROM interactions
                    WHERE datetime(timestamp) < datetime('now', '-{} days')
                """.format(days_old))

            deleted_count = cursor.rowcount
            conn.commit()

        # Reconstrói o índice FAISS
        self._rebuild_index()

        logging.info(f"Limpeza de memória: {deleted_count} interações antigas removidas.")
        return deleted_count

    def _rebuild_index(self):
        """
        Reconstrói o índice FAISS do zero.
        """
        # Cria novo índice
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.faiss_dim))
        self.last_indexed_id = 0

        # Reindexiza todas as interações
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, embedding FROM interactions ORDER BY id")
            all_rows = cursor.fetchall()

            if all_rows:
                embeddings = np.array([np.frombuffer(row[1], dtype=np.float32) for row in all_rows])
                ids = np.array([row[0] for row in all_rows])

                self.index.add_with_ids(embeddings, ids)
                self.last_indexed_id = int(ids[-1])

        self._save_index()
        logging.info(f"Índice FAISS reconstruído com {self.index.ntotal} vetores.")

    def validate_system_integrity(self) -> Dict[str, Any]:
        """
        Valida a integridade do sistema de memória.
        """
        issues = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total de interações
                cursor.execute("SELECT COUNT(*) FROM interactions")
                total_interactions = cursor.fetchone()[0]

                # Interações com embeddings
                cursor.execute("SELECT COUNT(*) FROM interactions WHERE embedding IS NOT NULL")
                with_embeddings = cursor.fetchone()[0]

                # Verificar índice FAISS
                faiss_vectors = self.index.ntotal if self.index else 0

                # Verificar arquivo do índice
                index_file_exists = os.path.exists(self.index_path)

                # Detectar problemas
                if total_interactions > 0 and with_embeddings == 0:
                    issues.append("Nenhuma interação tem embeddings")

                if with_embeddings > faiss_vectors:
                    issues.append(f"Embeddings não indexados: {with_embeddings - faiss_vectors}")

                if faiss_vectors > 0 and not index_file_exists:
                    issues.append("Índice FAISS em memória mas não persistido")

                if self.last_indexed_id < total_interactions:
                    issues.append(f"Sincronização atrasada: {total_interactions - self.last_indexed_id} interações")

                return {
                    "status": "healthy" if not issues else "issues_detected",
                    "total_interactions": total_interactions,
                    "with_embeddings": with_embeddings,
                    "faiss_vectors": faiss_vectors,
                    "index_file_exists": index_file_exists,
                    "last_indexed_id": self.last_indexed_id,
                    "issues": issues
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "issues": [f"Erro na validação: {e}"]
            }

    def get_relevant_context(self, query_text: str, user_id: int = None, limit: int = 5) -> List[Dict]:
        """
        Método auxiliar para compatibilidade - obtém contexto relevante através de busca semântica.
        """
        try:
            # Gerar embedding do texto da query (isso requer uma implementação de embedding)
            # Por enquanto, vou usar get_last_chats como fallback
            return self.get_last_chats(limit=limit, user_id=user_id)
        except Exception as e:
            logging.error(f"Erro ao obter contexto relevante: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas avançadas da memória.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total de interações
            cursor.execute("SELECT COUNT(*) FROM interactions")
            total_interactions = cursor.fetchone()[0]

            # Categorias mais usadas
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM interactions
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            """)
            top_categories = cursor.fetchall()

            # Interações por tipo
            cursor.execute("""
                SELECT interaction_type, COUNT(*) as count
                FROM interactions
                GROUP BY interaction_type
                ORDER BY count DESC
            """)
            types_distribution = cursor.fetchall()

            # Estatísticas de importância
            cursor.execute("""
                SELECT AVG(importance_score) as avg_importance,
                       MIN(importance_score) as min_importance,
                       MAX(importance_score) as max_importance
                FROM interactions
                WHERE importance_score IS NOT NULL
            """)
            importance_stats = cursor.fetchone()

        # Estatísticas do cache
        cache_stats = self.embedding_cache.get_stats()

        # Informações do índice FAISS
        index_info = {
            "type": type(self.index).__name__ if self.index else "None",
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimensions": self.faiss_dim,
            "last_indexed_id": self.last_indexed_id
        }

        return {
            "total_interactions": total_interactions,
            "faiss_vectors": self.index.ntotal if self.index else 0,
            "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
            "types_distribution": [{"type": typ, "count": count} for typ, count in types_distribution],
            "importance_stats": {
                "average": round(importance_stats[0], 2) if importance_stats[0] else 0,
                "min": importance_stats[1] if importance_stats[1] else 0,
                "max": importance_stats[2] if importance_stats[2] else 0
            },
            "cache_performance": cache_stats,
            "index_info": index_info,
            "system_health": self.validate_system_integrity()
        }