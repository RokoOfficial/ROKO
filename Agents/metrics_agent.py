
"""
Agente de Métricas - Monitora e analisa performance dos agentes.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
from .base_agent import BaseAgent

class MetricsAgent(BaseAgent):
    """Agente que monitora métricas de performance de todos os outros agentes."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.metrics_db = defaultdict(list)
        self.performance_thresholds = {
            'success_rate': 0.8,  # 80%
            'avg_execution_time': 30.0,  # 30 segundos
            'error_rate': 0.2  # 20%
        }
    
    def record_execution(self, agent_name: str, task: str, success: bool, 
                        execution_time: float, error_msg: str = None) -> None:
        """Registra uma execução de agente para análise posterior."""
        timestamp = datetime.now().isoformat()
        
        execution_record = {
            'timestamp': timestamp,
            'agent_name': agent_name,
            'task': task,
            'success': success,
            'execution_time': execution_time,
            'error_msg': error_msg
        }
        
        self.metrics_db[agent_name].append(execution_record)
        logging.info(f"📊 Métricas registradas para {agent_name}: {'✅' if success else '❌'} ({execution_time:.2f}s)")
    
    def analyze_agent_performance(self, agent_name: str, days_back: int = 7) -> Dict[str, Any]:
        """Analisa a performance de um agente específico."""
        if agent_name not in self.metrics_db:
            return {"error": f"Nenhuma métrica disponível para {agent_name}"}
        
        records = self.metrics_db[agent_name]
        if not records:
            return {"error": f"Nenhum registro encontrado para {agent_name}"}
        
        # Calcular métricas básicas
        total_executions = len(records)
        successful_executions = sum(1 for r in records if r['success'])
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        execution_times = [r['execution_time'] for r in records]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        error_rate = (total_executions - successful_executions) / total_executions if total_executions > 0 else 0
        
        # Identificar erros mais comuns
        error_messages = [r['error_msg'] for r in records if r['error_msg']]
        common_errors = {}
        for error in error_messages:
            if error:
                common_errors[error] = common_errors.get(error, 0) + 1
        
        # Status de saúde
        health_status = "HEALTHY"
        if success_rate < self.performance_thresholds['success_rate']:
            health_status = "CRITICAL"
        elif avg_execution_time > self.performance_thresholds['avg_execution_time']:
            health_status = "WARNING"
        elif error_rate > self.performance_thresholds['error_rate']:
            health_status = "WARNING"
        
        return {
            'agent_name': agent_name,
            'total_executions': total_executions,
            'success_rate': round(success_rate * 100, 2),
            'avg_execution_time': round(avg_execution_time, 2),
            'error_rate': round(error_rate * 100, 2),
            'health_status': health_status,
            'common_errors': dict(sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:5]),
            'recommendations': self._generate_recommendations(agent_name, success_rate, avg_execution_time, error_rate)
        }
    
    def _generate_recommendations(self, agent_name: str, success_rate: float, 
                                avg_time: float, error_rate: float) -> List[str]:
        """Gera recomendações baseadas nas métricas."""
        recommendations = []
        
        if success_rate < 0.7:
            recommendations.append(f"Taxa de sucesso baixa ({success_rate*100:.1f}%) - Revisar lógica de execução")
        
        if avg_time > 20.0:
            recommendations.append(f"Tempo de execução alto ({avg_time:.1f}s) - Otimizar performance")
        
        if error_rate > 0.3:
            recommendations.append(f"Taxa de erro alta ({error_rate*100:.1f}%) - Melhorar tratamento de erros")
        
        if not recommendations:
            recommendations.append("Performance dentro dos parâmetros esperados")
        
        return recommendations
    
    def generate_system_report(self) -> str:
        """Gera um relatório completo do sistema."""
        system_prompt = """
        Você é um analista de sistemas especializato. Baseado nas métricas fornecidas,
        gere um relatório completo sobre a saúde e performance do sistema ROKO.
        
        Inclua:
        - Resumo executivo
        - Principais problemas identificados
        - Recomendações prioritárias
        - Tendências observadas
        """
        
        # Coletar métricas de todos os agentes
        all_metrics = {}
        for agent_name in self.metrics_db.keys():
            all_metrics[agent_name] = self.analyze_agent_performance(agent_name)
        
        user_content = f"""
        Métricas do Sistema ROKO:
        {json.dumps(all_metrics, indent=2, default=str)}
        
        Gere um relatório detalhado sobre o estado atual do sistema.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao gerar relatório: {e}"
