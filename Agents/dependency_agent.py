
"""
Agente especializado em instalação automática de dependências.
"""

import subprocess
import sys
import logging
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent

class DependencyAgent(BaseAgent):
    """Agente especializado em instalação automática de dependências."""
    
    def install_package(self, package_name: str) -> Dict[str, Any]:
        """Instala um pacote Python usando pip com --break-system-packages para ambiente Nix."""
        logging.info(f"DependencyAgent a instalar pacote: {package_name}")
        try:
            # Tenta instalar com --break-system-packages para ambientes gerenciados
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", package_name], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return {"result": f"Pacote '{package_name}' instalado com sucesso!", "error": None}
            else:
                # Se falhar, sugere adicionar ao pyproject.toml
                return {"result": None, "error": f"Falha na instalação de '{package_name}': {result.stderr}\n\nDica: Adicione '{package_name}' ao pyproject.toml para instalação automática pelo Nix."}
                
        except Exception as e:
            logging.error(f"Erro no DependencyAgent: {e}")
            return {"result": None, "error": str(e)}
    
    def detect_missing_packages(self, error_message: str) -> List[str]:
        """Detecta pacotes em falta numa mensagem de erro."""
        import re
        missing_packages = []
        
        # Padrões comuns de erros de módulos em falta
        patterns = [
            r"No module named '([^']+)'",
            r"ModuleNotFoundError: No module named '([^']+)'",
            r"ImportError: No module named ([^\s]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, error_message)
            missing_packages.extend(matches)
        
        # Mapeamento de nomes comuns
        package_mapping = {
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'sklearn': 'scikit-learn',
            'newspaper': 'newspaper3k',
            'bs4': 'beautifulsoup4',
            'requests': 'requests',
            'lxml': 'lxml',
            'nltk': 'nltk'
        }
        
        # Aplicar mapeamentos
        resolved_packages = []
        for pkg in missing_packages:
            resolved_packages.append(package_mapping.get(pkg, pkg))
        
        return list(set(resolved_packages))  # Remove duplicatas
