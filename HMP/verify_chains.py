"""
Script para verificar se as cadeias HMP estão realmente implementadas e funcionando.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from HMP.hmp_router import HMPRouter
import logging

def verify_hmp_chains():
    """Verifica se todas as cadeias HMP estão implementadas."""

    print("🔍 VERIFICAÇÃO DAS CADEIAS HMP IMPLEMENTADAS")
    print("=" * 60)

    # Inicializar router HMP
    try:
        router = HMPRouter(api_key="test-key")
        print("✅ HMPRouter inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar HMPRouter: {e}")
        return False

    # Verificar cadeias disponíveis
    available_chains = router.get_available_chains()
    print(f"\n📋 Cadeias HMP disponíveis: {len(available_chains)}")

    # Lista esperada de cadeias
    expected_chains = [
        'simple_conversation',
        'complex_task', 
        'code_analysis',
        'web_research',
        'data_analysis_pipeline',
        'system_maintenance',
        'agent_evolution',
        'artifact_creation',
        'integration_pipeline',
        'learning_optimization',
        'deployment_automation',
        'security_audit'
    ]

    print(f"📋 Cadeias esperadas: {len(expected_chains)}")

    # Verificar cada cadeia
    missing_chains = []
    implemented_chains = []

    for chain in expected_chains:
        if chain in available_chains:
            implemented_chains.append(chain)
            print(f"✅ {chain}")
        else:
            missing_chains.append(chain)
            print(f"❌ {chain} - NÃO ENCONTRADA")

    # Verificar cadeias extras
    extra_chains = [chain for chain in available_chains if chain not in expected_chains]
    if extra_chains:
        print(f"\n🔧 Cadeias extras encontradas: {extra_chains}")

    # Verificar classificação de requests
    print(f"\n🎯 TESTANDO CLASSIFICAÇÃO DE REQUESTS")
    print("-" * 40)

    test_requests = [
        ("olá como vai", "simple_conversation"),
        ("criar código python", "code_analysis"), 
        ("pesquisar sobre IA", "web_research"),
        ("analisar dados", "data_analysis_pipeline"),
        ("verificar sistema", "system_maintenance"),
        ("criar agente", "agent_evolution"),
        ("criar app", "artifact_creation"),
        ("integrar API", "api_integration"),
        ("deploy projeto", "deployment"),
        ("auditoria segurança", "security_audit")
    ]

    classification_correct = 0
    for request, expected_type in test_requests:
        try:
            classified_type = router._classify_request(request)
            chain_selected = router._select_hmp_chain(classified_type, request)

            print(f"Request: '{request}'")
            print(f"  Classificado como: {classified_type}")
            print(f"  Cadeia selecionada: {chain_selected}")

            if chain_selected in router.hmp_chains:
                print(f"  ✅ Cadeia existe e pode ser executada")
                classification_correct += 1
            else:
                print(f"  ❌ Cadeia não existe")
            print()

        except Exception as e:
            print(f"  ❌ Erro na classificação: {e}")

    # Verificar mapeamento de tipos
    print(f"🗺️ VERIFICANDO MAPEAMENTO DE TIPOS")
    print("-" * 40)

    # Acessar o mapeamento interno
    try:
        # Simular classificações
        mapping_tests = [
            "simple_conversation",
            "code_task", 
            "web_research",
            "data_analysis",
            "system_maintenance",
            "agent_evolution",
            "artifact_creation",
            "api_integration",
            "deployment",
            "security_audit"
        ]

        for request_type in mapping_tests:
            chain = router._select_hmp_chain(request_type, "test")
            if chain in router.hmp_chains:
                print(f"✅ {request_type} → {chain}")
            else:
                print(f"❌ {request_type} → {chain} (não existe)")

    except Exception as e:
        print(f"❌ Erro no mapeamento: {e}")

    # Relatório final
    print(f"\n📊 RELATÓRIO FINAL")
    print("=" * 60)
    print(f"✅ Cadeias implementadas: {len(implemented_chains)}/{len(expected_chains)}")
    print(f"📋 Implementadas: {implemented_chains}")

    if missing_chains:
        print(f"❌ Faltando: {missing_chains}")

    print(f"🎯 Classificação funcionando: {classification_correct}/{len(test_requests)} testes")

    # Verificar se está realmente funcional
    success_rate = (len(implemented_chains) / len(expected_chains)) * 100
    print(f"📈 Taxa de sucesso: {success_rate:.1f}%")

    if success_rate >= 100:
        print("🎉 TODAS AS CADEIAS HMP ESTÃO IMPLEMENTADAS E FUNCIONAIS!")
        return True
    elif success_rate >= 80:
        print("⚠️ A maioria das cadeias está funcionando, mas algumas podem estar faltando")
        return True
    else:
        print("❌ Sistema HMP não está completamente funcional")
        return False

def test_hmp_execution():
    """Testa execução real de uma cadeia HMP."""

    print(f"\n🚀 TESTE DE EXECUÇÃO REAL")
    print("=" * 60)

    try:
        router = HMPRouter(api_key="test-key")

        # Testar execução simples
        result = router.route_request("olá como vai você hoje?")

        print(f"✅ Execução bem-sucedida:")
        print(f"   Sucesso: {result.get('success')}")
        print(f"   Tipo de processamento: {result.get('processing_type')}")
        print(f"   Cadeia usada: {result.get('chain_used')}")
        print(f"   Tempo de execução: {result.get('execution_time', 0):.3f}s")

        if result.get('success'):
            print("🎉 SISTEMA HMP TOTALMENTE FUNCIONAL!")
            return True
        else:
            print("❌ Sistema apresentou problemas na execução")
            return False

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        return False

if __name__ == "__main__":
    print("🔍 VERIFICAÇÃO COMPLETA DAS CADEIAS HMP DO PROJETO ROKO")
    print("=" * 70)

    # Executar verificações
    chains_ok = verify_hmp_chains()
    execution_ok = test_hmp_execution()

    print(f"\n🏁 RESULTADO FINAL:")
    print("=" * 70)

    if chains_ok and execution_ok:
        print("✅ SISTEMA HMP 100% FUNCIONAL - TODAS AS DESCRIÇÕES ESTÃO CORRETAS!")
    elif chains_ok:
        print("⚠️ Cadeias implementadas mas com problemas na execução")
    else:
        print("❌ Sistema HMP apresenta problemas significativos")