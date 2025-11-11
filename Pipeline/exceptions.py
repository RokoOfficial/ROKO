
"""
Exceções personalizadas para o sistema CODER Pipeline.
"""

class CoderNexusError(Exception):
    """Exceção base para erros no sistema CODER Nexus."""
    pass

class APIKeyNotFoundError(CoderNexusError):
    """Lançada quando a chave da API da OpenAI não é encontrada."""
    pass

class PipelineExecutionError(CoderNexusError):
    """Lançada quando há erro na execução do pipeline."""
    pass

class AgentCommunicationError(CoderNexusError):
    """Lançada quando há erro na comunicação entre agentes."""
    pass

class HMPExecutionError(CoderNexusError):
    """Lançada quando há erro na execução de cadeias HMP."""
    pass

class WorkspaceError(CoderNexusError):
    """Lançada quando há problema com workspace do usuário."""
    pass

class MemoryError(CoderNexusError):
    """Lançada quando há erro no sistema de memória cognitiva."""
    pass
