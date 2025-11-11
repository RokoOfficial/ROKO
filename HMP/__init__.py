"""
HMP (Human-Meaning Protocol) Package
Sistema de raciocínio estruturado para agentes IA
"""

# Importações lazy para evitar dependências circulares
def get_hmp_interpreter():
    from .hmp_interpreter import HMPInterpreter
    return HMPInterpreter

def get_hmp_tools():
    from .hmp_tools import HMPTools
    return HMPTools

def get_hmp_agent():
    from .hmp_agent import HMPAgent
    return HMPAgent

# Manter compatibilidade
HMPInterpreter = None
HMPTools = None
HMPAgent = None

def __getattr__(name):
    if name == 'HMPInterpreter':
        return get_hmp_interpreter()
    elif name == 'HMPTools':
        return get_hmp_tools()
    elif name == 'HMPAgent':
        return get_hmp_agent()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['HMPInterpreter', 'HMPTools', 'HMPAgent']

# Agent ROKO PRO imports
try:
    from .agent_roko_pro_chain import AgentROKOProChain
    from .agent_roko_pro_integration import AgentROKOProIntegration
    from .agent_roko_pro_hmp_chains import AgentROKOProHMPChains
    AGENT_ROKO_PRO_AVAILABLE = True
except ImportError:
    AGENT_ROKO_PRO_AVAILABLE = False

__all__.extend([
    'AgentROKOProChain',
    'AgentROKOProIntegration',
    'AgentROKOProHMPChains'
])