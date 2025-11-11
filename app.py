#!/usr/bin/env python3
"""
CODER - Sistema de IA Autônoma
Ponto de entrada único simplificado
"""

import logging
import os
import sys
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import WSGIRequestHandler

# Custom request handler para reduzir logs de HEAD
class QuietRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        # Não logar chamadas HEAD para /api para reduzir spam
        if self.command == 'HEAD' and '/api' in self.path:
            return
        super().log_request(code, size)


def setup_environment():
    """Configura ambiente e diretórios necessários."""
    # Adicionar diretório principal ao Python path
    roko_dir = Path(__file__).parent
    if str(roko_dir) not in sys.path:
        sys.path.insert(0, str(roko_dir))

    # Usar setup_directories das Utils
    try:
        from Utils import setup_roko_directories
        setup_roko_directories()
    except ImportError:
        # Fallback para criação manual
        dirs = ['logs', 'ARTEFATOS', 'embedding_cache', 'downloads', 'Utils', 'AutoFlux']
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/coder.log', mode='a')
        ]
    )

def main():
    """Função principal com modo de operação."""
    setup_environment()

    # Exibir informações do sistema
    print("🤖 CODER - Sistema de IA Autônoma v2.0 (Otimizada)")
    print("=" * 50)

    # Verificar configuração da API
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        print("✅ OpenAI API Key configurada")
    else:
        print("⚠️  OpenAI API Key não encontrada - sistema funcionará em modo limitado")
        print("💡 Configure OPENAI_API_KEY nos Secrets do Replit")

    # Verificar argumentos para modo CLI
    if len(sys.argv) > 1 and sys.argv[1] in ['cli', '--cli', '-c']:
        print("\n🚀 Iniciando CODER em modo CLI...")
        try:
            from Interface.cli_interface import CODERInterface
            interface = CODERInterface()
            interface.run()
        except KeyboardInterrupt:
            print("\n👋 CODER CLI encerrado.")
        except ImportError as e:
            print(f"❌ Erro ao importar interface CLI: {e}")
            print("💡 Certifique-se de que todas as dependências estão instaladas.")
            return 1
    else:
        # Modo Web (padrão)
        print("\n🌐 Iniciando CODER em modo Web...")
        print("🔗 Interface disponível em: http://0.0.0.0:5000")
        try:
            from Interface.web_interface import WebInterface
            web_interface = WebInterface()
            web_interface.app.run(host='0.0.0.0', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n👋 Servidor CODER encerrado.")
        except ImportError as e:
            print(f"❌ Erro ao importar interface web: {e}")
            print("💡 Instale as dependências: pip install flask rich")
            return 1
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            logging.error(f"Erro inesperado na inicialização: {e}")
            return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
