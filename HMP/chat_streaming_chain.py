
"""
Cadeia HMP especializada para Chat Streaming com blocos visuais de ações.
Baseado no fluxo visual solicitado pelo usuário.
"""

from typing import Dict, Any, List
import time
import uuid

class ChatStreamingChain:
    """Cadeia HMP para exibir ações dos agentes em blocos streaming"""
    
    @staticmethod
    def get_chat_streaming_chain() -> str:
        """Cadeia principal para chat streaming com blocos visuais"""
        return """
SET user_request TO {user_input}
SET streaming_mode TO "visual_blocks_streaming"
SET action_blocks TO empty_list

# FASE 1: ANÁLISE INICIAL E CONTEXTO
CALL analyze_chat_request WITH input = user_request
SET request_complexity TO analysis_result.complexity
SET required_agents TO analysis_result.agents_needed

# Criar bloco inicial de análise
SET analysis_block TO {
    id: "analysis_" + GENERATE_ID(),
    title: "Analisando solicitação",
    status: "running",
    agent: "analyzer",
    description: "Compreendendo sua solicitação e identificando as melhores abordagens",
    progress: 25,
    icon: "🧠",
    timestamp: NOW()
}
APPEND analysis_block TO action_blocks
YIELD streaming_event WITH type = "action_block", data = analysis_block

# FASE 2: PLANEJAMENTO INTELIGENTE
IF request_complexity > 50 THEN
    SET planning_block TO {
        id: "planning_" + GENERATE_ID(),
        title: "Criando plano de execução",
        status: "running", 
        agent: "planner",
        description: "Definindo etapas e coordenando agentes especializados",
        progress: 45,
        icon: "📋",
        timestamp: NOW()
    }
    APPEND planning_block TO action_blocks
    YIELD streaming_event WITH type = "action_block", data = planning_block
    
    CALL planner.create_intelligent_plan WITH request = user_request
    SET execution_plan TO planner_result.plan
    
    # Atualizar bloco de planejamento
    SET planning_block.status TO "completed"
    SET planning_block.progress TO 100
    SET planning_block.result TO "Plano criado com " + LENGTH(execution_plan) + " etapas"
    YIELD streaming_event WITH type = "action_block_update", data = planning_block
ENDIF

# FASE 3: EXECUÇÃO COM AGENTES ESPECIALIZADOS
FOR agent_name IN required_agents:
    SET agent_block TO {
        id: agent_name + "_" + GENERATE_ID(),
        title: agent_name + " está trabalhando",
        status: "running",
        agent: agent_name,
        description: "Executando tarefas especializadas para sua solicitação",
        progress: 0,
        icon: GET_AGENT_ICON(agent_name),
        timestamp: NOW(),
        steps: empty_list
    }
    APPEND agent_block TO action_blocks
    YIELD streaming_event WITH type = "action_block", data = agent_block
    
    # Executar ações do agente com progresso
    CALL execute_agent_with_progress WITH 
        agent = agent_name,
        task = user_request,
        block_id = agent_block.id
    
    # Atualizar progresso em tempo real
    FOR step IN agent_execution_steps:
        SET agent_block.progress TO step.progress
        APPEND step TO agent_block.steps
        YIELD streaming_event WITH type = "action_block_update", data = agent_block
        
        IF step.type == "sub_action" THEN
            SET sub_block TO {
                id: "sub_" + GENERATE_ID(),
                title: step.title,
                status: "running",
                agent: agent_name,
                description: step.description,
                progress: 0,
                icon: step.icon,
                parent_id: agent_block.id,
                timestamp: NOW()
            }
            YIELD streaming_event WITH type = "sub_action_block", data = sub_block
        ENDIF
    ENDFOR
    
    # Finalizar bloco do agente
    SET agent_block.status TO "completed"
    SET agent_block.progress TO 100
    YIELD streaming_event WITH type = "action_block_update", data = agent_block
ENDFOR

# FASE 4: SÍNTESE E RESULTADOS
SET synthesis_block TO {
    id: "synthesis_" + GENERATE_ID(),
    title: "Finalizando resposta",
    status: "running",
    agent: "synthesizer", 
    description: "Organizando resultados e preparando resposta final",
    progress: 80,
    icon: "🎯",
    timestamp: NOW()
}
APPEND synthesis_block TO action_blocks
YIELD streaming_event WITH type = "action_block", data = synthesis_block

CALL synthesize_final_response WITH 
    user_request = user_request,
    agent_results = collected_results,
    action_blocks = action_blocks

SET synthesis_block.status TO "completed"
SET synthesis_block.progress TO 100
SET synthesis_block.result TO "Resposta preparada com sucesso"
YIELD streaming_event WITH type = "action_block_update", data = synthesis_block

# FASE 5: ENTREGA FINAL
SET completion_block TO {
    id: "completion_" + GENERATE_ID(), 
    title: "Resposta completa",
    status: "completed",
    agent: "coder",
    description: "Sua solicitação foi processada com sucesso",
    progress: 100,
    icon: "✅",
    timestamp: NOW(),
    response: synthesized_response
}
YIELD streaming_event WITH type = "final_response", data = completion_block

RETURN {
    status: "completed",
    action_blocks: action_blocks,
    final_response: synthesized_response,
    total_time: ELAPSED_TIME()
}
"""

    @staticmethod
    def get_agent_icon(agent_name: str) -> str:
        """Retorna ícone para cada agente"""
        icons = {
            "web": "🌐",
            "code": "💻", 
            "shell": "⚡",
            "github": "🐙",
            "data": "📊",
            "roko": "🤖",
            "planner": "📋",
            "analyzer": "🧠",
            "synthesizer": "🎯"
        }
        return icons.get(agent_name, "🔧")

    @staticmethod
    def create_streaming_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria evento de streaming para o frontend"""
        return {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
            "id": str(uuid.uuid4())
        }
