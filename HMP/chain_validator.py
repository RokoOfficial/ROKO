
"""
Validador de conexões das cadeias HMP.
Garante que todas as funções estão registradas e conectadas ao router.
"""

import logging
from typing import Dict, List, Any
from .hmp_router import HMPRouter
from .hmp_tools import HMPTools

class HMPChainValidator:
    """Valida se as cadeias HMP estão corretamente conectadas."""
    
    def __init__(self):
        self.logger = logging.getLogger('HMP.ChainValidator')
    
    def validate_all_connections(self, api_key: str) -> Dict[str, Any]:
        """Valida todas as conexões do sistema HMP."""
        results = {
            "status": "checking",
            "router_initialized": False,
            "debugging_chain_available": False,
            "functions_registered": [],
            "missing_functions": [],
            "artifacts_forced_to_artefatos": False,
            "total_chains": 0
        }
        
        try:
            # 1. Verificar inicialização do router
            router = HMPRouter(api_key)
            results["router_initialized"] = True
            results["total_chains"] = len(router.get_available_chains())
            
            # 2. Verificar se debugging chain está disponível
            available_chains = router.get_available_chains()
            if 'debugger_root_cause_analysis' in available_chains:
                results["debugging_chain_available"] = True
            
            # 3. Verificar funções de debugging registradas
            debugging_functions = [
                'collect_error_payload',
                'parse_stack_trace', 
                'static_analyze',
                'synthesize_causes',
                'generate_patch',
                'validate_fix'
            ]
            
            for func_name in debugging_functions:
                if hasattr(HMPTools, '_instance') and func_name in HMPTools._instance.registered_functions:
                    results["functions_registered"].append(func_name)
                else:
                    results["missing_functions"].append(func_name)
            
            # 4. Verificar se artefatos são forçados para ARTEFATOS
            from ..Agents.artifact_manager import ArtifactManager
            artifact_manager = ArtifactManager()
            if hasattr(artifact_manager.save_artifact, '__code__') and 'force_artifacts_dir' in artifact_manager.save_artifact.__code__.co_varnames:
                results["artifacts_forced_to_artefatos"] = True
            
            # 5. Status final
            if (results["router_initialized"] and 
                results["debugging_chain_available"] and
                len(results["missing_functions"]) == 0 and
                results["artifacts_forced_to_artefatos"]):
                results["status"] = "all_connected"
            else:
                results["status"] = "partially_connected"
                
            self.logger.info(f"✅ Validação HMP: {results['status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Erro na validação HMP: {e}")
            results["status"] = "validation_failed"
            results["error"] = str(e)
            return results
    
    def test_debugging_chain(self, api_key: str, test_error: str = "TypeError: 'NoneType' object is not subscriptable") -> Dict[str, Any]:
        """Testa a cadeia de debugging com um erro exemplo."""
        try:
            router = HMPRouter(api_key)
            
            # Testar classificação
            request_type = router._classify_request(f"Preciso ajuda com este erro: {test_error}")
            
            # Testar execução da cadeia
            context = {"test_mode": True}
            result = router.route_request(f"Debug este erro: {test_error}", context)
            
            return {
                "test_passed": True,
                "classified_as": request_type,
                "execution_result": result.get("success", False),
                "chain_used": result.get("chain_used", "unknown")
            }
            
        except Exception as e:
            return {
                "test_passed": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # Teste rápido
    validator = HMPChainValidator()
    results = validator.validate_all_connections("test-key")
    print(f"Status das conexões HMP: {results['status']}")
    print(f"Funções registradas: {len(results['functions_registered'])}")
    print(f"Chains disponíveis: {results['total_chains']}")
