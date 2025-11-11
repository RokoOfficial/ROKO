
#!/usr/bin/env python3
"""
Script de limpeza e manutenção do MOMO
"""

import os
import shutil
import glob
import sqlite3
from pathlib import Path

def cleanup_logs():
    """Limpa logs antigos."""
    log_files = glob.glob("../logs/*.log")
    for log_file in log_files:
        if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            print(f"🧹 Limpando log grande: {log_file}")
            with open(log_file, 'w') as f:
                f.write("")

def cleanup_cache():
    """Limpa cache de embeddings antigos."""
    cache_dir = Path("../embedding_cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.cache"))
        if len(cache_files) > 100:
            print(f"🧹 Limpando {len(cache_files) - 50} arquivos de cache antigos")
            for cache_file in sorted(cache_files)[:-50]:
                cache_file.unlink()

def cleanup_artifacts():
    """Limpa artefatos antigos."""
    artifacts_dir = Path("../ARTEFATOS")
    if artifacts_dir.exists():
        html_files = list(artifacts_dir.glob("*.html"))
        if len(html_files) > 20:
            print(f"🧹 Limpando {len(html_files) - 10} artefatos antigos")
            for artifact in sorted(html_files, key=os.path.getmtime)[:-10]:
                artifact.unlink()

def optimize_database():
    """Otimiza a base de dados SQLite."""
    try:
        conn = sqlite3.connect("../roko_nexus.db")
        print("🔧 Otimizando base de dados...")
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        conn.close()
        print("✅ Base de dados otimizada")
    except Exception as e:
        print(f"⚠️ Erro ao otimizar base de dados: {e}")

def main():
    """Executa limpeza completa."""
    print("🚀 Iniciando limpeza e manutenção do MOMO...")
    
    cleanup_logs()
    cleanup_cache()
    cleanup_artifacts()
    optimize_database()
    
    print("✅ Limpeza concluída com sucesso!")

if __name__ == "__main__":
    main()
