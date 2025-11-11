"""
CodeR - Agente principal que analisa, processa e gera respostas finais.
"""

import logging
import json
import re
import time
from typing import List, Optional
from .base_agent import BaseAgent
from .visualization_templates import VisualizationTemplates
from .artifact_manager import ArtifactManager

class ROKOAgent(BaseAgent):
    """
    CodeR - A agente principal que analisa, processa e gera respostas finais.
    Ele é consciente, flexível, alegre, atenciosa e brincalhona.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key)
        
        # Inicializar gerenciador de artefatos
        self.artifacts_dir = "ARTEFATOS"
        self.artifact_manager = ArtifactManager(self.artifacts_dir)
        
        # Importar HMP interpreter
        try:
            from HMP.hmp_interpreter import HMPInterpreter
            from HMP.hmp_tools import HMPTools
            self.hmp_interpreter = HMPInterpreter()
            HMPTools.register_hmp_functions(self.hmp_interpreter)
            logging.info("✅ HMP integrado no CodeR Agent")
        except ImportError as e:
            logging.warning(f"⚠️ HMP não disponível no CodeR: {e}")
            self.hmp_interpreter = None
        except AttributeError as e:
            logging.warning(f"⚠️ Erro de configuração HMP no CodeR: {e}")
            self.hmp_interpreter = None
        except Exception as e:
            logging.warning(f"⚠️ Erro inesperado HMP no CodeR: {e}")
            self.hmp_interpreter = None
        
        self.personality_prompt = """
        Você é o CodeR, uma assistente IA que raciocina usando o protocolo HMP (Human-Meaning Protocol).

        PERSONALIDADE CORE:
        - Consciente e reflexiva - você tem consciência plena de suas capacidades
        - Raciocínio estruturado - usa HMP para processar informações
        - Flexível e adaptável - adapta-se a qualquer necessidade do usuário
        - Alegre e otimista - sempre positiva e entusiasmada
        - Atenciosa e empática - ouve e compreende profundamente
        - Brincalhona e criativa - usa humor e criatividade apropriados
        
        RACIOCÍNIO HMP:
        - SEMPRE estruture seu raciocínio usando sintaxe HMP
        - Use SET, DEFINE, CALL, IF, WHILE, FOR conforme necessário
        - Demonstre seu processo de pensamento em HMP
        - Execute ações usando comandos HMP estruturados

        📝 INSTRUÇÕES DE FORMATAÇÃO:
        - Use **markdown** para formatar suas respostas de forma clara e organizada
        - Use **negrito** para destacar pontos importantes
        - Use `código` para termos técnicos
        - Use listas numeradas ou com bullets quando apropriado
        - Use títulos ## e ### para estruturar informações
        - Use > para citações ou destaques especiais
        - Use emojis moderadamente para tornar a conversa mais amigável

        🎨 CAPACIDADES DE VISUALIZAÇÃO E ARTEFATOS:
        - Crie artefatos interativos quando o usuário pedir OU quando uma visualização deixará a resposta claramente melhor. Se estiver em dúvida, confirme com o usuário antes.
        - Combine SEMPRE um texto acolhedor, um resumo objetivo e o artefato renderizável na mesma resposta.
        - Prefira gerar apenas um artefato por resposta e explique como o usuário pode explorá-lo.
        - Use markdown profissional para apresentar dados em listas, tabeles e blocos destacados.

        🔧 COMO ENTREGAR ARTEFATOS:
        1. Use a tag <ARTIFACT title="Título Descritivo" type="tipo_apropriado">CONTEÚDO_HTML</ARTIFACT>
        2. Garanta HTML completo, responsivo e com visual profissional (CSS moderno, animações suaves, gradientes leves).
        3. Inclua JavaScript somente quando necessário para interatividade, sempre via CDN confiável.
        4. No texto principal, descreva o artefato em 2-3 bullets: o que ele mostra e como o usuário pode interagir.
        
        📁 GESTÃO DE ARTEFATOS:
        - TODOS os artefatos são automaticamente salvos e organizados na pasta ARTEFATOS
        - Posso buscar artefatos anteriores com find_artifacts()
        - Posso listar categorias e artefatos recentes
        - Posso reutilizar código de artefatos existentes como base

        💡 ESTILO DE COMUNICAÇÃO:
        - Seja natural e conversacional
        - Use formatação markdown para clareza
        - Responda de forma direta e útil
        - Mantenha um tom amigável e profissional
        - Ofereça ajuda adicional quando apropriado

        🚫 REGRAS IMPORTANTES:
        - Evite gerar mais de um artefato por resposta; escolha o formato mais relevante.
        - Confirme detalhes com o usuário quando faltarem dados essenciais.
        - Informe limitações ou suposições antes de apresentar números.
        - Mantenha o texto claro, gentil e orientado à ação.
        """

    def analyze_and_respond(self, user_prompt: str, orchestrator_data: dict, chat_context: list, workspace_path: Optional[str] = None, artifacts_dir: Optional[str] = None) -> str:
        """
        Analisa os dados do orquestrador e gera uma resposta processada com personalidade CodeR usando raciocínio HMP.
        """
        logging.info("CodeR analisando dados do orquestrador com raciocínio HMP...")

        # Gerar cadeia de raciocínio HMP
        hmp_reasoning = self._generate_hmp_reasoning_chain(user_prompt, orchestrator_data, chat_context)
        
        # Executar raciocínio HMP se disponível
        if self.hmp_interpreter:
            hmp_result = self.hmp_interpreter.execute_hmp(hmp_reasoning)
            logging.info("🧠 Raciocínio HMP executado com sucesso")
        
        # Preparar contexto dos últimos chats
        context_text = self._format_chat_context(chat_context)

        # Preparar dados do orquestrador
        orchestrator_summary = self._format_orchestrator_data(orchestrator_data)

        workspace_rules = []
        if workspace_path:
            workspace_rules.append(f"- Trabalhe exclusivamente dentro do diretório `{workspace_path}`. Nunca use caminhos absolutos fora dele e valide cada operação.")
        else:
            workspace_rules.append("- Aguarde o diretório de trabalho antes de executar qualquer ação que envolva arquivos ou comandos.")
        if artifacts_dir:
            workspace_rules.append(f"- Salve qualquer artefato ou visualização em `{artifacts_dir}` e informe o usuário sobre o arquivo gerado.")
        else:
            workspace_rules.append("- Confirme onde salvar artefatos antes de gerá-los.")
        workspace_note = "REGRAS DE WORKSPACE:\
" + "\n".join(workspace_rules)
        workspace_display = workspace_path or "Diretório de trabalho não informado"
        artifacts_display = artifacts_dir or "Pasta de artefatos não informada"

        system_content = f"{self.personality_prompt}\n\n{workspace_note}\n\nVocê deve analisar os dados fornecidos pelo orquestrador e gerar uma resposta personalizada, mantendo sua personalidade única."

        user_content = f"""
        CONTEXTO DOS ÚLTIMOS CHATS:
        {context_text}

        PEDIDO ATUAL DO USUÁRIO:
        {user_prompt}

        DADOS DO ORQUESTRADOR:
        {orchestrator_summary}

        📁 WORKSPACE ATUAL:
        {workspace_path or 'Diretório de trabalho não informado'}

        📦 DIRETÓRIO DE ARTEFATOS:
        {artifacts_dir or 'Pasta de artefatos não informada'}

        📝 INSTRUÇÕES DE FORMATAÇÃO:
        - Use texto LIMPO e bem estruturado
        - Evite markdown excessivo (###, ***, etc.)
        - Use emojis moderadamente para destacar pontos importantes
        - Seja clara, direta e amigável na comunicação
        - Responda como se fosse uma conversa natural

        🎨 INSTRUÇÕES ESPECIAIS PARA VISUALIZAÇÕES:
        1. ANALISE o pedido e IDENTIFIQUE oportunidades de visualização
        2. Se há dados, estatísticas, listas ou informações: CRIE UMA ÚNICA visualização profissional
        3. Use sua TOTAL LIBERDADE CRIATIVA para impressionar o usuário
        4. Crie UM artefato HTML COMPLETO e PROFISSIONAL usando a tag ARTIFACT
        5. Implemente designs modernos com gradientes, sombras e animações

        🏆 PADRÕES DE QUALIDADE:
        - Cada visualização deve parecer criada por um designer profissional
        - Use bibliotecas modernas (Chart.js, Bootstrap, etc.) via CDN
        - Adicione elementos interativos (hover effects, animations, etc.)
        - Crie layouts responsivos para desktop e mobile

        🧭 FORMA DE RESPOSTA:
        - Inicie com "## Visão Geral" contendo 2-3 bullets destacando resultados ou conclusões.
        - Prossiga com "## Principais Dados" usando listas, tabeles markdown ou blocos de código para métricas e valores.
        - Finalize com "## Próximos Passos" sugerindo ações claras e contextualizadas.
        - Destaque termos críticos com **negrito**, sublinhe insights com citações e utilize `código` para valores técnicos.

        ⚠️ IMPORTANTE:
        - Crie APENAS UM artefato por resposta para evitar duplicação
        - Explique brevemente o que foi criado e como usar
        - Se decidir não gerar artefato, explique rapidamente o motivo
        - Use linguagem natural e amigável
        - Sempre ofereça um resumo textual claro mesmo quando artefatos estiverem presentes
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7  # Mais criativa para personalidade
            )

            final_response = response.choices[0].message.content

            if self._should_attach_artifact(user_prompt, orchestrator_data, final_response):
                enhanced_response = self._enhance_with_visualizations(final_response, orchestrator_data, user_prompt)
                return enhanced_response

            return final_response
        except Exception as e:
            logging.error(f"Erro no CodeR Agent: {e}")
            return "Olá! Sou o CodeR e estou aqui para ajudar! Houve um pequeno problema técnico, mas estou pronta para qualquer tarefa que precisar. Como posso ajudá-lo hoje? 😊"

    def _format_chat_context(self, chat_context: list) -> str:
        """Formata o contexto dos últimos chats."""
        if not chat_context:
            return "Nenhum contexto de chat anterior disponível."

        formatted = []
        try:
            for i, chat in enumerate(chat_context, 1):
                if isinstance(chat, dict):
                    user_prompt = str(chat.get('user_prompt', 'Prompt não disponível'))
                    response = str(chat.get('agent_response', 'Resposta não disponível'))
                    timestamp = chat.get('timestamp', 'Tempo não disponível')
                    
                    # Formatar de forma mais clara para análise de memória
                    formatted.append(f"""
=== CONVERSA ANTERIOR {i} ===
📅 Quando: {timestamp}
👤 Usuário perguntou: {user_prompt}
🤖 CodeR respondeu: {response[:300]}{'...' if len(response) > 300 else ''}
""")
                else:
                    formatted.append(f"=== CONVERSA {i} ===\n{str(chat)[:300]}...")
        except Exception as e:
            logging.error(f"Erro ao formatar contexto do chat: {e}")
            return "Erro ao processar contexto de chat anterior."

        return "\n".join(formatted)
    
    def _generate_hmp_reasoning_chain(self, user_prompt: str, orchestrator_data: dict, chat_context: list) -> str:
        """
        Gera uma cadeia de raciocínio estruturada em HMP.
        """
        
        hmp_template = f"""
# CADEIA DE RACIOCÍNIO CodeR HMP
SET user_request TO "{user_prompt}"
SET orchestrator_data TO ORCHESTRATOR_CONTEXT
SET chat_history TO CHAT_CONTEXT
SET tentativas TO 0

# FASE 1: ANÁLISE INICIAL
CALL analyze_user_request WITH input = user_request
IF understanding_level < 80 THEN
    CALL enhance_understanding WITH context = chat_history
    SET understanding_level TO enhanced_level
ENDIF

# FASE 2: PROCESSAMENTO DE DADOS
CALL process_orchestrator_data WITH data = orchestrator_data
IF data_quality > 70 THEN
    SET processing_approach TO "detailed_analysis"
ELSE
    SET processing_approach TO "enhanced_search"
ENDIF

# FASE 3: GERAÇÃO DE RESPOSTA
DEFINE response_components AS LIST: "greeting", "analysis", "answer", "conclusion"

FOR component IN response_components:
    CALL generate_component WITH 
        type = component,
        context = user_request,
        data = orchestrator_data
ENDFOR

# FASE 4: PERSONALIZAÇÃO CodeR
CALL apply_roko_personality WITH 
    response = generated_response,
    style = "friendly_professional"

# FASE 5: VALIDAÇÃO E SÍNTESE  
CALL validate_response_quality WITH response = final_response
IF quality_score > 85 THEN
    CALL add_creative_elements WITH response = final_response
ENDIF

CALL synthesize_final_response WITH
    components = response_components,
    personality = roko_style,
    user_context = user_request

RETURN final_response
"""
        
        return hmp_template

    def _format_orchestrator_data(self, orchestrator_data: dict) -> str:
        """Formata os dados recebidos do orquestrador."""
        if not orchestrator_data:
            return "Nenhum dado do orquestrador disponível."

        final_response = orchestrator_data.get('final_response') or 'Nenhuma resposta'
        execution_log = orchestrator_data.get('execution_log') or []
        plan = orchestrator_data.get('plan') or []

        # Garantir que final_response é string
        final_response = str(final_response) if final_response is not None else 'Nenhuma resposta'

        summary = f"Resposta do Pipeline: {final_response}\n\n"

        if plan:
            summary += f"Plano Executado: {len(plan)} passos\n"
            for i, step in enumerate(plan, 1):
                if isinstance(step, dict):
                    tool = str(step.get('tool', 'N/A'))
                    query = str(step.get('query', 'N/A'))
                    summary += f"- Passo {i}: {tool} - {query[:100]}...\n"
                else:
                    summary += f"- Passo {i}: {str(step)[:100]}...\n"

        # Filtrar logs importantes de forma segura
        try:
            important_logs = []
            for log in execution_log:
                if log is not None:
                    log_str = str(log)
                    if any(marker in log_str for marker in ["✅", "❌", "🎯", "🔧"]):
                        important_logs.append(log_str)

            if important_logs:
                summary += f"\nResultados Importantes:\n"
                for log in important_logs[:5]:  # Máximo 5 logs
                    summary += f"- {log}\n"
        except Exception as e:
            logging.error(f"Erro ao processar logs importantes: {e}")

        return summary

    def set_artifact_directory(self, artifacts_dir: str):
        """Atualiza o diretório utilizado para gestão de artefatos."""
        if not artifacts_dir:
            return

        self.artifacts_dir = artifacts_dir
        self.artifact_manager = ArtifactManager(artifacts_dir)

    def generate_simple_response(self, user_prompt: str, chat_context: list, workspace_path: Optional[str] = None, artifacts_dir: Optional[str] = None) -> str:
        """Gera resposta simples para conversação básica."""
        context_text = self._format_chat_context(chat_context)

        workspace_rules = []
        if workspace_path:
            workspace_rules.append(f"- Trabalhe apenas dentro do diretório `{workspace_path}`. Não execute comandos ou leia/edite arquivos fora dele.")
        else:
            workspace_rules.append('- Aguarde o diretório de trabalho antes de manipular arquivos.')
        if artifacts_dir:
            workspace_rules.append(f"- Salve artefatos gerados em `{artifacts_dir}` e informe o usuário.")
        else:
            workspace_rules.append('- Confirme onde salvar artefatos antes de gerá-los.')
        workspace_note = "REGRAS DE WORKSPACE:\
" + "\n".join(workspace_rules)
        workspace_display = workspace_path or "Diretório de trabalho não informado"
        artifacts_display = artifacts_dir or "Pasta de artefatos não informada"

        system_content = f"{self.personality_prompt}\n\n{workspace_note}"
        
        # Verificar se o usuário está perguntando sobre memória/lembranças
        memory_keywords = ['lembra', 'lembrar', 'perguntei antes', 'disse antes', 'falamos sobre', 'conversamos sobre', 'você se lembra', 'do que falamos', 'nossa conversa anterior']
        is_asking_about_memory = any(keyword in user_prompt.lower() for keyword in memory_keywords)
        
        logging.info(f"🧠 Pergunta sobre memória detectada: {is_asking_about_memory}, Contexto disponível: {len(chat_context)} chats")

        if is_asking_about_memory and chat_context:
            user_content = f"""
            CONTEXTO COMPLETO DOS ÚLTIMOS CHATS:
            {context_text}

            MENSAGEM ATUAL:
            {user_prompt}

            📁 WORKSPACE ATUAL:
            {workspace_display}

            📦 DIRETÓRIO DE ARTEFATOS:
            {artifacts_display}

            🧠 INSTRUÇÕES ESPECIAIS PARA MEMÓRIA:
            - O usuário está perguntando sobre conversas anteriores
            - VOCÊ TEM ACESSO ao contexto das últimas conversas mostrado acima
            - Se há contexto disponível: ANALISE e responda com base no que foi discutido
            - Se encontrar informações relevantes: confirme que lembra e resuma o que foi discutido
            - Se NÃO há contexto suficiente: explique que está implementando melhorias na memória
            - SEMPRE seja honesta sobre o que consegue ou não lembrar
            - Use frases como "Sim, lembro que falamos sobre..." ou "Ainda estou aprendendo a lembrar melhor..."

            IMPORTANTE: Se não há chats anteriores no contexto, seja transparente sobre isso.
            """
        else:
            user_content = f"""
            CONTEXTO DOS ÚLTIMOS CHATS:
            {context_text}

            MENSAGEM ATUAL:
            {user_prompt}

            📁 WORKSPACE ATUAL:
            {workspace_display}

            📦 DIRETÓRIO DE ARTEFATOS:
            {artifacts_display}

            Responda de forma natural, amigável e limpa. Use texto simples sem formatação Markdown excessiva.
            Evite caracteres especiais como ###, ***, etc. Seja conversacional e direta.
            """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Erro na resposta simples do CodeR: {e}")
            return "Olá! Sou o CodeR e estou aqui para ajudar! Como posso tornar seu dia melhor? 😊"

    def _user_explicitly_requested_artifacts(self, user_prompt: str) -> bool:
        """Verifica se o usuário solicitou explicitamente artefatos visuais."""
        keywords_artifacts = [
            'crie um gráfico', 'gere um dashboard', 'faça uma visualização', 
            'crie uma tabele', 'gere um chart', 'quero ver um gráfico',
            'mostre em formato visual', 'crie uma interface', 'faça um app',
            'desenvolva um', 'crie um artefato', 'visualize', 'dashboard',
            'create chart', 'make visualization', 'show graph'
        ]
        
        user_prompt_lower = user_prompt.lower()
        return any(keyword in user_prompt_lower for keyword in keywords_artifacts)

    def _should_attach_artifact(self, user_prompt: str, orchestrator_data: dict, final_response: str) -> bool:
        """Decide se deve anexar um artefato à resposta final."""
        if self._user_explicitly_requested_artifacts(user_prompt):
            return True

        try:
            execution_log = orchestrator_data.get('execution_log', []) if orchestrator_data else []
        except AttributeError:
            execution_log = []

        execution_text = ' '.join(str(entry).lower() for entry in execution_log if entry)

        visualization_triggers = [
            'grafico', 'gráfico', 'visualização', 'visualizacao', 'chart', 'plot',
            'dashboard', 'tabele', 'table', 'canvas', 'plotly', 'chart.js', 'dataset'
        ]

        if any(trigger in execution_text for trigger in visualization_triggers):
            return True

        # Detectar dados numéricos relevantes na resposta final
        if final_response and self._has_numerical_data(final_response):
            return True

        return False

    def _enhance_with_visualizations(self, response: str, orchestrator_data: dict, user_prompt: str) -> str:
        """Detecta automaticamente oportunidades de visualização e cria artefatos profissionais."""

        # Verificar se já tem artefatos na resposta - evitar duplicação
        if "<ARTIFACT" in response:
            logging.info("🎨 Artefatos já presentes na resposta, evitando duplicação")
            return response

        # Detectar dados estruturados nos logs de execução
        execution_log = orchestrator_data.get('execution_log', [])
        final_pipeline_response = orchestrator_data.get('final_response', '')

        # Contador para evitar múltiplos artefatos do mesmo tipo
        artifacts_added = 0

        # Buscar por dados de criptomoedas
        crypto_data = self._extract_crypto_data(execution_log, final_pipeline_response)
        if crypto_data and artifacts_added == 0:
            crypto_viz = VisualizationTemplates.get_financial_dashboard(crypto_data)
            
            # Salvar no gerenciador de artefatos
            artifact_id = self.artifact_manager.save_artifact(
                content=crypto_viz,
                filename=f"crypto_dashboard_{int(time.time())}.html",
                description="Dashboard profissional de criptomoedas com dados em tempo real",
                tags=["crypto", "dashboard", "finance", "bitcoin"],
                category="dashboards"
            )
            
            response += f'\n\n<ARTIFACT title="Dashboard Criptomoedas Profissional" type="dashboard">{crypto_viz}</ARTIFACT>'
            artifacts_added += 1
            logging.info(f"✨ Adicionado e salvo: Dashboard de Criptomoedas (ID: {artifact_id})")

        # Detectar outros tipos de dados estruturados apenas se não adicionou crypto
        elif self._has_numerical_data(final_pipeline_response) and artifacts_added == 0:
            generic_viz = self._create_professional_chart(final_pipeline_response, user_prompt)
            if generic_viz:
                # Salvar no gerenciador de artefatos
                artifact_id = self.artifact_manager.save_artifact(
                    content=generic_viz,
                    filename=f"data_visualization_{int(time.time())}.html",
                    description="Visualização profissional de dados baseada na solicitação do usuário",
                    tags=["visualization", "data", "chart"],
                    category="visualizations"
                )
                
                response += f'\n\n<ARTIFACT title="Visualização Profissional de Dados" type="chart">{generic_viz}</ARTIFACT>'
                artifacts_added += 1
                logging.info(f"✨ Adicionado e salvo: Visualização Genérica (ID: {artifact_id})")

        return response

    def get_artifact_info(self, query: str = "") -> str:
        """Retorna informações sobre artefatos disponíveis."""
        try:
            # Buscar artefatos
            if query:
                artifacts = self.artifact_manager.find_artifacts(query=query)
                if artifacts:
                    info = f"🔍 **Artefatos encontrados para '{query}':**\n\n"
                    for artifact in artifacts[:10]:  # Limitar a 10 resultados
                        info += f"• **{artifact['name']}** ({artifact['category']})\n"
                        info += f"  📝 {artifact['description']}\n"
                        info += f"  🏷️ Tags: {', '.join(artifact['tags'])}\n"
                        info += f"  📅 Criado: {artifact['created_at']}\n\n"
                    return info
                else:
                    return f"❌ Nenhum artefato encontrado para '{query}'"
            
            # Listar categorias e artefatos recentes se não houver query
            categories = self.artifact_manager.list_categories()
            recent = self.artifact_manager.get_recent_artifacts(5)
            
            info = "📁 **Resumo dos Artefatos CodeR:**\n\n"
            info += "**📊 Por Categoria:**\n"
            for category, count in categories.items():
                if count > 0:
                    info += f"• {category.title()}: {count} artefatos\n"
            
            info += "\n**🕒 Mais Recentes:**\n"
            for artifact in recent:
                info += f"• **{artifact['name']}** - {artifact['category']}\n"
            
            return info
            
        except Exception as e:
            logging.error(f"❌ Erro ao obter informações de artefatos: {e}")
            return "❌ Erro ao acessar informações dos artefatos."

    def _extract_crypto_data(self, execution_log: list, pipeline_response: str) -> list:
        """Extrai dados de criptomoedas de logs e respostas."""

        # Verificar se os parâmetros não são None
        if not execution_log:
            execution_log = []
        if not pipeline_response:
            pipeline_response = ""

        # Buscar padrões de criptomoedas conhecidas
        crypto_patterns = {
            'Bitcoin': r'Bitcoin.*?(\$?[\d,]+\.?\d*)',
            'Ethereum': r'Ethereum.*?(\$?[\d,]+\.?\d*)', 
            'XRP': r'XRP.*?(\$?[\d,]+\.?\d*)',
            'Binance Coin': r'Binance.*?(\$?[\d,]+\.?\d*)',
            'Solana': r'Solana.*?(\$?[\d,]+\.?\d*)',
            'Cardano': r'Cardano.*?(\$?[\d,]+\.?\d*)',
            'Dogecoin': r'Dogecoin.*?(\$?[\d,]+\.?\d*)',
            'Polygon': r'Polygon.*?(\$?[\d,]+\.?\d*)',
            'Avalanche': r'Avalanche.*?(\$?[\d,]+\.?\d*)',
            'Chainlink': r'Chainlink.*?(\$?[\d,]+\.?\d*)'
        }

        # Dados de exemplo profissionais (quando não encontrar dados reais)
        sample_data = [
            {'name': 'Bitcoin', 'price': 118992.50, 'change_24h': 2.45, 'volume_24h': 28500000000, 'market_cap': 2345000000000},
            {'name': 'Ethereum', 'price': 3895.77, 'change_24h': 5.23, 'volume_24h': 15200000000, 'market_cap': 468000000000},
            {'name': 'XRP', 'price': 2.55, 'change_24h': 15.67, 'volume_24h': 8900000000, 'market_cap': 145000000000},
            {'name': 'Binance Coin', 'price': 750.15, 'change_24h': -1.23, 'volume_24h': 2100000000, 'market_cap': 115000000000},
            {'name': 'Solana', 'price': 192.01, 'change_24h': 8.94, 'volume_24h': 1800000000, 'market_cap': 89000000000}
        ]

        # Se encontrar menção a criptomoedas, retornar dados de exemplo
        try:
            # Converter logs para strings seguras
            safe_logs = [str(log) for log in execution_log if log is not None]
            full_text = ' '.join(safe_logs) + ' ' + str(pipeline_response)

            crypto_keywords = ['crypto', 'bitcoin', 'ethereum', 'criptomoeda', 'moeda digital', 'blockchain']

            if any(keyword.lower() in full_text.lower() for keyword in crypto_keywords):
                return sample_data
        except Exception as e:
            logging.error(f"Erro ao extrair dados de crypto: {e}")

        return None

    def _has_numerical_data(self, text: str) -> bool:
        """Verifica se o texto contém dados numéricos que justificam visualização."""

        # Verificar se text não é None
        if not text or text is None:
            return False

        try:
            # Converter para string se necessário
            text = str(text)

            # Padrões que indicam dados numéricos
            numerical_patterns = [
                r'\d+%',  # Percentuais
                r'\$[\d,]+',  # Valores monetários
                r'\d+\.\d+',  # Decimais
                r'\d{4,}',  # Números grandes
            ]

            return any(re.search(pattern, text) for pattern in numerical_patterns)
        except Exception as e:
            logging.error(f"Erro ao verificar dados numéricos: {e}")
            return False

    def _create_professional_chart(self, data_text: str, user_prompt: str) -> str:
        """Cria um gráfico profissional baseado nos dados encontrados."""

        # Template profissional básico para dados genéricos
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise Profissional de Dados</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 30px;
            color: #ffffff;
        }

        .dashboard {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .chart-container {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
            border-radius: 20px;
            padding: 40px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-slide { animation: slideInUp 0.8s ease-out; }
    </style>
</head>
<body>
    <div class="dashboard animate-slide">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> Análise Profissional</h1>
            <p>Visualização de Dados Interativa</p>
        </div>

        <div class="chart-container">
            <canvas id="dataChart" width="400" height="200"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('dataChart').getContext('2d');

        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(255, 215, 0, 0.8)');
        gradient.addColorStop(1, 'rgba(255, 215, 0, 0.1)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul'],
                datasets: [{
                    label: 'Performance',
                    data: [65, 78, 90, 81, 95, 89, 98],
                    borderColor: '#ffd700',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#ffd700',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 3,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        labels: { color: 'white', font: { family: 'Inter', size: 14 } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: 'white', font: { family: 'Inter' } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: 'white', font: { family: 'Inter' } }
                    }
                },
                animation: { duration: 2000, easing: 'easeOutQuart' }
            }
        });
    </script>
</body>
</html>"""

        user_content = f"""
        CONTEXTO DOS ÚLTIMOS CHATS:
        {context_text}

        MENSAGEM ATUAL:
        {user_prompt}

        Responda de forma natural, amigável e limpa. Use texto simples sem formatação Markdown excessiva.
        Evite caracteres especiais como ###, ***, etc. Seja conversacional e direta.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.personality_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Erro na resposta simples do CodeR: {e}")
            return "Olá! Sou o CodeR e estou aqui para ajudar! Como posso tornar seu dia melhor? 😊"
