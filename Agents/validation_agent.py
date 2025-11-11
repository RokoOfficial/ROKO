"""
Agente de Validação - Verifica e valida resultados de outros agentes.
"""

import logging
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ValidationAgent(BaseAgent):
    """Agente que valida e verifica a qualidade dos resultados de outros agentes."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.validation_criteria = {
            'web_search': ['relevance', 'completeness', 'accuracy'],
            'code_execution': ['syntax', 'logic', 'output_quality'],
            'shell_command': ['safety', 'effectiveness', 'error_handling']
        }

    def validate_result(self, agent_type: str, task: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Valida o resultado de um agente específico."""
        logging.info(f"ValidationAgent validando resultado de {agent_type}...")

        system_prompt = f"""
        Você é um agente de validação especializado. Sua tarefa é analisar criticamente 
        os resultados de outros agentes e fornecer uma avaliação detalhada.

        Critérios de validação para {agent_type}:
        {json.dumps(self.validation_criteria.get(agent_type, []), indent=2)}

        Responda APENAS com um JSON contendo:
        - "is_valid": boolean
        - "confidence_score": 0-100
        - "issues": lista de problemas encontrados
        - "suggestions": lista de melhorias
        - "quality_score": 0-10
        """

        user_content = f"""
        Tipo de Agente: {agent_type}
        Tarefa Original: {task}
        Resultado Obtido: {json.dumps(result, default=str)}

        Analise a qualidade, precisão e completude deste resultado.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3
            )

            validation_result = json.loads(response.choices[0].message.content)
            logging.info(f"✅ Validação concluída - Qualidade: {validation_result.get('quality_score', 0)}/10")
            return validation_result

        except Exception as e:
            logging.error(f"Erro na validação: {e}")
            return {
                "is_valid": False,
                "confidence_score": 0,
                "issues": [f"Erro na validação: {str(e)}"],
                "suggestions": ["Revisar processo de validação"],
                "quality_score": 0
            }

    def suggest_improvements(self, agent_type: str, validation_results: List[Dict]) -> Dict[str, Any]:
        """Sugere melhorias baseadas em múltiplas validações."""
        system_prompt = """
        Analise o histórico de validações e sugira melhorias específicas para tornar 
        o agente mais eficiente e preciso. Foque em padrões de erro e oportunidades de otimização.
        """

        user_content = f"""
        Agente: {agent_type}
        Histórico de Validações: {json.dumps(validation_results, default=str)}

        Identifique padrões e sugira melhorias concretas.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7
            )

            return {"improvements": response.choices[0].message.content}

        except Exception as e:
            logging.error(f"Erro ao gerar sugestões: {e}")
            return {"improvements": "Erro ao gerar sugestões de melhoria"}