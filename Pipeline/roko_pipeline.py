"""
Módulo do Pipeline Autônomo ROKO.

Este é o orquestrador principal do sistema. A classe ROKOPipeline gere
o ciclo de vida de um pedido do utilizador, desde o planeamento até à
execução e correção de erros, utilizando os agentes e a memória.
"""

import os
import logging
import json
import time
import uuid
import numpy as np
from typing import Dict, Any, List, Optional

# Importa as classes dos módulos organizados  
from Memory import CognitiveMemory, MemoryUtils
from Agents import (
    BaseAgent, ROKOAgent, PlannerAgent, ErrorFixAgent, 
    CheckInAgent, WebAgent, ShellAgent, CodeAgent, DependencyAgent, DataProcessingAgent
)
from Pipeline.exceptions import RokoNexusError, APIKeyNotFoundError

# Integração com AutoFlux modularizado
try:
    from AutoFlux import AutoFluxROKO, ROKODataProcessor
    # Teste de inicialização para verificar parâmetros
    test_autoflux = AutoFluxROKO(max_workers=2, memory_safe=True)
    logging.info(f"✅ AutoFlux disponível e testado no pipeline - Workers: {test_autoflux.max_workers}")
    AUTOFLUX_AVAILABLE = True
    del test_autoflux  # Limpar teste
except ImportError:
    AUTOFLUX_AVAILABLE = False
    logging.warning("⚠️ AutoFlux não disponível no pipeline")
except Exception as e:
    AUTOFLUX_AVAILABLE = False
    logging.error(f"❌ Erro na inicialização do AutoFlux: {e}")

# Configuração de logging detalhado para agentes
import os

# Criar diretório de logs se não existir
logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Caminho correto para o arquivo de log
log_file_path = os.path.join(logs_dir, 'roko_agents.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Criar logger específico para agentes
agent_logger = logging.getLogger('ROKO.AGENTS')
agent_logger.setLevel(logging.DEBUG)

class ExecutionAgent:
    """
    Agente Executor que opera as ferramentas (Web, Shell, Code, Dependencies).
    Funciona como a "mão" do sistema, executando ações concretas.
    """
    def __init__(self, api_key: str):
        self.tools = {
            "web_search": WebAgent(api_key),
            "shell": ShellAgent(api_key),
            "python_code": CodeAgent(api_key),
            "data_processing": DataProcessingAgent(api_key)
        }
        self.dependency_agent = DependencyAgent(api_key)
        self.workspace_path = None

    def run_step(self, step: Dict[str, str]) -> Dict[str, Any]:
        tool_name = step.get("tool")
        query = step.get("query")

        if not tool_name or not query:
            return {"result": None, "error": "Passo do plano inválido: 'tool' ou 'query' em falta."}

        if tool_name not in self.tools:
            return {"result": None, "error": f"Ferramenta '{tool_name}' desconhecida."}

        tool = self.tools[tool_name]
        result = tool.execute(query)

        # Se houve erro de módulo em falta, tentar instalar automaticamente
        if result["error"] and "No module named" in result["error"]:
            logging.info("🔧 Erro de módulo detectado. A tentar instalação automática...")
            missing_packages = self.dependency_agent.detect_missing_packages(result["error"])

            if missing_packages:
                for package in missing_packages:
                    install_result = self.dependency_agent.install_package(package)
                    if install_result["error"] is None:
                        logging.info(f"✅ Pacote '{package}' instalado! A tentar executar novamente...")
                        # Tentar executar o código novamente após instalação
                        result = tool.execute(query)
                        if result["error"] is None:
                            break
                    else:
                        logging.error(f"❌ Falha na instalação de '{package}': {install_result['error']}")

        return result

    def set_workspace(self, workspace_path: Optional[str], artifacts_dir: Optional[str] = None):
        self.workspace_path = workspace_path
        for tool in self.tools.values():
            if hasattr(tool, 'set_workspace'):
                try:
                    tool.set_workspace(workspace_path, artifacts_dir=artifacts_dir)
                except TypeError:
                    # Algumas ferramentas podem aceitar apenas o caminho
                    tool.set_workspace(workspace_path)

        if hasattr(self.dependency_agent, 'set_workspace'):
            try:
                self.dependency_agent.set_workspace(workspace_path)
            except TypeError:
                pass

class OrchestratorAgent:
    """
    Agente Orquestrador que coordena o planeamento, execução e correção.
    """
    def __init__(self, api_key: str, max_correction_attempts: int = 6):
        self.api_key = api_key
        self.base_agent = BaseAgent(api_key)
        self.planner = PlannerAgent(api_key)
        self.executor = ExecutionAgent(api_key)
        self.fixer = ErrorFixAgent(api_key)
        self.checker = CheckInAgent(api_key)
        self.max_correction_attempts = max_correction_attempts

    def set_workspace(self, workspace_path: Optional[str], artifacts_dir: Optional[str] = None):
        if hasattr(self.executor, 'set_workspace'):
            self.executor.set_workspace(workspace_path, artifacts_dir=artifacts_dir)

        for agent in (self.base_agent, self.planner, self.fixer, self.checker):
            if hasattr(agent, 'set_workspace'):
                try:
                    agent.set_workspace(workspace_path, artifacts_dir=artifacts_dir)
                except TypeError:
                    agent.set_workspace(workspace_path)

    def orchestrate(self, user_prompt: str, context_summary: str, user_id: int = None) -> Dict[str, Any]:
        """Orquestra o processo de planeamento e execução."""
        logging.info(f"OrchestratorAgent iniciando orquestração para user_id: {user_id}")

        # Criar plano
        plan = self.planner.create_plan(user_prompt, context_summary)

        if not plan:
            return {
                "plan": [],
                "final_response": "Plano vazio - conversação direta necessária",
                "execution_log": ["Plano vazio gerado pelo planejador"]
            }

        # Executar pipeline
        final_response, execution_log = self._execute_pipeline(plan, user_prompt, user_id=user_id)

        return {
            "plan": plan,
            "final_response": final_response,
            "execution_log": execution_log
        }

    def orchestrate_stream(self, user_prompt: str, context_summary: str, user_id: int = None):
        """Versão em streaming que emite eventos de plano e passos durante a execução."""
        logging.info(f"OrchestratorAgent (stream) iniciando para user_id: {user_id}")

        plan = self.planner.create_plan(user_prompt, context_summary)
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        title = user_prompt.strip()[:120] or "Plano de Execução"
        timestamp = time.time()

        if not plan:
            yield {
                'type': 'plan',
                'plan_id': plan_id,
                'title': title,
                'created_at': timestamp,
                'status': 'skipped',
                'steps': [],
                'total_steps': 0
            }
            yield {
                'type': 'plan_completed',
                'plan_id': plan_id,
                'status': 'skipped',
                'summary': 'Plano não necessário para esta solicitação',
                'execution_log': [],
                'total_steps': 0,
                'completed_steps': 0
            }
            return {
                'plan': [],
                'plan_id': plan_id,
                'final_response': "Plano vazio - conversação direta necessária",
                'execution_log': ["Plano vazio gerado pelo planejador"],
                'completed_steps': 0,
                'status': 'skipped'
            }

        steps_payload = []
        for index, step in enumerate(plan):
            step_summary = step.get('description') or step.get('summary') or step.get('goal') or step.get('query', '')
            step_summary = (step_summary or '').strip()
            if len(step_summary) > 160:
                step_summary = f"{step_summary[:157]}..."

            steps_payload.append({
                'id': step.get('id') or f"step_{index + 1}",
                'index': index,
                'tool': step.get('tool'),
                'query': step.get('query'),
                'summary': step_summary
            })

        yield {
            'type': 'plan',
            'plan_id': plan_id,
            'title': title,
            'created_at': timestamp,
            'status': 'in_progress',
            'steps': steps_payload,
            'total_steps': len(steps_payload)
        }

        final_response, execution_log, completed_steps = yield from self._execute_pipeline_stream(
            plan,
            user_prompt=user_prompt,
            user_id=user_id,
            plan_id=plan_id
        )

        status = 'completed'
        if isinstance(final_response, str) and final_response.lower().startswith('falha'):
            status = 'failed'

        yield {
            'type': 'plan_completed',
            'plan_id': plan_id,
            'status': status,
            'summary': self._summarize_result(final_response),
            'execution_log': execution_log,
            'total_steps': len(plan),
            'completed_steps': completed_steps
        }

        return {
            'plan': plan,
            'plan_id': plan_id,
            'final_response': final_response,
            'execution_log': execution_log,
            'completed_steps': completed_steps,
            'status': status
        }

    def _summarize_result(self, result: Any) -> str:
        """Gera um resumo compacto para exibição no quadro de tarefas."""
        if result is None:
            return 'Sem dados disponíveis.'

        try:
            if isinstance(result, str):
                snippet = result.strip()
                return snippet if len(snippet) <= 180 else f"{snippet[:177]}..."

            if isinstance(result, dict):
                items = list(result.items())[:3]
                formatted = ', '.join(f"{k}: {v}" for k, v in items)
                suffix = ' …' if len(result) > 3 else ''
                return f"{{{formatted}{suffix}}}"

            if isinstance(result, (list, tuple, set)):
                seq = list(result)
                excerpt = ', '.join(map(str, seq[:5]))
                if len(seq) > 5:
                    excerpt += ', …'
                return f"[{excerpt}]"

            return str(result)
        except Exception as error:
            logging.debug(f"Falha ao sintetizar resultado ({error}); convertendo para string.")
            return str(result)

    def _execute_pipeline(self, plan: List[Dict[str, str]], user_prompt: str = "", user_id: int = None) -> tuple:
        """Executa os passos do plano com lógica avançada de correção."""
        execution_log = []
        step_results = []
        previous_step_result = ""

        for i, step in enumerate(plan):
            step_log_prefix = f"Passo {i+1}/{len(plan)} [{step['tool']}]"

            # Substituir placeholder pelo resultado do passo anterior
            if 'previous_step_result' in step['query']:
                step['query'] = step['query'].replace('previous_step_result', str(previous_step_result))

            current_step = step
            error_history = []

            # Tentar executar o passo com user_id se disponível e relevante
            query_with_user_id = current_step.get("query", "")
            if user_id is not None and "user_id" not in query_with_user_id:
                 # Adicionar user_id se a ferramenta suportar ou se for uma consulta de banco de dados genérica
                if "db." in current_step.get("tool", "") or "query" in current_step.get("tool", ""):
                    query_with_user_id += f" --user_id={user_id}" # Exemplo de como adicionar, pode variar

            current_step['query'] = query_with_user_id

            # Tenta executar o passo
            log_msg = f"{step_log_prefix} (Tentativa inicial): a executar '{current_step['query'][:100]}...'"
            logging.info(log_msg)
            execution_log.append(log_msg)

            result = self.executor.run_step(current_step)

            if result["error"] is None:
                # Verificar se objetivo foi alcançado
                verification = self.checker.verify_step_completion(step, result["result"], user_prompt)

                if verification["objective_achieved"]:
                    log_msg = f"{step_log_prefix}: ✅ Objetivo alcançado! {verification['reason']}"
                    logging.info(log_msg)
                    execution_log.append(log_msg)
                    previous_step_result = result["result"]
                    step_results.append(previous_step_result)
                    continue
                else:
                    log_msg = f"{step_log_prefix}: ⚠️ Objetivo NÃO alcançado: {verification['reason']}"
                    logging.warning(log_msg)
                    execution_log.append(log_msg)
                    error_history = [f"Objetivo não alcançado: {verification['reason']}"]

            # Ciclo de correção
            error_history.append(result["error"])
            step_successful = False

            for correction_attempt in range(1, self.max_correction_attempts + 1):
                if correction_attempt == 4:
                    # Análise profunda
                    current_step = self.fixer.deep_analysis_and_fix(current_step, error_history)
                else:
                    current_step = self.fixer.fix_step(current_step, error_history[-1])

                # Tentar executar o passo corrigido com user_id
                query_with_user_id_corrected = current_step.get("query", "")
                if user_id is not None and "user_id" not in query_with_user_id_corrected:
                    if "db." in current_step.get("tool", "") or "query" in current_step.get("tool", ""):
                         query_with_user_id_corrected += f" --user_id={user_id}"
                current_step['query'] = query_with_user_id_corrected

                result = self.executor.run_step(current_step)

                if result["error"] is None:
                    verification = self.checker.verify_step_completion(current_step, result["result"], user_prompt)

                    if verification["objective_achieved"]:
                        log_msg = f"{step_log_prefix}: ✅ Sucesso após {correction_attempt} correções!"
                        logging.info(log_msg)
                        execution_log.append(log_msg)
                        previous_step_result = result["result"]
                        step_results.append(previous_step_result)
                        step_successful = True
                        break
                    else:
                        error_history.append(f"Objetivo não alcançado: {verification['reason']}")
                else:
                    error_history.append(result["error"])

            if not step_successful:
                log_msg = f"{step_log_prefix}: 🚫 Falha após {self.max_correction_attempts} tentativas"
                logging.error(log_msg)
                execution_log.append(log_msg)
                return f"Falha no {step_log_prefix}", execution_log

        final_response = "\n".join(map(str, step_results))
        return final_response if final_response else "Pipeline executado com sucesso", execution_log

    def _execute_pipeline_stream(
        self,
        plan: List[Dict[str, str]],
        user_prompt: str = "",
        user_id: int = None,
        plan_id: Optional[str] = None
    ):
        """Executa o plano emitindo eventos de progresso passo a passo."""

        def _clip(text: Any, limit: int = 280) -> str:
            text_str = str(text) if text is not None else ""
            text_str = text_str.strip()
            return text_str if len(text_str) <= limit else f"{text_str[:limit - 3]}..."

        execution_log = []
        step_results = []
        previous_step_result = ""

        total_steps = len(plan)

        for index, base_step in enumerate(plan):
            step = dict(base_step)
            step_id = step.get('id') or f"step_{index + 1}"
            step_label = step.get('description') or step.get('summary') or step.get('goal') or step.get('query', '')
            step_label = (step_label or '').strip()
            if len(step_label) > 160:
                step_label = f"{step_label[:157]}..."

            tool_display = step.get('tool') or 'passo'
            log_prefix = f"Passo {index + 1}/{total_steps} [{tool_display}]"

            yield {
                'type': 'plan_step_started',
                'plan_id': plan_id,
                'step_id': step_id,
                'index': index,
                'tool': step.get('tool'),
                'label': step_label,
                'query': step.get('query'),
                'message': f"Iniciando {tool_display}",
                'timestamp': time.time()
            }

            if 'previous_step_result' in step.get('query', ''):
                step['query'] = step['query'].replace('previous_step_result', str(previous_step_result))

            current_step = step
            error_history: List[str] = []

            query_with_user_id = current_step.get('query', '')
            if user_id is not None and 'user_id' not in query_with_user_id:
                if 'db.' in current_step.get('tool', '') or 'query' in current_step.get('tool', ''):
                    query_with_user_id += f" --user_id={user_id}"
            current_step['query'] = query_with_user_id

            log_msg = f"{log_prefix} (Tentativa inicial): a executar '{current_step['query'][:100]}...'"
            logging.info(log_msg)
            execution_log.append(log_msg)

            result = self.executor.run_step(current_step)

            if result["error"] is None:
                verification = self.checker.verify_step_completion(current_step, result["result"], user_prompt)

                if verification["objective_achieved"]:
                    log_msg = f"{log_prefix}: ✅ Objetivo alcançado! {verification['reason']}"
                    logging.info(log_msg)
                    execution_log.append(log_msg)
                    previous_step_result = result["result"]
                    step_results.append(previous_step_result)

                    yield {
                        'type': 'plan_step_completed',
                        'plan_id': plan_id,
                        'step_id': step_id,
                        'index': index,
                        'tool': current_step.get('tool'),
                        'result_summary': self._summarize_result(result['result']),
                        'raw_result_excerpt': _clip(result['result'], limit=400),
                        'verification': verification.get('reason'),
                        'timestamp': time.time()
                    }
                    continue

                error_history.append(f"Objetivo não alcançado: {verification['reason']}")
                yield {
                    'type': 'plan_step_retry',
                    'plan_id': plan_id,
                    'step_id': step_id,
                    'index': index,
                    'attempt': 0,
                    'status': 'verification_failed',
                    'message': verification['reason'],
                    'timestamp': time.time()
                }
            else:
                error_history.append(result["error"] or "Erro desconhecido")
                yield {
                    'type': 'plan_step_retry',
                    'plan_id': plan_id,
                    'step_id': step_id,
                    'index': index,
                    'attempt': 0,
                    'status': 'error',
                    'message': _clip(result['error']),
                    'timestamp': time.time()
                }

            step_successful = False

            for correction_attempt in range(1, self.max_correction_attempts + 1):
                if correction_attempt == 4:
                    current_step = self.fixer.deep_analysis_and_fix(current_step, error_history)
                else:
                    current_step = self.fixer.fix_step(current_step, error_history[-1])

                query_corrected = current_step.get('query', '')
                if user_id is not None and 'user_id' not in query_corrected:
                    if 'db.' in current_step.get('tool', '') or 'query' in current_step.get('tool', ''):
                        query_corrected += f" --user_id={user_id}"
                current_step['query'] = query_corrected

                result = self.executor.run_step(current_step)

                if result["error"] is None:
                    verification = self.checker.verify_step_completion(current_step, result["result"], user_prompt)

                    if verification["objective_achieved"]:
                        log_msg = f"{log_prefix}: ✅ Sucesso após {correction_attempt} correções!"
                        logging.info(log_msg)
                        execution_log.append(log_msg)
                        previous_step_result = result["result"]
                        step_results.append(previous_step_result)
                        step_successful = True

                        yield {
                            'type': 'plan_step_retry',
                            'plan_id': plan_id,
                            'step_id': step_id,
                            'index': index,
                            'attempt': correction_attempt,
                            'status': 'success',
                            'message': verification.get('reason'),
                            'timestamp': time.time()
                        }

                        yield {
                            'type': 'plan_step_completed',
                            'plan_id': plan_id,
                            'step_id': step_id,
                            'index': index,
                            'tool': current_step.get('tool'),
                            'result_summary': self._summarize_result(result['result']),
                            'raw_result_excerpt': _clip(result['result'], limit=400),
                            'verification': verification.get('reason'),
                            'timestamp': time.time()
                        }
                        break

                    error_history.append(f"Objetivo não alcançado: {verification['reason']}")
                    yield {
                        'type': 'plan_step_retry',
                        'plan_id': plan_id,
                        'step_id': step_id,
                        'index': index,
                        'attempt': correction_attempt,
                        'status': 'verification_failed',
                        'message': verification['reason'],
                        'timestamp': time.time()
                    }
                else:
                    error_history.append(result["error"] or "Erro desconhecido")
                    yield {
                        'type': 'plan_step_retry',
                        'plan_id': plan_id,
                        'step_id': step_id,
                        'index': index,
                        'attempt': correction_attempt,
                        'status': 'error',
                        'message': _clip(result['error']),
                        'timestamp': time.time()
                    }

            if not step_successful:
                log_msg = f"{log_prefix}: 🚫 Falha após {self.max_correction_attempts} tentativas"
                logging.error(log_msg)
                execution_log.append(log_msg)

                yield {
                    'type': 'plan_step_failed',
                    'plan_id': plan_id,
                    'step_id': step_id,
                    'index': index,
                    'tool': current_step.get('tool'),
                    'message': error_history[-1] if error_history else 'Falha desconhecida',
                    'attempts': self.max_correction_attempts,
                    'timestamp': time.time()
                }

                failure_message = error_history[-1] if error_history else 'Falha desconhecida'
                return (
                    f"Falha no Passo {index + 1}/{total_steps} [{tool_display}] - {failure_message}",
                    execution_log,
                    len(step_results)
                )

        final_response = "\n".join(map(str, step_results))
        summary = final_response if final_response else "Pipeline executado com sucesso"
        return summary, execution_log, len(step_results)

class ROKOPipeline:
    """Pipeline principal do sistema ROKO que coordena todo o fluxo de processamento usando HMP."""

    def __init__(self):
        logging.info("🚀 Inicializando ROKO Pipeline com suporte HMP...")

        # Verificar chave da API do Replit
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logging.warning("⚠️ OPENAI_API_KEY não encontrada - sistema funcionará em modo básico")
            logging.info("💡 Configure OPENAI_API_KEY nos Secrets do Replit para funcionalidade completa")
            self.api_key = None

        # Inicializar HMP com lazy loading para evitar dependências circulares
        try:
            # Usar lazy loading para evitar imports circulares
            self.hmp_interpreter = None
            self.hmp_enabled = False

            # Tentar importar e inicializar HMP
            self._initialize_hmp()

        except Exception as e:
            self.hmp_interpreter = None
            self.hmp_enabled = False
            logging.info(f"ℹ️ HMP não pôde ser inicializado, continuando em modo tradicional: {e}")

        # Continuar inicialização independente do HMP
        logging.info(f"🔧 Pipeline continuando: HMP {'habilitado' if self.hmp_enabled else 'desabilitado'}")

    def _initialize_hmp(self):
        """Inicializa o sistema HMP com lazy loading."""
        try:
            # Importar apenas quando necessário
            from HMP.hmp_interpreter import HMPInterpreter
            self.hmp_interpreter = HMPInterpreter()

            # Tentar registrar funções se disponível
            try:
                from HMP.hmp_tools import HMPTools
                if hasattr(HMPTools, 'register_hmp_functions'):
                    registration_success = HMPTools.register_hmp_functions(self.hmp_interpreter)
                    if registration_success:
                        self.hmp_enabled = True
                        logging.info("✅ Sistema HMP inicializado e funções registradas com sucesso")
                    else:
                        self.hmp_enabled = False
                        logging.info("ℹ️ HMP inicializado mas falha no registro de funções, usando modo tradicional")
                else:
                    self.hmp_enabled = True
                    logging.info("✅ Sistema HMP inicializado (sem registro de funções adicionais)")
            except ImportError as e:
                self.hmp_enabled = True
                logging.info(f"✅ HMP inicializado sem ferramentas extras: {e}")

        except ImportError as e:
            self.hmp_interpreter = None
            self.hmp_enabled = False
            logging.info(f"ℹ️ HMP não disponível, continuando em modo tradicional: {e}")
        except Exception as e:
            self.hmp_interpreter = None
            self.hmp_enabled = False
            logging.info(f"ℹ️ Erro na inicialização HMP, modo tradicional ativado: {e}")

        # Inicializar sistema de memória cognitiva
        self.cognitive_memory = CognitiveMemory()

        # Sistemas ultra-otimizados
        try:
            from Memory.ultra_cache_system import ultra_cache
            from HMP.intelligent_load_balancer import intelligent_balancer
            from HMP.ultra_performance_monitor import ultra_monitor
            self.ultra_cache = ultra_cache
            self.load_balancer = intelligent_balancer
            self.performance_monitor = ultra_monitor
            logging.info("🚀 Sistemas ultra-otimizados carregados com sucesso")
        except ImportError as e:
            logging.warning(f"⚠️ Sistemas ultra-otimizados não disponíveis: {e}")
            self.ultra_cache = None
            self.load_balancer = None
            self.performance_monitor = None

        self.base_agent = BaseAgent(self.api_key)  # Para embeddings
        self.roko_agent = ROKOAgent(self.api_key)  # Agente principal ROKO
        self.orchestrator = OrchestratorAgent(self.api_key, max_correction_attempts=6)
        self.default_workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace_projects'))
        self.default_artifacts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ARTEFATOS'))
        os.makedirs(self.default_workspace_root, exist_ok=True)
        os.makedirs(self.default_artifacts_root, exist_ok=True)
        self.current_workspace_path = self.default_workspace_root
        self.current_artifacts_dir = self.default_artifacts_root

    def _get_embedding(self, text: str) -> np.ndarray:
        try:
            response = self.base_agent.client.embeddings.create(input=text, model="text-embedding-3-large")
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            raise RokoNexusError(f"Falha na geração de embedding: {e}") from e

    def _prepare_workspace(
        self,
        workspace_path: Optional[str],
        artifact_prefix: Optional[str],
        workspace_label: Optional[str],
        user_id: Optional[int]
    ) -> tuple[str, str]:
        resolved_workspace = os.path.abspath(workspace_path) if workspace_path else self.default_workspace_root
        os.makedirs(resolved_workspace, exist_ok=True)

        label = None
        if workspace_label:
            label = workspace_label.strip().replace('..', '').replace('/', '_')
        if not label:
            label = os.path.basename(resolved_workspace) or (f"user_{user_id}" if user_id else 'workspace')

        sanitized_prefix = None
        if artifact_prefix:
            sanitized_prefix = artifact_prefix.replace('..', '').replace('/', '').rstrip('_')
        artifacts_dir = self.default_artifacts_root
        if sanitized_prefix:
            artifacts_dir = os.path.join(self.default_artifacts_root, sanitized_prefix)
        elif label:
            artifacts_dir = os.path.join(self.default_artifacts_root, label)

        artifacts_dir = os.path.abspath(artifacts_dir)
        if not artifacts_dir.startswith(self.default_artifacts_root):
            artifacts_dir = self.default_artifacts_root

        os.makedirs(artifacts_dir, exist_ok=True)

        self.current_workspace_path = resolved_workspace
        self.current_artifacts_dir = artifacts_dir

        self.orchestrator.set_workspace(resolved_workspace, artifacts_dir=artifacts_dir)

        if hasattr(self.roko_agent, 'set_artifact_directory'):
            self.roko_agent.set_artifact_directory(artifacts_dir)
        if hasattr(self.roko_agent, 'set_workspace'):
            try:
                self.roko_agent.set_workspace(resolved_workspace, artifacts_dir=artifacts_dir)
            except TypeError:
                self.roko_agent.set_workspace(resolved_workspace)

        return resolved_workspace, artifacts_dir

    def process_request_stream(
        self,
        user_input: str,
        user_id: int = None,
        workspace_path: Optional[str] = None,
        artifact_prefix: Optional[str] = None,
        workspace_label: Optional[str] = None
    ):
        """Processa requisição com streaming em tempo real."""
        # Gerar identificador único para esta requisição e controlar concorrência
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        # Controle rigoroso contra processamento duplo
        processing_id = f"proc_{hash(user_input)}_{int(time.time())}"

        workspace_path_resolved, artifacts_dir = self._prepare_workspace(workspace_path, artifact_prefix, workspace_label, user_id)

        # Verificar se já está processando esta requisição
        if hasattr(self, '_active_processing') and processing_id in self._active_processing:
            logging.warning(f"⚠️ Processamento duplicado bloqueado: {processing_id}")
            return

        # Marcar como em processamento
        if not hasattr(self, '_active_processing'):
            self._active_processing = set()
        self._active_processing.add(processing_id)

        print("="*80)
        print(f"🎯 INICIANDO PROCESSAMENTO ROKO - ID: {processing_id} - UserID: {user_id}")
        print(f"📝 PROMPT: {user_input}")
        print("="*80)

        logging.info(f"🎯 Iniciando processamento único: {processing_id} para user_id: {user_id}")
        agent_logger.info(f"PIPELINE: Iniciando processamento para prompt: {user_input[:100]}... para user_id: {user_id}")

        try:
            # Gerar embedding uma única vez
            embedding = self._get_embedding(user_input)
            yield {'type': 'thinking', 'message': 'Consultando memória cognitiva...'}

            # Buscar contexto relevante
            # TODO: Adicionar user_id à consulta de memória cognitiva
            context_items = self.cognitive_memory.retrieve_context(embedding)
            context_summary = "\n".join([f"- {item['user_prompt']}" for item in context_items])
            yield {'type': 'thinking', 'message': 'Analisando contexto e criando plano...'}

            # Obter últimas conversas ANTES do orquestrador (aumentado para melhor contexto)
            # TODO: Filtrar últimas conversas por user_id
            last_chats = self.cognitive_memory.get_last_chats(5)

            # Passar para o orquestrador com streaming do plano
            orchestrator_stream = self.orchestrator.orchestrate_stream(
                user_input,
                context_summary,
                user_id=user_id
            )

            orchestrator_data = None

            try:
                while True:
                    event = next(orchestrator_stream)
                    if isinstance(event, dict):
                        event.setdefault('timestamp', time.time())
                        event['request_id'] = request_id
                        yield event
            except StopIteration as stop_info:
                orchestrator_data = stop_info.value
            except Exception as stream_error:
                logging.error(f"Erro durante streaming do orquestrador: {stream_error}")
                orchestrator_data = {
                    'plan': [],
                    'final_response': "Plano vazio - conversação direta necessária",
                    'execution_log': [f"Erro no streaming do plano: {stream_error}"],
                    'plan_id': None
                }

            if orchestrator_data is None:
                orchestrator_data = {
                    'plan': [],
                    'final_response': "Plano vazio - conversação direta necessária",
                    'execution_log': ["Orquestração sem dados"],
                    'plan_id': None
                }

            yield {'type': 'thinking', 'message': 'Gerando resposta final...'}

            # Gerar resposta final com ROKO - ÚNICA CHAMADA
            try:
                if not orchestrator_data.get("plan") or len(orchestrator_data.get("plan", [])) == 0:
                    # Conversação simples - ROKO responde diretamente
                    print(f"💬 MODO: Conversação simples detectada")
                    print(f"🤖 AGENTE ATIVO: ROKO Agent (Resposta Direta)")
                    logging.info(f"📝 {processing_id}: Conversação simples detectada")
                    agent_logger.info("ROKO_AGENT: Gerando resposta simples")

                    final_response = self.roko_agent.generate_simple_response(user_input, last_chats, workspace_path=workspace_path_resolved, artifacts_dir=artifacts_dir)
                    execution_log = ["ROKO: Resposta conversacional direta"]

                    print(f"✅ ROKO Agent concluído")
                else:
                    # Usar orquestrador tradicional como fallback
                    print(f"⚙️ MODO: Orquestração completa")
                    print(f"📋 PLANO: {len(orchestrator_data.get('plan', []))} passos")
                    print(f"🎯 AGENTE ATIVO: Orchestrator + ROKO Agent")

                    agent_logger.info(f"ORCHESTRATOR: Executando plano com {len(orchestrator_data.get('plan', []))} passos")

                    # Log detalhado do plano
                    for i, step in enumerate(orchestrator_data.get('plan', []), 1):
                        print(f"  📌 Passo {i}: {step.get('tool', 'N/A')} - {step.get('query', 'N/A')[:50]}...")
                        agent_logger.debug(f"PLAN_STEP_{i}: Tool={step.get('tool')}, Query={step.get('query')}")

                    # orchestrator_data é preenchido dentro do orchestrate
                    # orchestrator_data = self.orchestrator.orchestrate(user_input, "Contexto da memória") # Chamada duplicada removida

                    agent_logger.info("ROKO_AGENT: Analisando resultado da orquestração")
                    final_response = self.roko_agent.analyze_and_respond(
                        user_input,
                        orchestrator_data,
                        context_items,
                        workspace_path=workspace_path_resolved,
                        artifacts_dir=artifacts_dir
                    )
                    execution_log = orchestrator_data.get("execution_log", [])

                    print(f"✅ Orchestrator + ROKO Agent concluídos")

            except Exception as e:
                logging.error(f"❌ {processing_id}: Erro ao gerar resposta final: {e}")
                final_response = "Desculpe, houve um problema ao processar sua solicitação. Como posso ajudá-lo de outra forma?"
                execution_log = [f"Erro na geração de resposta: {str(e)}"]

            # Verificar se a resposta final não é None
            if final_response is None:
                final_response = "Desculpe, houve um problema ao processar sua solicitação. Como posso ajudá-lo de outra forma?"

            # Verificar e extrair artefatos da resposta final
            artifacts = self._extract_artifacts_from_response(final_response)
            if self._response_needs_artifacts(final_response, user_input):
                logging.info("📊 Resposta indica necessidade de artefatos - extraindo...")
                artifacts_from_files = self._extract_artifacts_from_files()
                artifacts.extend(artifacts_from_files)
            else:
                logging.info("💬 Resposta conversacional simples - sem artefatos necessários")

            # Salvar a interação na memória ANTES de enviar resposta
            try:
                # Categorizar e extrair metadados
                category = self._categorize_interaction(user_input, final_response)
                tags = self._extract_tags(user_input, orchestrator_data)
                importance = self._calculate_importance(user_input, final_response)

                # TODO: Salvar user_id na memória cognitiva
                self.cognitive_memory.save_interaction(
                    interaction_type="pipeline_execution",
                    user_prompt=user_input,
                    agent_thoughts=f"Processamento: {processing_id}, Planos: {len(orchestrator_data.get('plan', []))}, Logs: {len(execution_log)}",
                    agent_response=final_response,
                    embedding=embedding,
                    tags=",".join(tags),
                    category=category,
                    importance_score=importance,
                    user_id=user_id if user_id is not None else 1
                )
                logging.info(f"💾 Interação salva na memória: {category} (importância: {importance})")

            except Exception as e:
                logging.error(f"❌ Erro ao salvar na memória: {e}")

            # Enviar resposta final com artefatos
            yield {
                'type': 'response',
                'message': final_response,
                'artifacts': artifacts,
                'execution_log': execution_log,
                'plan_id': orchestrator_data.get('plan_id'),
                'plan_status': orchestrator_data.get('status'),
                'completed_steps': orchestrator_data.get('completed_steps'),
                'total_steps': len(orchestrator_data.get('plan', [])),
                'plan': orchestrator_data.get('plan', []),
                'workspace_path': workspace_path_resolved,
                'artifacts_dir': artifacts_dir
            }

        except Exception as e:
            logging.error(f"❌ Erro no pipeline {processing_id}: {e}")
            yield {'type': 'error', 'message': f'Erro no processamento: {str(e)}'}
        finally:
            # Limpar controle de processamento
            if hasattr(self, '_active_processing') and processing_id in self._active_processing:
                self._active_processing.remove(processing_id)
                logging.info(f"🧹 Processamento {processing_id} removido da lista ativa")

    def _extract_artifacts_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extrai artefatos HTML da resposta."""
        artifacts = []

        # Padrão para encontrar tags ARTIFACT
        import re
        artifact_pattern = r'<ARTIFACT\s+title="([^"]+)"\s+type="([^"]+)">(.*?)</ARTIFACT>'

        matches = re.findall(artifact_pattern, response, re.DOTALL)

        for title, artifact_type, content in matches:
            artifacts.append({
                'title': title,
                'type': artifact_type,
                'content': content.strip()
            })

        return artifacts

    def _response_needs_artifacts(self, response: str, user_prompt: str) -> bool:
        """Verifica se a resposta realmente precisa de artefatos visuais."""
        # Palavras-chave que indicam necessidade de visualização
        visualization_keywords = [
            'gráfico', 'chart', 'visualiz', 'dashboard', 'tabela', 'dados',
            'clima', 'weather', 'estatística', 'relatório', 'criar', 'gerar',
            'mostrar dados', 'apresentar', 'plotar', 'desenhar'
        ]

        # Verificar no prompt do usuário
        user_needs_viz = any(keyword in user_prompt.lower() for keyword in visualization_keywords)

        # Verificar na resposta se menciona criação de visualização
        response_mentions_viz = any(keyword in response.lower() for keyword in visualization_keywords)

        # Verificar se há tags ARTIFACT explícitas na resposta
        has_artifact_tags = '<ARTIFACT' in response

        # Só extrair artefatos se houver indicação clara
        return user_needs_viz or response_mentions_viz or has_artifact_tags

    def _extract_artifacts_from_files(self) -> List[Dict[str, str]]:
        """Extrai artefatos de arquivos HTML criados."""
        artifacts = []
        artifacts_dir = getattr(self, 'current_artifacts_dir', self.default_artifacts_root)

        try:
            if os.path.exists(artifacts_dir):
                html_files = [f for f in os.listdir(artifacts_dir) if f.endswith('.html')]

                # Pegar apenas o arquivo mais recente para evitar duplicação
                if html_files:
                    html_files.sort(key=lambda x: os.path.getmtime(os.path.join(artifacts_dir, x)), reverse=True)
                    latest_file = html_files[0]  # Apenas o mais recente

                    logging.info(f"📁 Arquivo mais recente encontrado: {latest_file}")

                    file_path = os.path.join(artifacts_dir, latest_file)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Determinar tipo e título
                        artifact_type = self._determine_artifact_type(latest_file)
                        title = self._determine_artifact_title(latest_file)

                        artifacts.append({
                            'title': title,
                            'type': artifact_type,
                            'content': content
                        })

                        logging.info(f"📊 Artefato extraído: {title} ({latest_file})")

                    except Exception as e:
                        logging.error(f"Erro ao ler arquivo {latest_file}: {e}")

        except Exception as e:
            logging.error(f"Erro ao extrair artefatos de arquivos: {e}")

        return artifacts

    def _determine_artifact_type(self, filename):
        """Determina tipo do artefato."""
        if 'chart' in filename or 'graph' in filename:
            return 'chart'
        elif 'dashboard' in filename:
            return 'dashboard'
        elif 'calculator' in filename or 'timer' in filename or 'color' in filename:
            return 'interactive'
        elif 'weather' in filename:
            return 'weather'
        elif 'table' in filename or 'dados' in filename:
            return 'table'
        elif 'gallery' in filename:
            return 'gallery'
        elif 'video' in filename:
            return 'video'
        else:
            return 'visualization'

    def _determine_artifact_title(self, filename):
        """Determina título do artefato baseado no nome do arquivo."""
        type_map = {
            'chart': 'Gráfico Interativo',
            'dashboard': 'Dashboard de Dados',
            'calculator': 'Calculadora',
            'timer': 'Cronômetro',
            'color': 'Seletor de Cores',
            'weather': 'Dados Meteorológicos',
            'table': 'Tabela de Dados',
            'gallery': 'Galeria de Imagens',
            'video': 'Reprodutor de Vídeo',
            'dados': 'Visualização de Dados'
        }

        for key, title in type_map.items():
            if key in filename:
                return title

        return 'Visualização Interativa'

    def _categorize_interaction(self, user_prompt: str, response: str) -> str:
        """Categoriza a interação baseada no conteúdo."""
        prompt_lower = user_prompt.lower()
        response_lower = response.lower()

        if any(word in prompt_lower for word in ['código', 'python', 'programar', 'script']):
            return 'programming'
        elif any(word in prompt_lower for word in ['dados', 'gráfico', 'visualização', 'chart']):
            return 'data_analysis'
        elif any(word in prompt_lower for word in ['pesquisar', 'buscar', 'web', 'internet']):
            return 'research'
        elif any(word in prompt_lower for word in ['arquivo', 'ler', 'analisar arquivo']):
            return 'file_analysis'
        elif any(word in prompt_lower for word in ['olá', 'oi', 'como vai', 'tudo bem']):
            return 'conversation'
        elif any(word in response_lower for word in ['erro', 'falha', 'problema']):
            return 'error_handling'
        else:
            return 'general'

    def _extract_tags(self, user_prompt: str, orchestrator_data: Dict[str, Any]) -> List[str]:
        """Extrai tags relevantes da interação."""
        tags = []
        prompt_lower = user_prompt.lower()

        # Tags baseadas no prompt
        if 'python' in prompt_lower:
            tags.append('python')
        if 'dados' in prompt_lower or 'data' in prompt_lower:
            tags.append('data')
        if 'gráfico' in prompt_lower or 'chart' in prompt_lower:
            tags.append('visualization')
        if 'web' in prompt_lower or 'pesquis' in prompt_lower:
            tags.append('web_search')
        if 'arquivo' in prompt_lower:
            tags.append('file_processing')

        # Tags baseadas no plano de execução
        plan = orchestrator_data.get('plan', [])
        for step in plan:
            tool = step.get('tool', '')
            if tool == 'web_search':
                tags.append('web_search')
            elif tool == 'python_code':
                tags.append('python')
            elif tool == 'shell':
                tags.append('shell')
            elif tool == 'data_processing':
                tags.append('data')

        return list(set(tags))  # Remove duplicatas

    def _calculate_importance(self, user_prompt: str, response: str) -> int:
        """Calcula a importância da interação (1-10)."""
        importance = 5  # Base

        prompt_lower = user_prompt.lower()
        response_lower = response.lower()

        # Aumentar importância baseada em complexidade
        if len(user_prompt) > 100:
            importance += 1
        if len(response) > 500:
            importance += 1

        # Aumentar para tarefas específicas
        if any(word in prompt_lower for word in ['criar', 'gerar', 'implementar']):
            importance += 2
        if any(word in prompt_lower for word in ['analisar', 'processar', 'calcular']):
            importance += 1
        if any(word in response_lower for word in ['artefato', 'visualização', 'gráfico']):
            importance += 2

        # Diminuir para conversas simples
        if any(word in prompt_lower for word in ['olá', 'oi', 'tudo bem']):
            importance -= 2

        # Ajustar para erros
        if 'erro' in response_lower or 'falha' in response_lower:
            importance -= 1

        return max(1, min(10, importance))

    def process_request(
        self,
        user_input: str,
        user_id: int = None,
        workspace_path: Optional[str] = None,
        artifact_prefix: Optional[str] = None,
        workspace_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa um pedido do usuário através do pipeline completo com suporte HMP.
        """
        try:
            logging.info(f"📥 Processando pedido com HMP: {user_input[:100]}... para user_id: {user_id}")

            workspace_path_resolved, artifacts_dir = self._prepare_workspace(workspace_path, artifact_prefix, workspace_label, user_id)

            # Raciocínio HMP para o pipeline
            if self.hmp_enabled:
                pipeline_hmp = self._generate_pipeline_hmp_reasoning(user_input)
                hmp_result = self.hmp_interpreter.execute_hmp(pipeline_hmp)
                logging.info("🧠 Pipeline HMP executado")

            # 1. Recuperar contexto da memória
            embedding = self._get_embedding(user_input)
            # TODO: Filtrar contexto da memória por user_id
            chat_context_items = self.cognitive_memory.retrieve_context(embedding)
            chat_context_summary = "\n".join([f"- {item['user_prompt']}" for item in chat_context_items])

            # Obter últimas conversas ANTES do orquestrador (aumentado para melhor contexto)
            # TODO: Filtrar últimas conversas por user_id
            last_chats = self.cognitive_memory.get_last_chats(5)


            # 2. Verificar se é uma pergunta simples que não precisa do orquestrador
            if self._is_simple_conversation(user_input):
                logging.info("💬 Processando como conversa simples com HMP...")
                response = self.roko_agent.generate_simple_response(user_input, last_chats, workspace_path=workspace_path_resolved, artifacts_dir=artifacts_dir)

                # Salvar na memória
                # TODO: Salvar user_id na memória
                self.cognitive_memory.save_interaction(
                    interaction_type="simple_conversation_hmp",
                    user_prompt=user_input,
                    agent_thoughts="Conversa simples processada com raciocínio HMP",
                    agent_response=response,
                    embedding=embedding,
                    category="general",
                    importance_score=3,
                    user_id=user_id if user_id is not None else 1
                )

                return {
                    "final_response": response,
                    "execution_log": ["💬 Conversa simples processada com HMP"],
                    "processing_type": "simple_hmp",
                    "plan": [],
                    "artifacts": [],
                    "workspace_path": workspace_path_resolved,
                    "artifacts_dir": artifacts_dir
                }

            # 3. Processar com o orquestrador se não for conversa simples
            logging.info("⚙️ Processando com Orquestrador...")

            # Se HMP estiver habilitado e o roteamento for completo, usar HMP para o plano
            if self.hmp_enabled and self._is_complex_request(user_input):
                logging.info("🤖 Usando HMP Router para gerar plano...")
                hmp_plan_request = f"""
                # ROTEAMENTO HMP PARA O PLANO DO ORQUESTRADOR
                SET user_request TO "{user_input}"
                SET context_summary TO "{chat_context_summary}"
                CALL orchestrator.create_execution_plan WITH prompt = user_request, context = context_summary, user_id = {user_id}
                RETURN execution_plan_result
                """
                orchestrator_data = self.hmp_interpreter.execute_hmp(hmp_plan_request)
                execution_log = orchestrator_data.get("execution_log", []) if isinstance(orchestrator_data, dict) else ["HMP Router gerou plano."]

            else:
                 # Usar orquestrador tradicional como fallback ou se HMP não estiver habilitado
                logging.info("⚙️ Usando Orquestrador Tradicional para gerar plano...")
                orchestrator_data = self.orchestrator.orchestrate(user_input, chat_context_summary, user_id=user_id)
                execution_log = orchestrator_data.get("execution_log", [])

            # 4. Gerar resposta final com ROKO
            try:
                final_response = self.roko_agent.analyze_and_respond(
                    user_input,
                    orchestrator_data,
                    chat_context_items,
                    workspace_path=workspace_path_resolved,
                    artifacts_dir=artifacts_dir
                )

                # Se o orquestrador tradicional foi usado, adicionamos seu log
                if "processing_type" not in orchestrator_data or orchestrator_data["processing_type"] != "simple_hmp":
                    execution_log.extend(orchestrator_data.get("execution_log", []))


                if final_response is None:
                    final_response = "Desculpe, houve um problema ao processar sua solicitação. Como posso ajudá-lo de outra forma?"

            except Exception as e:
                logging.error(f"❌ Erro ao gerar resposta final: {e}")
                final_response = "Desculpe, ocorreu um erro interno. Posso tentar ajudá-lo de outra forma?"
                execution_log.append(f"Erro na geração de resposta: {str(e)}")

            # 5. Extrair artefatos e salvar na memória
            artifacts = self._extract_artifacts_from_response(final_response)
            if self._response_needs_artifacts(final_response, user_input):
                artifacts_from_files = self._extract_artifacts_from_files()
                artifacts.extend(artifacts_from_files)

            # Salvar na memória cognitiva
            try:
                category = self._categorize_interaction(user_input, final_response)
                tags = self._extract_tags(user_input, orchestrator_data)
                importance = self._calculate_importance(user_input, final_response)
                # TODO: Salvar user_id na memória cognitiva
                self.cognitive_memory.save_interaction(
                    interaction_type="pipeline_execution_hmp",
                    user_prompt=user_input,
                    agent_thoughts=f"HMP Router used for plan generation: {self.hmp_enabled and self._is_complex_request(user_input)}",
                    agent_response=final_response,
                    embedding=embedding, # Usar embedding já calculado
                    tags=",".join(tags),
                    category=category,
                    importance_score=importance,
                    user_id=user_id if user_id is not None else 1
                )
                logging.info(f"💾 Interação salva na memória (HMP): {category} (importância: {importance})")
            except Exception as e:
                logging.error(f"❌ Erro ao salvar na memória: {e}")

            return {
                "final_response": final_response,
                "execution_log": execution_log,
                "processing_type": "orchestration_hmp" if (self.hmp_enabled and self._is_complex_request(user_input)) else "orchestration_traditional",
                "plan": orchestrator_data.get("plan", []) if isinstance(orchestrator_data, dict) else [],
                "artifacts": artifacts,
                "workspace_path": workspace_path_resolved,
                "artifacts_dir": artifacts_dir
            }

        except Exception as e:
            logging.error(f"❌ Erro no processamento do pedido: {e}")
            return {
                "final_response": f"Ocorreu um erro interno: {str(e)}",
                "execution_log": [f"Erro geral no pipeline: {str(e)}"],
                "processing_type": "error"
            }

    def _is_simple_conversation(self, user_input: str) -> bool:
        """Verifica se a entrada do usuário é uma conversa simples."""
        simple_keywords = ["olá", "oi", "tudo bem", "como vai", "bom dia", "boa tarde", "boa noite", "obrigado", "tchau", "adeus"]
        complex_keywords = ["criar", "executar", "analisar", "gerar", "calcular", "programar", "pesquisar", "implementar", "atualizar", "modificar", "registrar", "obter", "enviar", "processar"]

        user_input_lower = user_input.lower()

        # Contar ocorrências de palavras-chave simples e complexas
        simple_matches = sum(keyword in user_input_lower for keyword in simple_keywords)
        complex_matches = sum(keyword in user_input_lower for keyword in complex_keywords)

        # Considera simples se houver mais palavras-chave simples do que complexas E nenhuma palavra-chave complexa for encontrada
        # Ou se nenhuma palavra-chave complexa for encontrada e a entrada for curta
        if simple_matches > 0 and complex_matches == 0:
            return True
        elif complex_matches == 0 and len(user_input.split()) < 5: # Conversa curta e sem palavras complexas
            return True

        return False

    def _is_complex_request(self, user_input: str) -> bool:
        """Verifica se a solicitação do usuário é complexa o suficiente para justificar o uso do HMP para planejamento."""
        complex_keywords = [
            "criar", "executar", "analisar", "gerar", "calcular", "programar", 
            "pesquisar", "implementar", "atualizar", "modificar", "registrar", 
            "obter", "enviar", "processar", "converter", "escrever", "resolver",
            "explicar", "resumir", "comparar", "descrever", "listar", "encontrar"
        ]
        user_input_lower = user_input.lower()

        # Se a solicitação contém palavras-chave complexas ou é uma pergunta direta com muitos detalhes
        has_complex_keywords = any(keyword in user_input_lower for keyword in complex_keywords)
        is_long_request = len(user_input.split()) > 15 # Critério arbitrário para solicitações longas

        return has_complex_keywords or is_long_request

    def _generate_pipeline_hmp_reasoning(self, user_input: str) -> str:
        """
        Gera raciocínio HMP para o pipeline principal.
        """

        pipeline_hmp = f"""
# PIPELINE ROKO HMP - RACIOCÍNIO PRINCIPAL
SET user_request TO "{user_input}"
SET processing_mode TO "unknown"
SET complexity_score TO 0

# ANÁLISE DE TIPO DE PEDIDO
CALL analyze_request_complexity WITH input = user_request
SET complexity_score TO complexity_result.score

# DECISÃO DE PROCESSAMENTO
IF complexity_score < 3 THEN
    SET processing_mode TO "simple_conversation"
    CALL log_info WITH message = "Modo conversa simples selecionado"
ELSE
    SET processing_mode TO "full_orchestration"
    CALL log_info WITH message = "Modo orquestração completa selecionado"
ENDIF

# PREPARAÇÃO DE CONTEXTO
CALL memory.retrieve WITH query = user_request
SET chat_context TO memory_result

# EXECUÇÃO DO MODO SELECIONADO
IF processing_mode == "simple_conversation" THEN
    CALL roko_agent.generate_simple_response WITH 
        input = user_request,
        context = chat_context
ELSE
    CALL orchestrator.create_execution_plan WITH
        prompt = user_request,
        context = chat_context
ENDIF

# LOGGING E AUDITORIA
CALL log_execution WITH
    user_request = user_request,
    processing_mode = processing_mode,
    complexity_score = complexity_score

RETURN processing_result
"""

        return pipeline_hmp

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória."""
        return self.cognitive_memory.get_memory_stats()

    def get_memory_insights(self) -> List[str]:
        """Retorna insights da memória."""
        return self.cognitive_memory.get_insights()

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do sistema."""
        try:
            return {
                'status': 'online',
                'hmp_enabled': self.hmp_enabled,
                'api_configured': self.api_key is not None,
                'components': {
                    'cognitive_memory': self.cognitive_memory is not None,
                    'roko_agent': self.roko_agent is not None,
                    'orchestrator': self.orchestrator is not None,
                    'hmp_interpreter': self.hmp_interpreter is not None
                },
                'memory_stats': self.cognitive_memory.get_memory_stats() if self.cognitive_memory else {},
                'version': '2.0.0-HMP'
            }
        except Exception as e:
            logging.error(f"Erro ao obter status do sistema: {e}")
            return {
                'status': 'online',
                'error': str(e),
                'basic_status': True
            }