
"""
Utilitários para o sistema de memória ROKO.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MemoryUtils:
    """
    Classe utilitária para operações de memória.
    """
    
    @staticmethod
    def format_interaction_for_display(interaction: Dict[str, Any]) -> str:
        """Formata uma interação para exibição."""
        timestamp = interaction.get('timestamp', 'N/A')
        user_prompt = interaction.get('user_prompt', 'N/A')
        agent_response = interaction.get('agent_response', 'N/A')
        
        return f"""
📅 {timestamp}
👤 Usuário: {user_prompt}
🤖 ROKO: {agent_response[:200]}{'...' if len(agent_response) > 200 else ''}
"""

    @staticmethod
    def calculate_importance_score(user_prompt: str, agent_response: str) -> int:
        """Calcula um score de importância baseado no conteúdo."""
        score = 5  # Score base
        
        # Palavras-chave que aumentam importância
        important_keywords = [
            'erro', 'problema', 'bug', 'falha', 'exception',
            'código', 'function', 'class', 'import', 'def',
            'install', 'pip', 'npm', 'git', 'deploy',
            'api', 'database', 'sql', 'query'
        ]
        
        text_combined = (user_prompt + ' ' + agent_response).lower()
        
        for keyword in important_keywords:
            if keyword in text_combined:
                score += 1
                
        # Limita entre 1 e 10
        return min(max(score, 1), 10)
    
    @staticmethod
    def extract_tags_from_content(user_prompt: str, agent_response: str) -> List[str]:
        """Extrai tags automaticamente do conteúdo."""
        tags = []
        text_combined = (user_prompt + ' ' + agent_response).lower()
        
        # Mapeamento de palavras-chave para tags
        keyword_to_tag = {
            'python': 'python',
            'javascript': 'javascript',
            'html': 'html',
            'css': 'css',
            'react': 'react',
            'flask': 'flask',
            'django': 'django',
            'api': 'api',
            'database': 'database',
            'sql': 'sql',
            'git': 'git',
            'debug': 'debug',
            'erro': 'error',
            'web': 'web',
            'scraping': 'web-scraping',
            'file': 'file-system',
            'install': 'installation'
        }
        
        for keyword, tag in keyword_to_tag.items():
            if keyword in text_combined:
                tags.append(tag)
                
        return list(set(tags))  # Remove duplicatas
    
    @staticmethod
    def categorize_interaction(user_prompt: str, agent_response: str) -> str:
        """Categoriza automaticamente uma interação."""
        text_combined = (user_prompt + ' ' + agent_response).lower()
        
        # Categorias e suas palavras-chave
        categories = {
            'Programação Python': ['python', 'pip', 'def', 'class', 'import'],
            'Web Development': ['html', 'css', 'javascript', 'react', 'flask', 'django'],
            'API & Web Services': ['api', 'request', 'json', 'http', 'rest'],
            'Base de Dados': ['database', 'sql', 'query', 'table', 'sqlite'],
            'Sistema de Ficheiros': ['file', 'directory', 'path', 'folder'],
            'Instalação & Config': ['install', 'pip', 'npm', 'config', 'setup'],
            'Debug & Erros': ['erro', 'error', 'debug', 'exception', 'bug'],
            'Web Scraping': ['scraping', 'requests', 'beautifulsoup', 'selenium'],
            'Conversação': ['olá', 'obrigado', 'ajuda', 'como está']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_combined for keyword in keywords):
                return category
                
        return 'Geral'
    
    @staticmethod
    def get_memory_insights(memory_stats: Dict[str, Any]) -> str:
        """Gera insights sobre as estatísticas de memória."""
        total = memory_stats.get('total_interactions', 0)
        vectors = memory_stats.get('faiss_vectors', 0)
        
        insights = f"""
📊 **Relatório de Memória ROKO**

📈 **Estatísticas Gerais:**
- Total de interações: {total}
- Vetores FAISS: {vectors}
- Eficiência do índice: {(vectors/total*100):.1f}% das interações indexadas

🏷️ **Categorias Mais Usadas:**
"""
        
        for cat_info in memory_stats.get('top_categories', []):
            insights += f"   • {cat_info['category']}: {cat_info['count']} interações\n"
            
        insights += "\n📝 **Distribuição por Tipo:**\n"
        for type_info in memory_stats.get('types_distribution', []):
            insights += f"   • {type_info['type']}: {type_info['count']} interações\n"
            
        return insights
