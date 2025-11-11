
"""
AutoFlux ROKO - Sistema de Processamento Paralelo Modular
========================================================

Sistema ultra-otimizado de processamento paralelo para ROKO
com suporte a múltiplas engines e processamento adaptativo.

Módulos:
- core: Núcleo principal do AutoFlux
- engines: Engines de processamento (Pandas, Polars, NumPy)
- processors: Processadores de dados especializados
- utils: Utilitários e ferramentas auxiliares
"""

from .core import AutoFluxROKO, create_autoflux
from .processors import ROKODataProcessor
from .engines import EngineManager
from .utils import PerformanceMonitor

__version__ = "2.0.0"
__author__ = "ROKO System"

__all__ = [
    'AutoFluxROKO',
    'ROKODataProcessor', 
    'EngineManager',
    'PerformanceMonitor'
]

# Configuração padrão
DEFAULT_CONFIG = {
    'memory_safe': True,
    'safe_mode': True,
    'engine': 'auto',
    'timeout': 30.0,
    'enable_gc': True,
    'flatten_3d': True
}

def create_autoflux(**kwargs):
    """
    Factory function para criar instância do AutoFlux com configuração otimizada.
    
    Args:
        **kwargs: Parâmetros de configuração
        
    Returns:
        AutoFluxROKO: Instância configurada do AutoFlux
    """
    config = DEFAULT_CONFIG.copy()
    config.update(kwargs)
    return AutoFluxROKO(**config)
