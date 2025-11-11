"""
Agente que analisa passos falhados e propõe correções.
"""

import logging
import json
from typing import Dict, List
from .base_agent import BaseAgent

# Modelo de IA a ser utilizado
FIXER_MODEL = "gpt-4o-mini"

class ErrorFixAgent(BaseAgent):
    """
    Agente que analisa um passo falhado e o seu erro, e propõe uma
    versão corrigida do comando ou código.
    """
    def fix_step(self, failed_step: Dict[str, str], error_message: str) -> Dict[str, str]:
        logging.info(f"ErrorFixAgent a tentar corrigir o passo: {failed_step}")
        system_prompt = """
        Você é um agente de correção de erros especializado. Sua tarefa é analisar um passo de um plano que falhou e propor uma correção.
        Responda APENAS com um objeto JSON contendo a chave "corrected_query" com o novo comando/código.

        TIPOS DE ERRO E CORREÇÕES:

        1. SyntaxError - invalid syntax:
           - Corrigir sintaxe Python inválida
           - Adicionar aspas em strings
           - Corrigir parênteses e vírgulas

        2. SyntaxError - invalid decimal literal:
           - Converter vírgulas para pontos em números
           - Corrigir formatação de números

        3. TypeError - comparação entre tipos incompatíveis:
           - Validar e converter tipos antes de comparações
           - Usar funções de tratamento de dados seguras

        4. ModuleNotFoundError:
           - Adicionar código de instalação automática
           - Usar imports condicionais com try/except
           - Sugerir alternativas com bibliotecas padrão

        SEMPRE gere código Python válido e testável.
        """
        user_content = f"""
        O seguinte passo falhou:
        - Ferramenta: {failed_step['tool']}
        - Query Original: {failed_step['query']}

        A mensagem de erro foi:
        {error_message}

        CORREÇÕES ESPECÍFICAS NECESSÁRIAS:

        Se for SyntaxError:
        - Corrigir sintaxe Python
        - Remover caracteres especiais problemáticos
        - Garantir strings válidas

        Se for comparação de tipos:
        - Adicionar validação de tipos
        - Converter strings numéricas para float
        - Usar funções de comparação seguras

        Se for sobre dados de web search:
        - Processar dados de texto para estruturas válidas
        - Extrair informações numéricas corretamente
        - Criar código que funciona com dados reais

        Por favor, forneça a query corrigida num objeto JSON com a chave "corrected_query".
        IMPORTANTE: O código deve ser 100% válido em Python e executável.
        """
        try:
            response = self.client.chat.completions.create(
                model=FIXER_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            correction_data = json.loads(response.choices[0].message.content)
            corrected_query = correction_data.get("corrected_query")

            if not corrected_query:
                raise ValueError("A resposta de correção não continha a chave 'corrected_query'.")

            logging.info(f"Correção proposta: {corrected_query}")
            return {"tool": failed_step["tool"], "query": corrected_query}
        except Exception as e:
            logging.error(f"Erro no ErrorFixAgent: {e}")
            return failed_step

    def deep_analysis_and_fix(self, failed_step: Dict[str, str], error_history: List[str]) -> Dict[str, str]:
        """
        Realiza uma análise profunda dos múltiplos erros e propõe uma estratégia de correção refinada.
        """
        logging.info(f"ErrorFixAgent a realizar análise profunda para o passo: {failed_step}")

        system_prompt = """
        Você é um agente especialista em análise profunda de erros. Após múltiplas tentativas falhadas,
        sua tarefa é analisar o padrão de erros e propor uma estratégia de correção completamente refinada.

        PADRÕES DE ERRO COMUNS E CORREÇÕES:

        1. SyntaxError com decimais:
           - Converter vírgulas para pontos em números
           - Remover caracteres especiais de strings
           - Usar dados estruturados ao invés de texto bruto

        2. TypeError de comparação:
           - Validar tipos antes de comparações
           - Converter strings numéricas para float
           - Usar funções de comparação seguras

        3. Problemas de encoding:
           - Remover caracteres unicode problemáticos
           - Usar encoding UTF-8 consistente
           - Substituir caracteres especiais

        Responda APENAS com um objeto JSON contendo a chave "corrected_query" com a nova estratégia.
        """

        # Processar histórico de erros de forma mais robusta
        safe_error_history = []
        if error_history and isinstance(error_history, list):
            for i, error in enumerate(error_history[-5:]):  # Pegar apenas os últimos 5 erros
                if isinstance(error, str):
                    safe_error_history.append(f"Erro {i+1}: {error[:200]}...")  # Limitar tamanho
                elif isinstance(error, Exception):
                    safe_error_history.append(f"Erro {i+1}: {type(error).__name__}: {str(error)[:200]}...")
                else:
                    safe_error_history.append(f"Erro {i+1}: {str(error)[:200]}...")
        else:
            safe_error_history.append("Erro: Histórico de erros indisponível")

        error_summary = "\n".join(safe_error_history)

        user_content = f"""
        ANÁLISE PROFUNDA REQUERIDA - Múltiplas falhas detectadas:

        Passo Original:
        - Ferramenta: {failed_step['tool']}
        - Query Original: {failed_step['query']}

        Histórico de Erros:
        {error_summary}

        Com base no padrão de erros, proponha uma abordagem completamente nova e refinada.
        Considere estratégias alternativas, simplificação da tarefa ou mudança de ferramenta se necessário.

        Responda com JSON com a chave corrected_query contendo a nova estratégia.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            correction_data = json.loads(response.choices[0].message.content)
            corrected_query = correction_data.get("corrected_query")

            if not corrected_query:
                raise ValueError("A resposta de análise profunda não continha a chave 'corrected_query'.")

            logging.info(f"🔬 Análise profunda concluída. Nova estratégia: {corrected_query[:100]}...")
            return {"tool": failed_step["tool"], "query": corrected_query}

        except Exception as e:
            logging.error(f"Erro na análise profunda do ErrorFixAgent: {e}")
            # Fallback para correção simples se a análise profunda falhar
            return self.fix_step(failed_step, error_history[-1] if error_history else "Erro desconhecido")