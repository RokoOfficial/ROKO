"""
Gerenciador de Artefatos ROKO.
Responsável por organizar, salvar e recuperar artefatos criados pela ROKO.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class ArtifactManager:
    """
    Gerenciador centralizado de artefatos da ROKO.
    """

    def __init__(self, artifacts_dir: str = "ARTEFATOS", workspace_path: str = None):
        if workspace_path:
            # Salvar no workspace do usuário
            self.artifacts_dir = Path(workspace_path) / "artefatos"
        else:
            # Fallback para diretório padrão
            self.artifacts_dir = Path(artifacts_dir)
        
        self.artifacts_dir.mkdir(exist_ok=True)
        self.index_file = self.artifacts_dir / "artifacts_index.json"
        self.logger = logging.getLogger('ROKO.ARTIFACT_MANAGER')

        # Criar índice se não existir
        if not self.index_file.exists():
            self._create_initial_index()

    def _create_initial_index(self):
        """Cria o índice inicial de artefatos."""
        initial_index = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "artifacts": {},
            "categories": {
                "visualizations": [],
                "games": [],
                "dashboards": [],
                "presentations": [],
                "utilities": [],
                "other": []
            }
        }

        # Indexar arquivos existentes
        for file_path in self.artifacts_dir.glob("*.html"):
            if file_path.name != "artifacts_index.json":
                artifact_id = self._generate_artifact_id(file_path.name)
                category = self._categorize_artifact(file_path.name)

                initial_index["artifacts"][artifact_id] = {
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.artifacts_dir)),
                    "category": category,
                    "created_at": datetime.now().isoformat(),
                    "type": "html",
                    "description": f"Artefato {category} - {file_path.name}",
                    "tags": self._extract_tags_from_name(file_path.name)
                }

                initial_index["categories"][category].append(artifact_id)

        self._save_index(initial_index)

    def _generate_artifact_id(self, filename: str) -> str:
        """Gera ID único para o artefato."""
        base_name = Path(filename).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"

    def _categorize_artifact(self, filename: str) -> str:
        """Categoriza automaticamente o artefato baseado no nome."""
        filename_lower = filename.lower()

        if any(keyword in filename_lower for keyword in ['chart', 'graph', 'visualization', 'dados']):
            return "visualizations"
        elif any(keyword in filename_lower for keyword in ['jogo', 'game', 'corrida', 'casino']):
            return "games"
        elif any(keyword in filename_lower for keyword in ['dashboard', 'crypto', 'btc']):
            return "dashboards"
        elif any(keyword in filename_lower for keyword in ['apresentacao', 'presentation']):
            return "presentations"
        else:
            return "other"

    def _extract_tags_from_name(self, filename: str) -> List[str]:
        """Extrai tags do nome do arquivo."""
        tags = []
        filename_lower = filename.lower()

        # Tags baseadas em palavras-chave
        tag_mapping = {
            'btc': 'bitcoin',
            'crypto': 'cryptocurrency',
            'jogo': 'game',
            'corrida': 'racing',
            'casino': 'gambling',
            'dados': 'data',
            'chart': 'visualization',
            'dashboard': 'analytics'
        }

        for keyword, tag in tag_mapping.items():
            if keyword in filename_lower:
                tags.append(tag)

        return tags

    def save_artifact(self, content: str, filename: str, description: str = "",
                     tags: List[str] = None, category: str = None, workspace_path: str = None) -> str:
        """
        Salva um novo artefato no diretório organizado.

        Args:
            content: Conteúdo do artefato (HTML, JSON, etc.)
            filename: Nome do arquivo
            description: Descrição do artefato
            tags: Tags para classificação
            category: Categoria específica (opcional)

        Returns:
            ID do artefato criado
        """
        try:
            # Se filename tem path, extrair apenas o nome
            filename = Path(filename).name

            # Garantir extensão .html se não especificada
            if not filename.endswith(('.html', '.json', '.txt', '.css', '.js', '.patch')):
                filename += '.html'

            # Gerar ID único
            artifact_id = self._generate_artifact_id(filename)

            # Determinar categoria
            if not category:
                category = self._categorize_artifact(filename)

            # Salvar no diretório de artefatos (workspace do usuário)
            file_path = self.artifacts_dir / filename

            # Garantir que o diretório existe
            self.artifacts_dir.mkdir(exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"📁 Artefato salvo no workspace: {filename}")

            # Atualizar índice
            self._add_to_index(artifact_id, filename, description, tags or [], category)

            self.logger.info(f"✅ Artefato salvo: {filename} (ID: {artifact_id})")
            return {"artifact_id": artifact_id, "filename": filename, "file_path": str(file_path)}

        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar artefato {filename}: {e}")
            return None

    def _add_to_index(self, artifact_id: str, filename: str, description: str,
                     tags: List[str], category: str):
        """Adiciona artefato ao índice."""
        index = self._load_index()

        index["artifacts"][artifact_id] = {
            "name": filename,
            "path": filename,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "type": Path(filename).suffix[1:] if Path(filename).suffix else "html",
            "description": description,
            "tags": tags
        }

        # Adicionar à categoria
        if category in index["categories"]:
            if artifact_id not in index["categories"][category]:
                index["categories"][category].append(artifact_id)

        self._save_index(index)

    def find_artifacts(self, query: str = "", category: str = "", tags: List[str] = None) -> List[Dict]:
        """
        Busca artefatos baseado em critérios.

        Args:
            query: Termo de busca (nome ou descrição)
            category: Categoria específica
            tags: Tags para filtrar

        Returns:
            Lista de artefatos encontrados
        """
        index = self._load_index()
        results = []

        for artifact_id, artifact_data in index["artifacts"].items():
            match = True

            # Filtro por query
            if query:
                query_lower = query.lower()
                if not (query_lower in artifact_data["name"].lower() or
                       query_lower in artifact_data["description"].lower()):
                    match = False

            # Filtro por categoria
            if category and artifact_data["category"] != category:
                match = False

            # Filtro por tags
            if tags:
                artifact_tags = set(artifact_data.get("tags", []))
                if not set(tags).intersection(artifact_tags):
                    match = False

            if match:
                results.append({
                    "id": artifact_id,
                    "name": artifact_data["name"],
                    "path": str(self.artifacts_dir / artifact_data["path"]),
                    "category": artifact_data["category"],
                    "description": artifact_data["description"],
                    "tags": artifact_data.get("tags", []),
                    "created_at": artifact_data["created_at"]
                })

        return results

    def get_artifact_content(self, artifact_id: str) -> Optional[str]:
        """Recupera o conteúdo de um artefato."""
        index = self._load_index()

        if artifact_id in index["artifacts"]:
            artifact_path = self.artifacts_dir / index["artifacts"][artifact_id]["path"]
            try:
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"❌ Erro ao ler artefato {artifact_id}: {e}")
                return None

        return None

    def list_categories(self) -> Dict[str, int]:
        """Lista categorias e quantidade de artefatos."""
        index = self._load_index()
        return {cat: len(artifacts) for cat, artifacts in index["categories"].items()}

    def get_recent_artifacts(self, limit: int = 5) -> List[Dict]:
        """Retorna os artefatos mais recentes."""
        index = self._load_index()

        # Ordenar por data de criação
        artifacts = list(index["artifacts"].items())
        artifacts.sort(key=lambda x: x[1]["created_at"], reverse=True)

        results = []
        for artifact_id, artifact_data in artifacts[:limit]:
            results.append({
                "id": artifact_id,
                "name": artifact_data["name"],
                "category": artifact_data["category"],
                "description": artifact_data["description"],
                "created_at": artifact_data["created_at"]
            })

        return results

    def _load_index(self) -> Dict:
        """Carrega o índice de artefatos."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar índice: {e}")
            return {"artifacts": {}, "categories": {}}

    def _save_index(self, index: Dict):
        """Salva o índice de artefatos."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar índice: {e}")