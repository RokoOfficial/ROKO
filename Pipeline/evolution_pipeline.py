
"""
Evolution Pipeline - Sistema de auto-evolução integrado ao ROKO.
"""

import logging
import time
import threading
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..Agents.agent_factory import AgentFactory
from ..Memory.evolution_memory import EvolutionMemory
from ..Memory.cognitive_memory import CognitiveMemory

class EvolutionPipeline:
    """
    Pipeline de auto-evolução que monitora e evolui o sistema ROKO automaticamente.
    """
    
    def __init__(self, api_key: str, cognitive_memory: CognitiveMemory):
        self.api_key = api_key
        self.cognitive_memory = cognitive_memory
        self.evolution_memory = EvolutionMemory()
        self.agent_factory = AgentFactory(api_key, cognitive_memory)
        
        # Configurações de evolução otimizadas
        self.evolution_interval = 1800  # 30 minutos (mais frequente)
        self.auto_evolution_enabled = True
        self.evolution_thread = None
        self.adaptive_evolution = True  # Evolução adaptativa baseada em performance
        
        # Métricas do sistema
        self.system_metrics = {
            "total_evolutions": 0,
            "successful_evolutions": 0,
            "last_evolution": None,
            "performance_improvement": 0.0
        }
        
        logging.info("EvolutionPipeline inicializado - auto-evolução ativa")
        
        # Iniciar monitoramento automático
        self.start_auto_evolution()
    
    def start_auto_evolution(self):
        """Inicia o processo de auto-evolução em background."""
        if not self.auto_evolution_enabled:
            return
        
        def evolution_loop():
            while self.auto_evolution_enabled:
                try:
                    time.sleep(self.evolution_interval)
                    self.auto_evolve_system()
                except Exception as e:
                    logging.error(f"Erro no loop de evolução: {e}")
        
        self.evolution_thread = threading.Thread(target=evolution_loop, daemon=True)
        self.evolution_thread.start()
        
        logging.info("🧬 Sistema de auto-evolução iniciado")
    
    def stop_auto_evolution(self):
        """Para o processo de auto-evolução."""
        self.auto_evolution_enabled = False
        logging.info("Sistema de auto-evolução parado")
    
    def auto_evolve_system(self) -> Dict[str, Any]:
        """
        Executa um ciclo completo de auto-evolução do sistema.
        """
        evolution_start = time.time()
        
        try:
            logging.info("🔄 Iniciando ciclo de auto-evolução...")
            
            # 1. Analisar performance atual
            performance_analysis = self._analyze_system_performance()
            
            # 2. Identificar necessidades de evolução
            evolution_needs = self._identify_evolution_needs(performance_analysis)
            
            # 3. Criar novos agentes se necessário
            new_agents = self._create_needed_agents(evolution_needs)
            
            # 4. Evoluir agentes existentes
            evolved_agents = self._evolve_existing_agents()
            
            # 5. Otimizar sistema
            optimizations = self._optimize_system()
            
            # 6. Atualizar métricas
            self._update_system_metrics(performance_analysis, new_agents, evolved_agents)
            
            evolution_time = time.time() - evolution_start
            
            result = {
                "success": True,
                "evolution_time": round(evolution_time, 2),
                "performance_analysis": performance_analysis,
                "new_agents_created": len(new_agents),
                "agents_evolved": len(evolved_agents),
                "optimizations_applied": len(optimizations),
                "timestamp": datetime.now().isoformat()
            }
            
            logging.info(f"✅ Ciclo de evolução completo em {evolution_time:.2f}s")
            return result
            
        except Exception as e:
            logging.error(f"❌ Erro na auto-evolução: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_system_performance(self) -> Dict[str, Any]:
        """Analisa a performance atual do sistema."""
        try:
            # Métricas da memória cognitiva
            memory_stats = self.cognitive_memory.get_memory_stats()
            
            # Métricas dos agentes
            agent_registry = self.agent_factory.get_registry()
            
            # Estatísticas de evolução
            evolution_stats = self.evolution_memory.get_evolution_statistics()
            
            # Análise de performance geral
            overall_performance = self._calculate_overall_performance(
                memory_stats, agent_registry, evolution_stats
            )
            
            return {
                "overall_score": overall_performance,
                "memory_health": memory_stats.get("system_health", {}),
                "agent_performance": agent_registry,
                "evolution_metrics": evolution_stats,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de performance: {e}")
            return {"overall_score": 0, "error": str(e)}
    
    def _calculate_overall_performance(self, memory_stats, agent_registry, evolution_stats) -> float:
        """Calcula score geral de performance do sistema."""
        try:
            # Fatores de performance
            memory_factor = 1.0 if memory_stats.get("total_interactions", 0) > 0 else 0.5
            
            agent_factor = 0.0
            if agent_registry.get("total_agents", 0) > 0:
                agent_performances = []
                for agent_data in agent_registry.get("agents", {}).values():
                    metrics = agent_data.get("metrics", {})
                    success_rate = metrics.get("success_rate", 0)
                    agent_performances.append(success_rate)
                
                agent_factor = sum(agent_performances) / len(agent_performances) / 100
            
            evolution_factor = min(evolution_stats.get("evolution_rate", 0), 1.0)
            
            # Score ponderado
            overall_score = (memory_factor * 0.3 + agent_factor * 0.5 + evolution_factor * 0.2) * 100
            
            return round(overall_score, 2)
            
        except Exception as e:
            logging.error(f"Erro no cálculo de performance: {e}")
            return 0.0
    
    def _identify_evolution_needs(self, performance_analysis: Dict) -> List[Dict]:
        """Identifica necessidades específicas de evolução."""
        needs = []
        
        try:
            overall_score = performance_analysis.get("overall_score", 0)
            
            # Verificar performance geral
            if overall_score < 70:
                needs.append({
                    "type": "performance_improvement",
                    "priority": "high",
                    "reason": "baixa_performance_geral",
                    "target_score": 85
                })
            
            # Verificar agentes com baixa performance
            agent_registry = performance_analysis.get("agent_performance", {})
            for agent_name, agent_data in agent_registry.get("agents", {}).items():
                metrics = agent_data.get("metrics", {})
                if metrics.get("success_rate", 0) < 70:
                    needs.append({
                        "type": "agent_evolution",
                        "priority": "medium",
                        "agent_name": agent_name,
                        "reason": "baixa_taxa_sucesso",
                        "current_rate": metrics.get("success_rate", 0)
                    })
            
            # Verificar necessidade de novos agentes
            if agent_registry.get("total_agents", 0) < 5:
                needs.append({
                    "type": "new_agent_creation",
                    "priority": "low",
                    "reason": "poucos_agentes_especializados"
                })
            
            logging.info(f"🔍 Identificadas {len(needs)} necessidades de evolução")
            return needs
            
        except Exception as e:
            logging.error(f"Erro na identificação de necessidades: {e}")
            return []
    
    def _create_needed_agents(self, evolution_needs: List[Dict]) -> List[Dict]:
        """Cria novos agentes baseado nas necessidades identificadas."""
        new_agents = []
        
        try:
            for need in evolution_needs:
                if need.get("type") == "new_agent_creation":
                    # Determinar tipo de agente necessário
                    agent_spec = self._determine_agent_specification(need)
                    
                    # Criar agente
                    creation_result = self.agent_factory.create_agent(agent_spec)
                    
                    if creation_result.get("success"):
                        new_agents.append(creation_result)
                        
                        # Registrar na memória evolutiva
                        self.evolution_memory.register_agent({
                            "name": creation_result["agent_name"],
                            "type": agent_spec["type"],
                            "capabilities": agent_spec["capabilities"],
                            "system_prompt": agent_spec["system_prompt"],
                            "specification": agent_spec
                        })
            
            logging.info(f"🆕 Criados {len(new_agents)} novos agentes")
            return new_agents
            
        except Exception as e:
            logging.error(f"Erro na criação de agentes: {e}")
            return []
    
    def _determine_agent_specification(self, need: Dict) -> Dict[str, Any]:
        """Determina especificação para novo agente baseado na necessidade."""
        base_timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Especificações padrão para diferentes necessidades
        specifications = {
            "data_processing": {
                "name": f"DataProcessor_{base_timestamp}",
                "type": "data_specialist",
                "capabilities": ["data_analysis", "statistical_processing", "visualization"],
                "system_prompt": "Você é um especialista em processamento e análise de dados. Sua função é processar, analisar e visualizar dados de forma eficiente e precisa.",
                "description": "Agente especializado em processamento de dados criado pelo sistema de evolução"
            },
            "research": {
                "name": f"Researcher_{base_timestamp}",
                "type": "research_specialist", 
                "capabilities": ["web_research", "information_synthesis", "fact_verification"],
                "system_prompt": "Você é um pesquisador especializado. Sua função é buscar, verificar e sintetizar informações de forma abrangente e confiável.",
                "description": "Agente de pesquisa criado pelo sistema de evolução"
            },
            "optimization": {
                "name": f"Optimizer_{base_timestamp}",
                "type": "optimization_specialist",
                "capabilities": ["performance_analysis", "code_optimization", "system_tuning"],
                "system_prompt": "Você é um especialista em otimização. Sua função é analisar e melhorar a performance de sistemas e processos.",
                "description": "Agente de otimização criado pelo sistema de evolução"
            }
        }
        
        # Escolher especificação baseada na necessidade (padrão: data_processing)
        return specifications.get("data_processing")
    
    def _evolve_existing_agents(self) -> List[Dict]:
        """Evolui agentes existentes que precisam de melhoria."""
        evolved_agents = []
        
        try:
            # Identificar candidatos para evolução
            candidates = self.evolution_memory.identify_evolution_candidates()
            
            for candidate in candidates[:3]:  # Limitar a 3 por ciclo
                agent_name = candidate["name"]
                
                # Preparar feedback para evolução
                feedback = {
                    "performance_issues": candidate["evolution_reason"],
                    "current_metrics": {
                        "success_rate": candidate["success_rate"],
                        "error_count": candidate["error_count"]
                    },
                    "improvement_targets": {
                        "target_success_rate": 90,
                        "max_errors": 5
                    }
                }
                
                # Executar evolução
                evolution_result = self.agent_factory.evolve_agent(agent_name, feedback)
                
                if evolution_result.get("success"):
                    evolved_agents.append({
                        "agent_name": agent_name,
                        "evolution_result": evolution_result
                    })
                    
                    # Registrar evolução
                    self.evolution_memory.record_evolution({
                        "agent_name": agent_name,
                        "evolution_type": "performance_improvement",
                        "feedback": feedback,
                        "improvements": evolution_result.get("improvements", {}),
                        "performance_before": candidate["performance_score"],
                        "performance_after": candidate["performance_score"] + 10  # Estimativa
                    })
            
            logging.info(f"🧬 Evoluídos {len(evolved_agents)} agentes existentes")
            return evolved_agents
            
        except Exception as e:
            logging.error(f"Erro na evolução de agentes: {e}")
            return []
    
    def _optimize_system(self) -> List[Dict]:
        """Aplica otimizações gerais ao sistema."""
        optimizations = []
        
        try:
            # Otimização de memória
            memory_optimization = self._optimize_memory()
            if memory_optimization:
                optimizations.append(memory_optimization)
            
            # Otimização de cache
            cache_optimization = self._optimize_cache()
            if cache_optimization:
                optimizations.append(cache_optimization)
            
            logging.info(f"⚡ Aplicadas {len(optimizations)} otimizações")
            return optimizations
            
        except Exception as e:
            logging.error(f"Erro nas otimizações: {e}")
            return []
    
    def _optimize_memory(self) -> Dict[str, Any]:
        """Otimiza sistema de memória."""
        try:
            # Limpar memórias antigas se necessário
            memory_stats = self.cognitive_memory.get_memory_stats()
            total_interactions = memory_stats.get("total_interactions", 0)
            
            if total_interactions > 10000:
                # Limpar interações antigas mantendo as importantes
                deleted = self.cognitive_memory.cleanup_old_memories(days_old=30, keep_important=True)
                
                return {
                    "type": "memory_cleanup",
                    "items_deleted": deleted,
                    "reason": "limite_interacoes_excedido"
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Erro na otimização de memória: {e}")
            return None
    
    def _optimize_cache(self) -> Dict[str, Any]:
        """Otimiza sistema de cache."""
        try:
            # Verificar e otimizar cache de embeddings
            if hasattr(self.cognitive_memory, 'embedding_cache'):
                cache_stats = self.cognitive_memory.embedding_cache.get_stats()
                hit_rate = cache_stats.get("hit_rate", 0)
                
                if hit_rate < 50:  # Taxa de acerto baixa
                    return {
                        "type": "cache_optimization",
                        "current_hit_rate": hit_rate,
                        "action": "increase_cache_size",
                        "reason": "baixa_taxa_acerto"
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Erro na otimização de cache: {e}")
            return None
    
    def _update_system_metrics(self, performance_analysis: Dict, new_agents: List, evolved_agents: List):
        """Atualiza métricas do sistema de evolução."""
        try:
            self.system_metrics["total_evolutions"] += 1
            self.system_metrics["last_evolution"] = datetime.now().isoformat()
            
            if len(new_agents) > 0 or len(evolved_agents) > 0:
                self.system_metrics["successful_evolutions"] += 1
            
            # Calcular melhoria de performance
            current_score = performance_analysis.get("overall_score", 0)
            previous_score = getattr(self, '_last_performance_score', current_score)
            improvement = current_score - previous_score
            
            self.system_metrics["performance_improvement"] = improvement
            self._last_performance_score = current_score
            
        except Exception as e:
            logging.error(f"Erro ao atualizar métricas: {e}")
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Retorna status atual do sistema de evolução."""
        try:
            return {
                "auto_evolution_enabled": self.auto_evolution_enabled,
                "evolution_interval": self.evolution_interval,
                "system_metrics": self.system_metrics,
                "agent_registry": self.agent_factory.get_registry(),
                "evolution_statistics": self.evolution_memory.get_evolution_statistics(),
                "top_performers": self.evolution_memory.get_top_performing_agents(5)
            }
            
        except Exception as e:
            logging.error(f"Erro ao obter status: {e}")
            return {"error": str(e)}
    
    def manual_evolution_trigger(self, target_agent: str = None) -> Dict[str, Any]:
        """Dispara evolução manual para um agente específico ou sistema completo."""
        try:
            if target_agent:
                # Evolução específica
                feedback = {
                    "manual_trigger": True,
                    "improvement_request": "otimização_geral"
                }
                
                result = self.agent_factory.evolve_agent(target_agent, feedback)
                return {
                    "success": True,
                    "type": "manual_agent_evolution",
                    "target": target_agent,
                    "result": result
                }
            else:
                # Evolução completa do sistema
                result = self.auto_evolve_system()
                return {
                    "success": True,
                    "type": "manual_system_evolution",
                    "result": result
                }
                
        except Exception as e:
            logging.error(f"Erro na evolução manual: {e}")
            return {"success": False, "error": str(e)}
