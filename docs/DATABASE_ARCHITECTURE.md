
# 🗃️ Arquitetura de Banco de Dados ROKO

## 📋 Visão Geral

O sistema ROKO utiliza uma arquitetura híbrida inovadora de banco de dados que combina:

- **SQLite** para metadados estruturados e gestão de usuários
- **FAISS IndexHNSW** para busca semântica vetorial ultra-rápida
- **Sistema de Cache Triplo** (L1/L2/L3) com speedup de até 100x
- **Re-ranking Contextual** para relevância inteligente

## 🏗️ Componentes Principais

### 1. CognitiveMemory (Núcleo Principal)
**Localização**: `ROKO/Memory/cognitive_memory.py`

```python
# Inicialização
memory = CognitiveMemory(
    db_path="roko_nexus.db",           # SQLite principal
    index_path="faiss_index.bin",      # Índice FAISS
    faiss_dim=3072                     # Dimensões embeddings OpenAI
)
```

### 2. UltraCacheSystem (Cache Multicamada)
**Localização**: `ROKO/Memory/ultra_cache_system.py`

```python
# Cache com 3 camadas otimizadas
cache = UltraCacheSystem(
    max_size=10000,                    # Tamanho máximo
    ttl_hours=24                       # Time-to-live
)
```

### 3. EmbeddingCache (Cache de Embeddings)
**Localização**: `ROKO/Memory/embedding_cache.py`

```python
# Cache específico para embeddings
embedding_cache = EmbeddingCache(
    cache_dir="embedding_cache",       # Diretório de cache
    max_size=1000,                     # Máximo de entradas
    ttl_hours=24                       # Expiração
)
```

## 📊 Esquema do Banco de Dados

### Tabela: `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_login REAL,
    is_active INTEGER DEFAULT 1
);
```

### Tabela: `interactions`
```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp REAL DEFAULT CURRENT_TIMESTAMP,
    interaction_type TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    agent_thoughts TEXT,
    agent_response TEXT,
    embedding BLOB NOT NULL,           -- Vetor de 3072 dimensões
    tags TEXT,
    category TEXT,
    importance_score INTEGER DEFAULT 5,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Tabela: `metadata`
```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value INTEGER
);
```

## ⚡ Sistema de Cache Triplo

### L1 Cache - Memória RAM
- **Speedup**: 100x
- **Armazenamento**: Memória volátil
- **Uso**: Dados mais acessados

### L2 Cache - Persistente
- **Speedup**: 50x
- **Armazenamento**: Disco local
- **Uso**: Dados frequentemente acessados

### L3 Cache - Semântico
- **Speedup**: 20x
- **Armazenamento**: Busca por similaridade
- **Uso**: Conteúdo semanticamente similar

```python
# Exemplo de uso do cache
result = ultra_cache.get(
    key="user_query",
    content="Como funciona IA?",
    context="tecnologia"
)

if not result:
    # Processar e armazenar
    result = process_complex_query(query)
    ultra_cache.set(
        key="user_query",
        data=result,
        content="Como funciona IA?",
        context="tecnologia"
    )
```

## 🎯 FAISS IndexHNSW (Busca Vetorial)

### Configuração Otimizada
```python
# Parâmetros otimizados para embeddings OpenAI
base_index = faiss.IndexHNSWFlat(3072, 32)  # M=32 para qualidade/velocidade
base_index.hnsw.efConstruction = 200        # Construção otimizada
base_index.hnsw.efSearch = 128              # Busca rápida
index = faiss.IndexIDMap(base_index)
```

### Performance
- **Dimensões**: 3072 (embeddings OpenAI)
- **Algoritmo**: HNSW (Hierarchical Navigable Small World)
- **Complexidade**: O(log N) para busca
- **Precision@10**: >95% comparado com busca exaustiva

## 🔧 APIs Principais

### Operações de Usuário
```python
# Criar usuário
user_id = memory.create_user(
    username="alice",
    email="alice@example.com", 
    password_hash="hashed_password"
)

# Buscar usuário
user = memory.get_user_by_username("alice")

# Atualizar último login
memory.update_last_login(user_id)
```

### Operações de Interação
```python
# Salvar interação
memory.save_interaction(
    user_id=1,
    interaction_type="pipeline_execution",
    user_prompt="Analise estes dados",
    agent_thoughts="Processando análise...",
    agent_response="Análise concluída",
    embedding=embedding_vector,
    category="analytics",
    tags="data,analysis",
    importance_score=8
)

# Buscar contexto relevante
context = memory.retrieve_context(
    query_embedding=query_vector,
    top_k=5,
    query_context={"category": "analytics"},
    session_context=["data", "analysis"],
    use_reranking=True,
    user_id=1
)
```

### Operações de Busca
```python
# Buscar por categoria
results = memory.search_by_category("analytics", limit=10)

# Buscar por tags
results = memory.search_by_tags(["data", "ai"], limit=10)

# Últimos chats
chats = memory.get_last_chats(limit=3, user_id=1)
```

## 📈 Configurações de Performance

### SQLite Otimizado
```sql
PRAGMA busy_timeout = 10000;      -- Timeout para concorrência
PRAGMA journal_mode = WAL;        -- Write-Ahead Logging
PRAGMA synchronous = NORMAL;      -- Balance performance/safety
PRAGMA cache_size = 10000;        -- Cache de 10MB
PRAGMA temp_store = memory;       -- Temp tables em RAM
```

### Thread Safety
- **Thread-local storage** para conexões SQLite
- **RLock** para operações críticas
- **WAL mode** para concorrência sem bloqueios
- **Connection pooling** automático

## 🛠️ Manutenção e Otimização

### Limpeza Automática
```python
# Remover interações antigas (mantém importantes)
deleted = memory.cleanup_old_memories(
    days_old=30,
    keep_important=True  # Mantém score > 7
)

# Reconstruir índice FAISS
memory._rebuild_index()
```

### Validação de Integridade
```python
# Verificar saúde do sistema
health = memory.validate_system_integrity()
print(f"Status: {health['status']}")
print(f"Issues: {health['issues']}")

# Estatísticas detalhadas
stats = memory.get_memory_stats()
print(f"Total interactions: {stats['total_interactions']}")
print(f"FAISS vectors: {stats['faiss_vectors']}")
print(f"Cache hit rate: {stats['cache_performance']['hit_rate']}")
```

## 📊 Métricas de Performance

### Benchmarks Típicos
- **Insert Rate**: ~1000 interações/segundo
- **Query Time**: <50ms para busca semântica
- **Cache Hit Rate**: 85-95%
- **Memory Usage**: ~100MB para 100k interações
- **Disk Usage**: ~500MB para 100k interações + embeddings

### Estatísticas em Tempo Real
```python
stats = memory.get_memory_stats()
{
    "total_interactions": 15847,
    "faiss_vectors": 15847,
    "cache_performance": {
        "hit_rate": "94.67%",
        "estimated_speedup": 92.2
    },
    "index_info": {
        "type": "IndexIDMap",
        "total_vectors": 15847,
        "dimensions": 3072
    }
}
```

## 🔒 Segurança e Backup

### Backup Automático
- Backup antes de operações críticas
- Verificação de integridade pós-salvamento
- Recuperação automática de falhas

### Segurança
- Senhas hasheadas (nunca plaintext)
- Validação de input em todas as operações
- Isolamento de dados por usuário
- Logs de auditoria completos

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Índice FAISS Corrompido
```python
# Detectar e corrigir
if memory.index.ntotal == 0:
    memory._rebuild_index()
```

#### 2. Embeddings com Dimensão Incorreta
```python
# Verificar dimensões
if embedding.shape[0] != 3072:
    print(f"Dimensão incorreta: {embedding.shape[0]}")
```

#### 3. Database Lock
```python
# Configurar timeout maior
conn.execute("PRAGMA busy_timeout = 30000;")
```

#### 4. Cache Miss Alto
```python
# Verificar TTL e tamanho
cache_stats = ultra_cache.get_cache_stats()
if cache_stats["hit_rate"] < 80:
    # Aumentar TTL ou tamanho do cache
    pass
```

### Logs de Debug
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs específicos do sistema
logger = logging.getLogger('CognitiveMemory')
logger.setLevel(logging.DEBUG)
```

## 🔄 Migrations e Versionamento

### Migrações Automáticas
O sistema detecta e aplica migrações automaticamente:

```python
# Verificar colunas existentes
cursor.execute("PRAGMA table_info(interactions)")
columns = [column[1] for column in cursor.fetchall()]

# Adicionar colunas se não existirem
if 'tags' not in columns:
    cursor.execute("ALTER TABLE interactions ADD COLUMN tags TEXT")
    
if 'category' not in columns:
    cursor.execute("ALTER TABLE interactions ADD COLUMN category TEXT")
    
if 'importance_score' not in columns:
    cursor.execute("ALTER TABLE interactions ADD COLUMN importance_score INTEGER DEFAULT 5")
```

## 📚 Referências e Links

- **SQLite WAL Mode**: https://sqlite.org/wal.html
- **FAISS Documentation**: https://github.com/facebookresearch/faiss
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Thread Safety**: https://docs.python.org/3/library/threading.html

---

**Nota**: Esta arquitetura foi projetada para alta performance em aplicações de IA com busca semântica intensiva. O sistema é auto-otimizante e requer manutenção mínima.
