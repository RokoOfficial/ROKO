
"""
Pipeline AGI - Sistema simplificado focado em capacidades de Inteligência Artificial Geral.
"""

import os
import logging
import numpy as np
from typing import Dict, Any, Optional, List

from Memory import CognitiveMemory
from Agents.base_agent import BaseAgent
from Agents.agi_core import AGICore
from Pipeline.exceptions import APIKeyNotFoundError, RokoNexusError
from Pipeline.evolution_pipeline import EvolutionPipeline

class AGIPipeline:
    """
    Pipeline AGI - Sistema otimizado para processamento inteligente e autônomo.
    Foca em eficiência, confiabilidade e capacidades AGI avançadas.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise APIKeyNotFoundError("OPENAI_API_KEY não encontrada")
        
        # Componentes core
        self.memory = CognitiveMemory()
        self.base_agent = BaseAgent(self.api_key)
        self.agi_core = AGICore(self.api_key)
        
        # Sistema de evolução
        self.evolution_pipeline = EvolutionPipeline(self.api_key, self.memory)
        
        logging.info("AGIPipeline inicializado com sucesso - sistema de evolução ativo")
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Processamento principal - entrada única para todas as requisições.
        """
        try:
            # 1. Recuperar contexto relevante
            context = self._get_relevant_context(user_input)
            
            # 2. Processar com AGI Core
            result = self.agi_core.process_request(user_input, context)
            
            # 3. Salvar na memória
            self._save_to_memory(user_input, result)
            
            # 4. Retornar resultado estruturado
            return {
                "final_response": result.get("response", ""),
                "execution_log": result.get("execution_log", []),
                "analysis": result.get("analysis", {}),
                "success": result.get("success", True)
            }
            
        except Exception as e:
            logging.error(f"Erro no AGIPipeline: {e}")
            return {
                "final_response": "Erro interno no processamento. Sistema em recuperação automática.",
                "execution_log": [f"❌ Erro: {str(e)}"],
                "success": False
            }
    
    def _get_relevant_context(self, user_input: str) -> List[Dict]:
        """Recupera contexto relevante da memória."""
        try:
            embedding = self._get_embedding(user_input)
            context = self.memory.retrieve_context(embedding, top_k=3)
            return context
        except Exception as e:
            logging.warning(f"Erro ao recuperar contexto: {e}")
            return []
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Gera embedding para o texto."""
        try:
            response = self.base_agent.client.embeddings.create(
                input=text, 
                model="text-embedding-3-large"
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            raise RokoNexusError(f"Erro ao gerar embedding: {e}")
    
    def _save_to_memory(self, user_input: str, result: Dict):
        """Salva interação na memória cognitiva."""
        try:
            embedding = self._get_embedding(user_input)
            
            self.memory.save_interaction(
                interaction_type="agi_processing",
                user_prompt=user_input,
                agent_thoughts=str(result.get("analysis", {})),
                agent_response=result.get("response", ""),
                embedding=embedding,
                tags="agi,professional",
                category="general",
                importance_score=self._calculate_importance(result)
            )
        except Exception as e:
            logging.warning(f"Erro ao salvar na memória: {e}")
    
    def _calculate_importance(self, result: Dict) -> int:
        """Calcula importância da interação (1-10)."""
        analysis = result.get("analysis", {})
        
        if analysis.get("complexity") == "complexa":
            return 8
        elif analysis.get("complexity") == "moderada":
            return 6
        else:
            return 4
    
    def get_system_status(self) -> Dict[str, Any]:
        """Status do sistema AGI."""
        try:
            memory_stats = self.memory.get_memory_stats()
            evolution_status = self.evolution_pipeline.get_evolution_status()
            
            return {
                "status": "operational",
                "memory": memory_stats,
                "evolution": evolution_status,
                "capabilities": [
                    "advanced_reasoning",
                    "autonomous_execution", 
                    "continuous_learning",
                    "multi_domain_expertise",
                    "self_evolution",
                    "dynamic_agent_creation"
                ]
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def create_agent(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interface para criação de novos agentes.
        """
        try:
            return self.evolution_pipeline.agent_factory.create_agent(specification)
        except Exception as e:
            logging.error(f"Erro ao criar agente via pipeline: {e}")
            return {"success": False, "error": str(e)}
    
    def evolve_agent(self, agent_name: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interface para evolução de agentes específicos.
        """
        try:
            return self.evolution_pipeline.agent_factory.evolve_agent(agent_name, feedback)
        except Exception as e:
            logging.error(f"Erro ao evoluir agente via pipeline: {e}")
            return {"success": False, "error": str(e)}
    
    def trigger_evolution(self, target_agent: str = None) -> Dict[str, Any]:
        """
        Interface para disparar evolução manual.
        """
        try:
            return self.evolution_pipeline.manual_evolution_trigger(target_agent)
        except Exception as e:
            logging.error(f"Erro ao disparar evolução via pipeline: {e}")
            return {"success": False, "error": str(e)}
    
    def get_agent_registry(self) -> Dict[str, Any]:
        """
        Interface para obter registro de agentes.
        """
        try:
            return self.evolution_pipeline.agent_factory.get_registry()
        except Exception as e:
            logging.error(f"Erro ao obter registro de agentes: {e}")
            return {"error": str(e)}
