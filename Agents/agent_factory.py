
"""
Agent Factory - Sistema de criação dinâmica de agentes com auto-evolução.
"""

import os
import json
import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
from .base_agent import BaseAgent

class AgentFactory:
    """
    Fábrica de agentes com capacidade de criação dinâmica e evolução.
    """
    
    def __init__(self, api_key: str, memory_system=None):
        self.api_key = api_key
        self.memory = memory_system
        self.agent_registry = {}
        self.evolution_history = []
        self.templates_path = "ROKO/Agents/templates"
        
        # Criar diretório de templates se não existir
        os.makedirs(self.templates_path, exist_ok=True)
        
        logging.info("AgentFactory inicializada - sistema de evolução ativo")
    
    def create_agent(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo agente baseado na especificação fornecida.
        """
        try:
            agent_name = specification.get("name", f"Agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            agent_type = specification.get("type", "specialized")
            capabilities = specification.get("capabilities", [])
            system_prompt = specification.get("system_prompt", "")
            
            # Gerar código do agente
            agent_code = self._generate_agent_code(
                name=agent_name,
                type=agent_type,
                capabilities=capabilities,
                system_prompt=system_prompt,
                specification=specification
            )
            
            # Salvar agente em arquivo
            agent_file_path = f"ROKO/Agents/{agent_name.lower()}_agent.py"
            with open(agent_file_path, 'w', encoding='utf-8') as f:
                f.write(agent_code)
            
            # Carregar e registrar agente
            agent_class = self._load_agent_class(agent_file_path, agent_name)
            agent_instance = agent_class(self.api_key)
            
            # Registrar no sistema
            self.agent_registry[agent_name] = {
                "class": agent_class,
                "instance": agent_instance,
                "file_path": agent_file_path,
                "specification": specification,
                "created_at": datetime.now().isoformat(),
                "performance_metrics": {
                    "success_rate": 0.0,
                    "avg_response_time": 0.0,
                    "usage_count": 0
                }
            }
            
            # Salvar na memória evolutiva
            if self.memory:
                self._save_agent_to_memory(agent_name, specification, agent_code)
            
            # Registrar evolução
            self.evolution_history.append({
                "action": "agent_created",
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "specification": specification
            })
            
            logging.info(f"✅ Agente '{agent_name}' criado e registrado com sucesso")
            
            return {
                "success": True,
                "agent_name": agent_name,
                "agent_instance": agent_instance,
                "capabilities": capabilities,
                "file_path": agent_file_path
            }
            
        except Exception as e:
            logging.error(f"❌ Erro ao criar agente: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_agent_code(self, name: str, type: str, capabilities: List[str], 
                           system_prompt: str, specification: Dict) -> str:
        """
        Gera o código Python para o novo agente.
        """
        class_name = f"{name.replace('_', '').title()}Agent"
        
        # Template base do agente
        agent_template = f'''"""
{name} - Agente criado dinamicamente pelo sistema de evolução ROKO.
Criado em: {datetime.now().isoformat()}
Tipo: {type}
Capacidades: {', '.join(capabilities)}
"""

import logging
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent

class {class_name}(BaseAgent):
    """
    {name} - {specification.get('description', 'Agente especializado criado dinamicamente')}
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "{name}"
        self.type = "{type}"
        self.capabilities = {capabilities}
        self.system_prompt = """{system_prompt}"""
        self.performance_metrics = {{
            "total_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0.0
        }}
    
    def process_request(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """
        Processamento principal do agente.
        """
        import time
        start_time = time.time()
        
        try:
            logging.info(f"{self.name} processando requisição...")
            
            # Incrementar métricas
            self.performance_metrics["total_requests"] += 1
            
            # Processar baseado nas capacidades
            result = self._execute_capabilities(user_input, context)
            
            # Atualizar métricas de sucesso
            self.performance_metrics["successful_requests"] += 1
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            return {{
                "success": True,
                "response": result,
                "agent_name": self.name,
                "capabilities_used": self.capabilities,
                "response_time": response_time
            }}
            
        except Exception as e:
            logging.error(f"Erro no {self.name}: {{e}}")
            return {{
                "success": False,
                "error": str(e),
                "agent_name": self.name
            }}
    
    def _execute_capabilities(self, user_input: str, context: Dict) -> str:
        """
        Executa as capacidades específicas do agente.
        """
        # Preparar prompt contextual
        capability_prompt = f"""
        Você é {self.name}, um agente especializado com as seguintes capacidades:
        {', '.join(self.capabilities)}
        
        {self.system_prompt}
        
        Requisição do usuário: {user_input}
        Contexto: {json.dumps(context or {{}}, indent=2)}
        
        Execute suas capacidades especializadas para atender esta requisição.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {{"role": "system", "content": self.system_prompt}},
                    {{"role": "user", "content": capability_prompt}}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Erro na execução de capacidades: {{e}}"
    
    def evolve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evolui o agente baseado no feedback recebido.
        """
        try:
            # Analisar feedback e sugerir melhorias
            evolution_prompt = f"""
            Analise o feedback do agente {self.name} e sugira melhorias:
            
            Feedback: {json.dumps(feedback, indent=2)}
            Capacidades atuais: {self.capabilities}
            Métricas: {json.dumps(self.performance_metrics, indent=2)}
            
            Sugira melhorias específicas para:
            1. System prompt
            2. Capacidades adicionais
            3. Otimizações de performance
            
            Responda em JSON com as sugestões.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {{"role": "user", "content": evolution_prompt}}
                ],
                temperature=0.2
            )
            
            evolution_suggestions = json.loads(response.choices[0].message.content)
            
            return {{
                "success": True,
                "evolution_suggestions": evolution_suggestions,
                "current_performance": self.performance_metrics
            }}
            
        except Exception as e:
            logging.error(f"Erro na evolução do {self.name}: {{e}}")
            return {{"success": False, "error": str(e)}}
    
    def _update_response_time(self, new_time: float):
        """Atualiza tempo médio de resposta."""
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]
        
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + new_time) / total_requests
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do agente."""
        success_rate = (
            self.performance_metrics["successful_requests"] / 
            max(self.performance_metrics["total_requests"], 1)
        ) * 100
        
        return {{
            "name": self.name,
            "type": self.type,
            "capabilities": self.capabilities,
            "success_rate": round(success_rate, 2),
            "total_requests": self.performance_metrics["total_requests"],
            "average_response_time": round(self.performance_metrics["average_response_time"], 3)
        }}
'''
        
        return agent_template
    
    def _load_agent_class(self, file_path: str, agent_name: str) -> Type[BaseAgent]:
        """
        Carrega dinamicamente a classe do agente do arquivo.
        """
        try:
            # Converter caminho para módulo
            module_path = file_path.replace('/', '.').replace('.py', '')
            
            # Importar módulo dinamicamente
            spec = importlib.util.spec_from_file_location(agent_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Encontrar classe do agente
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj != BaseAgent:
                    return obj
            
            raise Exception(f"Classe de agente não encontrada em {file_path}")
            
        except Exception as e:
            logging.error(f"Erro ao carregar agente: {e}")
            raise
    
    def _save_agent_to_memory(self, name: str, specification: Dict, code: str):
        """
        Salva o agente na memória evolutiva.
        """
        try:
            import numpy as np
            
            # Criar embedding do agente
            agent_description = f"Agente: {name}\nTipo: {specification.get('type')}\nCapacidades: {', '.join(specification.get('capabilities', []))}\nCódigo: {code[:1000]}"
            
            response = self.memory.base_agent.client.embeddings.create(
                input=agent_description,
                model="text-embedding-3-large"
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # Salvar na memória
            self.memory.save_interaction(
                interaction_type="agent_evolution",
                user_prompt=f"Criação do agente {name}",
                agent_thoughts=json.dumps(specification),
                agent_response=f"Agente {name} criado com capacidades: {', '.join(specification.get('capabilities', []))}",
                embedding=embedding,
                tags=f"agent,evolution,{specification.get('type', 'specialized')}",
                category="agent_creation",
                importance_score=9
            )
            
            logging.info(f"💾 Agente {name} salvo na memória evolutiva")
            
        except Exception as e:
            logging.warning(f"Erro ao salvar agente na memória: {e}")
    
    def evolve_agent(self, agent_name: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evolui um agente existente baseado no feedback.
        """
        if agent_name not in self.agent_registry:
            return {"success": False, "error": "Agente não encontrado"}
        
        try:
            agent_info = self.agent_registry[agent_name]
            agent_instance = agent_info["instance"]
            
            # Executar evolução
            evolution_result = agent_instance.evolve(feedback)
            
            if evolution_result.get("success"):
                # Aplicar melhorias sugeridas
                suggestions = evolution_result.get("evolution_suggestions", {})
                
                # Atualizar especificação
                updated_spec = agent_info["specification"].copy()
                if "new_capabilities" in suggestions:
                    updated_spec["capabilities"].extend(suggestions["new_capabilities"])
                if "improved_system_prompt" in suggestions:
                    updated_spec["system_prompt"] = suggestions["improved_system_prompt"]
                
                # Recriar agente evoluído
                evolved_agent = self.create_agent(updated_spec)
                
                if evolved_agent.get("success"):
                    # Registrar evolução
                    self.evolution_history.append({
                        "action": "agent_evolved",
                        "agent_name": agent_name,
                        "timestamp": datetime.now().isoformat(),
                        "feedback": feedback,
                        "improvements": suggestions
                    })
                    
                    logging.info(f"🧬 Agente {agent_name} evoluído com sucesso")
                    
                    return {
                        "success": True,
                        "evolution_applied": True,
                        "improvements": suggestions,
                        "new_agent": evolved_agent
                    }
            
            return evolution_result
            
        except Exception as e:
            logging.error(f"Erro na evolução do agente {agent_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_registry(self) -> Dict[str, Any]:
        """
        Retorna o registro completo de agentes.
        """
        registry_summary = {}
        
        for name, info in self.agent_registry.items():
            registry_summary[name] = {
                "type": info["specification"].get("type"),
                "capabilities": info["specification"].get("capabilities"),
                "created_at": info["created_at"],
                "metrics": info["instance"].get_metrics() if hasattr(info["instance"], "get_metrics") else {}
            }
        
        return {
            "total_agents": len(self.agent_registry),
            "agents": registry_summary,
            "evolution_history": self.evolution_history[-10:]  # Últimas 10 evoluções
        }
    
    def auto_evolve_system(self) -> Dict[str, Any]:
        """
        Sistema de auto-evolução baseado em métricas de performance.
        """
        try:
            evolution_results = []
            
            for name, info in self.agent_registry.items():
                agent_instance = info["instance"]
                
                if hasattr(agent_instance, "get_metrics"):
                    metrics = agent_instance.get_metrics()
                    
                    # Verificar se precisa evoluir (baixa performance)
                    if metrics.get("success_rate", 100) < 70:
                        feedback = {
                            "performance_issue": "low_success_rate",
                            "current_metrics": metrics,
                            "suggestion": "improve_capability_execution"
                        }
                        
                        evolution_result = self.evolve_agent(name, feedback)
                        evolution_results.append({
                            "agent": name,
                            "evolution": evolution_result
                        })
            
            return {
                "success": True,
                "evolutions_applied": len(evolution_results),
                "results": evolution_results
            }
            
        except Exception as e:
            logging.error(f"Erro na auto-evolução: {e}")
            return {"success": False, "error": str(e)}
