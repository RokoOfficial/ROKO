
#!/usr/bin/env python3
"""
Sistema Automático de Instalação de Dependências para MOMO
Detecta e instala automaticamente dependências em falta
"""

import subprocess
import sys
import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Set

class AutoDependencyInstaller:
    """Instalador automático de dependências."""
    
    def __init__(self):
        self.common_mappings = {
            'cv2': 'opencv-python',
            'PIL': 'Pillow', 
            'sklearn': 'scikit-learn',
            'newspaper': 'newspaper3k',
            'bs4': 'beautifulsoup4',
            'serial': 'pyserial',
            'yaml': 'PyYAML',
            'dotenv': 'python-dotenv',
            'streamlit': 'streamlit',
            'plotly': 'plotly',
            'dash': 'dash',
            'psutil': 'psutil',
            'matplotlib': 'matplotlib',
            'seaborn': 'seaborn',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'scipy': 'scipy',
            'requests': 'requests',
            'flask': 'flask',
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'sqlalchemy': 'sqlalchemy',
            'pymongo': 'pymongo',
            'redis': 'redis',
            'celery': 'celery',
            'pydantic': 'pydantic',
            'click': 'click',
            'typer': 'typer',
            'rich': 'rich',
            'tqdm': 'tqdm',
            'pytest': 'pytest',
            'black': 'black',
            'flake8': 'flake8',
            'mypy': 'mypy'
        }
        
    def scan_imports_in_directory(self, directory: str = ".") -> Set[str]:
        """Escaneia todos os arquivos Python em busca de imports."""
        imports = set()
        
        for py_file in Path(directory).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Padrões de import
                import_patterns = [
                    r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    imports.update(matches)
                    
            except Exception as e:
                logging.warning(f"Erro ao ler {py_file}: {e}")
                
        return imports
    
    def get_missing_packages(self, imports: Set[str]) -> List[str]:
        """Identifica pacotes em falta."""
        missing = []
        
        # Módulos built-in e padrões do Python
        builtin_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'random', 're', 'math', 'logging', 
            'traceback', 'io', 'pathlib', 'subprocess', 'threading', 'multiprocessing', 
            'collections', 'itertools', 'functools', 'typing', 'urllib', 'http', 'ssl',
            'socket', 'email', 'html', 'xml', 'sqlite3', 'csv', 'configparser', 'hashlib',
            'base64', 'uuid', 'tempfile', 'shutil', 'glob', 'fnmatch', 'linecache', 'pickle',
            'copyreg', 'copy', 'pprint', 'reprlib', 'enum', 'numbers', 'cmath', 'decimal',
            'fractions', 'statistics', 'array', 'weakref', 'types', 'gc', 'inspect', 'site'
        }
        
        # Padrões de nomes que são claramente funções/classes internas
        internal_patterns = {
            # Constantes e tipos internos
            'DEVNULL', 'Q', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'NULL',
            # Tipos de dados específicos
            'Int64Dtype', 'TensorDataset', 'ArffSparseDataType',
            # Funções com padrões específicos
            'ParserCreate', 'ImageUriValidator', 'BaseConnectionHandler',
            # Nomes muito genéricos
            'root', 'Assistant', 'EvolutionPipeline',
            # Funções com underscore
            '_TYPE_BODY_POSITION', '_check_for_pyarrow', '_raise_warning'
        }
        
        for module in imports:
            # Pular módulos built-in
            if module in builtin_modules:
                continue
                
            # Pular padrões internos conhecidos
            if module in internal_patterns:
                continue
                
            # Pular imports que começam com underscore (funções/classes internas)
            if module.startswith('_'):
                continue
                
            # Pular imports que são claramente funções ou classes (CamelCase)
            if module[0].isupper() and any(c.isupper() for c in module[1:]):
                continue
                
            # Pular imports muito curtos (provavelmente variáveis)
            if len(module) < 3:
                continue
                
            # Pular nomes que contêm números ou caracteres especiais suspeitos
            if any(c.isdigit() for c in module) or any(c in module for c in ['_SEMVER', '_POSITION']):
                continue
                
            try:
                __import__(module)
            except ImportError:
                # Mapear para nome de pacote real
                package_name = self.common_mappings.get(module, module)
                if package_name not in missing and package_name.isalpha():
                    missing.append(package_name)
                    
        return missing
    
    def install_packages(self, packages: List[str]) -> Dict[str, bool]:
        """Instala lista de pacotes."""
        results = {}
        
        for package in packages:
            print(f"📦 Instalando {package}...")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    print(f"✅ {package} instalado com sucesso!")
                    results[package] = True
                else:
                    print(f"❌ Falha ao instalar {package}: {result.stderr}")
                    results[package] = False
                    
            except Exception as e:
                print(f"❌ Erro ao instalar {package}: {e}")
                results[package] = False
                
        return results
    
    def auto_install_dependencies(self) -> Dict[str, any]:
        """Processo completo de instalação automática."""
        print("🔍 Escaneando dependências...")
        
        # Escanear imports
        imports = self.scan_imports_in_directory()
        print(f"📋 Encontrados {len(imports)} imports únicos")
        
        # Identificar pacotes em falta
        missing = self.get_missing_packages(imports)
        print(f"❓ {len(missing)} pacotes potencialmente em falta")
        
        if not missing:
            print("✅ Todas as dependências parecem estar instaladas!")
            return {"status": "success", "installed": [], "failed": []}
        
        print(f"🚀 Instalando {len(missing)} pacotes...")
        results = self.install_packages(missing)
        
        installed = [pkg for pkg, success in results.items() if success]
        failed = [pkg for pkg, success in results.items() if not success]
        
        print(f"\n📊 Relatório de Instalação:")
        print(f"✅ Instalados: {len(installed)}")
        print(f"❌ Falharam: {len(failed)}")
        
        if installed:
            print("✅ Pacotes instalados:", ", ".join(installed))
        if failed:
            print("❌ Pacotes com falha:", ", ".join(failed))
            
        return {
            "status": "success" if len(failed) == 0 else "partial",
            "installed": installed,
            "failed": failed,
            "total_scanned": len(imports),
            "total_missing": len(missing)
        }

def main():
    """Função principal para uso standalone."""
    print("🤖 MOMO - Instalador Automático de Dependências")
    print("=" * 50)
    
    installer = AutoDependencyInstaller()
    result = installer.auto_install_dependencies()
    
    if result["status"] == "success":
        print("\n🎉 Todas as dependências foram instaladas com sucesso!")
        return 0
    elif result["status"] == "partial":
        print(f"\n⚠️ Instalação parcial: {len(result['failed'])} pacotes falharam")
        return 1
    else:
        print("\n❌ Falha na instalação de dependências")
        return 1

if __name__ == "__main__":
    sys.exit(main())
