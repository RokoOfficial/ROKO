"""
Módulo do Orquestrador ROKO.

O orquestrador é responsável por coordenar os diferentes agentes
e executar planos complexos de forma autônoma.
"""

import logging
import json
import time
import os
import numpy as np
from typing import Dict, Any, List, Optional
from Agents import (
    WebAgent, ShellAgent, DependencyAgent, CodeAgent, 
    PlannerAgent, CheckInAgent, ErrorFixAgent, ROKOAgent,
    ValidationAgent, AdaptiveContextAgent, MetricsAgent,
    DataProcessingAgent, ArtifactManager, GitHubAgent
)

# Configurar logging seguro para o orquestrador
orchestrator_logger = logging.getLogger('ROKO.ORCHESTRATOR')
orchestrator_logger.setLevel(logging.DEBUG)

# Cria o diretório de logs se não existir
log_dir = os.path.dirname("ROKO/logs/roko_agents.log")
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)
    orchestrator_logger.info(f"Diretório de logs criado: {log_dir}")

# Define o handler para o arquivo de log
file_handler = logging.FileHandler('ROKO/logs/roko_agents.log', mode='a')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
orchestrator_logger.addHandler(file_handler)

# Assume que BaseAgent e HMPInterpreter estão disponíveis em caminhos relativos
# Se não estiverem, ajuste os imports conforme a estrutura do seu projeto.
# Exemplo: from roko.agents.base_agent import BaseAgent
# Exemplo: from roko.hmp.hmp_interpreter import HMPInterpreter

# Placeholder para BaseAgent caso não esteja disponível diretamente
class BaseAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        orchestrator_logger.info(f"BaseAgent inicializado com API Key: {'*' * len(api_key)}")

class OrchestratorAgent(BaseAgent):
    """
    Orquestrador principal que coordena todos os agentes especializados usando raciocínio HMP.
    """
    def __init__(self, api_key: str, max_correction_attempts: int = 6):
        super().__init__(api_key)
        self.max_correction_attempts = max_correction_attempts
        self.workspace_path = None

        # Integrar HMP Interpreter
        try:
            from HMP.hmp_interpreter import HMPInterpreter
            from HMP.hmp_tools import HMPTools
            self.hmp_interpreter = HMPInterpreter()
            HMPTools.register_hmp_functions(self.hmp_interpreter)
            self.hmp_enabled = True
            orchestrator_logger.info("✅ HMP Interpreter integrado com sucesso no Orchestrator")
        except ImportError as e:
            orchestrator_logger.error(f"❌ Erro ao carregar HMP no Orchestrator: {e}")
            self.hmp_interpreter = None
            self.hmp_enabled = False
            orchestrator_logger.warning("HMP não disponível ou não pôde ser importado no Orchestrator")

        # Inicializar agentes especializados
        self.web_agent = WebAgent(api_key)
        self.shell_agent = ShellAgent(api_key)
        self.dependency_agent = DependencyAgent(api_key)
        self.code_agent = CodeAgent(api_key)
        self.planner_agent = PlannerAgent(api_key)
        self.checkin_agent = CheckInAgent(api_key)
        self.error_fix_agent = ErrorFixAgent(api_key)
        self.roko_agent = ROKOAgent(api_key)
        self.validation_agent = ValidationAgent(api_key)
        self.adaptive_context_agent = AdaptiveContextAgent(api_key)
        self.metrics_agent = MetricsAgent(api_key)
        self.data_processing_agent = DataProcessingAgent(api_key)
        self.artifact_manager = ArtifactManager(api_key)
        self.github_agent = GitHubAgent(api_key)

        # Registro de agentes para roteamento
        self.agents = {
            'web': self.web_agent,
            'shell': self.shell_agent,
            'dependency': self.dependency_agent,
            'code': self.code_agent,
            'planner': self.planner_agent,
            'checkin': self.checkin_agent,
            'error_fix': self.error_fix_agent,
            'roko': self.roko_agent,
            'validation': self.validation_agent,
            'adaptive_context': self.adaptive_context_agent,
            'metrics': self.metrics_agent,
            'data_processing': self.data_processing_agent,
            'artifact_manager': self.artifact_manager,
            'github': self.github_agent
        }

    def orchestrate_stream(self, user_prompt: str, memory_context: list):
        """Orquestra execução com streaming."""
        try:
            # Criar plano
            yield {'type': 'thinking', 'message': 'Criando plano detalhado...'}
            plan = self.planner.create_plan(user_prompt, memory_context)

            if not plan:
                yield {'type': 'error', 'message': 'Não foi possível criar um plano'}
                return

            yield {'type': 'thinking', 'message': f'Executando {len(plan)} ações...'}

            execution_log = []
            final_response = ""

            # Executar cada passo
            for i, step in enumerate(plan, 1):
                tool = step.get("tool")
                query = step.get("query", "")

                yield {
                    'type': 'step_start',
                    'step': i,
                    'total': len(plan),
                    'tool': tool,
                    'action': query[:100] + "..." if len(query) > 100 else query
                }

                # Executar passo
                success, result, log_entries = self._execute_step_with_retry(step, user_prompt)
                execution_log.extend(log_entries)

                if success:
                    yield {
                        'type': 'step_complete',
                        'step': i,
                        'result': result[:200] + "..." if len(result) > 200 else result,
                        'success': True
                    }
                    final_response += f"\n{result}"
                else:
                    yield {
                        'type': 'step_complete',
                        'step': i,
                        'result': result,
                        'success': False
                    }

            yield {
                'type': 'complete',
                'data': {
                    'final_response': final_response.strip(),
                    'execution_log': execution_log,
                    'plan': plan
                }
            }

        except Exception as e:
            orchestrator_logger.error(f"Erro na orquestração: {e}")
            yield {'type': 'error', 'message': f'Erro na orquestração: {str(e)}'}

    def orchestrate(self, user_prompt: str, context_summary: str) -> Dict[str, Any]:
        """
        Orquestra a execução de um pedido complexo.
        """
        orchestrator_logger.info("🎯 Orquestrador iniciando análise do pedido...")

        # 1. Criar plano usando o método correto  
        plan = self.create_execution_plan(user_prompt, context_summary, workspace_path=getattr(self, 'workspace_path', None)) # Chamada para o método unificado

        if not plan or not plan.get("plan"): # Verifica se o plano foi gerado corretamente
            # Pedido simples - não requer orquestração ou plano inválido
            orchestrator_logger.warning("Pedido simples ou plano inválido, processando diretamente.")
            return {
                "plan": [],
                "execution_log": ["Pedido simples ou plano inválido - resposta direta necessária"],
                "final_response": "Conversação direta",
                "success": True
            }

        # 2. Executar plano com correção de erros
        execution_result = self._execute_plan_with_error_correction(
            {"plan": plan["plan"]}, user_prompt # Passa apenas a lista de passos do plano
        )

        return {
            "plan": plan["plan"],
            "execution_log": execution_result.get("execution_log", []),
            "final_response": execution_result.get("final_result", ""),
            "success": execution_result.get("success", False)
        }

    def _execute_plan_with_error_correction(self, plan_data: Dict, user_prompt: str) -> Dict[str, Any]:
        """
        Executa o plano com correção automática de erros.
        """
        execution_log = []
        final_result = None
        success = False

        for attempt in range(self.max_correction_attempts):
            try:
                orchestrator_logger.info(f"🔄 Tentativa {attempt + 1} de execução do plano...")

                # Executar plano
                result = self._execute_plan_steps(plan_data["plan"])
                execution_log.extend(result["log"])

                if result["success"]:
                    final_result = result["final_output"]
                    success = True
                    orchestrator_logger.info("✅ Plano executado com sucesso!")
                    break
                else:
                    # Tentar corrigir erro
                    error_msg = result.get("error", "Erro desconhecido")
                    orchestrator_logger.warning(f"⚠️ Erro na execução: {error_msg}")

                    if attempt < self.max_correction_attempts - 1:
                        correction = self.error_fixer.fix_error(
                            plan_data["plan"], error_msg
                        )

                        if correction and correction.get("corrected_plan"):
                            plan_data["plan"] = correction["corrected_plan"]
                            execution_log.append(f"🔧 Tentativa de correção: {correction.get('explanation', 'N/A')}")
                        else:
                            orchestrator_logger.error("❌ Não foi possível corrigir o erro.")
                            break
                    else:
                        orchestrator_logger.error("❌ Número máximo de tentativas de correção atingido.")
                        break

            except Exception as e:
                orchestrator_logger.error(f"❌ Erro inesperado na execução: {e}")
                execution_log.append(f"❌ Erro: {str(e)}")
                break

        return {
            "plan": plan_data["plan"], # Retorna o plano (possivelmente corrigido)
            "execution_log": execution_log,
            "final_result": final_result,
            "success": success
        }

    def _execute_plan_steps(self, plan: List[Dict]) -> Dict[str, Any]:
        """
        Executa os passos individuais de um plano.
        """
        log = []
        outputs = []

        try:
            print(f"\n🔄 EXECUTANDO {len(plan)} PASSOS DO PLANO:")
            for i, step in enumerate(plan):
                step_type = step.get("type") # O step original pode não ter 'type', mas 'tool'
                tool = step.get("tool")
                query = step.get("query")

                if not tool or not query:
                    print(f"❌ Passo {i+1} INVÁLIDO: 'tool' ou 'query' ausente")
                    log.append(f"❌ Passo {i+1} inválido: 'tool' ou 'query' ausente.")
                    continue # Pula para o próximo passo se o formato estiver incorreto

                print(f"\n⚡ EXECUTANDO PASSO {i+1}/{len(plan)}:")
                print(f"  🛠️ FERRAMENTA: {tool}")
                print(f"  📋 TAREFA: {query}")

                orchestrator_logger.info(f"📋 Executando passo {i+1}: Ferramenta='{tool}', Tarefa='{query[:50]}...'")
                # Renomeado o logger para o definido globalmente
                orchestrator_logger.info(f"ORCHESTRATOR_STEP_{i+1}: Executando {tool} - {query}")
                log.append(f"Passo {i+1}: Ferramenta='{tool}', Tarefa='{query}'")

                # Executar passo usando checkin agent
                # O checkin.execute_step espera um dicionário representando o passo
                step_data = {"tool": tool, "query": query}

                print(f"  🎯 CHAMANDO AGENTE: CheckInAgent")
                orchestrator_logger.info(f"CHECKIN_AGENT: Executando step_data={step_data}")

                result = self.checkin_agent.execute_step(step_data)

                if result and result.get("success"):
                    output = result.get("output", "")
                    outputs.append(output)
                    print(f"  ✅ SUCESSO: {output[:100]}...")
                    orchestrator_logger.info(f"CHECKIN_AGENT: Sucesso - Output: {output[:100]}...")
                    log.append(f"✅ Passo {i+1} concluído com sucesso.")
                else:
                    error_msg = result.get("error", "Erro desconhecido no CheckInAgent") if result else "Resultado inválido do CheckInAgent"
                    print(f"  ❌ FALHOU: {error_msg}")
                    orchestrator_logger.error(f"CHECKIN_AGENT: Falha - Error: {error_msg}")
                    log.append(f"❌ Passo {i+1} falhou: {error_msg}")
                    # Se um passo falhar, o plano geral falha.
                    return {
                        "success": False,
                        "error": error_msg,
                        "log": log,
                        "final_output": None
                    }

            return {
                "success": True,
                "log": log,
                "final_output": "\n".join(outputs)
            }

        except Exception as e:
            orchestrator_logger.error(f"❌ Exceção ao executar passos do plano: {e}")
            return {
                "success": False,
                "error": str(e),
                "log": log + [f"❌ Exceção durante execução: {str(e)}"],
                "final_output": None
            }

    def _execute_step_with_retry(self, step, user_prompt):
        """Executa um passo com retry automático."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Simular execução do passo
                tool = step.get("tool", "unknown")
                query = step.get("query", "")

                # Aqui você implementaria a lógica real de execução
                # Por enquanto, simulo um resultado
                orchestrator_logger.info(f"Tentando executar passo: Tool='{tool}', Query='{query[:50]}...'")
                result = f"Executado com sucesso: {tool} - {query}"

                return True, result, [f"Passo executado com sucesso em tentativa {attempt + 1}"]

            except Exception as e:
                orchestrator_logger.error(f"Erro ao executar passo na tentativa {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return False, f"Falha após {max_retries} tentativas: {str(e)}", [f"Erro na tentativa {attempt + 1}: {str(e)}"]
                else:
                    # Esperar um pouco antes de tentar novamente (backoff)
                    time.sleep(1)
                    continue
        return False, "Falha desconhecida na execução do passo", ["Erro desconhecido"] # Caso algo inesperado ocorra no loop

    def create_execution_plan(self, user_prompt: str, context: dict, workspace_path: str = None) -> Dict[str, Any]:
        """Cria um plano de execução baseado no prompt do usuário usando raciocínio HMP."""
        orchestrator_logger.info("OrchestratorAgent criando plano de execução com HMP...")

        hmp_reasoning_output = None
        plan_details = None

        # Gerar plano usando HMP se disponível
        if self.hmp_enabled and self.hmp_interpreter:
            try:
                hmp_plan_code = f"""
# PLANO DE EXECUÇÃO HMP ORCHESTRATOR PARA: {user_prompt}
SET user_request TO "{user_prompt}"
SET available_context TO {context} # Contexto passado como string JSON ou similar
SET complexity_level TO 0

# ANÁLISE DE COMPLEXIDADE (Exemplo baseado em palavras-chave)
CALL analyze_request_complexity WITH input = user_request
IF CONTAINS(user_request, "código", "script", "python", "debug") THEN
    SET complexity_level TO complexity_level + 3
ENDIF
IF CONTAINS(user_request, "pesquisar", "buscar", "web", "internet") THEN
    SET complexity_level TO complexity_level + 2
ENDIF
IF CONTAINS(user_request, "executar", "shell", "comando", "terminal") THEN
    SET complexity_level TO complexity_level + 2
ENDIF
IF CONTAINS(user_request, "validar", "verificar", "confirmar") THEN
    SET complexity_level TO complexity_level + 1
ENDIF

# SELEÇÃO DE AGENTES BASEADA NA COMPLEXIDADE
DEFINE agents_plan AS LIST
DEFINE reasoning_steps AS LIST

IF complexity_level >= 5 THEN
    DEFINE agents_plan AS LIST: \x27web\x27, \x27code\x27, \x27shell\x27, \x27validation\x27
    APPEND \x27Alta complexidade detectada, utilizando web, code, shell e validation.\x27 TO reasoning_steps
ELSE IF complexity_level >= 3 THEN
    DEFINE agents_plan AS LIST: \x27web\x27, \x27code\x27, \x27validation\x27
    APPEND \x27Complexidade moderada, utilizando web, code e validation.\x27 TO reasoning_steps
ELSE
    DEFINE agents_plan AS LIST: \x27web\x27, \x27validation\x27
    APPEND \x27Baixa complexidade, utilizando web e validation.\x27 TO reasoning_steps
ENDIF

# GERAÇÃO DE QUERIES ESPECÍFICAS (Simplificado)
DEFINE final_plan AS LIST
FOR agent IN agents_plan:
    IF agent == \x27web\x27 THEN
        APPEND {{"tool": "web", "query": f"Pesquisar sobre: {user_request}"}} TO final_plan
        APPEND f"Gerada query para agent web: Pesquisar sobre {user_request}" TO reasoning_steps
    ELSE IF agent == \x27code\x27 THEN
        APPEND {{"tool": "code", "query": f"Analisar/executar código relacionado a: {user_request}"}} TO final_plan
        APPEND f"Gerada query para agent code: Analisar/executar código relacionado a {user_request}" TO reasoning_steps
    ELSE IF agent == \x27shell\x27 THEN
        APPEND {{"tool": "shell", "query": f"Executar comando do sistema relacionado a: {user_request}"}} TO final_plan
        APPEND f"Gerada query para agent shell: Executar comando do sistema relacionado a {user_request}" TO reasoning_steps
    ELSE IF agent == \x27validation\x27 THEN
        APPEND {{"tool": "validation", "query": f"Validar o resultado da solicitação: {user_request}"}} TO final_plan
        APPEND f"Gerada query para agent validation: Validar o resultado da solicitação {user_request}" TO reasoning_steps
    ENDIF
ENDFOR

# VALIDAÇÃO DO PLANO (Simplificado)
CALL validate_execution_plan WITH plan = final_plan
IF validation_score < 70 THEN
    CALL optimize_plan WITH current_plan = final_plan
    APPEND "Plano otimizado devido à baixa pontuação de validação." TO reasoning_steps
ENDIF

RETURN { "hmp_reasoning": JOIN(reasoning_steps, "\\n"), "plan": final_plan }
"""
                # Executa o código HMP usando o interpretador
                hmp_result = self.hmp_interpreter.execute_hmp(
                    hmp_plan_code,
                    context={'user_prompt': user_prompt, 'context': context} # Passa o contexto como um objeto
                )

                hmp_reasoning_output = hmp_result.get('hmp_reasoning', 'Nenhum raciocínio HMP retornado.')
                plan_details = hmp_result.get('plan', [])

                if not isinstance(plan_details, list):
                    orchestrator_logger.error("HMP Interpreter retornou um plano em formato inválido.")
                    plan_details = [] # Garante que plan_details seja uma lista

                orchestrator_logger.info("🧠 Plano HMP gerado com sucesso")

            except Exception as e:
                orchestrator_logger.error(f"Erro ao gerar plano HMP: {e}")
                hmp_reasoning_output = f"Erro na geração do plano HMP: {str(e)}"
                plan_details = []
        else:
            orchestrator_logger.warning("HMP não habilitado ou interpretador não disponível. Usando planejamento padrão.")
            # Fallback para planejamento padrão se HMP não estiver disponível
            plan_details = self._generate_default_plan(user_prompt)
            hmp_reasoning_output = "Planejamento padrão executado pois HMP não está disponível."

        # Retorna a estrutura unificada
        return {
            "hmp_reasoning": hmp_reasoning_output,
            "plan": plan_details
        }

    def _generate_default_plan(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Gera um plano de execução padrão se o HMP não estiver disponível."""
        orchestrator_logger.info("Gerando plano de execução padrão...")
        # Análise de contexto para roteamento inteligente
        if any(keyword in user_prompt.lower() for keyword in ['github', 'git', 'repositório', 'repo', 'commit', 'branch', 'issue', 'pull request', 'pr', 'workflow', 'ci/cd']):
            primary_agent = 'github'
        elif any(keyword in user_prompt.lower() for keyword in ['pesquisar', 'buscar', 'web', 'site', 'url']):
            primary_agent = 'web'
        elif any(keyword in user_prompt.lower() for keyword in ['executar', 'comando', 'shell', 'terminal']):
            primary_agent = 'shell'
        elif any(keyword in user_prompt.lower() for keyword in ['código', 'programar', 'python', 'script']):
            primary_agent = 'code'
        elif any(keyword in user_prompt.lower() for keyword in ['dados', 'csv', 'json', 'análise']):
            primary_agent = 'data_processing'
        elif any(keyword in user_prompt.lower() for keyword in ['gráfico', 'visualização', 'dashboard']):
            primary_agent = 'artifact_manager'
        else:
            primary_agent = 'roko'
        
        # Lógica simplificada para criar um plano padrão
        if primary_agent == "github":
            return [{"tool": "github", "query": f"Processar solicitação relacionada ao GitHub: {user_prompt}"}]
        elif primary_agent == "web":
            return [{"tool": "web", "query": f"Pesquisar sobre: {user_prompt}"}]
        elif primary_agent == "code":
            return [{"tool": "code", "query": f"Executar ou analisar código relacionado a: {user_prompt}"}]
        else:
            return [{"tool": "roko", "query": user_prompt}] # Agente genérico ROKO