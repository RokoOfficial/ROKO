
"""
Agente para realizar pesquisas na web com dados reais.
"""

import logging
from typing import Dict, Any
from .base_agent import BaseAgent

# Modelo de IA a ser utilizado
WEB_SEARCH_MODEL = "gpt-4o-mini-search-preview"

class WebAgent(BaseAgent):
    """Agente para realizar pesquisas na web com dados reais."""
    def execute(self, query: str) -> Dict[str, Any]:
        logging.info(f"WebAgent a executar a pesquisa: '{query}'")
        try:
            # Primeiro, fazer uma pesquisa real usando requests para obter dados atuais
            search_results = self._search_web(query)
            
            # Depois usar GPT para processar e resumir os resultados
            response = self.client.chat.completions.create(
                model=WEB_SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um agente de busca web. Analise os dados fornecidos e responda de forma concisa com a informação pedida. Use sempre os dados mais recentes fornecidos."},
                    {"role": "user", "content": f"Query: {query}\n\nDados obtidos da web:\n{search_results}\n\nPor favor, analise e resuma essas informações."}
                ]
            )
            return {"result": response.choices[0].message.content, "error": None}
        except Exception as e:
            logging.error(f"Erro no WebAgent: {e}")
            return {"result": None, "error": str(e)}
    
    def _search_web(self, query: str) -> str:
        """Realiza pesquisa web real usando várias fontes."""
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        import time
        
        results = []
        
        # Headers para parecer mais com um browser real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            # Pesquisa de notícias de cripto usando APIs públicas gratuitas
            if any(term in query.lower() for term in ['crypto', 'bitcoin', 'ethereum', 'cripto', 'moeda']):
                crypto_data = self._get_crypto_data(headers)
                if crypto_data:
                    results.append(f"Dados de Criptomoedas:\n{crypto_data}")
            
            # Pesquisa usando DuckDuckGo (não requer API key)
            duck_results = self._search_duckduckgo(query, headers)
            if duck_results:
                results.append(f"Resultados de pesquisa:\n{duck_results}")
            
            # Pesquisa em fontes de notícias públicas
            news_results = self._get_public_news(query, headers)
            if news_results:
                results.append(f"Notícias:\n{news_results}")
            
            # Se não encontrou nada específico, fazer uma pesquisa genérica
            if not results:
                generic_result = self._generic_search_fallback(query)
                if generic_result:
                    results.append(f"Informações encontradas:\n{generic_result}")
                
        except Exception as e:
            results.append(f"Erro na pesquisa web: {e}")
            logging.error(f"WebAgent search error: {e}")
        
        final_result = "\n\n".join(results) if results else "Nenhum dado específico obtido da web. Tente uma pesquisa mais específica."
        return final_result
    
    def _get_crypto_data(self, headers=None) -> str:
        """Obtém dados de cripto usando APIs públicas confiáveis."""
        try:
            import requests
            
            if headers is None:
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; ROKO/1.0)'}
            
            # CoinGecko API pública (sem necessidade de chave)
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,cardano,solana&vs_currencies=usd&include_24hr_change=true"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = []
                for coin, info in data.items():
                    price = info.get('usd', 'N/A')
                    change = info.get('usd_24h_change', 0)
                    change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
                    results.append(f"{coin.title()}: ${price} ({change_str})")
                return "\n".join(results)
        except Exception as e:
            logging.error(f"Crypto data error: {e}")
        return ""
    
    def _search_duckduckgo(self, query: str, headers=None) -> str:
        """Pesquisa usando DuckDuckGo (método simplificado)."""
        try:
            import requests
            from bs4 import BeautifulSoup
            import urllib.parse
            import time
            
            if headers is None:
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; ROKO/1.0)'}
            
            # DuckDuckGo instant answer API
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                results = []
                
                # Abstract (resumo direto)
                if data.get('Abstract'):
                    results.append(f"Resumo: {data['Abstract']}")
                
                # Definition
                if data.get('Definition'):
                    results.append(f"Definição: {data['Definition']}")
                
                # Related topics
                if data.get('RelatedTopics'):
                    topics = data['RelatedTopics'][:3]  # Primeiros 3
                    for topic in topics:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(f"Info: {topic['Text'][:200]}...")
                
                return "\n".join(results) if results else ""
                
        except Exception as e:
            logging.error(f"DuckDuckGo search error: {e}")
        return ""
    
    def _generic_search_fallback(self, query: str) -> str:
        """Fallback genérico quando outras pesquisas falham."""
        try:
            # Simulação de uma resposta básica baseada na query
            if any(term in query.lower() for term in ['erro', 'error', 'problema', 'falha']):
                return "Não foi possível encontrar informações específicas sobre esse termo. Pode ser um erro de digitação ou um termo muito específico."
            elif any(term in query.lower() for term in ['crypto', 'bitcoin', 'moeda']):
                return "Mercado de criptomoedas em constante mudança. Recomendo verificar fontes atualizadas para informações precisas."
            else:
                return f"Pesquisa realizada para: '{query}'. Sem resultados específicos encontrados nas fontes disponíveis."
        except:
            return "Informações limitadas disponíveis no momento."
    
    def _get_public_news(self, query: str, headers=None) -> str:
        """Obtém notícias de fontes públicas."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            if headers is None:
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; ROKO/1.0)'}
            
            # Pesquisa simplificada em RSS feeds públicos
            if 'crypto' in query.lower() or 'bitcoin' in query.lower():
                url = "https://cointelegraph.com/rss"
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:3]  # Primeiras 3 notícias
                    
                    news = []
                    for item in items:
                        title = item.title.text if item.title else "Sem título"
                        description = item.description.text if item.description else "Sem descrição"
                        news.append(f"• {title}: {description[:150]}...")
                    
                    return "\n".join(news)
        except Exception as e:
            logging.error(f"Public news error: {e}")
        return ""
