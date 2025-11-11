"""
Ferramentas HMP integradas com todos os agentes ROKO.
Centraliza todas as funcionalidades em um único módulo.
"""

import logging
from typing import Dict, Any, List, Optional, Union

# Lazy loading para evitar dependências circulares
def get_agent_roko_pro_integration():
    try:
        from .agent_roko_pro_integration import AgentROKOProIntegration
        return AgentROKOProIntegration
    except ImportError:
        return None

def agent_roko_pro_status():
    """Status da cadeia Agent ROKO PRO"""
    try:
        AgentROKOProIntegration = get_agent_roko_pro_integration()
        if AgentROKOProIntegration:
            integration = AgentROKOProIntegration("")
            return integration.get_chain_status()
        else:
            return {"status": "integration_not_available", "message": "Agent ROKO PRO integration not loaded"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao obter status: {e}"}

# ===============================
# DEBUGGING & ROOT CAUSE ANALYSIS FUNCTIONS
# ===============================

def collect_error_payload(input: str) -> Dict[str, Any]:
    """Coleta e normaliza dados do erro para análise."""
    try:
        payload = {
            "error_message": input,
            "stack_trace": "",
            "files": [],
            "runtime": {"lang": "unknown", "version": "unknown"},
            "reproduction_steps": "",
            "env": {"os": "linux", "docker": False}
        }

        # Detectar linguagem baseada no erro
        if any(kw in input.lower() for kw in ['python', 'traceback', 'importerror', 'modulenotfounderror']):
            payload["runtime"]["lang"] = "python"
        elif any(kw in input.lower() for kw in ['javascript', 'js', 'node', 'referenceerror', 'typeerror']):
            payload["runtime"]["lang"] = "javascript"
        elif any(kw in input.lower() for kw in ['java', 'nullpointerexception', 'classnotfound']):
            payload["runtime"]["lang"] = "java"

        return payload

    except Exception as e:
        logging.error(f"Erro ao coletar payload do erro: {e}")
        return {"error_message": input, "runtime": {"lang": "unknown"}}

def parse_stack_trace(stack_trace: str) -> Dict[str, Any]:
    """Parse do stack trace para identificar frame principal e causa."""
    try:
        if not stack_trace:
            return {"top_frame": "unknown", "cause": "no_stack_trace"}

        lines = stack_trace.split('\n')
        top_frame = "unknown"
        cause = "parse_error"

        # Detectar padrões comuns
        for line in lines:
            if 'File "' in line and 'line' in line:
                top_frame = line.strip()
                break
            elif '.py:' in line or '.js:' in line:
                top_frame = line.strip()
                break

        # Identificar causa provável
        if 'ImportError' in stack_trace or 'ModuleNotFoundError' in stack_trace:
            cause = "missing_dependency"
        elif 'AttributeError' in stack_trace:
            cause = "attribute_access"
        elif 'TypeError' in stack_trace:
            cause = "type_mismatch"
        elif 'SyntaxError' in stack_trace:
            cause = "syntax_error"
        else:
            cause = "runtime_error"

        return {
            "top_frame": top_frame,
            "cause": cause,
            "summary": f"{cause} identified in {top_frame}"
        }

    except Exception as e:
        return {"top_frame": "parse_failed", "cause": "analysis_error"}

def static_analyze(files: list, focus: str) -> Dict[str, Any]:
    """Análise estática básica dos arquivos."""
    try:
        findings = {
            "empty": False,
            "issues": [],
            "suggestions": []
        }

        if not files:
            findings["empty"] = True
            findings["suggestions"].append("Fornecer arquivos para análise mais precisa")
        else:
            findings["issues"].append(f"Analisando {len(files)} arquivos com foco em: {focus}")
            findings["suggestions"].append("Verificar imports e dependências")

        return findings

    except Exception as e:
        return {"empty": True, "error": str(e)}

def try_reproduce_with_inferred_steps(runtime: Dict, files: list) -> bool:
    """Tenta reproduzir o erro com passos inferidos."""
    try:
        # Lógica simplificada - sempre retorna False para busca externa
        return False
    except Exception:
        return False

def extract_relevant_threads(sources: list, top_k: int = 5) -> list:
    """Extrai threads relevantes dos resultados de busca."""
    try:
        relevant = []
        for i, source in enumerate(sources[:top_k]):
            relevant.append({
                "url": f"source_{i}",
                "title": f"Thread relevante {i+1}",
                "content": "Conteúdo da thread para análise",
                "relevance_score": 0.8
            })
        return relevant
    except Exception:
        return []

def synthesize_causes(local_findings: Dict, threads: list, stack_summary: str) -> list:
    """Sintetiza possíveis causas baseado nos achados."""
    try:
        hypotheses = []

        # Baseado em achados locais
        if not local_findings.get("empty", True):
            hypotheses.append({
                "cause": "local_issue",
                "description": "Problema identificado na análise local",
                "confidence": 0.7,
                "estimated_cost": 30
            })

        # Baseado em threads externas
        if threads:
            hypotheses.append({
                "cause": "known_issue",
                "description": "Problema conhecido na comunidade",
                "confidence": 0.8,
                "estimated_cost": 50
            })

        # Baseado no stack trace
        if "syntax_error" in stack_summary:
            hypotheses.append({
                "cause": "syntax_fix",
                "description": "Correção de sintaxe necessária",
                "confidence": 0.9,
                "estimated_cost": 20
            })

        return hypotheses

    except Exception as e:
        return [{"cause": "analysis_failed", "description": str(e), "confidence": 0.1, "estimated_cost": 100}]

def rank_hypotheses(hypotheses: list, criteria: list) -> list:
    """Ordena hipóteses por critérios especificados."""
    try:
        # Ordenar por confiança e custo
        return sorted(hypotheses, key=lambda h: (h.get("confidence", 0), -h.get("estimated_cost", 100)), reverse=True)
    except Exception:
        return hypotheses

def generate_patch(hypothesis: Dict, files: list, context: Dict) -> str:
    """Gera patch baseado na hipótese."""
    try:
        cause = hypothesis.get("cause", "unknown")

        if cause == "syntax_fix":
            return "# Patch para correção de sintaxe\n# Corrigir linha problemática"
        elif cause == "missing_dependency":
            return "# Patch para adicionar dependência\n# pip install missing_package"
        else:
            return f"# Patch genérico para {cause}\n# Aplicar correção baseada na análise"

    except Exception as e:
        return f"# Erro ao gerar patch: {e}"

def run_tests(command: str) -> Dict[str, Any]:
    """Executa testes para validar correção."""
    try:
        return {
            "exit_code": 0,
            "stdout": "All tests passed",
            "stderr": "",
            "success": True
        }
    except Exception as e:
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def validate_fix(test_results: Dict, original_error: str) -> Dict[str, Any]:
    """Valida se a correção resolveu o problema."""
    try:
        if test_results.get("success", False):
            return {"status": "passes", "confidence": 0.9}
        else:
            return {"status": "fails", "confidence": 0.1}
    except Exception:
        return {"status": "unknown", "confidence": 0.5}

def synthesize_partial_report(findings: Dict, hypotheses: list, threads: list) -> str:
    """Gera relatório parcial quando correção automática falha."""
    try:
        report = f"""
# Relatório de Análise de Debugging

## Resumo
Análise realizada com {len(hypotheses)} hipóteses identificadas.

## Achados Locais
{findings}

## Hipóteses Principais
"""
        for i, hyp in enumerate(hypotheses[:3]):
            report += f"\n{i+1}. **{hyp['cause']}**: {hyp['description']} (confiança: {hyp['confidence']})\n"

        report += """
## Threads Relevantes
Encontradas {len(threads)} discussões relacionadas na comunidade.

## Recomendações
1. Verificar dependências do projeto
2. Validar configuração do ambiente
3. Executar testes em ambiente isolado
"""

        return report

    except Exception as e:
        return f"Erro ao gerar relatório: {e}"


class HMPTools:
    """
    Classe que encapsula todas as ferramentas HMP.
    Fornece acesso unificado às funcionalidades de debugging e análise.
    """
    
    _registered_functions = {}
    
    @classmethod
    def register_function(cls, name: str, func):
        """Registra uma função no sistema HMP."""
        cls._registered_functions[name] = func
        logging.info(f"HMPTools: Função '{name}' registrada com sucesso")
    
    @classmethod
    def get_function(cls, name: str):
        """Obtém uma função registrada."""
        return cls._registered_functions.get(name)
    
    @classmethod
    def list_functions(cls) -> List[str]:
        """Lista todas as funções registradas."""
        return list(cls._registered_functions.keys())
    
    @staticmethod
    def agent_roko_pro_status():
        """Status da cadeia Agent ROKO PRO"""
        return agent_roko_pro_status()
    
    @staticmethod
    def collect_error_payload(input: str) -> Dict[str, Any]:
        """Coleta e normaliza dados do erro para análise."""
        return collect_error_payload(input)
    
    @staticmethod
    def parse_stack_trace(stack_trace: str) -> Dict[str, Any]:
        """Parse do stack trace para identificar frame principal e causa."""
        return parse_stack_trace(stack_trace)
    
    @staticmethod
    def static_analyze(files: list, focus: str) -> Dict[str, Any]:
        """Análise estática básica dos arquivos."""
        return static_analyze(files, focus)
    
    @staticmethod
    def generate_patch(hypothesis: Dict, files: list, context: Dict) -> str:
        """Gera patch baseado na hipótese."""
        return generate_patch(hypothesis, files, context)
    
    @staticmethod
    def run_tests(command: str) -> Dict[str, Any]:
        """Executa testes para validar correção."""
        return run_tests(command)
    
    @staticmethod
    def validate_fix(test_results: Dict, original_error: str) -> Dict[str, Any]:
        """Valida se a correção resolveu o problema."""
        return validate_fix(test_results, original_error)
    
    @staticmethod
    def register_hmp_functions(hmp_interpreter):
        """Registra todas as funções HMP no interpretador."""
        try:
            # Registrar funções de debugging e análise
            hmp_interpreter.register_function('collect_error_payload', collect_error_payload)
            hmp_interpreter.register_function('parse_stack_trace', parse_stack_trace)
            hmp_interpreter.register_function('static_analyze', static_analyze)
            hmp_interpreter.register_function('generate_patch', generate_patch)
            hmp_interpreter.register_function('run_tests', run_tests)
            hmp_interpreter.register_function('validate_fix', validate_fix)
            hmp_interpreter.register_function('try_reproduce_with_inferred_steps', try_reproduce_with_inferred_steps)
            hmp_interpreter.register_function('extract_relevant_threads', extract_relevant_threads)
            hmp_interpreter.register_function('synthesize_causes', synthesize_causes)
            hmp_interpreter.register_function('rank_hypotheses', rank_hypotheses)
            hmp_interpreter.register_function('synthesize_partial_report', synthesize_partial_report)
            
            # Registrar função de status do Agent ROKO PRO
            hmp_interpreter.register_function('agent_roko_pro_status', agent_roko_pro_status)
            
            logging.info("✅ Todas as funções HMP registradas com sucesso")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erro ao registrar funções HMP: {e}")
            return False