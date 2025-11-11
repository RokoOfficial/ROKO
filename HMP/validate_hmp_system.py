
"""
Script de validação completa do sistema HMP
Verifica se todas as conexões estão funcionando corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from HMP.chain_validator import HMPChainValidator

def main():
    """Executa validação completa do sistema HMP."""
    
    print("🔍 VALIDAÇÃO COMPLETA DO SISTEMA HMP")
    print("=" * 50)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Inicializar validador
    validator = HMPChainValidator()
    
    # 1. Validar todas as conexões
    print("\n1️⃣ Validando conexões do sistema...")
    results = validator.validate_all_connections("test-api-key")
    
    print(f"Status: {results['status']}")
    print(f"Router inicializado: {'✅' if results['router_initialized'] else '❌'}")
    print(f"Cadeia de debugging disponível: {'✅' if results['debugging_chain_available'] else '❌'}")
    print(f"Funções registradas: {len(results['functions_registered'])}")
    print(f"Funções ausentes: {len(results['missing_functions'])}")
    print(f"Artefatos forçados para ARTEFATOS: {'✅' if results['artifacts_forced_to_artefatos'] else '❌'}")
    print(f"Total de cadeias: {results['total_chains']}")
    
    # 2. Testar cadeia de debugging
    print("\n2️⃣ Testando cadeia de debugging...")
    debug_test = validator.test_debugging_chain("test-api-key")
    
    print(f"Teste passou: {'✅' if debug_test['test_passed'] else '❌'}")
    if debug_test['test_passed']:
        print(f"Classificado como: {debug_test['classified_as']}")
        print(f"Execução bem-sucedida: {'✅' if debug_test['execution_result'] else '❌'}")
        print(f"Cadeia usada: {debug_test['chain_used']}")
    
    # 3. Verificar pasta ARTEFATOS
    print("\n3️⃣ Verificando pasta ARTEFATOS...")
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ARTEFATOS")
    
    if os.path.exists(artifacts_dir):
        artifacts_count = len([f for f in os.listdir(artifacts_dir) if f.endswith(('.html', '.json', '.txt'))])
        print(f"✅ Pasta ARTEFATOS existe com {artifacts_count} arquivos")
    else:
        print("❌ Pasta ARTEFATOS não encontrada")
    
    # 4. Status final
    print("\n" + "=" * 50)
    if results['status'] == 'all_connected' and debug_test['test_passed']:
        print("✅ SISTEMA HMP TOTALMENTE FUNCIONAL")
        print("🚀 Todas as cadeias estão conectadas e operacionais")
        print("📁 Artefatos serão salvos em ARTEFATOS/")
    else:
        print("⚠️ SISTEMA HMP COM PROBLEMAS PARCIAIS")
        print("🔧 Executando em modo básico")
        
        if results.get('missing_functions'):
            print(f"🔗 Funções ausentes: {', '.join(results['missing_functions'])}")

if __name__ == "__main__":
    main()
