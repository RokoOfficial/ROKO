
# 🚨 Troubleshooting - Banco de Dados ROKO

## 🔍 Diagnóstico Rápido

### Script de Verificação Automática
```python
from Memory import CognitiveMemory

def quick_health_check():
    """Verificação rápida da saúde do banco."""
    memory = CognitiveMemory()
    
    # 1. Validar integridade
    health = memory.validate_system_integrity()
    print(f"🏥 Status: {health['status']}")
    
    if health['issues']:
        print("⚠️  Problemas detectados:")
        for issue in health['issues']:
            print(f"   - {issue}")
    
    # 2. Estatísticas básicas
    stats = memory.get_memory_stats()
    print(f"📊 Interações: {stats['total_interactions']}")
    print(f"🧠 Vetores FAISS: {stats['faiss_vectors']}")
    print(f"💾 Cache hit rate: {stats['cache_performance']['hit_rate']}")
    
    # 3. Verificar arquivos essenciais
    import os
    files_to_check = [
        "roko_nexus.db",
        "faiss_index.bin"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024*1024)  # MB
            print(f"✅ {file}: {size:.2f} MB")
        else:
            print(f"❌ {file}: Arquivo não encontrado")
    
    return health

# Executar verificação
quick_health_check()
```

## 🐛 Problemas Comuns e Soluções

### 1. Erro: "Database is locked"

**Sintoma**: `sqlite3.OperationalError: database is locked`

**Causas**:
- Múltiplas conexões simultâneas
- Processo anterior não fechou conexão
- Arquivo corrompido

**Soluções**:
```python
# Solução 1: Aumentar timeout
memory._get_connection().execute("PRAGMA busy_timeout = 30000;")

# Solução 2: Forçar fechamento de conexões
memory.close_connections()

# Solução 3: Verificar processos usando o arquivo
import subprocess
result = subprocess.run(['lsof', 'roko_nexus.db'], capture_output=True, text=True)
print(result.stdout)
```

### 2. Erro: "FAISS index dimension mismatch"

**Sintoma**: `RuntimeError: Wrong vector dimension`

**Causas**:
- Embedding com dimensão incorreta
- Índice corrompido
- Mudança no modelo de embedding

**Soluções**:
```python
# Verificar dimensões
embedding = get_embedding("test")
print(f"Dimensão do embedding: {embedding.shape[0]}")
print(f"Dimensão esperada: {memory.faiss_dim}")

# Reconstruir índice se necessário
if embedding.shape[0] != memory.faiss_dim:
    memory._rebuild_index()
```

### 3. Cache com Low Hit Rate (<80%)

**Sintoma**: Performance lenta, hit rate baixo

**Diagnóstico**:
```python
from Memory import ultra_cache

stats = ultra_cache.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")
print(f"L1 hits: {stats['l1_hits']}")
print(f"L2 hits: {stats['l2_hits']}")
print(f"L3 hits: {stats['l3_hits']}")
print(f"Misses: {stats['cache_misses']}")
```

**Soluções**:
```python
# Aumentar TTL
ultra_cache.ttl_hours = 48

# Aumentar tamanho do cache
ultra_cache.max_size = 20000

# Limpar cache corrompido
ultra_cache.memory_cache.clear()
ultra_cache.persistent_cache.clear()
```

### 4. Erro: "Memory usage too high"

**Sintoma**: Uso excessivo de RAM

**Diagnóstico**:
```python
import psutil
import os

# Uso de memória do processo
process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")

# Tamanho dos caches
print(f"Memory cache entries: {len(ultra_cache.memory_cache)}")
print(f"Embedding cache entries: {len(memory.embedding_cache.memory_cache)}")
```

**Soluções**:
```python
# Reduzir tamanho dos caches
ultra_cache.max_size = 5000
memory.embedding_cache.max_size = 500

# Limpeza forçada
ultra_cache._cleanup_if_needed()
memory.embedding_cache._cleanup_old_entries()

# Limpeza de interações antigas
memory.cleanup_old_memories(days_old=7, keep_important=True)
```

### 5. Erro: "Embedding cache corruption"

**Sintoma**: Erros ao carregar embeddings do cache

**Verificação**:
```python
import os
cache_dir = "embedding_cache"

# Listar arquivos corrompidos
for filename in os.listdir(cache_dir):
    if filename.endswith('.npy'):
        file_path = os.path.join(cache_dir, filename)
        try:
            embedding = np.load(file_path)
            if embedding.shape[0] != 3072:
                print(f"Arquivo corrompido: {filename} (dim: {embedding.shape[0]})")
        except Exception as e:
            print(f"Erro ao carregar {filename}: {e}")
```

**Soluções**:
```python
# Limpar cache de embeddings
memory.embedding_cache.clear()

# Remover arquivos corrompidos
import os
import glob

corrupted_files = glob.glob("embedding_cache/*.npy")
for file in corrupted_files:
    try:
        embedding = np.load(file)
        if embedding.shape[0] != 3072:
            os.remove(file)
            print(f"Removido: {file}")
    except:
        os.remove(file)
        print(f"Removido (corrompido): {file}")
```

## 🔧 Ferramentas de Manutenção

### Script de Reparação Automática
```python
def auto_repair_database():
    """Repara problemas comuns automaticamente."""
    from Memory import CognitiveMemory
    import os
    
    print("🔧 Iniciando reparação automática...")
    
    try:
        memory = CognitiveMemory()
        
        # 1. Verificar integridade
        health = memory.validate_system_integrity()
        
        if health['status'] == 'error':
            print("❌ Erro crítico detectado")
            return False
        
        # 2. Sincronizar índice FAISS
        if 'Embeddings não indexados' in str(health['issues']):
            print("🔄 Sincronizando índice FAISS...")
            memory._sync_index()
        
        # 3. Reconstruir índice se necessário
        if memory.index.ntotal == 0 and health['total_interactions'] > 0:
            print("🏗️  Reconstruindo índice FAISS...")
            memory._rebuild_index()
        
        # 4. Limpar caches
        print("🧹 Limpando caches...")
        memory.embedding_cache._cleanup_old_entries()
        
        # 5. Otimizar SQLite
        conn = memory._get_connection()
        print("⚡ Otimizando SQLite...")
        conn.execute("VACUUM;")
        conn.execute("ANALYZE;")
        conn.commit()
        
        print("✅ Reparação concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante reparação: {e}")
        return False

# Executar reparação
auto_repair_database()
```

### Backup e Restauração
```python
def backup_database():
    """Cria backup completo do banco."""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup/roko_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup SQLite
    shutil.copy2("roko_nexus.db", f"{backup_dir}/roko_nexus.db")
    
    # Backup FAISS
    if os.path.exists("faiss_index.bin"):
        shutil.copy2("faiss_index.bin", f"{backup_dir}/faiss_index.bin")
    
    # Backup cache de embeddings
    if os.path.exists("embedding_cache"):
        shutil.copytree("embedding_cache", f"{backup_dir}/embedding_cache")
    
    print(f"✅ Backup criado em: {backup_dir}")
    return backup_dir

def restore_database(backup_dir):
    """Restaura banco de backup."""
    import shutil
    
    # Parar sistema
    memory.close_connections()
    
    # Restaurar arquivos
    shutil.copy2(f"{backup_dir}/roko_nexus.db", "roko_nexus.db")
    
    if os.path.exists(f"{backup_dir}/faiss_index.bin"):
        shutil.copy2(f"{backup_dir}/faiss_index.bin", "faiss_index.bin")
    
    if os.path.exists(f"{backup_dir}/embedding_cache"):
        if os.path.exists("embedding_cache"):
            shutil.rmtree("embedding_cache")
        shutil.copytree(f"{backup_dir}/embedding_cache", "embedding_cache")
    
    print("✅ Banco restaurado com sucesso!")
```

## 📊 Monitoramento Contínuo

### Script de Monitoramento
```python
def monitor_database():
    """Monitora saúde do banco em tempo real."""
    import time
    import json
    
    while True:
        try:
            memory = CognitiveMemory()
            stats = memory.get_memory_stats()
            
            # Métricas importantes
            metrics = {
                "timestamp": time.time(),
                "total_interactions": stats['total_interactions'],
                "faiss_vectors": stats['faiss_vectors'],
                "cache_hit_rate": float(stats['cache_performance']['hit_rate'].rstrip('%')),
                "memory_cache_size": len(memory.embedding_cache.memory_cache)
            }
            
            # Alertas
            if metrics['cache_hit_rate'] < 70:
                print(f"⚠️  Cache hit rate baixo: {metrics['cache_hit_rate']:.1f}%")
            
            if metrics['total_interactions'] != metrics['faiss_vectors']:
                print(f"⚠️  Dessincronia: {metrics['total_interactions']} vs {metrics['faiss_vectors']}")
            
            # Log métricas
            with open("logs/db_metrics.jsonl", "a") as f:
                f.write(json.dumps(metrics) + "\n")
            
            time.sleep(60)  # Verificar a cada minuto
            
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            time.sleep(10)
```

## 📞 Suporte e Escalação

### Logs de Debug
```python
# Ativar logging detalhado
import logging
logging.basicConfig(level=logging.DEBUG)

# Logger específico para memória
memory_logger = logging.getLogger('CognitiveMemory')
memory_logger.setLevel(logging.DEBUG)

# Logger para cache
cache_logger = logging.getLogger('UltraCacheSystem')
cache_logger.setLevel(logging.DEBUG)
```

### Coleta de Informações para Suporte
```python
def collect_debug_info():
    """Coleta informações para suporte técnico."""
    import platform
    import sys
    
    info = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "memory_available": psutil.virtual_memory().available // 1024 // 1024  # MB
        },
        "roko": {
            "database_health": memory.validate_system_integrity(),
            "memory_stats": memory.get_memory_stats(),
            "cache_stats": ultra_cache.get_cache_stats()
        },
        "files": {
            "db_size": os.path.getsize("roko_nexus.db") if os.path.exists("roko_nexus.db") else 0,
            "faiss_size": os.path.getsize("faiss_index.bin") if os.path.exists("faiss_index.bin") else 0
        }
    }
    
    # Salvar relatório
    with open("debug_report.json", "w") as f:
        json.dump(info, f, indent=2)
    
    print("📋 Relatório de debug salvo em: debug_report.json")
    return info
```

---

**🆘 Emergência**: Se o sistema estiver completamente inacessível, delete os arquivos `roko_nexus.db` e `faiss_index.bin` para reinicialização completa (perda de dados).
