
"""
Interface AGI - Interface otimizada para interações profissionais com sistema AGI.
"""

import logging
from flask import Flask, request, jsonify, render_template
from Pipeline.agi_pipeline import AGIPipeline
from Pipeline.exceptions import APIKeyNotFoundError

class AGIInterface:
    """
    Interface web profissional para sistema AGI.
    Foco em UX limpa, responsiva e eficiente.
    """
    
    def __init__(self):
        self.app = Flask(__name__, template_folder='../templates')
        self.pipeline = None
        self._setup_routes()
        self._initialize_system()
    
    def _initialize_system(self):
        """Inicializa o sistema AGI."""
        try:
            self.pipeline = AGIPipeline()
            logging.info("✅ Sistema AGI inicializado")
        except APIKeyNotFoundError as e:
            logging.error(f"❌ Erro de configuração: {e}")
            self.pipeline = None
        except Exception as e:
            logging.error(f"❌ Erro na inicialização: {e}")
            self.pipeline = None
    
    def _setup_routes(self):
        """Configura rotas da API."""
        
        @self.app.route('/')
        def index():
            return render_template('agi_interface.html')
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            if not self.pipeline:
                return jsonify({
                    'error': 'Sistema não inicializado',
                    'response': 'Sistema AGI em modo de recuperação. Verifique a configuração.'
                }), 503
            
            try:
                data = request.get_json()
                user_input = data.get('message', '').strip()
                
                if not user_input:
                    return jsonify({
                        'error': 'Mensagem vazia',
                        'response': 'Por favor, forneça uma mensagem válida.'
                    }), 400
                
                # Processar com AGI Pipeline
                result = self.pipeline.process_request(user_input)
                
                return jsonify({
                    'response': result.get('final_response', ''),
                    'success': result.get('success', True),
                    'analysis': result.get('analysis', {}),
                    'execution_log': result.get('execution_log', [])
                })
                
            except Exception as e:
                logging.error(f"Erro no chat endpoint: {e}")
                return jsonify({
                    'error': 'Erro interno',
                    'response': 'Erro no processamento. Sistema em auto-recuperação.'
                }), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def status():
            if not self.pipeline:
                return jsonify({'status': 'offline'})
            
            try:
                status_info = self.pipeline.get_system_status()
                return jsonify(status_info)
            except Exception as e:
                return jsonify({'status': 'error', 'error': str(e)})
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Inicia o servidor."""
        logging.info(f"🚀 Iniciando AGI Interface em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
