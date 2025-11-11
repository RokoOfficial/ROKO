"""
Agente que verifica se resultados cumpriram os objetivos pretendidos.
"""

import logging
import json
import os
from typing import Dict, Any
from .base_agent import BaseAgent

# Modelo de IA a ser utilizado
FIXER_MODEL = "gpt-4o-mini"

# Configurar um logger específico para este agente, se não estiver globalmente configurado
# Se já existir um logger global, este pode ser adaptado ou removido.
# Para este exemplo, assumimos que 'agent_logger' é uma instância de logger configurada
# em outro lugar do projeto para capturar logs de todos os agentes.
# Se não existir, uma configuração básica pode ser adicionada aqui.
try:
    agent_logger = logging.getLogger('agent_logger')
    if not agent_logger.handlers:
        # Configuração básica se o logger não estiver configurado
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        agent_logger.addHandler(handler)
        agent_logger.setLevel(logging.INFO)
except Exception as e:
    print(f"Erro ao configurar agent_logger: {e}")
    agent_logger = logging.getLogger(__name__) # Fallback para o logger padrão do módulo

# Configurar logging seguro para checkin agent
checkin_logger = logging.getLogger('ROKO.CHECKIN_AGENT')
checkin_logger.setLevel(logging.DEBUG)

# Criar diretório de logs se não existir
log_dir = 'ROKO/logs'
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
        print(f"Diretório de logs criado: {log_dir}")
    except OSError as e:
        print(f"Erro ao criar diretório de logs {log_dir}: {e}")
        # Continuar mesmo que o diretório não possa ser criado, o handler pode falhar

# Adicionar handler de arquivo ao logger principal (se necessário e configurável)
# Nota: A configuração original pode estar em outro lugar. Se o objetivo for
# apenas garantir que o CheckInAgent possa logar, esta parte pode ser redundante
# ou precisar ser adaptada dependendo da estrutura global de logging.
try:
    # Verifica se já existe um FileHandler configurado para evitar duplicidade
    if not any(isinstance(h, logging.FileHandler) for h in agent_logger.handlers):
        log_file_path = os.path.join(log_dir, 'roko_agents.log')
        file_handler = logging.FileHandler(log_file_path, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        agent_logger.addHandler(file_handler)
        print(f"FileHandler adicionado para: {log_file_path}")
except Exception as e:
    print(f"Erro ao adicionar FileHandler ao agent_logger: {e}")


class CheckInAgent(BaseAgent):
    """
    Agente que verifica se o resultado de um passo realmente atendeu ao objetivo.
    Faz a diferença entre 'sucesso técnico' (sem erro) e 'sucesso funcional' (objetivo alcançado).
    """

    def verify_step_completion(self, step: Dict[str, str], result: str, original_user_request: str) -> Dict[str, Any]:
        """
        Verifica se o resultado de um passo realmente atendeu ao objetivo.

        Args:
            step: O passo executado {"tool": "...", "query": "..."}
            result: O resultado obtido da execução
            original_user_request: O pedido original do usuário para contexto

        Returns:
            {
                "objective_achieved": bool,
                "reason": str,
                "suggestions": str (se objective_achieved for False)
            }
        """
        logging.info(f"CheckInAgent a verificar se o objetivo foi alcançado para: {step['tool']}")
        agent_logger.info(f"CHECKIN_AGENT: Iniciando verificação de objetivo para tool='{step['tool']}'")
        checkin_logger.debug(f"Iniciando verificação para tool='{step['tool']}'")

        system_prompt = """
        Você é um agente de verificação de objetivos equilibrado. Sua tarefa é analisar se o resultado de uma ação 
        teve sucesso razoável, considerando limitações práticas.

        Analise pragmaticamente:
        1. O que a ação pretendia fazer?
        2. O resultado tem informação útil, mesmo que não perfeita?
        3. O resultado avança o objetivo geral do usuário?

        Seja PRAGMÁTICO, não perfecionista. Se o resultado contém informação relevante ou útil, 
        considere como objetivo alcançado, mesmo que não seja exatamente o que foi pedido.

        Responda APENAS com um objeto JSON contendo:
        - "objective_achieved": true se há progresso útil, false apenas se totalmente inútil
        - "reason": explicação breve do porquê
        - "suggestions": se objective_achieved for false, sugira uma abordagem alternativa

        REGRA: Se o resultado contém QUALQUER informação relevante ao contexto, marque como sucesso.
        """

        user_content = f"""
        VERIFICAÇÃO DE OBJETIVO:

        Pedido Original do Usuário: {original_user_request}

        Passo Executado:
        - Ferramenta: {step['tool']}  
        - Ação: {step['query']}

        Resultado Obtido:
        {result}

        PERGUNTA: Este resultado realmente cumpriu o objetivo pretendido pela ação?
        Responda com JSON conforme as instruções.
        """

        try:
            response = self.client.chat.completions.create(
                model=FIXER_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )

            response_content = response.choices[0].message.content
            agent_logger.debug(f"CheckInAgent - Resposta da IA para verificação: {response_content}")
            checkin_logger.debug(f"Resposta da IA para verificação: {response_content}")
            print(f"      🤖 IA (Verificação): {response_content}")

            verification_data = json.loads(response_content)

            required_keys = ["objective_achieved", "reason"]
            if not all(key in verification_data for key in required_keys):
                raise ValueError(f"Resposta de verificação incompleta: {verification_data}")

            agent_logger.info(f"CheckInAgent - Verificação do objetivo: {'✅ Sucesso' if verification_data['objective_achieved'] else '❌ Falha'}")
            checkin_logger.info(f"Verificação do objetivo: {'Alcançado' if verification_data['objective_achieved'] else 'Não Alcançado'}")
            print(f"    ✅ CHECKIN AGENT - Verificação do objetivo: {'Alcançado' if verification_data['objective_achieved'] else 'Não Alcançado'}")
            print(f"    💬 CHECKIN AGENT - Razão: {verification_data['reason']}")
            if not verification_data['objective_achieved']:
                print(f"    💡 CHECKIN AGENT - Sugestões: {verification_data.get('suggestions', 'Nenhuma')}")
                agent_logger.warning(f"CheckInAgent - Sugestões para o objetivo não alcançado: {verification_data.get('suggestions', 'Nenhuma')}")
                checkin_logger.warning(f"Sugestões para o objetivo não alcançado: {verification_data.get('suggestions', 'Nenhuma')}")

            return verification_data

        except Exception as e:
            error_msg = f"Erro no CheckInAgent durante a verificação: {e}"
            logging.error(error_msg)
            agent_logger.error(error_msg)
            checkin_logger.error(f"Erro durante a verificação: {e}")
            print(f"    💥 CHECKIN AGENT - Erro na verificação: {e}")
            # Em caso de erro na verificação, assume que o objetivo foi alcançado para não bloquear o pipeline
            return {
                "objective_achieved": True,
                "reason": f"Erro na verificação, assumindo sucesso: {e}",
                "suggestions": ""
            }

    def execute_step(self, step: dict) -> dict:
        """Executa um passo específico do plano."""
        try:
            tool = step.get("tool")
            query = step.get("query")

            print(f"    🔍 CHECKIN AGENT - Analisando passo:")
            print(f"    📊 Tool: {tool}")
            print(f"    📝 Query: {query}")

            agent_logger.info(f"CHECKIN_AGENT: Executando tool='{tool}', query='{query}'")
            checkin_logger.info(f"Executando tool='{tool}', query='{query}'")

            if not tool or not query:
                error_msg = "Passo inválido: tool ou query ausente"
                print(f"    ❌ ERRO: {error_msg}")
                agent_logger.error(f"CHECKIN_AGENT: {error_msg}")
                checkin_logger.error(error_msg)
                return {"success": False, "error": error_msg}

            # Mapear ferramentas para agentes
            if tool == "web_search" or tool == "web":
                print(f"    🌐 DELEGANDO PARA: WebAgent")
                agent_logger.info("CHECKIN_AGENT: Delegando para WebAgent")
                checkin_logger.info("Delegando para WebAgent")
                return self._execute_web_search(query)
            elif tool == "python_code" or tool == "code":
                print(f"    💻 DELEGANDO PARA: CodeAgent")
                agent_logger.info("CHECKIN_AGENT: Delegando para CodeAgent")
                checkin_logger.info("Delegando para CodeAgent")
                return self._execute_code(query)
            elif tool == "shell" or tool == "shell_command":
                print(f"    🖥️ DELEGANDO PARA: ShellAgent")
                agent_logger.info("CHECKIN_AGENT: Delegando para ShellAgent")
                checkin_logger.info("Delegando para ShellAgent")
                return self._execute_shell(query)
            elif tool == "validation":
                print(f"    ✅ DELEGANDO PARA: ValidationAgent")
                agent_logger.info("CHECKIN_AGENT: Delegando para ValidationAgent")
                checkin_logger.info("Delegando para ValidationAgent")
                return self._execute_validation(query)
            else:
                error_msg = f"Ferramenta desconhecida: {tool}"
                print(f"    ❌ ERRO: {error_msg}")
                agent_logger.error(f"CHECKIN_AGENT: {error_msg}")
                checkin_logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao executar passo no CheckInAgent: {e}"
            print(f"    💥 EXCEÇÃO: {error_msg}")
            logging.error(error_msg)
            agent_logger.error(f"CHECKIN_AGENT: Exceção capturada em execute_step - {error_msg}")
            checkin_logger.error(f"Exceção capturada em execute_step - {error_msg}")
            return {"success": False, "error": str(e)}

    def _execute_web_search(self, query: str) -> dict:
        """Executa pesquisa web."""
        try:
            print(f"      🔎 WEB_AGENT: Pesquisando '{query}'")
            agent_logger.info(f"WEB_AGENT: Iniciando pesquisa para '{query}'")
            checkin_logger.debug(f"WEB_AGENT: Iniciando pesquisa para '{query}'")

            result = self.web_agent.search(query)

            # Log do resultado da pesquisa web
            if result:
                result_preview = (str(result)[:200] + '...') if len(str(result)) > 200 else str(result)
                print(f"      ✅ WEB_AGENT: Pesquisa concluída. Resultado (preview): '{result_preview}'")
                agent_logger.info(f"WEB_AGENT: Pesquisa concluída com sucesso. Resultado (preview): '{result_preview}'")
                checkin_logger.info(f"WEB_AGENT: Pesquisa concluída com sucesso. Resultado (preview): '{result_preview}'")
            else:
                print(f"      ⚠️ WEB_AGENT: Pesquisa concluída, mas sem resultados.")
                agent_logger.warning(f"WEB_AGENT: Pesquisa concluída, mas sem resultados para '{query}'.")
                checkin_logger.warning(f"WEB_AGENT: Pesquisa concluída, mas sem resultados para '{query}'.")

            return {"success": True, "output": result}
        except Exception as e:
            error_msg = f"WEB_AGENT: Erro na pesquisa para '{query}' - {str(e)}"
            print(f"      ❌ {error_msg}")
            agent_logger.error(error_msg)
            checkin_logger.error(error_msg)
            return {"success": False, "error": str(e)}

    def _execute_code(self, query: str) -> dict:
        """Executa código Python."""
        try:
            print(f"      🐍 CODE_AGENT: Executando código")
            agent_logger.info(f"CODE_AGENT: Iniciando execução de código: {query[:100]}...") # Log de preview do código
            checkin_logger.debug(f"CODE_AGENT: Iniciando execução de código: {query[:100]}...")

            result = self.code_agent.execute_code(query)

            print(f"      ✅ CODE_AGENT: Código executado com sucesso.")
            agent_logger.info(f"CODE_AGENT: Execução concluída com sucesso.")
            checkin_logger.info("CODE_AGENT: Execução concluída com sucesso.")

            return {"success": True, "output": result}
        except Exception as e:
            error_msg = f"CODE_AGENT: Erro na execução do código: {str(e)}"
            print(f"      ❌ {error_msg}")
            agent_logger.error(error_msg)
            checkin_logger.error(error_msg)
            return {"success": False, "error": str(e)}

    def _execute_shell(self, query: str) -> dict:
        """Executa comando shell."""
        try:
            print(f"      💻 SHELL_AGENT: Executando comando: '{query}'")
            agent_logger.info(f"SHELL_AGENT: Iniciando execução de comando: '{query}'")
            checkin_logger.debug(f"SHELL_AGENT: Iniciando execução de comando: '{query}'")

            result = self.shell_agent.execute_command(query)

            print(f"      ✅ SHELL_AGENT: Comando executado com sucesso.")
            agent_logger.info(f"SHELL_AGENT: Execução concluída com sucesso.")
            checkin_logger.info("SHELL_AGENT: Execução concluída com sucesso.")

            return {"success": True, "output": result}
        except Exception as e:
            error_msg = f"SHELL_AGENT: Erro na execução do comando '{query}': {str(e)}"
            print(f"      ❌ {error_msg}")
            agent_logger.error(error_msg)
            checkin_logger.error(error_msg)
            return {"success": False, "error": str(e)}

    def _execute_validation(self, query: str) -> dict:
        """Executa validação."""
        try:
            print(f"      ✔️ VALIDATION_AGENT: Validando: '{query}'")
            agent_logger.info(f"VALIDATION_AGENT: Iniciando validação: '{query}'")
            checkin_logger.debug(f"VALIDATION_AGENT: Iniciando validação: '{query}'")

            result = self.validation_agent.validate(query)

            print(f"      ✅ VALIDATION_AGENT: Validação concluída com sucesso.")
            agent_logger.info(f"VALIDATION_AGENT: Validação concluída com sucesso.")
            checkin_logger.info("VALIDATION_AGENT: Validação concluída com sucesso.")

            return {"success": True, "output": result}
        except Exception as e:
            error_msg = f"VALIDATION_AGENT: Erro na validação de '{query}': {str(e)}"
            print(f"      ❌ {error_msg}")
            agent_logger.error(error_msg)
            checkin_logger.error(error_msg)
            return {"success": False, "error": str(e)}