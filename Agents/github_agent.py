
"""
GitHub Agent Nível 4 - Agente avançado para automação GitHub
Integrado ao sistema ROKO com suporte completo HMP
"""

import logging
import json
import sqlite3
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logging.warning("PyGithub não disponível - GitHub Agent funcionará em modo simulado")

class GitHubAgent(BaseAgent):
    """
    GitHub Agent Nível 4 - Automação completa do GitHub com IA.
    
    Capacidades:
    - Criação automática de repositórios
    - Gerenciamento de branches e issues
    - Análise de código via IA
    - Automação de workflows
    - Integração com pipeline CI/CD
    - Memória persistente de ações
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.github_token = os.environ.get('GITHUB_API_KEY')
        self.db_path = "ROKO/github_agent_memory.db"
        
        # Inicializar GitHub API
        if GITHUB_AVAILABLE and self.github_token:
            self.github = Github(self.github_token)
            self.github_user = self.github.get_user()
            logging.info("✅ GitHub Agent conectado com sucesso")
        else:
            self.github = None
            self.github_user = None
            logging.warning("⚠️ GitHub Agent em modo simulado - configure GITHUB_TOKEN")

        # Inicializar base de dados local
        self._init_database()
        
        # Configurar sistema de planejamento avançado
        self.planning_system = "gpt-4o-mini"  # Modelo para planejamento multi-passos

    def _init_database(self):
        """Inicializa base de dados SQLite para memória persistente."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Criar tabelas
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS github_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    repo TEXT,
                    branch TEXT,
                    issue_number INTEGER,
                    pull_request_number INTEGER,
                    file_path TEXT,
                    details TEXT,
                    result TEXT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    success INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS repo_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_name TEXT NOT NULL,
                    language TEXT,
                    framework TEXT,
                    complexity_score INTEGER,
                    last_analysis TEXT,
                    suggestions TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    trigger_event TEXT,
                    condition_pattern TEXT,
                    action_sequence TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );
            """)
            
            self.conn.commit()
            logging.info("✅ GitHub Agent database inicializada")
            
        except Exception as e:
            logging.error(f"❌ Erro ao inicializar database GitHub Agent: {e}")
            self.conn = None

    def save_action_memory(self, action: str, **kwargs):
        """Salva ação na memória persistente."""
        if not self.conn:
            return

        try:
            timestamp = datetime.now().isoformat()
            self.conn.execute("""
                INSERT INTO github_history 
                (action, repo, branch, issue_number, pull_request_number, file_path, details, result, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action,
                kwargs.get('repo', ''),
                kwargs.get('branch', ''),
                kwargs.get('issue_number'),
                kwargs.get('pull_request_number'),
                kwargs.get('file_path', ''),
                kwargs.get('details', ''),
                kwargs.get('result', ''),
                timestamp,
                kwargs.get('success', 1)
            ))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Erro ao salvar memória: {e}")

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Recupera histórico recente de ações."""
        if not self.conn:
            return []

        try:
            cursor = self.conn.execute("""
                SELECT action, repo, branch, details, result, timestamp, success
                FROM github_history 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'action': row[0],
                    'repo': row[1],
                    'branch': row[2],
                    'details': row[3],
                    'result': row[4],
                    'timestamp': row[5],
                    'success': bool(row[6])
                })
            return results
        except Exception as e:
            logging.error(f"Erro ao recuperar histórico: {e}")
            return []

    def ai_planning_system(self, user_command: str) -> List[Dict[str, Any]]:
        """
        Sistema de planejamento avançado usando IA para converter comandos em ações GitHub.
        """
        planning_prompt = f"""
Você é o núcleo de planejamento do GitHub Agent Nível 4. Converta o comando do usuário em uma sequência de ações GitHub detalhadas.

COMANDO: {user_command}

RETORNE UM JSON com esta estrutura exata:
[
    {{
        "action": "criar_repo | criar_branch | criar_issue | criar_pr | listar_repos | analisar_repo | automatizar_workflow | clonar_repo | fazer_commit | merge_pr | fechar_issue | criar_release",
        "params": {{
            "repo_name": "nome_do_repo",
            "description": "descrição",
            "branch_name": "nome_da_branch", 
            "title": "título",
            "body": "corpo/descrição",
            "file_path": "caminho_do_arquivo",
            "content": "conteúdo_do_arquivo",
            "base_branch": "branch_base",
            "target_branch": "branch_destino",
            "tag_name": "v1.0.0",
            "private": false
        }},
        "priority": 1,
        "description": "Descrição da ação"
    }}
]

REGRAS:
- Analise o contexto e intenção do usuário
- Crie ações sequenciais lógicas
- Priorize ações (1=alta, 2=média, 3=baixa)
- Seja específico nos parâmetros
- Considere dependências entre ações
"""

        try:
            response = self.client.chat.completions.create(
                model=self.planning_system,
                messages=[
                    {"role": "system", "content": "Você é um especialista em automação GitHub que converte linguagem natural em ações estruturadas."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.1
            )

            content = response.choices[0].message.content
            
            # Extrair JSON da resposta
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    actions = json.loads(json_match.group())
                    logging.info(f"✅ Planejamento AI: {len(actions)} ações geradas")
                    return actions
                except json.JSONDecodeError as e:
                    logging.error(f"Erro ao parsear JSON do planejamento: {e}")
            
            return []
        except Exception as e:
            logging.error(f"Erro no sistema de planejamento AI: {e}")
            return []

    def execute_github_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma ação específica do GitHub."""
        if not self.github:
            return self._simulate_action(action, params)

        try:
            if action == "criar_repo":
                return self._criar_repositorio(params)
            elif action == "criar_branch":
                return self._criar_branch(params)
            elif action == "criar_issue":
                return self._criar_issue(params)
            elif action == "criar_pr":
                return self._criar_pull_request(params)
            elif action == "listar_repos":
                return self._listar_repositorios(params)
            elif action == "analisar_repo":
                return self._analisar_repositorio(params)
            elif action == "automatizar_workflow":
                return self._automatizar_workflow(params)
            elif action == "clonar_repo":
                return self._clonar_repositorio(params)
            elif action == "fazer_commit":
                return self._fazer_commit(params)
            elif action == "merge_pr":
                return self._merge_pull_request(params)
            elif action == "fechar_issue":
                return self._fechar_issue(params)
            elif action == "criar_release":
                return self._criar_release(params)
            else:
                return {"success": False, "error": f"Ação desconhecida: {action}"}

        except Exception as e:
            error_msg = f"Erro ao executar {action}: {str(e)}"
            logging.error(error_msg)
            self.save_action_memory(action, **params, result=error_msg, success=0)
            return {"success": False, "error": error_msg}

    def _criar_repositorio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo repositório."""
        repo_name = params.get('repo_name', 'novo-repo')
        description = params.get('description', 'Repositório criado pelo ROKO GitHub Agent')
        private = params.get('private', False)

        try:
            repo = self.github_user.create_repo(
                name=repo_name,
                description=description,
                private=private
            )
            
            result = f"Repositório '{repo.full_name}' criado com sucesso!"
            self.save_action_memory("criar_repo", repo=repo_name, details=description, result=result)
            
            return {
                "success": True,
                "result": result,
                "repo_url": repo.html_url,
                "repo_name": repo.full_name
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _criar_branch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova branch."""
        repo_name = params.get('repo_name')
        branch_name = params.get('branch_name', 'nova-feature')
        base_branch = params.get('base_branch', 'main')

        try:
            repo = self.github_user.get_repo(repo_name)
            source_branch = repo.get_branch(base_branch)
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source_branch.commit.sha
            )
            
            result = f"Branch '{branch_name}' criada com sucesso no repositório '{repo_name}'"
            self.save_action_memory("criar_branch", repo=repo_name, branch=branch_name, result=result)
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _criar_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova issue."""
        repo_name = params.get('repo_name')
        title = params.get('title', 'Nova Issue')
        body = params.get('body', 'Issue criada pelo ROKO GitHub Agent')

        try:
            repo = self.github_user.get_repo(repo_name)
            issue = repo.create_issue(title=title, body=body)
            
            result = f"Issue #{issue.number} '{issue.title}' criada no repositório '{repo_name}'"
            self.save_action_memory("criar_issue", repo=repo_name, issue_number=issue.number, details=title, result=result)
            
            return {
                "success": True,
                "result": result,
                "issue_number": issue.number,
                "issue_url": issue.html_url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _listar_repositorios(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lista repositórios do usuário."""
        try:
            repos = []
            for repo in self.github_user.get_repos():
                repos.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "url": repo.html_url
                })
            
            result = f"Encontrados {len(repos)} repositórios"
            self.save_action_memory("listar_repos", details=result, result=json.dumps(repos[:5]))  # Salvar apenas primeiros 5
            
            return {"success": True, "result": result, "repositories": repos}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analisar_repositorio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa um repositório usando IA."""
        repo_name = params.get('repo_name')
        
        try:
            repo = self.github_user.get_repo(repo_name)
            
            # Coletar informações do repositório
            repo_info = {
                "name": repo.name,
                "description": repo.description,
                "language": repo.language,
                "size": repo.size,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "topics": repo.get_topics()
            }

            # Analisar com IA
            analysis_prompt = f"""
Analise este repositório GitHub e forneça insights:

DADOS DO REPOSITÓRIO:
{json.dumps(repo_info, indent=2)}

Forneça:
1. Avaliação da qualidade (1-10)
2. Linguagem/framework principal
3. Complexidade estimada (baixa/média/alta)
4. Sugestões de melhorias
5. Pontos fortes identificados

Responda em formato estruturado.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )

            analysis = response.choices[0].message.content
            
            # Salvar análise na base de dados
            if self.conn:
                self.conn.execute("""
                    INSERT INTO repo_analysis (repo_name, language, complexity_score, suggestions, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (repo_name, repo.language, 7, analysis, datetime.now().isoformat()))
                self.conn.commit()

            result = f"Análise completa do repositório '{repo_name}' concluída"
            self.save_action_memory("analisar_repo", repo=repo_name, result=result, details=analysis[:200])
            
            return {
                "success": True, 
                "result": result,
                "analysis": analysis,
                "repo_info": repo_info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _simulate_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simula ações quando GitHub API não está disponível."""
        simulation_results = {
            "criar_repo": f"✅ Simulação: Repositório '{params.get('repo_name', 'test-repo')}' criado",
            "criar_branch": f"✅ Simulação: Branch '{params.get('branch_name', 'feature-branch')}' criada",
            "criar_issue": f"✅ Simulação: Issue '{params.get('title', 'Test Issue')}' criada",
            "listar_repos": "✅ Simulação: Lista de repositórios gerada",
            "analisar_repo": f"✅ Simulação: Análise do repositório '{params.get('repo_name', 'test-repo')}' concluída"
        }

        result = simulation_results.get(action, f"✅ Simulação: Ação '{action}' executada")
        self.save_action_memory(action, **params, result=result)
        
        return {"success": True, "result": result, "simulated": True}

    def process_github_request(self, user_prompt: str) -> str:
        """Processa solicitação do usuário para automação GitHub."""
        logging.info(f"GitHub Agent processando: {user_prompt}")

        try:
            # 1. Planejamento AI
            actions = self.ai_planning_system(user_prompt)
            
            if not actions:
                return "❌ Não foi possível gerar plano de ações para sua solicitação GitHub."

            # 2. Executar ações sequencialmente
            results = []
            for action_data in actions:
                action = action_data.get('action')
                params = action_data.get('params', {})
                priority = action_data.get('priority', 2)
                description = action_data.get('description', action)

                logging.info(f"🔧 Executando: {description}")
                
                action_result = self.execute_github_action(action, params)
                results.append({
                    "action": action,
                    "description": description,
                    "result": action_result,
                    "priority": priority
                })

            # 3. Gerar resposta final
            return self._generate_execution_summary(user_prompt, results)

        except Exception as e:
            error_msg = f"❌ Erro no GitHub Agent: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def _generate_execution_summary(self, original_request: str, results: List[Dict]) -> str:
        """Gera resumo executivo da execução."""
        successful_actions = [r for r in results if r['result'].get('success', False)]
        failed_actions = [r for r in results if not r['result'].get('success', False)]

        summary = f"## 🚀 Execução GitHub Agent Concluída\n\n"
        summary += f"**Solicitação:** {original_request}\n\n"
        
        if successful_actions:
            summary += f"### ✅ Ações Executadas com Sucesso ({len(successful_actions)}):\n"
            for action in successful_actions:
                summary += f"- **{action['description']}**: {action['result'].get('result', 'Concluído')}\n"
        
        if failed_actions:
            summary += f"\n### ❌ Ações com Erro ({len(failed_actions)}):\n"
            for action in failed_actions:
                summary += f"- **{action['description']}**: {action['result'].get('error', 'Erro desconhecido')}\n"

        # Adicionar histórico recente
        recent_history = self.get_recent_history(5)
        if recent_history:
            summary += f"\n### 📋 Histórico Recente:\n"
            for history in recent_history:
                status_emoji = "✅" if history['success'] else "❌"
                summary += f"- {status_emoji} {history['action']} ({history['timestamp'][:19]})\n"

        return summary

    def get_github_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do agente GitHub."""
        if not self.conn:
            return {"error": "Database não disponível"}

        try:
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_actions,
                    SUM(success) as successful_actions,
                    COUNT(DISTINCT repo) as repos_touched,
                    COUNT(DISTINCT DATE(timestamp)) as active_days
                FROM github_history
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            
            stats = cursor.fetchone()
            
            return {
                "total_actions_30d": stats[0] if stats[0] else 0,
                "successful_actions_30d": stats[1] if stats[1] else 0,
                "repos_touched_30d": stats[2] if stats[2] else 0,
                "active_days_30d": stats[3] if stats[3] else 0,
                "success_rate": f"{(stats[1]/stats[0]*100):.1f}%" if stats[0] > 0 else "0%",
                "github_connected": bool(self.github),
                "database_connected": True
            }
        except Exception as e:
            logging.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}
