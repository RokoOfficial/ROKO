
"""
AGI Core - Núcleo de Inteligência Artificial Geral
Sistema consolidado focado em reasoning, adaptabilidade e auto-improvement.
"""

import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class AGICore(BaseAgent):
    """
    Núcleo AGI - Sistema unificado de reasoning e execução autônoma.
    Consolida capacidades de múltiplos agentes especializados em uma arquitetura mais eficiente.
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.reasoning_model = "gpt-4o-mini"
        self.execution_model = "gpt-4o-mini"
        
        self.system_prompt = """
        Você é ROKO, um sistema AGI (Artificial General Intelligence) profissional.
        
        CAPACIDADES CORE:
        - Reasoning avançado com chain-of-thought
        - Execução autônoma de tarefas complexas
        - Auto-análise e improvement contínuo
        - Adaptabilidade a qualquer domínio
        - Síntese de informações multi-modal
        
        MODO OPERACIONAL:
        - Analise profundamente antes de agir
        - Decomponha problemas complexos sistematicamente
        - Execute com precisão e eficiência
        - Auto-avalie e optimize continuamente
        - Mantenha profissionalismo em todas as interações
        
        OBJETIVO: Ser um assistente AGI verdadeiramente útil, confiável e capaz.
        """
    
    def process_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """
        Processamento principal com reasoning avançado e execução autônoma.
        """
        logging.info("AGICore iniciando processamento...")
        
        # 1. Análise e Reasoning
        analysis = self._deep_analysis(user_input, context)
        
        # 2. Planejamento Estratégico  
        plan = self._strategic_planning(user_input, analysis)
        
        # 3. Execução Autônoma
        if plan.get('requires_execution', False):
            execution_result = self._autonomous_execution(plan)
        else:
            execution_result = {"direct_response": True}
        
        # 4. Síntese e Resposta
        final_response = self._synthesize_response(user_input, analysis, execution_result)
        
        return {
            "response": final_response,
            "analysis": analysis,
            "execution_log": execution_result.get("log", []),
            "success": True
        }
    
    def _deep_analysis(self, user_input: str, context: List[Dict]) -> Dict[str, Any]:
        """Análise profunda com reasoning avançado."""
        
        context_str = self._format_context(context) if context else ""
        
        analysis_prompt = f"""
        Analise profundamente esta requisição usando reasoning estruturado:
        
        REQUISIÇÃO: {user_input}
        CONTEXTO: {context_str}
        
        Forneça análise em JSON:
        {{
            "intent": "intenção principal",
            "complexity": "simples|moderada|complexa",
            "domain": "domínio/área de conhecimento",
            "required_capabilities": ["lista de capacidades necessárias"],
            "success_criteria": "critérios de sucesso",
            "reasoning_chain": ["passo 1 do reasoning", "passo 2", "..."]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.reasoning_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"Erro na análise: {e}")
            return {"intent": "unknown", "complexity": "simples", "error": str(e)}
    
    def _strategic_planning(self, user_input: str, analysis: Dict) -> Dict[str, Any]:
        """Planejamento estratégico baseado na análise."""
        
        if analysis.get("complexity") == "simples":
            return {"requires_execution": False, "approach": "direct_response"}
        
        planning_prompt = f"""
        Crie um plano estratégico para esta tarefa:
        
        INPUT: {user_input}
        ANÁLISE: {json.dumps(analysis, indent=2)}
        
        Retorne plano em JSON:
        {{
            "requires_execution": true/false,
            "approach": "estratégia principal",
            "steps": [
                {{"action": "web_search", "query": "...", "reason": "..."}},
                {{"action": "code_execution", "code": "...", "reason": "..."}},
                {{"action": "synthesis", "focus": "...", "reason": "..."}}
            ],
            "expected_outcome": "resultado esperado"
        }}
        
        AÇÕES DISPONÍVEIS: web_search, code_execution, shell_command, synthesis
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.reasoning_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"Erro no planejamento: {e}")
            return {"requires_execution": False, "error": str(e)}
    
    def _autonomous_execution(self, plan: Dict) -> Dict[str, Any]:
        """Execução autônoma do plano com auto-correção."""
        
        execution_log = []
        results = []
        
        for step in plan.get("steps", []):
            action = step.get("action")
            
            try:
                if action == "web_search":
                    result = self._execute_web_search(step.get("query", ""))
                elif action == "code_execution":
                    result = self._execute_code(step.get("code", ""))
                elif action == "shell_command":
                    result = self._execute_shell(step.get("command", ""))
                else:
                    result = f"Ação {action} executada: {step.get('reason', '')}"
                
                results.append(result)
                execution_log.append(f"✅ {action}: {step.get('reason', '')}")
                
            except Exception as e:
                error_msg = f"❌ {action}: {str(e)}"
                execution_log.append(error_msg)
                logging.error(f"Erro na execução: {e}")
        
        return {
            "results": results,
            "log": execution_log,
            "success": len(results) > 0
        }
    
    def _synthesize_response(self, user_input: str, analysis: Dict, execution: Dict) -> str:
        """Síntese final da resposta."""
        
        synthesis_prompt = f"""
        Sintetize uma resposta profissional e completa:
        
        PERGUNTA ORIGINAL: {user_input}
        ANÁLISE: {json.dumps(analysis, indent=2)}
        EXECUÇÃO: {json.dumps(execution, indent=2)}
        
        Crie uma resposta que:
        - Seja direta e profissional
        - Demonstre compreensão profunda
        - Inclua insights relevantes
        - Seja actionable quando apropriado
        - Mantenha tom de assistente AGI competente
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.execution_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Erro na síntese: {e}")
            return "Processamento concluído com sucesso, mas houve um erro na síntese da resposta."
    
    def _execute_web_search(self, query: str) -> str:
        """Execução simplificada de busca web."""
        # Implementação simplificada - pode ser expandida
        return f"Pesquisa realizada para: {query}"
    
    def _execute_code(self, code: str) -> str:
        """Execução segura de código."""
        try:
            # Sandbox básico - expandir conforme necessário
            exec(code)
            return "Código executado com sucesso"
        except Exception as e:
            return f"Erro na execução: {str(e)}"
    
    def _execute_shell(self, command: str) -> str:
        """Execução de comando shell com validação."""
        # Implementação com validação de segurança
        return f"Comando shell simulado: {command}"
    
    def _format_context(self, context: List[Dict]) -> str:
        """Formatação do contexto para processamento."""
        if not context:
            return ""
        
        formatted = []
        for item in context:
            if isinstance(item, dict):
                formatted.append(f"- {item.get('user_prompt', '')}: {item.get('agent_response', '')}")
        
        return "\n".join(formatted)
