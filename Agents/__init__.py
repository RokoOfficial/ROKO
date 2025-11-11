"""
Pacote de Agentes ROKO - Módulos especializados para diferentes tarefas.
"""

from .base_agent import BaseAgent
from .web_agent import WebAgent
from .shell_agent import ShellAgent
from .dependency_agent import DependencyAgent
from .code_agent import CodeAgent
from .planner_agent import PlannerAgent
from .checkin_agent import CheckInAgent
from .error_fix_agent import ErrorFixAgent
from .coder_agent import CODERAgent
from .roko_agent import ROKOAgent
from .validation_agent import ValidationAgent
from .adaptive_context_agent import AdaptiveContextAgent
from .metrics_agent import MetricsAgent
from .data_processing_agent import DataProcessingAgent
from .artifact_manager import ArtifactManager
from .github_agent import GitHubAgent

__all__ = [
    'BaseAgent',
    'WebAgent',
    'ShellAgent',
    'DependencyAgent',
    'CodeAgent',
    'PlannerAgent',
    'CheckInAgent',
    'ErrorFixAgent',
    'CODERAgent',
    'ROKOAgent',
    'ValidationAgent',
    'AdaptiveContextAgent',
    'MetricsAgent',
    'DataProcessingAgent',
    'ArtifactManager',
    'GitHubAgent'
]