
"""
Sistema de Diagnóstico Completo para MOMO
Identifica e resolve erros automaticamente
"""

import logging
import traceback
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import sys

class MOMODiagnostics:
    """Sistema de diagnóstico avançado para MOMO."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors_found = []
        self.warnings = []
        self.fixes_applied = []
        self.base_path = os.path.dirname(os.path.dirname(__file__))  # MOMO root
        
    def run_complete_diagnosis(self) -> Dict[str, Any]:
        """Executa diagnóstico completo do sistema."""
        print("🔍 Iniciando diagnóstico completo do sistema MOMO...")
        
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "checking",
            "errors": [],
            "warnings": [],
            "fixes_applied": [],
            "recommendations": []
        }
        
        # Verificar estrutura de arquivos
        self._check_file_structure(diagnosis)
        
        # Verificar dependências
        self._check_dependencies(diagnosis)
        
        # Verificar base de dados
        self._check_database(diagnosis)
        
        # Verificar configurações
        self._check_configuration(diagnosis)
        
        # Verificar logs de erro
        self._check_error_logs(diagnosis)
        
        # Verificar integridade do código
        self._check_code_integrity(diagnosis)
        
        # Verificar sistemas ultra-otimizados
        self._check_ultra_systems(diagnosis)
        
        # Aplicar correções automáticas
        self._apply_automatic_fixes(diagnosis)
        
        # Determinar status final
        if not diagnosis["errors"]:
            diagnosis["system_status"] = "healthy"
        elif len(diagnosis["errors"]) <= 2:
            diagnosis["system_status"] = "warning"
        else:
            diagnosis["system_status"] = "critical"
            
        self._generate_report(diagnosis)
        return diagnosis
    
    def _check_file_structure(self, diagnosis: Dict):
        """Verifica integridade da estrutura de arquivos."""
        print("📁 Verificando estrutura de arquivos...")
        
        required_files = [
            "Pipeline/__init__.py",
            "Pipeline/roko_pipeline.py",
            "Agents/__init__.py", 
            "Interface/web_interface.py",
            "Memory/__init__.py",
            "app.py",
            "templates/index.html"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(self.base_path, file_path)
            if not os.path.exists(full_path):
                diagnosis["errors"].append({
                    "type": "missing_file",
                    "file": file_path,
                    "severity": "high",
                    "message": f"Arquivo obrigatório não encontrado: {file_path}"
                })
            else:
                # Verificar se arquivo não está vazio
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) == 0:
                            diagnosis["warnings"].append({
                                "type": "empty_file",
                                "file": file_path,
                                "message": f"Arquivo está vazio: {file_path}"
                            })
                except Exception as e:
                    diagnosis["errors"].append({
                        "type": "file_read_error",
                        "file": file_path,
                        "error": str(e)
                    })
    
    def _check_dependencies(self, diagnosis: Dict):
        """Verifica dependências Python."""
        print("📦 Verificando dependências...")
        
        required_packages = [
            "flask", "openai", "requests", "beautifulsoup4", 
            "sqlite3", "json", "logging", "faiss-cpu"
        ]
        
        for package in required_packages:
            try:
                if package == "sqlite3":
                    import sqlite3
                elif package == "json":
                    import json
                elif package == "logging":
                    import logging
                else:
                    __import__(package.replace("-", "_"))
                    
            except ImportError as e:
                diagnosis["errors"].append({
                    "type": "missing_dependency",
                    "package": package,
                    "error": str(e),
                    "fix": f"pip install {package}"
                })
    
    def _check_database(self, diagnosis: Dict):
        """Verifica integridade da base de dados."""
        print("🗄️ Verificando base de dados...")
        
        db_path = os.path.join(self.base_path, "roko_nexus.db")
        if not os.path.exists(db_path):
            diagnosis["errors"].append({
                "type": "missing_database",
                "message": "Base de dados não encontrada",
                "auto_fix": True
            })
            return
            
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar tabelas essenciais
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["interactions", "agent_registry", "memory_vectors"]
                for table in required_tables:
                    if table not in tables:
                        diagnosis["warnings"].append({
                            "type": "missing_table",
                            "table": table,
                            "auto_fix": True
                        })
                        
        except Exception as e:
            diagnosis["errors"].append({
                "type": "database_error",
                "error": str(e)
            })
    
    def _check_configuration(self, diagnosis: Dict):
        """Verifica configurações do sistema."""
        print("⚙️ Verificando configurações...")
        
        # Verificar variáveis de ambiente
        if not os.getenv("OPENAI_API_KEY"):
            diagnosis["warnings"].append({
                "type": "missing_api_key",
                "message": "Chave OpenAI não configurada. Sistema funcionará em modo limitado."
            })
        
        # Verificar permissões de escrita
        test_dirs = [
            os.path.join(self.base_path, "ARTEFATOS"),
            os.path.join(self.base_path, "embedding_cache")
        ]
        for dir_path in test_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    diagnosis["fixes_applied"].append(f"Criado diretório: {dir_path}")
                except Exception as e:
                    diagnosis["errors"].append({
                        "type": "permission_error",
                        "directory": dir_path,
                        "error": str(e)
                    })
    
    def _check_error_logs(self, diagnosis: Dict):
        """Analisa logs de erro recentes."""
        print("📋 Analisando logs de erro...")
        
        # Verificar se há erros de sintaxe nos arquivos Python
        python_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Verificar sintaxe compilando o código
                compile(content, py_file, 'exec')
                
            except SyntaxError as e:
                diagnosis["errors"].append({
                    "type": "syntax_error",
                    "file": py_file,
                    "line": e.lineno,
                    "error": str(e),
                    "severity": "critical"
                })
            except Exception as e:
                diagnosis["warnings"].append({
                    "type": "file_issue",
                    "file": py_file,
                    "error": str(e)
                })
    
    def _check_code_integrity(self, diagnosis: Dict):
        """Verifica integridade do código."""
        print("🔬 Verificando integridade do código...")
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                # Verificar f-strings aninhadas específicamente
                                if "f'" in line and line.count("f'") > 1:
                                    diagnosis["warnings"].append({
                                        "type": "nested_f_string",
                                        "file": file_path,
                                        "line": i,
                                        "content": line.strip()
                                    })
                    except Exception as e:
                        diagnosis["warnings"].append({
                            "type": "code_analysis_error",
                            "file": file_path,
                            "error": str(e)
                        })
    
    def _check_ultra_systems(self, diagnosis: Dict):
        """Verifica sistemas ultra-otimizados."""
        print("🚀 Verificando sistemas ultra-otimizados...")
        
        ultra_systems = [
            "Memory/ultra_cache_system.py",
            "HMP/intelligent_load_balancer.py",
            "HMP/ultra_performance_monitor.py"
        ]
        
        for system_path in ultra_systems:
            full_path = os.path.join(self.base_path, system_path)
            if not os.path.exists(full_path):
                diagnosis["warnings"].append({
                    "type": "missing_ultra_system",
                    "system": system_path,
                    "message": f"Sistema ultra-otimizado não encontrado: {system_path}",
                    "impact": "Performance reduzida"
                })
    
    def _apply_automatic_fixes(self, diagnosis: Dict):
        """Aplica correções automáticas."""
        print("🔧 Aplicando correções automáticas...")
        
        for error in diagnosis["errors"]:
            if error.get("auto_fix"):
                if error["type"] == "missing_database":
                    self._create_database()
                    diagnosis["fixes_applied"].append("Base de dados criada automaticamente")
        
        for warning in diagnosis["warnings"]:
            if warning.get("auto_fix"):
                if warning["type"] == "missing_table":
                    self._create_missing_table(warning["table"])
                    diagnosis["fixes_applied"].append(f"Tabela {warning['table']} criada")
    
    def _create_database(self):
        """Cria base de dados com esquema básico."""
        db_path = os.path.join(self.base_path, "roko_nexus.db")
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Criar tabela de interações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_prompt TEXT,
                    agent_response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    interaction_type TEXT DEFAULT 'standard'
                )
            """)
            
            # Criar tabela de registro de agentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT UNIQUE,
                    agent_type TEXT,
                    capabilities TEXT,
                    performance_score REAL DEFAULT 100.0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _create_missing_table(self, table_name: str):
        """Cria tabela em falta."""
        db_path = os.path.join(self.base_path, "roko_nexus.db")
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            if table_name == "memory_vectors":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_vectors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT,
                        vector_data BLOB,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            conn.commit()
    
    def _generate_report(self, diagnosis: Dict):
        """Gera relatório de diagnóstico."""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE DIAGNÓSTICO MOMO")
        print("="*60)
        
        print(f"⏰ Timestamp: {diagnosis['timestamp']}")
        print(f"🏥 Status do Sistema: {diagnosis['system_status'].upper()}")
        
        if diagnosis["errors"]:
            print(f"\n❌ ERROS ENCONTRADOS ({len(diagnosis['errors'])}):")
            for i, error in enumerate(diagnosis["errors"], 1):
                print(f"  {i}. [{error['type']}] {error.get('message', error.get('error', 'Erro desconhecido'))}")
                if 'file' in error:
                    print(f"     📁 Arquivo: {error['file']}")
                if 'line' in error:
                    print(f"     📍 Linha: {error['line']}")
        else:
            print("\n✅ Nenhum erro crítico encontrado!")
        
        if diagnosis["warnings"]:
            print(f"\n⚠️ AVISOS ({len(diagnosis['warnings'])}):")
            for i, warning in enumerate(diagnosis["warnings"], 1):
                print(f"  {i}. [{warning['type']}] {warning.get('message', warning.get('error', 'Aviso'))}")
        
        if diagnosis["fixes_applied"]:
            print(f"\n🔧 CORREÇÕES APLICADAS ({len(diagnosis['fixes_applied'])}):")
            for i, fix in enumerate(diagnosis["fixes_applied"], 1):
                print(f"  {i}. {fix}")
        
        # Salvar relatório em arquivo
        report_path = os.path.join(self.base_path, f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo em: {report_path}")
        print("="*60)

def main():
    """Função principal de diagnóstico."""
    diagnostics = MOMODiagnostics()
    result = diagnostics.run_complete_diagnosis()
    
    # Retornar código de saída baseado no status
    if result["system_status"] == "critical":
        sys.exit(1)
    elif result["system_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
