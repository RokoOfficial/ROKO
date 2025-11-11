
"""
Módulo Pipeline CODER - Orquestração e processamento de pedidos.
"""

from .orchestrator import OrchestratorAgent
try:
    from .coder_pipeline import CODERPipeline
    from .exceptions import CoderNexusError, APIKeyNotFoundError
except ImportError:
    from .coder_pipeline import CODERPipeline
    from .exceptions import CoderNexusError, APIKeyNotFoundError

__all__ = [
    'CODERPipeline',
    'OrchestratorAgent',
    'CoderNexusError',
    'APIKeyNotFoundError'
]
