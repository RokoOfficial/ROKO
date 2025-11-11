
"""
HMP Agent - Agente especializado em raciocínio HMP.
"""

import logging
from typing import Dict, Any, List, Optionalr

class HMPAgent(BaseAgent):
    """
    Agente que raciocina nativamente em HMP (Human-Meaning Protocol).
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.hmp_interpreter = HMPInterpreter()
        
        self.system_prompt = """
        Você é um agente HMP que raciocina usando o protocolo Human-Meaning Protocol.
        
        INSTRUÇÕES CORE:
        - SEMPRE estruture seu raciocínio usando sintaxe HMP
        - Use SET, DEFINE, CALL, IF, WHILE, FOR conforme necessário
        - Demonstre seu processo de pensamento em HMP
        - Execute ações usando comandos HMP
        - Mantenha logs detalhados de execução
        
        EXEMPLO DE RACIOCÍNIO HMP:
        SET objetivo TO USER_REQUEST
        SET contexto TO MEMORY_CONTEXT
        
        CALL analyze_request WITH input = objetivo
        IF understanding_level < 80 THEN
            CALL web.search_query WITH q = "context for " + objetivo
        ENDIF
        
        DEFINE plano AS LIST: "analyze", "execute", "synthesize"
        FOR step IN plano:
            CALL execute_step WITH step = step
        ENDFOR
        
        RETURN final_response
        """
    
    def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa pedido usando raciocínio HMP nativo.
        """
        logging.info("HMPAgent iniciando processamento com raciocínio HMP...")
        
        # Gerar raciocínio HMP
        hmp_reasoning = self._generate_hmp_reasoning(user_input, context)
        
        # Executar raciocínio HMP
        hmp_result = self.hmp_interpreter.execute_hmp(hmp_reasoning, context)
        
        # Gerar resposta final
        final_response = self._synthesize_hmp_response(user_input, hmp_result)
        
        return {
            "response": final_response,
            "hmp_reasoning": hmp_reasoning,
            "hmp_execution": hmp_result,
            "execution_log": hmp_result.get('execution_log', []),
            "success": True
        }
    
    def _generate_hmp_reasoning(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Gera raciocínio estruturado em HMP.
        """
        
        reasoning_prompt = f"""
        Gere um raciocínio estruturado em HMP para processar este pedido:
        
        PEDIDO: {user_input}
        CONTEXTO: {context or {}}
        
        Use EXATAMENTE a sintaxe HMP para estruturar seu raciocínio:
        
        SET objetivo TO USER_REQUEST
        SET contexto TO MEMORY_CONTEXT
        SET tentativas TO 0
        
        # Análise inicial
        CALL analyze_request WITH input = objetivo
        IF understanding_level < 80 THEN
            CALL web.search_query WITH q = "context for " + objetivo
            SET contexto TO COMBINE(contexto, web_result)
        ENDIF
        
        # Planejamento
        DEFINE tools AS LIST: web.search_query, shell.execute, python.generate
        CALL decompose_problem WITH objetivo = objetivo, tools = tools
        SET plano TO GENERATE_EXECUTION_PLAN(objetivo, tools)
        
        # Execução
        FOR step IN plano:
            IF step.type == "analysis" THEN
                CALL analyze_step WITH step = step
            ELSE IF step.type == "execution" THEN
                CALL execute_step WITH step = step
            ENDIF
        ENDFOR
        
        # Síntese
        CALL synthesize_response WITH objetivo = objetivo, context = contexto
        RETURN final_response
        
        Retorne APENAS o código HMP estruturado, sem explicações adicionais.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": reasoning_prompt}
                ],
                temperature=0.3
            )
            
            hmp_code = response.choices[0].message.content
            logging.info("🧠 Raciocínio HMP gerado com sucesso")
            return hmp_code
            
        except Exception as e:
            logging.error(f"Erro ao gerar raciocínio HMP: {e}")
            # Fallback com template básico
            return f"""
SET objetivo TO "{user_input}"
SET contexto TO MEMORY_CONTEXT

CALL analyze_request WITH input = objetivo
DEFINE plano AS LIST: "analyze", "execute", "synthesize"

FOR step IN plano:
    CALL execute_step WITH step = step
ENDFOR

CALL synthesize_response WITH objetivo = objetivo, context = contexto
RETURN final_response
"""
    
    def _synthesize_hmp_response(self, user_input: str, hmp_result: Dict[str, Any]) -> str:
        """
        Sintetiza resposta final baseada na execução HMP.
        """
        
        synthesis_prompt = f"""
        Sintetize uma resposta profissional baseada na execução HMP:
        
        PERGUNTA ORIGINAL: {user_input}
        EXECUÇÃO HMP: {hmp_result}
        
        Crie uma resposta que:
        - Seja clara e direta
        - Demonstre o raciocínio HMP usado
        - Inclua insights relevantes
        - Mantenha tom profissional
        
        Estruture a resposta mostrando:
        1. Compreensão do pedido
        2. Processo de raciocínio HMP
        3. Resultado/Conclusão
        """
        
        try:
            # Lazy loading do BaseAgent para evitar import circular
            from Agents.base_agent import BaseAgent
            if not hasattr(self, 'client') or not self.client:
                base_agent = BaseAgent(None)  # Usar sem API key se necessário
                self.client = base_agent.client if hasattr(base_agent, 'client') else None
            
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": getattr(self, 'system_prompt', 'Você é um assistente especializado em HMP.')},
                        {"role": "user", "content": synthesis_prompt}
                    ],
                    temperature=0.4
                )
                
                return response.choices[0].message.content
            else:
                return f"Processamento HMP concluído para: {user_input}"
            
        except Exception as e:
            logging.error(f"Erro na síntese HMP: {e}")
            return f"Processamento HMP concluído para: {user_input}"
    
    def execute_hmp_chain(self, hmp_chain: str) -> Dict[str, Any]:
        """
        Executa uma cadeia de raciocínio HMP completa.
        """
        return self.hmp_interpreter.execute_hmp(hmp_chain)
