"""
Agente de Contexto Adaptativo - Aprende e adapta estratégias baseado em experiências passadas.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class AdaptiveContextAgent(BaseAgent):
    """Agente que mantém e adapta contexto baseado em experiências passadas."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.success_patterns = {}
        self.failure_patterns = {}
        self.adaptation_threshold = 0.7

    def analyze_execution_pattern(self, task_type: str, execution_history: List[Dict]) -> Dict[str, Any]:
        """Analisa padrões de execução para um tipo de tarefa."""
        logging.info(f"AdaptiveContextAgent analisando padrões para {task_type}...")

        system_prompt = """
        Você é um agente de análise de padrões. Analise o histórico de execuções
        e identifique padrões de sucesso e falha para otimização futura.

        Responda APENAS com um JSON contendo:
        - "success_factors": fatores que levam ao sucesso
        - "failure_factors": fatores que causam falhas
        - "optimization_suggestions": sugestões de otimização
        - "confidence_pattern": 0-100 (confiança no padrão identificado)
        """

        user_content = f"""
        Tipo de Tarefa: {task_type}
        Histórico de Execuções: {json.dumps(execution_history, default=str)}

        Identifique padrões claros de sucesso e falha.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.4
            )

            pattern_analysis = json.loads(response.choices[0].message.content)

            # Armazenar padrões identificados
            if pattern_analysis.get('confidence_pattern', 0) > 70:
                if task_type not in self.success_patterns:
                    self.success_patterns[task_type] = []
                self.success_patterns[task_type].append(pattern_analysis['success_factors'])

                if task_type not in self.failure_patterns:
                    self.failure_patterns[task_type] = []
                self.failure_patterns[task_type].append(pattern_analysis['failure_factors'])

            logging.info(f"🧠 Padrões identificados para {task_type} - Confiança: {pattern_analysis.get('confidence_pattern', 0)}%")
            return pattern_analysis

        except Exception as e:
            logging.error(f"Erro na análise de padrões: {e}")
            return {
                "success_factors": [],
                "failure_factors": [],
                "optimization_suggestions": [],
                "confidence_pattern": 0
            }

    def adapt_strategy(self, task: str, current_approach: str) -> str:
        """Adapta a estratégia baseada em padrões aprendidos."""
        if not self.success_patterns:
            return current_approach

        system_prompt = """
        Baseado nos padrões de sucesso aprendidos, adapte e melhore a estratégia atual
        para maximizar as chances de sucesso.
        """

        user_content = f"""
        Tarefa: {task}
        Estratégia Atual: {current_approach}

        Padrões de Sucesso Conhecidos: {json.dumps(self.success_patterns, default=str)}
        Padrões de Falha a Evitar: {json.dumps(self.failure_patterns, default=str)}

        Adapte a estratégia para incorporar os fatores de sucesso e evitar os de falha.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.6
            )

            adapted_strategy = response.choices[0].message.content
            logging.info("🎯 Estratégia adaptada baseada em padrões aprendidos")
            return adapted_strategy

        except Exception as e:
            logging.error(f"Erro na adaptação de estratégia: {e}")
            return current_approach