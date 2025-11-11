"""
Agente base com cliente OpenAI.
"""

import openai
import os
import logging

class BaseAgent:
    """Agente base com cliente OpenAI."""
    def __init__(self, api_key: str = None):
        # Usar API key do Replit se não fornecida
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"
            self.has_api = True
        else:
            logging.warning("⚠️ OpenAI API key não disponível - funcionando em modo limitado")
            self.client = None
            self.model = None
            self.has_api = False