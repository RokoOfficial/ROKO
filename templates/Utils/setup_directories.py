
#!/usr/bin/env python3
"""
Script para configurar diretórios necessários do MOMO.
"""

import os
import logging

def setup_roko_directories():
    """Cria todos os diretórios necessários para o MOMO funcionar."""
    
    directories = [
        'logs',
        'ARTEFATOS', 
        'Memory',
        'embedding_cache',
        'backup'
    ]
    
    base_path = os.path.dirname(os.path.dirname(__file__))  # MOMO root
    
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Diretório criado/verificado: {dir_path}")
        except Exception as e:
            print(f"❌ Erro ao criar diretório {dir_path}: {e}")
    
    # Criar arquivo .gitkeep nos diretórios vazios
    gitkeep_dirs = ['logs', 'embedding_cache']
    for directory in gitkeep_dirs:
        gitkeep_path = os.path.join(base_path, directory, '.gitkeep')
        try:
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write('# Mantém o diretório no controle de versão\n')
                print(f"✅ .gitkeep criado: {gitkeep_path}")
        except Exception as e:
            print(f"❌ Erro ao criar .gitkeep em {gitkeep_path}: {e}")

if __name__ == "__main__":
    print("🔧 Configurando diretórios do MOMO...")
    setup_roko_directories()
    print("✅ Configuração concluída!")
