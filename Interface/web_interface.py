"""
Interface web para o CODER usando Flask.
"""

import logging
import os
import json
import time
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file, session, redirect, url_for, send_from_directory
try:
    from Pipeline import CODERPipeline, APIKeyNotFoundError
    from Interface.auth import AuthSystem, require_login
except ImportError:
    from ..Pipeline import CODERPipeline, APIKeyNotFoundError
    from .auth import AuthSystem, require_login

class WebInterface:
    """Interface web do CODER."""

    def __init__(self):
        self.app = Flask(
            __name__,
            template_folder='../templates',
            static_folder='../static',
            static_url_path='/static'
        )
        self.app.secret_key = os.environ.get('SECRET_KEY', 'roko-dev-secret-key-change-in-production')
        self.coder_system = None
        self.auth_system = None
        self.template_dir = '../templates' # Adicionado para uso nas rotas
        # CODERSPACE - Diretório principal para todos os usuários
        project_root_env = os.environ.get('ROKO_PROJECTS_ROOT')
        default_coderspace = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CODERSPACE'))
        self.coderspace_root = os.path.abspath(project_root_env) if project_root_env else default_coderspace
        self.base_projects_root = self.coderspace_root  # compatibilidade retroativa
        self.projects_root = self.coderspace_root  # compatibilidade retroativa
        os.makedirs(self.coderspace_root, exist_ok=True)

        # Criar arquivo README no CODERSPACE
        readme_path = os.path.join(self.coderspace_root, 'README.md')
        if not os.path.exists(readme_path):
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("# CODERSPACE\n\nDiretório principal para workspaces dos usuários do CODER.\n\nCada usuário possui seu próprio diretório isolado.\n")
        self.artifacts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ARTEFATOS'))
        os.makedirs(self.artifacts_root, exist_ok=True)
        self._setup_routes()
        self._initialize_coder()

    def _initialize_coder(self):
        """Inicializa o sistema CODER."""
        try:
            self.coder_system = CODERPipeline()
            logging.info("✅ Sistema CODER inicializado para interface web")
        except APIKeyNotFoundError:
            logging.error("❌ Chave da API da OpenAI não encontrada")
            self.coder_system = None
        except Exception as e:
            self._log_error_with_context(e, "Inicialização CODER")
            self.coder_system = None
            # Tentar inicialização básica sem HMP como fallback
            try:
                logging.info("🔄 Tentando inicialização básica sem HMP...")
                # Importar diretamente componentes básicos para fallback
                from Agents import CODERAgent, BaseAgent
                from Memory import CognitiveMemory

                # Criar sistema mínimo funcional
                memory = CognitiveMemory()
                api_key = os.environ.get('OPENAI_API_KEY')
                if api_key:
                    coder_agent = CODERAgent(api_key)
                    base_agent = BaseAgent(api_key)

                    # Criar objeto pipeline mínimo
                    class MinimalPipeline:
                        def __init__(self):
                            self.coder_agent = coder_agent
                            self.memory = memory

                        def process_request_stream(self, user_input, user_id=None, **_):
                            yield {'type': 'thinking', 'message': 'Processando em modo básico...'}
                            try:
                                response = self.coder_agent.generate_simple_response(user_input, [])
                                yield {'type': 'response', 'message': response, 'artifacts': [], 'execution_log': ['Modo básico ativo']}
                            except Exception as e:
                                yield {'type': 'error', 'message': f'Erro no modo básico: {str(e)}'}

                        def get_memory_stats(self):
                            return {'mode': 'basic', 'interactions': 0}

                        def get_memory_insights(self):
                            return ['Sistema em modo básico']

                    self.coder_system = MinimalPipeline()
                    logging.info("✅ Sistema CODER inicializado em modo básico")
            except Exception as fallback_error:
                logging.error(f"❌ Falha também na inicialização básica: {fallback_error}")
                self.coder_system = None

        # Sempre inicializar sistema de autenticação
        try:
            # Se CODER disponível, usar sua memória; senão, criar memória independente
            if self.coder_system and hasattr(self.coder_system, 'memory'):
                self.auth_system = AuthSystem(self.coder_system.memory)
                logging.info("✅ Sistema de autenticação inicializado com memória CODER")
            else:
                # Criar sistema de memória independente para autenticação
                from Memory.cognitive_memory import CognitiveMemory
                standalone_memory = CognitiveMemory()
                self.auth_system = AuthSystem(standalone_memory)
                logging.info("✅ Sistema de autenticação inicializado com memória independente")
        except Exception as e:
            self._log_error_with_context(e, "Inicialização Sistema de Autenticação")
            self.auth_system = None

    # --- Helpers de workspace e artefatos ---

    def _get_workspace_info(self, ensure_exists: bool = True) -> tuple[str, str]:
        """Retorna caminho absoluto do workspace do usuário e o rótulo associado."""
        base = self.coderspace_root
        user = self.auth_system.get_current_user() if self.auth_system else None

        if not user:
            # Usuário não logado - criar workspace temporário
            temp_workspace = os.path.join(base, 'temp_anonymous')
            if ensure_exists:
                os.makedirs(temp_workspace, exist_ok=True)
            return temp_workspace, 'anonymous'

        # Criar nome único do diretório do usuário: username_userid
        username = user.get('username', 'user')
        user_id = user.get('user_id', 1)
        workspace_dirname = f"{username}_{user_id}"

        # Sanitizar nome do diretório
        import re
        workspace_dirname = re.sub(r'[^a-zA-Z0-9_-]', '_', workspace_dirname)

        workspace_path = os.path.join(base, workspace_dirname)

        # Garantir que permaneça dentro do CODERSPACE
        if not workspace_path.startswith(base):
            workspace_path = os.path.join(base, f"user_{user_id}")
            workspace_dirname = f"user_{user_id}"

        if ensure_exists:
            os.makedirs(workspace_path, exist_ok=True)

            # Criar arquivo README no workspace do usuário
            readme_path = os.path.join(workspace_path, 'README.md')
            if not os.path.exists(readme_path):
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Workspace de {username}\n\nEste é o workspace pessoal do usuário {username}.\n\nTodos os projetos criados pelo usuário ficarão organizados aqui.\n\n## Projetos:\n- (Seus projetos aparecerão aqui)\n")

        return workspace_path, workspace_dirname

    def _get_artifact_prefix(self) -> str:
        user = self.auth_system.get_current_user() if self.auth_system else None
        if user and user.get('user_id'):
            return f"u{user['user_id']}_"
        return "anon_"

    def _get_artifacts_directory(self) -> str:
        prefix = self._get_artifact_prefix().rstrip('_')
        if prefix == 'anon':
            artifacts_path = self.artifacts_root
        else:
            artifacts_path = os.path.join(self.artifacts_root, prefix)
        os.makedirs(artifacts_path, exist_ok=True)
        return artifacts_path

    def _setup_routes(self):
        """Configura as rotas da aplicação web."""

        @self.app.route('/')
        def index():
            """Página principal - redireciona para login se não autenticado."""
            if session.get('logged_in'):
                return redirect(url_for('chat_interface'))
            return redirect(url_for('login'))

        @self.app.route('/login')
        def login():
            """Página de login."""
            if session.get('logged_in'):
                return redirect(url_for('chat_interface'))
            return render_template('login.html')

        @self.app.route('/register')
        def register():
            """Página de registro."""
            if session.get('logged_in'):
                return redirect(url_for('chat_interface'))
            return render_template('register.html')

        @self.app.route('/chat')
        @require_login
        def chat_interface():
            """Página da interface de chat original."""
            user = self.auth_system.get_current_user() if self.auth_system else None
            return render_template('chat.html', user=user)

        @self.app.route('/agi')
        @require_login
        def agi_interface():
            """Página da interface AGI - redireciona para chat original."""
            return redirect(url_for('chat_interface'))

        @self.app.route('/api/auth/register', methods=['POST'])
        def auth_register():
            """Endpoint para registro de usuário."""
            if not self.auth_system:
                logging.error("Sistema de autenticação não disponível durante registro")
                return jsonify({'success': False, 'error': 'Sistema de autenticação temporariamente indisponível. Tente novamente em alguns segundos.'}), 503

            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

                username = data.get('username', '').strip()
                email = data.get('email', '').strip()
                password = data.get('password', '')

                # Validações básicas
                if not username or len(username) < 3:
                    return jsonify({'success': False, 'error': 'Nome de usuário deve ter pelo menos 3 caracteres'}), 400

                if not email or '@' not in email:
                    return jsonify({'success': False, 'error': 'Email inválido'}), 400

                if not password or len(password) < 6:
                    return jsonify({'success': False, 'error': 'Senha deve ter pelo menos 6 caracteres'}), 400

                logging.info(f"Tentativa de registro para usuário: {username}")
                result = self.auth_system.register_user(username, email, password)

                if result.get('success'):
                    logging.info(f"✅ Usuário registrado com sucesso: {username}")
                else:
                    logging.warning(f"❌ Falha no registro para {username}: {result.get('error')}")

                return jsonify(result)

            except ValueError as ve:
                # Erros de validação específicos
                logging.warning(f"Erro de validação no registro: {ve}")
                return jsonify({'success': False, 'error': str(ve)}), 400
            except Exception as e:
                self._log_error_with_context(e, "Registro de usuário")
                return jsonify({'success': False, 'error': 'Erro interno do servidor. Tente novamente.'}), 500

        @self.app.route('/api/auth/login', methods=['POST'])
        def auth_login():
            """Endpoint para login de usuário."""
            if not self.auth_system:
                return jsonify({'success': False, 'error': 'Sistema de autenticação não disponível'}), 503

            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

                username = data.get('username', '').strip()
                password = data.get('password', '')

                result = self.auth_system.login_user(username, password)
                return jsonify(result)

            except Exception as e:
                self._log_error_with_context(e, "Login de usuário")
                return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

        @self.app.route('/api/auth/logout', methods=['POST'])
        def auth_logout():
            """Endpoint para logout de usuário."""
            try:
                # Limpar sessão Flask
                session.clear()

                # Se sistema de auth disponível, usar logout formal
                if self.auth_system:
                    try:
                        result = self.auth_system.logout_user()
                        logging.info(f"Logout realizado via auth_system: {result}")
                    except Exception as e:
                        logging.warning(f"Erro no logout via auth_system: {e}")

                # Sempre retornar sucesso para logout
                return jsonify({
                    'success': True, 
                    'message': 'Logout realizado com sucesso',
                    'redirect': '/login'
                })

            except Exception as e:
                self._log_error_with_context(e, "Logout de usuário")
                # Mesmo com erro, permitir logout
                session.clear()
                return jsonify({
                    'success': True, 
                    'message': 'Logout realizado (com avisos)',
                    'redirect': '/login'
                })

        @self.app.route('/api/auth/user')
        def auth_user():
            """Endpoint para obter dados do usuário atual."""
            if not self.auth_system:
                return jsonify({'logged_in': False}), 503

            try:
                user = self.auth_system.get_current_user()
                if user:
                    # Try to get avatar from memory system
                    avatar = None
                    if hasattr(self.auth_system.memory, 'get_user_avatar'):
                        try:
                            avatar = self.auth_system.memory.get_user_avatar(user['user_id'])
                        except Exception:
                            pass

                    # Fallback to session avatar
                    if not avatar:
                        avatar = session.get('user_avatar')

                    # Get email from memory system
                    email = None
                    if hasattr(self.auth_system.memory, 'get_user_email'):
                        try:
                            email = self.auth_system.memory.get_user_email(user['user_id'])
                        except Exception:
                            pass

                    user_data = user.copy()
                    user_data['avatar'] = avatar
                    user_data['email'] = email or f"{user['username']}@coder.local"

                    return jsonify(user_data)
                else:
                    return jsonify({'logged_in': False})

            except Exception as e:
                self._log_error_with_context(e, "Obter usuário atual")
                return jsonify({'logged_in': False}), 500

        @self.app.route('/api/user')
        def get_user():
            """Endpoint alternativo para compatibilidade - obter dados do usuário atual."""
            if not self.auth_system:
                return jsonify({'logged_in': False}), 503

            try:
                user = self.auth_system.get_current_user()
                if user:
                    return jsonify(user)
                else:
                    return jsonify({'logged_in': False})

            except Exception as e:
                self._log_error_with_context(e, "Obter usuário atual")
                return jsonify({'logged_in': False}), 500

        @self.app.route('/api/status')
        def status():
            """Status do sistema."""
            try:
                # Verificar se API está configurada
                api_key = os.environ.get('OPENAI_API_KEY')
                api_configured = api_key is not None and len(api_key.strip()) > 0

                base_status = {
                    'status': 'online' if (self.coder_system and api_configured) else 'offline',
                    'coder_available': self.coder_system is not None,
                    'api_configured': api_configured,
                    'message': 'Sistema operacional' if (self.coder_system and api_configured) else 'Sistema em modo básico'
                }

                if not api_configured:
                    base_status['warning'] = 'Configure OPENAI_API_KEY para funcionalidade completa'
                elif not self.coder_system:
                    base_status['warning'] = 'Sistema CODER não inicializado corretamente'

                # Adicionar informações de evolução se sistema disponível
                if self.coder_system:
                    try:
                        system_status = self.coder_system.get_system_status()
                        base_status.update(system_status)
                    except AttributeError:
                        # Método não existe ainda, usar status básico
                        base_status['hmp_enabled'] = hasattr(self.coder_system, 'hmp_enabled') and self.coder_system.hmp_enabled
                    except Exception as e:
                        self._log_error_with_context(e, "Obtenção status avançado")
                        base_status['warning'] = 'Status avançado indisponível'

                return jsonify(base_status)
            except Exception as e:
                self._log_error_with_context(e, "Obtenção status do sistema")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/chat', methods=['POST'])
        @require_login
        def chat():
            """Endpoint para chat com CODER com streaming ou modo fallback."""
            request_id = f"req_{hash(request.json.get('message', ''))}_{int(time.time())}" if request.json else f"req_{int(time.time())}"
            logging.info(f"Nova requisição recebida: {request_id}")
            try:
                data = request.get_json()
                user_message = data.get('message', '').strip()
                uploaded_files = data.get('files', [])

                if not user_message and not uploaded_files:
                    return jsonify({
                        'error': 'Mensagem ou arquivo é obrigatório',
                        'success': False
                    }), 400

                # Modo fallback quando CODER não está disponível
                if not self.coder_system:
                    def generate_fallback_stream():
                        yield f"data: {self._safe_json_dumps({'type': 'status', 'message': 'Sistema em modo fallback'})}\n\n"

                        # Processar arquivos se houver
                        file_info = ""
                        if uploaded_files:
                            file_names = [f.get('filename', 'arquivo') for f in uploaded_files]
                            file_info = f"\n\n**Arquivos recebidos:** {', '.join(file_names)}"

                        # Resposta fallback inteligente
                        fallback_response = self._generate_fallback_response(user_message, uploaded_files)

                        yield f"data: {self._safe_json_dumps({'type': 'response', 'message': fallback_response + file_info}) }\n\n"
                        yield f"data: {self._safe_json_dumps({'type': 'complete'})}\n\n"

                    return Response(
                        generate_fallback_stream(),
                        mimetype='text/event-stream',
                        headers={
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Cache-Control'
                        }
                    )

                # Obter ID do usuário atual
                current_user = self.auth_system.get_current_user() if self.auth_system else None
                user_id = current_user['user_id'] if current_user else 1

                workspace_path, workspace_dirname = self._get_workspace_info()
                artifact_prefix = self._get_artifact_prefix()

                # Processar arquivos enviados e adicionar ao contexto
                if uploaded_files:
                    file_context = self._build_file_context(uploaded_files)
                    if file_context:
                        user_message = f"{user_message}\n\n{file_context}" if user_message else file_context

                # Log da requisição para debug
                logging.info(f"Nova requisição recebida: {request_id} (Usuário: {user_id})")

                def generate_stream():
                    response_sent = False
                    events_sent = 0
                    try:
                        # Início detalhado do processamento
                        yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Iniciando análise da solicitação...', 'request_id': request_id})}\n\n"
                        events_sent += 1

                        yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Identificando tipo de solicitação e agentes necessários...', 'request_id': request_id})}\n\n"
                        events_sent += 1

                        # Análise inicial
                        yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': 'analysis', 'action_name': 'Análise Inicial', 'action_type': 'analysis', 'description': 'Analisando prompt do usuário e contexto', 'request_id': request_id})}\n\n"
                        events_sent += 1

                        # Processar com CODER de forma detalhada
                        pipeline_events = []
                        for event in self.coder_system.process_request_stream(
                            user_message,
                            user_id=user_id,
                            workspace_path=workspace_path,
                            artifact_prefix=artifact_prefix,
                            workspace_label=workspace_dirname
                        ):
                            pipeline_events.append(event)

                        # Processar eventos com mais detalhes
                        for i, event in enumerate(pipeline_events):
                            # Adicionar ID da requisição
                            event['request_id'] = request_id

                            # Enviar eventos detalhados baseados no tipo
                            event_type = event.get('type')

                            if event_type == 'thinking':
                                # Melhorar mensagens de pensamento
                                thinking_msg = event.get('message', '')
                                enhanced_thinking = self._enhance_thinking_message(thinking_msg, i + 1)

                                yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': enhanced_thinking, 'step': i + 1, 'request_id': request_id})}\n\n"
                                events_sent += 1

                                # Adicionar ação correspondente ao pensamento
                                if 'web' in thinking_msg.lower() or 'pesquis' in thinking_msg.lower():
                                    yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': f'web_search_{i}', 'action_name': 'Busca na Web', 'action_type': 'web_search', 'description': 'Pesquisando informações relevantes', 'request_id': request_id})}\n\n"
                                    yield f"data: {self._safe_json_dumps({'type': 'action_progress', 'action_id': f'web_search_{i}', 'progress': 75, 'details': 'Coletando dados...', 'request_id': request_id})}\n\n"
                                elif 'código' in thinking_msg.lower() or 'execut' in thinking_msg.lower():
                                    yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': f'code_exec_{i}', 'action_name': 'Execução de Código', 'action_type': 'code_execution', 'description': 'Processando e executando código', 'request_id': request_id})}\n\n"
                                    yield f"data: {self._safe_json_dumps({'type': 'tool_execution', 'tool_name': 'Python Interpreter', 'command': 'python script.py', 'details': 'Executando script Python...', 'request_id': request_id})}\n\n"
                                elif 'plan' in thinking_msg.lower() or 'decomp' in thinking_msg.lower():
                                    yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': f'planning_{i}', 'action_name': 'Planejamento', 'action_type': 'planning', 'description': 'Criando plano de execução estruturado', 'request_id': request_id})}\n\n"

                                events_sent += 2

                            elif event_type == 'orchestrator_planning':
                                yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Orquestrador criando plano de execução...', 'request_id': request_id})}\n\n"
                                yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': 'orchestrator_plan', 'action_name': 'Planejamento Orquestrador', 'action_type': 'planning', 'description': 'Definindo sequência de agentes e ações', 'request_id': request_id})}\n\n"
                                events_sent += 2

                            elif event_type == 'agent_execution':
                                agent_name = event.get('agent', 'desconhecido')
                                yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': f'Ativando agente {agent_name}...', 'request_id': request_id})}\n\n"
                                yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': f'agent_{agent_name}', 'action_name': f'Agente {agent_name.title()}', 'action_type': 'agent_execution', 'description': f'Executando tarefas do agente {agent_name}', 'request_id': request_id})}\n\n"
                                events_sent += 2

                            elif event_type == 'tool_usage':
                                tool_name = event.get('tool', 'ferramenta')
                                yield f"data: {self._safe_json_dumps({'type': 'tool_execution', 'tool_name': tool_name, 'command': event.get('command', ''), 'details': f'Usando {tool_name}...', 'request_id': request_id})}\n\n"
                                events_sent += 1

                            elif event_type == 'validation':
                                yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Validando resultados e qualidade...', 'request_id': request_id})}\n\n"
                                yield f"data: {self._safe_json_dumps({'type': 'validation', 'result': event.get('result', 'OK'), 'details': 'Verificação de qualidade concluída', 'request_id': request_id})}\n\n"
                                events_sent += 2

                            elif event_type == 'synthesis':
                                yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Sintetizando resposta final...', 'request_id': request_id})}\n\n"
                                yield f"data: {self._safe_json_dumps({'type': 'action_start', 'action_id': 'synthesis', 'action_name': 'Síntese Final', 'action_type': 'synthesis', 'description': 'Organizando e formatando resposta', 'request_id': request_id})}\n\n"
                                events_sent += 2

                            elif event_type == 'response':
                                # Completar ações pendentes
                                yield f"data: {self._safe_json_dumps({'type': 'action_complete', 'action_id': 'analysis', 'result': 'Análise concluída com sucesso', 'request_id': request_id})}\n\n"

                                # Controle contra duplicação de resposta
                                if response_sent:
                                    continue
                                response_sent = True
                                logging.info(f"Resposta final para {request_id}")

                                # Preparar artefatos se presentes na resposta
                                if event.get('artifacts'):
                                    event = self._process_response_with_artifacts(event)

                                yield f"data: {self._safe_json_dumps(event)}\n\n"
                                events_sent += 2

                            elif event_type in ['error', 'complete']:
                                yield f"data: {self._safe_json_dumps(event)}\n\n"
                                events_sent += 1
                                if event_type == 'complete':
                                    break

                        # Completar processo se não houve resposta ainda
                        if not response_sent:
                            yield f"data: {self._safe_json_dumps({'type': 'thinking', 'message': 'Finalizando processamento...', 'request_id': request_id})}\n\n"
                            yield f"data: {self._safe_json_dumps({'type': 'response', 'message': 'Processamento concluído. Como posso ajudar mais?', 'request_id': request_id})}\n\n"
                            events_sent += 2

                    except Exception as e:
                        self._log_error_with_context(e, "Geração de stream", request_id)
                        yield f"data: {self._safe_json_dumps({'type': 'error', 'message': f'Erro durante processamento: {str(e)}', 'request_id': request_id})}\n\n"
                        events_sent += 1
                    finally:
                        # Garantir sinal de completude único
                        yield f"data: {self._safe_json_dumps({'type': 'complete', 'request_id': request_id, 'events_total': events_sent, 'response_sent': response_sent})}\n\n"
                        logging.info(f"Streaming detalhado finalizado para {request_id} com {events_sent} eventos (resposta enviada: {response_sent})")

                return Response(
                    generate_stream(),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Cache-Control'
                    }
                )

            except Exception as e:
                self._log_error_with_context(e, "Endpoint Chat", request_id)
                return jsonify({
                    'error': f'Erro interno: {str(e)}',
                    'success': False
                }), 500

        @self.app.route('/api/chat/stream', methods=['POST'])
        @require_login
        def chat_stream():
            """Endpoint para chat com streaming com CODER."""
            if not self.coder_system:
                logging.error("Sistema CODER não disponível para chat stream")
                return jsonify({
                    'error': 'Sistema CODER não está disponível',
                    'success': False
                }), 503

            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'error': 'Dados JSON inválidos',
                        'success': False
                    }), 400

                user_message = data.get('message', '').strip()

                if not user_message:
                    return jsonify({
                        'error': 'Mensagem não pode estar vazia',
                        'success': False
                    }), 400

                logging.info(f"Processando mensagem via stream: {user_message[:50]}...")

                current_user = self.auth_system.get_current_user() if self.auth_system else None
                user_id = current_user['user_id'] if current_user else 1
                workspace_path, workspace_dirname = self._get_workspace_info()
                artifact_prefix = self._get_artifact_prefix()

                # Por enquanto, redirecionamos para o endpoint regular
                # Em futuras versões, implementaremos streaming real
                result = self.coder_system.process_request(
                    user_message,
                    user_id=user_id,
                    workspace_path=workspace_path,
                    artifact_prefix=artifact_prefix,
                    workspace_label=workspace_dirname
                )

                return jsonify({
                    'response': result.get('final_response'),
                    'execution_log': result.get('execution_log', []),
                    'plan': result.get('plan', []),
                    'artifacts': result.get('artifacts', []),
                    'workspace_path': result.get('workspace_path'),
                    'artifacts_dir': result.get('artifacts_dir'),
                    'workspace_label': current_user.get('username') if current_user else workspace_dirname,
                    'success': True
                })

            except Exception as e:
                self._log_error_with_context(e, "Endpoint Chat Stream")
                return jsonify({
                    'error': f'Erro interno: {str(e)}',
                    'success': False
                }), 500

        @self.app.route('/api/memory/stats')
        def memory_stats():
            """Estatísticas da memória."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema não disponível'}), 503

            try:
                stats = self.coder_system.get_memory_stats()
                return jsonify(stats)
            except Exception as e:
                self._log_error_with_context(e, "Estatísticas de Memória")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/memory/insights')
        def memory_insights():
            """Insights da memória."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema não disponível'}), 503

            try:
                insights = self.coder_system.get_memory_insights()
                return jsonify({'insights': insights})
            except Exception as e:
                self._log_error_with_context(e, "Insights de Memória")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/upload', methods=['POST'])
        def upload_file():
            """Endpoint para upload de arquivos."""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'Nenhum arquivo enviado'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'Nome do arquivo vazio'}), 400

                # Verificar tamanho do arquivo (máximo 10MB)
                file.seek(0, 2)  # Ir para o final do arquivo
                file_size = file.tell()
                file.seek(0)  # Voltar ao início

                if file_size > 10 * 1024 * 1024:  # 10MB
                    return jsonify({'error': 'Arquivo muito grande. Máximo 10MB.'}), 400

                # Ler conteúdo do arquivo
                file_content = file.read()
                filename = file.filename
                content_type = file.content_type or 'application/octet-stream'

                # Processar arquivo baseado no tipo
                processed_data = self._process_uploaded_file(file_content, filename, content_type)

                return jsonify({
                    'success': True,
                    'filename': filename,
                    'content_type': content_type,
                    'size': file_size,
                    'processed_data': processed_data,
                    'file_type': self._get_file_type(filename, content_type)
                })

            except Exception as e:
                self._log_error_with_context(e, "Upload de Arquivo")
                return jsonify({'error': f'Erro no upload: {str(e)}'}), 500

        @self.app.route('/api/user/avatar', methods=['POST'])
        @require_login
        def update_user_avatar():
            """Endpoint para atualizar avatar do usuário."""
            if not self.auth_system:
                return jsonify({'success': False, 'error': 'Sistema de autenticação não disponível'}), 503

            try:
                data = request.get_json()
                avatar_data = data.get('avatar')

                current_user = self.auth_system.get_current_user()
                if not current_user:
                    return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 401

                user_id = current_user['user_id']

                # Save avatar in memory system
                if hasattr(self.auth_system.memory, 'update_user_avatar'):
                    success = self.auth_system.memory.update_user_avatar(user_id, avatar_data)
                    if success:
                        return jsonify({'success': True, 'message': 'Avatar atualizado com sucesso'})
                    else:
                        return jsonify({'success': False, 'error': 'Erro ao salvar avatar'}), 500
                else:
                    # Fallback - store in session for now
                    session['user_avatar'] = avatar_data
                    return jsonify({'success': True, 'message': 'Avatar atualizado temporariamente'})

            except Exception as e:
                self._log_error_with_context(e, "Atualizar Avatar")
                return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

        @self.app.route('/api/projects/tree', methods=['GET'])
        @require_login
        def project_tree():
            """Retorna a árvore de diretórios e arquivos dos projetos."""
            try:
                workspace_path, workspace_dirname = self._get_workspace_info()
                user = self.auth_system.get_current_user() if self.auth_system else None
                display_label = user['username'] if user and user.get('username') else workspace_dirname

                # Construir árvore de projetos real
                projects = self._build_project_tree(workspace_path)

                # Log para debug
                logging.info(f"📁 Usuário {display_label} acessando workspace: {workspace_path}")
                logging.info(f"📂 Projetos encontrados: {len(projects)} itens")

                return jsonify({
                    'success': True,
                    'projects': projects,
                    'root': display_label,
                    'workspace_root': workspace_dirname,
                    'workspace_label': display_label,
                    'workspace_path': workspace_path,
                    'total_items': len(projects)
                })
            except Exception as e:
                self._log_error_with_context(e, "Listar Projetos")
                return jsonify({'success': False, 'error': 'Não foi possível listar os projetos'}), 500

        @self.app.route('/api/projects', methods=['POST'])
        @require_login
        def create_project_item():
            """Cria pastas ou arquivos dentro do diretório de projetos."""
            try:
                data = request.get_json(force=True)
            except Exception:
                return jsonify({'success': False, 'error': 'Payload JSON inválido'}), 400

            item_type = (data or {}).get('type')
            target_path = (data or {}).get('path', '')
            content = (data or {}).get('content', '')

            if item_type not in {'folder', 'file'}:
                return jsonify({'success': False, 'error': 'Tipo inválido. Use "folder" ou "file"'}), 400

            workspace_path, workspace_dirname = self._get_workspace_info()

            try:
                full_path = self._safe_project_path(workspace_path, target_path)
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

            try:
                if item_type == 'folder':
                    os.makedirs(full_path, exist_ok=False)
                else:
                    parent_dir = os.path.dirname(full_path)
                    os.makedirs(parent_dir, exist_ok=True)
                    if os.path.exists(full_path):
                        return jsonify({'success': False, 'error': 'Arquivo já existe'}), 409
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content or '')

                relative = os.path.relpath(full_path, workspace_path).replace('\\', '/')
                return jsonify({
                    'success': True,
                    'item': {
                        'type': item_type,
                        'path': relative,
                        'name': os.path.basename(full_path)
                    }
                })
            except FileExistsError:
                return jsonify({'success': False, 'error': 'Item já existe'}), 409
            except OSError as e:
                self._log_error_with_context(e, "Criar Projeto")
                return jsonify({'success': False, 'error': f'Não foi possível criar o item: {str(e)}'}), 500

        @self.app.route('/api/projects/file', methods=['GET'])
        @require_login
        def read_project_file():
            """Retorna o conteúdo de um arquivo do diretório de projetos."""
            relative_path = request.args.get('path', '')
            workspace_path, _ = self._get_workspace_info()

            try:
                full_path = self._safe_project_path(workspace_path, relative_path)
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                return jsonify({'success': False, 'error': 'Arquivo não é texto UTF-8'}), 415
            except OSError as e:
                self._log_error_with_context(e, "Ler Arquivo Projeto")
                return jsonify({'success': False, 'error': 'Não foi possível abrir o arquivo'}), 500

            relative = os.path.relpath(full_path, workspace_path).replace('\\', '/')
            return jsonify({'success': True, 'path': relative, 'content': content})

        @self.app.route('/api/projects/file', methods=['PUT'])
        @require_login
        def update_project_file():
            """Atualiza o conteúdo de um arquivo existente."""
            try:
                data = request.get_json(force=True)
            except Exception:
                return jsonify({'success': False, 'error': 'Payload JSON inválido'}), 400

            relative_path = (data or {}).get('path')
            content = (data or {}).get('content')

            if not relative_path:
                return jsonify({'success': False, 'error': 'Path é obrigatório'}), 400

            workspace_path, _ = self._get_workspace_info()

            try:
                full_path = self._safe_project_path(workspace_path, relative_path)
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404

            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content or '')
            except OSError as e:
                self._log_error_with_context(e, "Atualizar Arquivo Projeto")
                return jsonify({'success': False, 'error': 'Não foi possível salvar o arquivo'}), 500

            relative = os.path.relpath(full_path, workspace_path).replace('\\', '/')
            return jsonify({'success': True, 'path': relative})

        @self.app.route('/api/artifacts/save', methods=['POST'])
        @require_login
        def save_artifact():
            """Salva artefato no servidor."""
            try:
                data = request.get_json()
                filename = data.get('filename')
                content = data.get('content')
                title = data.get('title', 'Artefato')
                artifact_type = data.get('type', 'visualization')

                if not filename or not content:
                    return jsonify({'error': 'Filename e content são obrigatórios'}), 400

                artifacts_dir = self._get_artifacts_directory()
                prefix = self._get_artifact_prefix()

                # Limpar nome do arquivo e adicionar timestamp único
                import time
                timestamp = int(time.time() * 1000)  # timestamp em milissegundos
                safe_filename = filename.replace('/', '_').replace('\\', '_')

                # Adicionar timestamp se não estiver presente
                if str(timestamp) not in safe_filename:
                    base_name = safe_filename.replace('.html', '')
                    safe_filename = f"{base_name}_{timestamp}.html"
                elif not safe_filename.endswith('.html'):
                    safe_filename += '.html'

                if not safe_filename.startswith(prefix):
                    safe_filename = f"{prefix}{safe_filename}"

                file_path = os.path.join(artifacts_dir, safe_filename)

                # Verificar se arquivo já existe para evitar sobrescrita
                counter = 1
                original_path = file_path
                while os.path.exists(file_path):
                    base_name = safe_filename.replace('.html', '')
                    safe_filename = f"{base_name}_{counter}.html"
                    file_path = os.path.join(artifacts_dir, safe_filename)
                    counter += 1

                # Melhorar conteúdo HTML se necessário
                enhanced_content = self._enhance_artifact_formatting(content)

                # Salvar arquivo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)

                logging.info(f"✅ Artefato salvo: {title} -> {file_path}")

                relative_path = os.path.relpath(file_path, self.artifacts_root).replace('\\', '/')
                return jsonify({
                    'success': True,
                    'filename': safe_filename,
                    'path': relative_path,
                    'url': f'/artifact/{relative_path}',
                    'type': artifact_type
                })

            except Exception as e:
                self._log_error_with_context(e, "Salvar Artefato")
                return jsonify({'error': f'Erro ao salvar: {str(e)}'}), 500

        @self.app.route('/api/artifacts/list')
        @require_login
        def list_artifacts():
            """Lista todos os artefatos disponíveis."""
            try:
                artifacts_dir = self._get_artifacts_directory()
                prefix = self._get_artifact_prefix()
                if not os.path.exists(artifacts_dir):
                    return jsonify({'artifacts': []})

                artifacts = []
                for filename in os.listdir(artifacts_dir):
                    if filename.endswith('.html'):
                        file_path = os.path.join(artifacts_dir, filename)

                        # Se estiver usando diretório compartilhado, filtrar por prefixo
                        if artifacts_dir == self.artifacts_root and not filename.startswith(prefix):
                            continue

                        # Obter informações do arquivo
                        stat = os.stat(file_path)
                        created_time = stat.st_mtime

                        # Determinar tipo e título baseado no nome
                        artifact_type = self._determine_artifact_type(filename)
                        title = self._determine_artifact_title(filename)

                        relative_path = os.path.relpath(file_path, self.artifacts_root).replace('\\', '/')
                        artifacts.append({
                            'filename': filename,
                            'path': relative_path,
                            'title': title,
                            'type': artifact_type,
                            'created': created_time,
                            'url': f'/artifact/{relative_path}'
                        })

                # Ordenar por data de criação (mais recente primeiro)
                artifacts.sort(key=lambda x: x['created'], reverse=True)

                return jsonify({'artifacts': artifacts})

            except Exception as e:
                self._log_error_with_context(e, "Listar Artefatos")
                return jsonify({'error': f'Erro ao listar: {str(e)}'}), 500

        @self.app.route('/artifact/<path:filename>')
        @require_login
        def serve_artifact(filename):
            """Serve artefatos HTML individuais."""
            try:
                logging.info(f"📂 Tentando servir artefato: {filename}")

                normalized = os.path.normpath(filename).strip('\/')
                if normalized.startswith('..'):
                    return jsonify({'error': 'Artefato não encontrado'}), 404

                file_path = os.path.abspath(os.path.join(self.artifacts_root, normalized))

                if not file_path.startswith(self.artifacts_root):
                    return jsonify({'error': 'Artefato não encontrado'}), 404

                if not os.path.exists(file_path):
                    logging.error(f"❌ Artefato não encontrado: {file_path}")
                    return jsonify({'error': 'Artefato não encontrado'}), 404

                prefix = self._get_artifact_prefix()
                if not os.path.basename(file_path).startswith(prefix):
                    logging.warning("Tentativa de acesso a artefato de outro usuário bloqueada")
                    return jsonify({'error': 'Artefato não encontrado'}), 404

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Melhorar formatação do conteúdo
                enhanced_content = self._enhance_artifact_formatting(content)

                logging.info(f"✅ Artefato servido com sucesso: {filename}")
                return enhanced_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

            except Exception as e:
                self._log_error_with_context(e, f"Servir Artefato {filename}")
                return jsonify({'error': f'Erro ao carregar artefato: {str(e)}'}), 500

        @self.app.route('/code/<filename>')
        def serve_code(filename):
            """Serve arquivos de código para download."""
            try:
                # Verificar se o arquivo existe no diretório de códigos
                codes_dir = "CODES"
                file_path = os.path.join(codes_dir, filename)

                if not os.path.exists(file_path):
                    return jsonify({'error': 'Arquivo de código não encontrado'}), 404

                # Ler o conteúdo do arquivo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Determinar tipo de conteúdo baseado na extensão
                content_types = {
                    '.py': 'text/x-python',
                    '.js': 'text/javascript',
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.sql': 'text/plain',
                    '.sh': 'text/x-shellscript',
                    '.json': 'application/json',
                    '.xml': 'text/xml'
                }

                ext = os.path.splitext(filename)[1]
                content_type = content_types.get(ext, 'text/plain')

                return content, 200, {
                    'Content-Type': f'{content_type}; charset=utf-8',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }

            except Exception as e:
                self._log_error_with_context(e, f"Servir Código {filename}")
                return jsonify({'error': f'Erro ao carregar código: {str(e)}'}), 500

        # ---- ROTAS PARA SISTEMA DE EVOLUÇÃO E AGENTES ----

        @self.app.route('/api/agents')
        def agents():
            """Endpoint para listar agentes registrados."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema CODER não está disponível'}), 503
            try:
                agents_info = self.coder_system.get_agent_registry()
                return jsonify(agents_info)
            except Exception as e:
                self._log_error_with_context(e, "Listar Agentes")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/create_agent', methods=['POST'])
        def create_agent():
            """Endpoint para criar novo agente."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema CODER não está disponível'}), 503
            try:
                specification = request.json
                if not specification:
                    return jsonify({'error': 'Especificação do agente é necessária'}), 400
                result = self.coder_system.create_agent(specification)
                return jsonify(result)
            except Exception as e:
                self._log_error_with_context(e, "Criar Agente")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/evolve_agent', methods=['POST'])
        def evolve_agent():
            """Endpoint para evoluir agente específico."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema CODER não está disponível'}), 503
            try:
                data = request.json
                agent_name = data.get('agent_name')
                feedback = data.get('feedback', {})

                if not agent_name:
                    return jsonify({'error': 'Nome do agente é necessário'}), 400

                result = self.coder_system.evolve_agent(agent_name, feedback)
                return jsonify(result)
            except Exception as e:
                self._log_error_with_context(e, "Evoluir Agente")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/trigger_evolution', methods=['POST'])
        def trigger_evolution():
            """Endpoint para disparar evolução manual."""
            if not self.coder_system:
                return jsonify({'error': 'Sistema CODER não está disponível'}), 503
            try:
                data = request.json or {}
                target_agent = data.get('target_agent') # Pode ser None para evolução geral

                result = self.coder_system.trigger_evolution(target_agent)
                return jsonify(result)
            except Exception as e:
                self._log_error_with_context(e, "Disparar Evolução")
                return jsonify({"error": str(e)}), 500

        # ---- FIM DAS ROTAS DE EVOLUÇÃO ----

        @self.app.route('/templates/assets/js/<path:filename>')
        def serve_template_js(filename):
            """Serve arquivos JavaScript do diretório templates/assets/js."""
            try:
                js_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'assets', 'js')
                return send_from_directory(js_path, filename, mimetype='application/javascript')
            except Exception as e:
                logging.error(f"Erro ao servir JS {filename}: {e}")
                return jsonify({'error': 'Arquivo não encontrado'}), 404

        @self.app.route('/templates/assets/css/<path:filename>')
        def serve_template_css(filename):
            """Serve arquivos CSS do diretório templates/assets/css."""
            try:
                css_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'assets', 'css')
                return send_from_directory(css_path, filename, mimetype='text/css')
            except Exception as e:
                logging.error(f"Erro ao servir CSS {filename}: {e}")
                return jsonify({'error': 'Arquivo não encontrado'}), 404

        @self.app.route('/favicon.ico')
        def favicon():
            """Serve favicon."""
            try:
                return send_from_directory(
                    os.path.join(os.path.dirname(__file__), '..', 'static'), 
                    'favicon.ico', 
                    mimetype='image/vnd.microsoft.icon'
                )
            except:
                return '', 204

        @self.app.route('/api', methods=['GET', 'HEAD'])
        def api_root():
            """Endpoint raiz da API - usado para health checks."""
            try:
                # Para chamadas HEAD, retornar apenas o status sem logs excessivos
                if request.method == 'HEAD':
                    return '', 200

                api_key = os.environ.get('OPENAI_API_KEY')
                api_configured = api_key is not None and len(api_key.strip()) > 0

                return jsonify({
                    'status': 'online',
                    'service': 'CODER API',
                    'version': '2.0.0',
                    'api_configured': api_configured,
                    'roko_available': self.coder_system is not None,
                    'endpoints': [
                        '/api/chat',
                        '/api/status', 
                        '/api/auth/*',
                        '/api/user',
                        '/api/memory/*'
                    ]
                })
            except Exception as e:
                if request.method == 'HEAD':
                    return '', 500
                return jsonify({'error': str(e), 'status': 'error'}), 500

        @self.app.route('/api/system_status')
        def system_status():
            """Endpoint para status do sistema."""
            try:
                status = {
                    'status': 'operational',
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0.0',
                    'features': {
                        'hmp_router': True,
                        'autoflux': True,
                        'memory_system': True,
                        'agents': True
                    }
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500


        @self.app.route('/manifest.json')
        def manifest():
            """Serve manifest PWA."""
            try:
                manifest_path = os.path.join(self.template_dir, 'manifest.json')
                if os.path.exists(manifest_path):
                    return send_from_directory(self.template_dir, 'manifest.json', 
                                               mimetype='application/json')
                else:
                    # Gerar manifest dinâmico
                    manifest_data = {
                        "name": "CODER - Advanced AI Assistant",
                        "short_name": "CODER",
                        "description": "Assistente IA Avançada com capacidades autônomas",
                        "start_url": "/",
                        "display": "standalone",
                        "background_color": "#0f172a",
                        "theme_color": "#6366f1",
                        "orientation": "portrait-primary",
                        "scope": "/",
                        "icons": [
                            {
                                "src": "https://i.ibb.co/zh78CmPv/file-00000000732061f48150b71cdeef53c1.png",
                                "sizes": "192x192",
                                "type": "image/png",
                                "purpose": "any maskable"
                            },
                            {
                                "src": "https://i.ibb.co/zh78CmPv/file-00000000732061f48150b71cdeef53c1.png",
                                "sizes": "512x512",
                                "type": "image/png",
                                "purpose": "any maskable"
                            }
                        ],
                        "categories": ["productivity", "utilities"],
                        "screenshots": [
                            {
                                "src": "https://i.ibb.co/zh78CmPv/file-00000000732061f48150b71cdeef53c1.png",
                                "sizes": "1280x720",
                                "type": "image/png"
                            }
                        ]
                    }
                    return jsonify(manifest_data), 200, {'Content-Type': 'application/manifest+json'}
            except Exception as e:
                self._log_error_with_context(e, "Servir Manifest")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/sw.js')
        def service_worker():
            """Serve Service Worker para PWA."""
            try:
                sw_path = os.path.join(self.template_dir, 'sw.js')
                if os.path.exists(sw_path):
                    with open(sw_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return content, 200, {'Content-Type': 'application/javascript'}
                else:
                    return "// Service Worker não encontrado", 404
            except Exception as e:
                self._log_error_with_context(e, "Servir Service Worker")
                return "// Erro no Service Worker", 500


        @self.app.errorhandler(404)
        def not_found(error):
            """Handler para páginas não encontradas."""
            # Evitar spam de logs para chamadas HEAD frequentes
            if request.method != 'HEAD':
                logging.warning(f"Endpoint não encontrado: {request.path}")
            return jsonify({'error': 'Endpoint não encontrado'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handler para erros internos."""
            self._log_error_with_context(error, "Erro Interno do Servidor")
            return jsonify({'error': 'Erro interno do servidor'}), 500

    def _extract_artifacts_from_logs(self, execution_log):
        """Extrai artefatos HTML dos logs de execução."""
        artifacts = []
        processed_files = set()

        for log in execution_log:
            # Buscar por visualizações HTML criadas
            if 'visualization' in log.lower() and '.html' in log:
                try:
                    # Extrair nome do arquivo
                    import re
                    filename_match = re.search(r'(\w+_visualization\.html)', log)
                    if filename_match:
                        filename = filename_match.group(1)

                        # Evitar processamento duplicado do mesmo arquivo
                        if filename in processed_files:
                            logging.info(f"📋 Arquivo já processado, ignorando: {filename}")
                            continue

                        processed_files.add(filename)

                        # Tentar ler o arquivo
                        try:
                            with open(filename, 'r', encoding='utf-8') as f:
                                html_content = f.read()

                            # Determinar tipo e título baseado no nome do arquivo
                            artifact_type = self._determine_artifact_type(filename)
                            title = self._determine_artifact_title(filename)

                            artifacts.append({
                                'title': title,
                                'type': artifact_type,
                                'content': html_content
                            })

                            logging.info(f"✅ Artefato extraído: {title} ({filename})")

                        except FileNotFoundError:
                            logging.warning(f"Arquivo de visualização não encontrado: {filename}")

                except Exception as e:
                    self._log_error_with_context(e, "Extração de Artefato")

        # Remover duplicatas baseado em título e tipo
        unique_artifacts = []
        seen_artifacts = set()

        for artifact in artifacts:
            artifact_key = f"{artifact['title']}_{artifact['type']}"
            if artifact_key not in seen_artifacts:
                unique_artifacts.append(artifact)
                seen_artifacts.add(artifact_key)
            else:
                logging.info(f"🚫 Artefato duplicado removido: {artifact['title']}")

        return unique_artifacts

    def _determine_artifact_type(self, filename):
        """Determina o tipo de artefato baseado no nome do arquivo."""
        if 'chart' in filename or 'graph' in filename:
            return 'chart'
        elif 'dashboard' in filename:
            return 'dashboard'
        elif 'calculator' in filename or 'timer' in filename or 'color' in filename:
            return 'interactive'
        elif 'weather' in filename:
            return 'weather'
        elif 'table' in filename or 'dados' in filename:
            return 'table'
        elif 'gallery' in filename:
            return 'gallery'
        elif 'video' in filename:
            return 'video'
        else:
            return 'visualization'

    def _determine_artifact_title(self, filename):
        """Determina o título do artefato baseado no nome do arquivo."""
        type_map = {
            'chart': 'Gráfico Interativo',
            'dashboard': 'Dashboard de Dados',
            'calculator': 'Calculadora',
            'timer': 'Cronômetro',
            'color': 'Seletor de Cores',
            'weather': 'Dados Meteorológicos',
            'table': 'Tabela de Dados',
            'gallery': 'Galeria de Imagens',
            'video': 'Reprodutor de Vídeo',
            'dados': 'Visualização de Dados'
        }

        for key, title in type_map.items():
            if key in filename:
                return title

        return 'Visualização Interativa'

    def _enhance_artifact_formatting(self, content):
        """Melhora a formatação de artefatos HTML."""
        # CSS melhorado para artefatos
        enhanced_styles = """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                color: #334155; 
                line-height: 1.6;
                min-height: 100vh;
                padding: 20px;
            }
            .main-container { 
                max-width: 1200px;
                margin: 0 auto;
                background: white; 
                border-radius: 16px; 
                padding: 32px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }
            h1, h2, h3 { 
                color: #1e293b; 
                margin-bottom: 20px; 
                font-weight: 600;
            }
            h1 { 
                font-size: 28px; 
                text-align: center;
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 30px;
                padding-bottom: 16px;
                border-bottom: 2px solid #e2e8f0;
            }
            h2 { font-size: 22px; }
            h3 { font-size: 18px; }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 24px 0; 
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            }
            th, td { 
                padding: 16px; 
                text-align: left; 
                border-bottom: 1px solid #f1f5f9; 
            }
            th { 
                background: linear-gradient(135deg, #f8fafc, #e2e8f0);
                font-weight: 600; 
                color: #475569;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            tr:hover { 
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
                transform: translateY(-1px);
                transition: all 0.2s;
            }
            .metric, .info-card { 
                background: linear-gradient(135deg, #6366f1, #8b5cf6); 
                color: white; 
                padding: 24px; 
                border-radius: 12px; 
                margin: 16px 0; 
                text-align: center;
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
            }
            .chart-container { 
                margin: 24px 0; 
                padding: 24px; 
                background: white; 
                border-radius: 12px; 
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                border: 1px solid #f1f5f9;
            }
            input, button, select { 
                padding: 12px 16px; 
                border: 2px solid #e2e8f0; 
                border-radius: 8px; 
                font-size: 14px; 
                margin: 8px 4px;
                transition: all 0.2s;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }
            button { 
                background: linear-gradient(135deg, #6366f1, #8b5cf6); 
                color: white; 
                border: none; 
                cursor: pointer; 
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            button:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
            }
            .data-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .data-card {
                background: white;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                transition: all 0.2s;
            }
            .data-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 24px rgba(0,0,0,0.1);
            }
            .text-center { text-align: center; }
            .text-primary { color: #6366f1; }
            .text-muted { color: #64748b; }
            .mb-4 { margin-bottom: 16px; }
            .mt-4 { margin-top: 16px; }
            .p-4 { padding: 16px; }
        </style>
        """

        # Verificar se já tem estilos e melhorar
        if '<style>' in content:
            # Substituir estilos existentes pelos melhorados
            import re
            content = re.sub(r'<style>.*?</style>', enhanced_styles, content, flags=re.DOTALL)
        else:
            # Adicionar estilos se não existirem
            if '</head>' in content:
                content = content.replace('</head>', enhanced_styles + '</head>')
            elif '<body>' in content:
                content = content.replace('<body>', '<head>' + enhanced_styles + '</head><body>')
            else:
                content = enhanced_styles + content

        # Envolver conteúdo em container se necessário
        if '<body>' in content and 'main-container' not in content:
            content = content.replace('<body>', '<body><div class="main-container">')
            content = content.replace('</body>', '</div></body>')

        return content

    def _format_response_with_artifacts(self, response, artifacts):
        """Formata a resposta incluindo os artefatos."""
        formatted_response = response

        for artifact in artifacts:
            artifact_html = f'<ARTIFACT title="{artifact["title"]}" type="{artifact["type"]}">{artifact["content"]}</ARTIFACT>'
            formatted_response += f'\n\n{artifact_html}'

        return formatted_response

    def _process_uploaded_file(self, file_content, filename, content_type):
        """Processa arquivo enviado para formato compatível com GPT com suporte universal."""
        import base64
        import mimetypes
        import json
        import csv
        import io

        # Determinar tipo de arquivo
        file_type = self._get_file_type(filename, content_type)

        processed_data = {
            'filename': filename,
            'type': file_type,
            'content_type': content_type,
            'size': len(file_content),
            'metadata': {},
            'preview': None,
            'analysis': {}
        }

        try:
            if file_type in ['text', 'code']:
                # Arquivos de texto - tentar decodificar como UTF-8
                try:
                    text_content = file_content.decode('utf-8')
                    processed_data['content'] = text_content
                    processed_data['encoding'] = 'text'
                    processed_data['preview'] = text_content[:500] + ('...' if len(text_content) > 500 else '')

                    # Análise específica por tipo
                    processed_data['analysis'] = self._analyze_text_content(text_content, file_type)

                except UnicodeDecodeError:
                    # Se não conseguir decodificar, tratar como binário
                    processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                    processed_data['encoding'] = 'base64'
                    processed_data['analysis']['encoding_issue'] = True

            elif file_type == 'data':
                # Arquivos de dados (CSV, JSON, XML, etc.)
                try:
                    text_content = file_content.decode('utf-8')
                    processed_data['content'] = text_content
                    processed_data['encoding'] = 'text'

                    # Processamento específico por tipo de dado
                    data_analysis = self._analyze_data_file(text_content, filename)
                    processed_data['analysis'] = data_analysis
                    processed_data['preview'] = data_analysis.get('preview', text_content[:500])

                except Exception as e:
                    processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                    processed_data['encoding'] = 'base64'
                    processed_data['analysis']['data_error'] = str(e)

            elif file_type == 'image':
                # Imagens - converter para base64 e extrair metadados
                processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                processed_data['encoding'] = 'base64'
                processed_data['data_url'] = f"data:{content_type};base64,{processed_data['content']}"

                # Extrair metadados de imagem se possível
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(file_content))
                    processed_data['metadata']['dimensions'] = img.size
                    processed_data['metadata']['format'] = img.format
                    processed_data['metadata']['mode'] = img.mode
                    processed_data['analysis']['image_info'] = {
                        'width': img.size[0],
                        'height': img.size[1],
                        'format': img.format,
                        'mode': img.mode
                    }
                except Exception:
                    # Se PIL não estiver disponível, continuar sem metadados
                    pass

            elif file_type == 'document':
                # Documentos - tentar extrair texto se possível
                processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                processed_data['encoding'] = 'base64'

                # Tentar extrair texto de PDFs
                if filename.lower().endswith('.pdf'):
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        text_content = ""
                        for page in pdf_reader.pages[:5]:  # Primeiras 5 páginas
                            text_content += page.extract_text() + "\n"

                        processed_data['extracted_text'] = text_content
                        processed_data['preview'] = text_content[:500]
                        processed_data['analysis']['pages'] = len(pdf_reader.pages)
                        processed_data['analysis']['text_extracted'] = len(text_content) > 0
                    except Exception:
                        processed_data['analysis']['text_extraction_failed'] = True

            elif file_type == 'pdf':
                # Arquivos PDF - base64 e análise básica
                processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                processed_data['encoding'] = 'base64'
                processed_data['analysis']['pdf_info'] = True # Indica que é um PDF

            elif file_type in ['video', 'audio']:
                # Arquivos de mídia - base64 e metadados básicos
                processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                processed_data['encoding'] = 'base64'
                processed_data['analysis']['media_type'] = file_type
                processed_data['analysis']['playable'] = content_type in [
                    'video/mp4', 'video/webm', 'audio/mp3', 'audio/wav', 'audio/ogg'
                ]

            else:
                # Outros arquivos - base64
                processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
                processed_data['encoding'] = 'base64'
                processed_data['analysis']['file_type'] = 'binary'

            # Análise universal de qualquer arquivo
            processed_data['analysis'].update({
                'file_size_mb': round(len(file_content) / (1024 * 1024), 2),
                'processable': processed_data['encoding'] == 'text',
                'has_preview': processed_data.get('preview') is not None,
                'suggested_actions': self._suggest_file_actions(file_type, processed_data)
            })

        except Exception as e:
            self._log_error_with_context(e, f"Processamento de Arquivo {filename}")
            # Fallback para base64
            processed_data['content'] = base64.b64encode(file_content).decode('utf-8')
            processed_data['encoding'] = 'base64'
            processed_data['analysis']['processing_error'] = str(e)

        return processed_data

    def _analyze_text_content(self, text, file_type):
        """Analisa conteúdo de texto para extrair informações relevantes."""
        analysis = {
            'lines': len(text.split('\n')),
            'words': len(text.split()),
            'characters': len(text),
            'empty_lines': text.count('\n\n'),
        }

        if file_type == 'code':
            # Análise específica para código
            analysis.update({
                'language': self._detect_programming_language(text),
                'has_functions': 'def ' in text or 'function ' in text or 'class ' in text,
                'has_imports': 'import ' in text or '#include' in text or 'require(' in text,
                'complexity_indicators': {
                    'loops': text.count('for ') + text.count('while '),
                    'conditionals': text.count('if ') + text.count('else'),
                    'functions': text.count('def ') + text.count('function ')
                }
            })

        return analysis

    def _analyze_data_file(self, content, filename):
        """Analisa arquivos de dados (CSV, JSON, XML, etc.)."""
        analysis = {}

        try:
            if filename.lower().endswith('.csv'):
                # Análise CSV
                csv_reader = csv.reader(io.StringIO(content))
                rows = list(csv_reader)
                if rows:
                    analysis.update({
                        'rows': len(rows),
                        'columns': len(rows[0]) if rows else 0,
                        'headers': rows[0] if rows else [],
                        'preview_rows': rows[:5],
                        'data_types': self._infer_csv_data_types(rows[1:] if len(rows) > 1 else [])
                    })

            elif filename.lower().endswith('.json'):
                # Análise JSON
                import json
                data = json.loads(content)
                analysis.update({
                    'json_type': type(data).__name__,
                    'keys': list(data.keys()) if isinstance(data, dict) else None,
                    'length': len(data) if isinstance(data, (list, dict)) else None,
                    'structure_depth': self._calculate_json_depth(data),
                    'preview': json.dumps(data, indent=2)[:500]
                })

            elif filename.lower().endswith(('.xml', '.html')):
                # Análise XML/HTML básica
                import re
                tags = re.findall(r'<(\w+)', content)
                analysis.update({
                    'total_tags': len(tags),
                    'unique_tags': len(set(tags)),
                    'most_common_tags': list(set(tags))[:10],
                    'is_html': 'html' in tags or 'HTML' in content,
                    'preview': content[:500]
                })

        except Exception as e:
            analysis['parse_error'] = str(e)
            analysis['preview'] = content[:500]

        return analysis

    def _detect_programming_language(self, code):
        """Detecta linguagem de programação baseado no conteúdo."""
        indicators = {
            'python': ['def ', 'import ', 'print(', 'if __name__', 'class '],
            'javascript': ['function ', 'var ', 'let ', 'const ', 'console.log'],
            'java': ['public class', 'public static', 'System.out', 'import java'],
            'cpp': ['#include', 'std::', 'int main(', 'cout <<', 'namespace'],
            'html': ['<html', '<head', '<body', '<!DOCTYPE', '<div'],
            'css': ['{', '}', ':', ';', '@media'],
            'sql': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE']
        }

        code_lower = code.lower()
        scores = {}

        for lang, patterns in indicators.items():
            score = sum(1 for pattern in patterns if pattern.lower() in code_lower)
            if score > 0:
                scores[lang] = score

        return max(scores.items(), key=lambda x: x[1])[0] if scores else 'unknown'

    def _infer_csv_data_types(self, rows):
        """Infere tipos de dados das colunas CSV."""
        if not rows or not rows[0]:
            return []

        data_types = []
        num_cols = len(rows[0])

        for col_idx in range(num_cols):
            col_values = [row[col_idx] for row in rows if col_idx < len(row)]
            data_type = self._infer_column_type(col_values)
            data_types.append(data_type)

        return data_types

    def _infer_column_type(self, values):
        """Infere tipo de dados de uma coluna."""
        if not values:
            return 'empty'

        # Remover valores vazios para análise
        non_empty = [v.strip() for v in values if v.strip()]
        if not non_empty:
            return 'empty'

        # Verificar se é numérico
        numeric_count = 0
        date_count = 0

        for value in non_empty[:10]:  # Analisa primeiros 10 valores
            # Teste numérico
            try:
                float(value)
                numeric_count += 1
            except ValueError:
                pass

            # Teste de data (básico)
            if any(sep in value for sep in ['-', '/', '.']):
                import re
                if re.match(r'\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}', value):
                    date_count += 1

        total = len(non_empty[:10])
        if numeric_count / total > 0.8:
            return 'numeric'
        elif date_count / total > 0.8:
            return 'date'
        else:
            return 'text'

    def _calculate_json_depth(self, obj, current_depth=0):
        """Calcula profundidade máxima de estrutura JSON."""
        if isinstance(obj, dict):
            return max([self._calculate_json_depth(v, current_depth + 1) for v in obj.values()] + [current_depth])
        elif isinstance(obj, list):
            return max([self._calculate_json_depth(item, current_depth + 1) for item in obj] + [current_depth])
        else:
            return current_depth

    def _suggest_file_actions(self, file_type, processed_data):
        """Sugere ações possíveis baseado no tipo de arquivo."""
        suggestions = []

        if file_type == 'data':
            suggestions.extend(['Analyze data', 'Create visualization', 'Generate summary'])
        elif file_type == 'code':
            suggestions.extend(['Review code', 'Explain functionality', 'Suggest improvements'])
        elif file_type == 'image':
            suggestions.extend(['Analyze image', 'Extract text (OCR)', 'Describe content'])
        elif file_type == 'document':
            suggestions.extend(['Summarize content', 'Extract key points', 'Translate'])
        elif file_type in ['video', 'audio']:
            suggestions.extend(['Extract metadata', 'Generate transcript', 'Analyze content'])
        else:
            suggestions.extend(['Analyze structure', 'Convert format', 'Extract information'])

        return suggestions

    def _get_file_type(self, filename, content_type):
        """Determina o tipo de arquivo baseado na extensão e content-type."""
        import os

        extension = os.path.splitext(filename.lower())[1]

        # Mapear extensões para tipos
        type_mapping = {
            # Texto
            '.txt': 'text',
            '.md': 'text',
            '.rtf': 'text',

            # Código
            '.py': 'code',
            '.js': 'code',
            '.html': 'code',
            '.css': 'code',
            '.json': 'code',
            '.xml': 'code',
            '.yaml': 'code',
            '.yml': 'code',
            '.sql': 'code',
            '.sh': 'code',
            '.bat': 'code',
            '.php': 'code',
            '.java': 'code',
            '.cpp': 'code',
            '.c': 'code',
            '.h': 'code',
            '.go': 'code',
            '.rs': 'code',
            '.rb': 'code',

            # Imagens
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.svg': 'image',
            '.webp': 'image',

            # Documentos
            '.pdf': 'pdf',
            '.doc': 'document',
            '.docx': 'document',
            '.xls': 'document',
            '.xlsx': 'document',
            '.ppt': 'document',
            '.pptx': 'document',

            # Arquivos
            '.zip': 'archive',
            '.rar': 'archive',
            '.tar': 'archive',
            '.gz': 'archive',

            # Áudio/Vídeo
            '.mp3': 'audio',
            '.wav': 'audio',
            '.mp4': 'video',
            '.avi': 'video',
        }

        # Verificar extensão primeiro
        if extension in type_mapping:
            return type_mapping[extension]

        # Verificar content-type como fallback
        if content_type:
            if content_type.startswith('text/'):
                return 'text'
            elif content_type.startswith('image/'):
                return 'image'
            elif content_type == 'application/pdf':
                return 'pdf'
            elif content_type.startswith('audio/'):
                return 'audio'
            elif content_type.startswith('video/'):
                return 'video'

        return 'file'  # Tipo genérico

    def _generate_fallback_response(self, user_message, uploaded_files):
        """Gera resposta inteligente quando CODER não está disponível."""
        responses = {
            'cumprimento': "Olá! Sou a CODER em modo básico. Como posso ajudá-lo?",
            'arquivo': "Recebi seu arquivo! Em modo completo, eu poderia analisá-lo em detalhes.",
            'codigo': "Posso ajudar com código! Para funcionalidades completas, configure a API OpenAI.",
            'dados': "Entendi que você quer trabalhar com dados. Configure a API para análises avançadas.",
            'ajuda': "Estou aqui para ajudar! Configure a chave da API OpenAI para ter acesso completo às minhas funcionalidades.",
            'default': "Sistema em modo básico. Para funcionalidades completas, configure a chave da API OpenAI nas variáveis de ambiente."
        }

        message_lower = user_message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'hello', 'hi']):
            return responses['cumprimento']
        elif uploaded_files:
            return responses['arquivo']
        elif any(word in message_lower for word in ['código', 'code', 'python', 'javascript']):
            return responses['codigo']
        elif any(word in message_lower for word in ['dados', 'data', 'análise', 'gráfico']):
            return responses['dados']
        elif any(word in message_lower for word in ['ajuda', 'help', 'como']):
            return responses['ajuda']
        else:
            return f"**Pergunta:** {user_message}\n\n**Resposta:** {responses['default']}\n\n**Dica:** Adicione sua chave OpenAI como variável de ambiente OPENAI_API_KEY para ativar todas as funcionalidades da CODER!"

    def _detect_agent_from_message(self, message):
        """Detecta qual agente está processando baseado na mensagem."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['web', 'pesquis', 'internet', 'buscar', 'site', 'url']):
            return 'web'
        elif any(word in message_lower for word in ['código', 'code', 'python', 'executar', 'script', 'programar']):
            return 'code'
        elif any(word in message_lower for word in ['shell', 'comando', 'terminal', 'bash', 'executar comando']):
            return 'shell'
        elif any(word in message_lower for word in ['plan', 'estratégia', 'decomp', 'etapas', 'passos']):
            return 'planner'
        elif any(word in message_lower for word in ['erro', 'error', 'corrig', 'fix', 'debug']):
            return 'error_fix'
        elif any(word in message_lower for word in ['valid', 'verific', 'test', 'chec']):
            return 'validation'
        elif any(word in message_lower for word in ['memória', 'memory', 'lembr', 'context']):
            return 'memory'
        elif any(word in message_lower for word in ['dados', 'data', 'process', 'análise']):
            return 'data_processing'
        elif any(word in message_lower for word in ['visual', 'gráfico', 'chart', 'plot']):
            return 'visualization'
        elif any(word in message_lower for word in ['orquest', 'pipeline', 'coordena']):
            return 'orchestrator'
        else:
            return 'roko'

    def _create_narrative_message(self, message, step_counter):
        """Cria mensagem narrativa mais amigável para o usuário."""
        narratives = {
            'planning': f"📋 Passo {step_counter}: Criando plano estratégico...",
            'analyzing': f"🔍 Passo {step_counter}: Analisando os dados fornecidos...",
            'executing': f"⚙️ Passo {step_counter}: Executando ações necessárias...",
            'processing': f"🔄 Passo {step_counter}: Processando informações...",
            'searching': f"🌐 Passo {step_counter}: Buscando informações na web...",
            'coding': f"💻 Passo {step_counter}: Gerando e executando código...",
            'validating': f"✅ Passo {step_counter}: Validando resultados...",
            'finalizing': f"🎯 Passo {step_counter}: Finalizando resposta..."
        }

        message_lower = message.lower()
        for key, narrative in narratives.items():
            if key in message_lower:
                return f"{narrative} {message}"

        return f"🧠 Passo {step_counter}: {message}"

    def _enhance_thinking_message(self, message, step):
        """Melhora mensagens de pensamento com mais detalhes."""
        enhanced_messages = {
            'analisando': f"🔍 Analisando sua solicitação em detalhes...",
            'criando': f"📋 Criando plano de execução estruturado...", 
            'processando': f"⚙️ Processando dados e contexto...",
            'executando': f"🚀 Executando ações necessárias...",
            'validando': f"✅ Validando resultados e qualidade...",
            'sintetizando': f"🎯 Sintetizando resposta final...",
            'buscando': f"🌐 Buscando informações relevantes...",
            'gerando': f"💻 Gerando código e solutions...",
            'verificando': f"🔎 Verificando integridade dos dados...",
            'organizando': f"📊 Organizando informações coletadas..."
        }

        message_lower = message.lower()
        for key, enhanced in enhanced_messages.items():
            if key in message_lower:
                return enhanced

        # Se não encontrou padrão específico, melhorar genericamente
        if len(message) < 50:
            return f"🧠 {message} (Etapa {step})"

        return message

    def _get_agent_emoji(self, agent_type):
        """Retorna emoji para cada tipo de agente."""
        emojis = {
            'orchestrator': '🎭',
            'web': '🌐',
            'code': '💻',
            'shell': '⚡',
            'planner': '📋',
            'roko': '🤖',
            'data_processing': '📊',
            'visualization': '📈',
            'validation': '✅',
            'error_fix': '🔧',
            'memory': '🧠'
        }
        return emojis.get(agent_type, '🔹')

    def _get_agent_name(self, agent_type):
        """Retorna nome amigável para cada tipo de agente."""
        names = {
            'orchestrator': 'Orchestrator',
            'web': 'Web Agent',
            'code': 'Code Agent',
            'shell': 'Shell Agent',
            'planner': 'Planner Agent',
            'roko': 'CODER Agent',
            'data_processing': 'Data Processing Agent',
            'visualization': 'Visualization Agent',
            'validation': 'Validation Agent',
            'error_fix': 'Error Fix Agent',
            'memory': 'Memory Agent'
        }
        return names.get(agent_type, agent_type.replace('_', ' ').title())

    def _log_error_with_context(self, error: Exception, context: str, request_id: str = None):
        """Log de erro com contexto detalhado."""
        error_info = {
            'timestamp': time.time(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'request_id': request_id
        }

        logging.error(f"🚨 ERRO DETALHADO [{context}]: {error_info}")

        # Salvar erro em arquivo para diagnóstico
        error_log_path = "ROKO/error_logs.json"
        try:
            if os.path.exists(error_log_path):
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    error_logs = json.load(f)
            else:
                error_logs = []

            error_logs.append(error_info)

            # Manter apenas os últimos 100 erros
            if len(error_logs) > 100:
                error_logs = error_logs[-100:]

            with open(error_log_path, 'w', encoding='utf-8') as f:
                json.dump(error_logs, f, indent=2, ensure_ascii=False)

        except Exception as log_error:
            logging.error(f"Erro ao salvar log de erro: {log_error}")

    def _safe_json_dumps(self, data: dict) -> str:
        """JSON dumps seguro que evita erros de encoding."""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logging.warning(f"Erro ao serializar JSON: {e}")
            # Fallback seguro
            safe_data = {
                'type': data.get('type', 'unknown'),
                'message': str(data.get('message', '')),
                'request_id': data.get('request_id', 'unknown')
            }
            return json.dumps(safe_data, ensure_ascii=False)

    def _get_tool_display_name(self, tool_name):
        """Retorna nome amigável para ferramentas."""
        names = {
            'web_search': 'Busca Web',
            'python_code': 'Executor Python',
            'shell': 'Terminal Shell',
            'planner': 'Planeador',
            'validation': 'Validador',
            'error_fix': 'Corretor de Erros'
        }
        return names.get(tool_name, tool_name.replace('_', ' ').title())

    def _summarize_result(self, result):
        """Cria resumo amigável do resultado."""
        if not result:
            return "Processo concluído"

        result_str = str(result)

        if len(result_str) <= 100:
            return result_str

        # Detectar tipo de conteúdo para resumo inteligente
        if result_str.startswith('<!DOCTYPE html') or '<html' in result_str:
            return "Visualização HTML criada com sucesso"
        elif result_str.startswith('```'):
            return "Código gerado e executado"
        elif 'error' in result_str.lower() or 'erro' in result_str.lower():
            return f"Erro detectado: {result_str[:50]}..."
        elif result_str.count('\n') > 5:
            lines = result_str.split('\n')
            return f"Dados processados ({len(lines)} linhas): {lines[0][:50]}..."
        else:
            return f"{result_str[:80]}{'...' if len(result_str) > 80 else ''}"

    def _process_response_with_artifacts(self, event):
        """Processa evento de resposta e salva artefatos no workspace do usuário."""
        if not event.get('artifacts'):
            return event

        artifacts = event['artifacts']
        processed_artifacts = []

        workspace_path, workspace_dirname = self._get_workspace_info()

        for artifact in artifacts:
            # Salvar artefato no workspace do usuário
            try:
                filename = artifact.get('filename', f"artifact_{int(time.time())}.html")

                # Criar diretório de artefatos no workspace
                artefatos_dir = os.path.join(workspace_path, 'artefatos')
                os.makedirs(artefatos_dir, exist_ok=True)

                file_path = os.path.join(artefatos_dir, filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(artifact.get('content', ''))

                # Criar referência para visualização na página de arquivos
                relative_path = os.path.relpath(file_path, workspace_path).replace('\\', '/')

                processed_artifacts.append({
                    'title': artifact.get('title', 'Artefato'),
                    'type': artifact.get('type', 'visualization'),
                    'filename': filename,
                    'workspace_path': relative_path,
                    'description': f"Artefato salvo em: {relative_path}"
                })

                logging.info(f"✅ Artefato salvo no workspace: {relative_path}")

            except Exception as e:
                logging.error(f"❌ Erro ao salvar artefato no workspace: {e}")

        # Atualizar evento com artefatos processados
        event['artifacts'] = processed_artifacts
        return event

    def _ensure_complete_artifact_content(self, content: str, artifact_type: str, title: str) -> str:
        """Garante que o conteúdo do artefato está completo e renderizável."""
        try:
            # Se já é um HTML completo, apenas melhorar
            if content.strip().startswith('<!DOCTYPE html') or '<html' in content:
                return self._enhance_artifact_formatting(content)

            # Se é apenas conteúdo HTML fragmentado, envolver em estrutura completa
            if '<div' in content or '<table' in content or '<canvas' in content:
                complete_html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: #334155; 
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }}
        .artifact-container {{ 
            max-width: 1200px;
            margin: 0 auto;
            background: white; 
            border-radius: 16px; 
            padding: 32px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }}
        h1, h2, h3 {{ 
            color: #1e293b; 
            margin-bottom: 20px; 
            font-weight: 600;
        }}
        .interactive-element {{
            margin: 16px 0;
            padding: 16px;
            border-radius: 8px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
        }}
        button {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="artifact-container">
        <h1>{title}</h1>
        {content}
    </div>
    <script>
        // Adicionar interatividade automaticamente
        document.addEventListener('DOMContentLoaded', function() {{
            // Fazer tabelas interativas
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {{
                table.style.cursor = 'pointer';
                table.addEventListener('click', function(e) {{
                    if (e.target.tagName === 'TD') {{
                        e.target.style.background = e.target.style.background === 'rgb(239, 246, 255)' ? '' : '#eff6ff';
                    }}
                }});
            }});

            // Fazer gráficos responsivos
            const canvases = document.querySelectorAll('canvas');
            canvases.forEach(canvas => {{
                canvas.style.maxWidth = '100%';
                canvas.style.height = 'auto';
            }});
        }});
    </script>
</body>
</html>"""
                return complete_html

            # Se é apenas texto, criar uma interface básica
            return self._create_text_artifact_interface(content, title)

        except Exception as e:
            logging.error(f"Erro ao processar conteúdo do artefato: {e}")
            return content

    def _validate_artifact_completeness(self, content: str) -> bool:
        """Valida se o artefato está completo e renderizável."""
        required_elements = ['<html', '<head', '<body', '</html>']
        return all(element in content for element in required_elements)

    def _contains_html_content(self, message: str) -> bool:
        """Verifica se a mensagem contém conteúdo HTML que pode ser transformado em artefato."""
        html_indicators = ['<div', '<table', '<canvas', '<svg', '<form', '<!DOCTYPE', '<html']
        return any(indicator in message for indicator in html_indicators)

    def _create_auto_artifact_from_response(self, message: str) -> dict:
        """Cria automaticamente um artefato a partir de conteúdo HTML detectado na resposta."""
        try:
            import re
            # Extrair blocos de código HTML
            html_blocks = re.findall(r'```html\n(.*?)\n```', message, re.DOTALL)
            if not html_blocks:
                # Buscar HTML inline
                html_blocks = re.findall(r'(<(?:div|table|canvas|svg|form)[^>]*>.*?</(?:div|table|canvas|svg|form)>)', message, re.DOTALL)

            if html_blocks:
                content = html_blocks[0]
                title = "Interface Interativa"

                # Detectar tipo baseado no conteúdo
                if '<table' in content:
                    artifact_type = 'table'
                    title = "Tabela Interativa"
                elif '<canvas' in content:
                    artifact_type = 'chart'
                    title = "Gráfico Interativo"
                elif '<form' in content:
                    artifact_type = 'form'
                    title = "Formulário Interativo"
                else:
                    artifact_type = 'interface'

                processed_content = self._ensure_complete_artifact_content(content, artifact_type, title)
                timestamp = int(time.time())
                filename = f"auto_artifact_{timestamp}.html"
                preview_url = f"/artifact/{filename}"

                # Salvar o artefato processado para reutilização
                self._save_artifact_file(processed_content, filename)

                return {
                    'title': title,
                    'type': artifact_type,
                    'content': processed_content,
                    'filename': filename,
                    'description': f"Artefato gerado automaticamente: {title}",
                    'summary': self._summarize_artifact_details(title, artifact_type),
                    'preview_url': preview_url,
                    'is_complete': True,
                    'render_mode': 'inline'
                }
        except Exception as e:
            logging.error(f"Erro ao criar artefato automático: {e}")
        return None

    def _create_text_artifact_interface(self, content: str, title: str) -> str:
        """Cria uma interface interativa a partir de texto simples."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .content {{
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 16px;
            color: #334155;
        }}
        .interactive-controls {{
            margin-top: 20px;
            padding: 16px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        button {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin: 4px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="content" id="content">{content}</div>
        <div class="interactive-controls">
            <button onclick="copyToClipboard()">📋 Copiar</button>
            <button onclick="toggleWrap()">🔄 Quebra de Linha</button>
            <button onclick="changeFont()">🔤 Mudar Fonte</button>
        </div>
    </div>
    <script>
        function copyToClipboard() {{
            const content = document.getElementById('content').textContent;
            navigator.clipboard.writeText(content).then(() => {{
                alert('Conteúdo copiado!');
            }});
        }}

        function toggleWrap() {{
            const content = document.getElementById('content');
            content.style.whiteSpace = content.style.whiteSpace === 'nowrap' ? 'pre-wrap' : 'nowrap';
        }}

        function changeFont() {{
            const content = document.getElementById('content');
            const fonts = ['monospace', 'serif', 'sans-serif'];
            const current = getComputedStyle(content).fontFamily;
            const currentIndex = fonts.findIndex(font => current.includes(font));
            content.style.fontFamily = fonts[(currentIndex + 1) % fonts.length];
        }}
    </script>
</body>
</html>"""

    def _save_artifact_file(self, content: str, filename: str):
        """Salva o arquivo do artefato no diretório apropriado."""
        try:
            artifacts_dir = "ARTEFATOS"
            os.makedirs(artifacts_dir, exist_ok=True)

            file_path = os.path.join(artifacts_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logging.info(f"✅ Arquivo do artefato salvo: {file_path}")
        except Exception as e:
            logging.error(f"❌ Erro ao salvar arquivo do artefato: {e}")

    def _categorize_artifact_type(self, artifact_type):
        """Categoriza tipo de artefato para o artifact manager."""
        type_mapping = {
            'chart': 'visualizations',
            'dashboard': 'dashboards', 
            'visualization': 'visualizations',
            'interactive': 'utilities',
            'table': 'visualizations',
            'weather': 'utilities',
            'gallery': 'presentations',
            'game': 'games'
        }
        return type_mapping.get(artifact_type, 'other')

    def _summarize_artifact_details(self, title: str, artifact_type: str) -> str:
        """Gera resumo curto para exibir junto do artefato."""
        readable_type = (artifact_type or 'visualização').replace('_', ' ').strip().title()
        safe_title = title or 'Visualização Interativa'
        return f"{safe_title} · {readable_type} gerado para complementar a resposta."

    def _build_file_context(self, uploaded_files):
        """Constrói contexto dos arquivos para o GPT."""
        if not uploaded_files:
            return ""

        context_parts = ["=== ARQUIVOS ANEXADOS ==="]

        for file_data in uploaded_files:
            filename = file_data.get('filename', 'arquivo_desconhecido')
            file_type = file_data.get('file_type', 'file')
            encoding = file_data.get('processed_data', {}).get('encoding', 'unknown')
            content = file_data.get('processed_data', {}).get('content', '')

            context_parts.append(f"\n📁 ARQUIVO: {filename}")
            context_parts.append(f"   Tipo: {file_type}")
            context_parts.append(f"   Codificação: {encoding}")

            if encoding == 'text' and content:
                # Para arquivos de texto, incluir o conteúdo diretamente
                context_parts.append(f"   Conteúdo:\n```\n{content[:2000]}{'...' if len(content) > 2000 else ''}\n```")
            elif encoding == 'base64' and file_type == 'image':
                # Para imagens, incluir informação sobre o base64
                context_parts.append(f"   Imagem em base64 (primeiros 100 chars): {content[:100]}...")
            elif encoding == 'base64':
                # Para outros arquivos base64, indicar apenas que está disponível
                context_parts.append(f"   Arquivo codificado em base64 disponível para análise")

        context_parts.append("\n=== FIM DOS ARQUIVOS ===\n")

        return "\n".join(context_parts)

    def _safe_project_path(self, base_path: str, relative_path: str, allow_empty: bool = False) -> str:
        """Resolve caminho de projeto garantindo que permaneça dentro do diretório base."""
        base = base_path

        if relative_path is None:
            if allow_empty:
                return base
            raise ValueError('Caminho do projeto é obrigatório')

        sanitized = relative_path.strip()
        if not sanitized:
            if allow_empty:
                return base
            raise ValueError('Caminho do projeto é obrigatório')

        normalized = os.path.normpath(sanitized)

        if normalized in ('', '.'):
            if allow_empty:
                return base
            raise ValueError('Caminho do projeto é obrigatório')

        if normalized.startswith('..') or os.path.isabs(normalized):
            raise ValueError('Caminho de projeto inválido')

        full_path = os.path.abspath(os.path.join(base, normalized))
        if not full_path.startswith(base):
            raise ValueError('Caminho de projeto inválido')

        return full_path

    def _build_project_tree(self, base_path: str, relative_path: str = '') -> list:
        """Monta árvore de diretórios e arquivos a partir de um caminho base."""
        tree = []
        try:
            entries = sorted(os.listdir(base_path))
        except FileNotFoundError:
            return tree
        except PermissionError:
            logging.warning(f"Sem permissão para ler diretório: {base_path}")
            return tree

        for entry in entries:
            full_path = os.path.join(base_path, entry)
            relative = os.path.join(relative_path, entry) if relative_path else entry
            safe_relative = relative.replace('\\', '/')

            if os.path.isdir(full_path):
                tree.append({
                    'name': entry,
                    'path': safe_relative,
                    'type': 'folder',
                    'children': self._build_project_tree(full_path, relative)
                })
            else:
                try:
                    stats = os.stat(full_path)
                    updated_at = datetime.fromtimestamp(stats.st_mtime).isoformat()
                    size = stats.st_size
                except OSError:
                    updated_at = None
                    size = None

                tree.append({
                    'name': entry,
                    'path': safe_relative,
                    'type': 'file',
                    'size': size,
                    'updated_at': updated_at
                })

        return tree

    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Executa a aplicação web."""
        logging.info("🚀 Iniciando servidor web CODER...")
        logging.info(f"CODER Pipeline disponível: {self.coder_system is not None}")

        # Tenta diferentes portas em caso de conflito, incluindo preferência por variável de ambiente
        ports_to_try = []

        preferred_ports = []
        env_port = os.environ.get('ROKO_PORT') or os.environ.get('PORT')
        if env_port:
            try:
                preferred_ports.append(int(env_port))
            except ValueError:
                logging.warning("PORT/ROKO_PORT inválida, ignorando valor não numérico: %s", env_port)

        # Usar porta fornecida como parâmetro ou padrão 5000
        preferred_ports.append(port)

        fallback_ports = [5000, 5001, 5002, 8000, 8080]

        for p in preferred_ports + fallback_ports:
            if p not in ports_to_try:
                ports_to_try.append(p)

        for p in ports_to_try:
            try:
                logging.info(f"🌐 Tentando iniciar servidor na porta {p}...")
                self.app.run(host=host, port=p, debug=debug)
                break
            except OSError as e:
                if "Address already in use" in str(e) and p != ports_to_try[-1]:
                    logging.warning(f"Porta {p} em uso, tentando próxima...")
                    continue
                else:
                    self._log_error_with_context(e, f"Execução do Servidor na Porta {p}")
                    raise

    def cleanup(self):
        """Limpa recursos da interface web."""
        try:
            if self.auth_system and hasattr(self.auth_system, 'memory'):
                self.auth_system.memory.close_connections()
            if self.coder_system and hasattr(self.coder_system, 'memory'):
                self.coder_system.memory.close_connections()
            logging.info("🧹 Recursos da interface web limpos")
        except Exception as e:
            logging.warning(f"Erro durante limpeza: {e}")

# The following lines are added to ensure that the code can be executed.
if __name__ == '__main__':
    # Configurar logging básico para ver as mensagens
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    interface = WebInterface()
    try:
        interface.run()
    finally:
        interface.cleanup()