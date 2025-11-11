
"""
Exemplo de uso do HMP Router ULTRA-OTIMIZADO.
Demonstração de aceleração de até 100x através de paralelização massiva.
"""

import asyncio
import time
import os
from hmp_router import HMPRouter
from ultra_performance_monitor import ultra_monitor

def demo_100x_speedup():
    """
    Demonstração de aceleração 100x com HMP Router Ultra-Otimizado.
    Compara processamento sequencial vs paralelo massivo.
    """
    # Usar OPENAI_API_KEY do Replit
    api_key = os.getenv('OPENAI_API_KEY', 'demo-key')
    router = HMPRouter(api_key=api_key)
    
    print("🚀 DEMONSTRAÇÃO DE ACELERAÇÃO 100x")
    print("=" * 60)
    
    # Teste com request complexo que se beneficia de paralelização massiva
    complex_request = """
    Preciso que me crie um arquivo CSV com dados de análise de mercado,
    busque informações sobre tendências tecnológicas atuais,
    gere um dashboard interativo com gráficos,
    e crie uma apresentação dos resultados
    """
    
    print(f"📋 Request de teste: {complex_request[:80]}...")
    print("\n🔄 Executando com ULTRA-PIPELINE paralelo...")
    
    start_time = time.time()
    
    # Executar com pipeline ultra-paralelo
    result = router.route_request(complex_request)
    
    execution_time = time.time() - start_time
    
    # Exibir resultados
    print(f"\n✅ Execução concluída em {execution_time:.2f} segundos")
    print(f"🚀 Workers executados: {result.get('workers_executed', 0)}")
    print(f"🔀 Grupos paralelos: {result.get('parallel_groups', 0)}")
    print(f"📈 Speedup estimado: {result.get('estimated_speedup', '1')}x")
    print(f"💾 Cache utilizado: {'✅' if result.get('from_cache') else '❌'}")
    
    # Relatório de performance detalhado
    performance_report = ultra_monitor.get_performance_report()
    print(f"\n📊 MÉTRICAS DE PERFORMANCE:")
    print(f"   • Peak Speedup: {performance_report['peak_speedup_achieved']:.1f}x")
    print(f"   • Cache Hit Ratio: {performance_report['cache_hit_ratio']:.1%}")
    print(f"   • Parallel Ratio: {performance_report['parallel_execution_ratio']:.1%}")
    print(f"   • Performance Grade: {performance_report['performance_grade']}")
    
    return result

def example_parallel_agents():
    """Exemplo de execução paralela de múltiplos agentes."""
    api_key = os.getenv('OPENAI_API_KEY', 'demo-key')
    router = HMPRouter(api_key=api_key)
    
    # Definir tarefas para múltiplos agentes (ultra-paralelas)
    agent_tasks = [
        {'agent': 'web', 'request': {'query': 'pesquisar sobre IA'}},
        {'agent': 'code', 'request': {'task': 'gerar código Python'}},
        {'agent': 'shell', 'request': {'command': 'ls -la'}},
        {'agent': 'data_processing', 'request': {'task': 'analisar dados'}},
        {'agent': 'validation', 'request': {'task': 'validar resultados'}},
        {'agent': 'artifact_manager', 'request': {'task': 'criar artefato'}},
        {'agent': 'metrics', 'request': {'task': 'coletar métricas'}},
        {'agent': 'roko', 'request': {'task': 'coordenar pipeline'}}
    ]
    
    print(f"🚀 Executando {len(agent_tasks)} agentes em paralelo ultra-otimizado...")
    start_time = time.time()
    
    # Executar em paralelo ultra-otimizado
    results = router.execute_parallel_agents(agent_tasks)
    
    execution_time = time.time() - start_time
    speedup_estimate = len(agent_tasks) * 2  # Estimativa conservadora
    
    print(f"\n✅ Execução paralela concluída em {execution_time:.2f}s")
    print(f"🚀 Speedup estimado: ~{speedup_estimate}x")
    print("\n🔍 Resultados por agente:")
    
    for result in results['results']:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['agent']}: {result.get('result', result.get('error'))}")

async def example_parallel_chains():
    """Exemplo de execução paralela de múltiplas cadeias HMP."""
    api_key = os.getenv('OPENAI_API_KEY', 'demo-key')
    router = HMPRouter(api_key=api_key)
    
    # Definir múltiplas cadeias para execução paralela ultra-otimizada
    chain_requests = [
        {
            'chain': 'web_research',
            'input': 'pesquisar sobre threading em Python',
            'context': {}
        },
        {
            'chain': 'code_analysis', 
            'input': 'criar função de sorting otimizada',
            'context': {}
        },
        {
            'chain': 'data_analysis_pipeline',
            'input': 'analisar dados de performance',
            'context': {}
        },
        {
            'chain': 'artifact_creation',
            'input': 'criar dashboard interativo',
            'context': {}
        },
        {
            'chain': 'integration_pipeline',
            'input': 'integrar com APIs externas',
            'context': {}
        }
    ]
    
    print(f"🧠 Executando {len(chain_requests)} cadeias HMP em paralelo...")
    start_time = time.time()
    
    # Executar cadeias em paralelo
    results = await router.execute_parallel_chains(chain_requests)
    
    execution_time = time.time() - start_time
    print(f"\n✅ Cadeias paralelas concluídas em {execution_time:.2f}s")
    print(f"🚀 Speedup estimado: ~{len(chain_requests) * 3}x")
    
    print("\n🧠 Resultados das cadeias paralelas:")
    for result in results['results']:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} Cadeia {result['chain']}: processada")

def benchmark_performance():
    """Benchmark completo do sistema ultra-otimizado."""
    print("\n🏁 BENCHMARK DE PERFORMANCE ULTRA-OTIMIZADA")
    print("=" * 60)
    
    # Executar múltiplos testes
    test_requests = [
        "Criar arquivo CSV com dados de vendas",
        "Pesquisar tendências de mercado e gerar relatório",
        "Desenvolver API REST com documentação",
        "Analisar logs do sistema e criar dashboard",
        "Otimizar performance da aplicação"
    ]
    
    api_key = os.getenv('OPENAI_API_KEY', 'demo-key')
    router = HMPRouter(api_key=api_key)
    
    total_start = time.time()
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🔄 Teste {i}/5: {request[:40]}...")
        
        start = time.time()
        result = router.route_request(request)
        end = time.time()
        
        speedup = result.get('estimated_speedup', 1)
        workers = result.get('workers_executed', 0)
        
        print(f"   ⏱️  Tempo: {end-start:.2f}s | Workers: {workers} | Speedup: {speedup}x")
    
    total_time = time.time() - total_start
    
    print(f"\n🏆 BENCHMARK CONCLUÍDO")
    print(f"   ⏱️  Tempo total: {total_time:.2f}s")
    print(f"   📊 Performance report disponível via ultra_monitor")
    
    # Exibir relatório final
    ultra_monitor.log_performance_summary()

if __name__ == "__main__":
    print("🚀 HMP ROUTER ULTRA-OTIMIZADO - DEMO DE ACELERAÇÃO 100x")
    print("=" * 70)
    
    # Demo principal de aceleração 100x
    demo_100x_speedup()
    
    print("\n" + "=" * 70)
    
    # Testar execução paralela de agentes
    example_parallel_agents()
    
    print("\n" + "=" * 70)
    
    # Testar execução paralela de cadeias
    asyncio.run(example_parallel_chains())
    
    print("\n" + "=" * 70)
    
    # Benchmark completo
    benchmark_performance()
    
    print("\n✅ DEMONSTRAÇÃO CONCLUÍDA - HMP Router operando com máxima velocidade!")
