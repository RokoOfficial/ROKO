"""
Agente que cria planos de ação estruturados em formato JSON.
"""

import logging
import json
import re
from typing import List, Dict
from .base_agent import BaseAgent

# Modelo de IA a ser utilizado  
PLANNER_MODEL = "gpt-4o-mini"

class PlannerAgent(BaseAgent):
    """
    Agente que recebe um pedido do utilizador e o decompõe num plano de
    ação estruturado em formato JSON, incluindo capacidades de visualização.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.user_workspace_path = None
    
    def set_workspace_context(self, workspace_path: str):
        """Define o contexto do workspace para planeamento correto."""
        self.user_workspace_path = workspace_path
        logging.info(f"📁 PlannerAgent workspace configurado: {workspace_path}")
    
    def create_plan(self, user_prompt: str, context: str, workspace_path: str = None) -> List[Dict[str, str]]:
        logging.info("PlannerAgent a criar um plano...")
        
        # Configurar workspace se fornecido
        if workspace_path:
            self.set_workspace_context(workspace_path)
        
        # Detectar se é uma query de workspace
        workspace_keywords = ['listar', 'liste', 'projetos', 'arquivos', 'mostrar', 'ver', 'explorar', 'navegar', 'buscar', 'encontrar', 'ls', 'dir']
        is_workspace_query = any(keyword in user_prompt.lower() for keyword in workspace_keywords)
        
        if is_workspace_query and self.user_workspace_path:
            # Para queries de workspace, criar plano simples com caminho correto
            workspace_plan = [{
                "tool": "shell",
                "query": f"ls -la '{self.user_workspace_path}' && find '{self.user_workspace_path}' -type f -name '*.py' -o -name '*.js' -o -name '*.html' -o -name '*.md' | head -20"
            }]
            logging.info(f"📁 Plano de workspace criado para: {self.user_workspace_path}")
            return workspace_plan
        
        system_prompt = """
        Você é um agente de planeamento avançado com capacidades de visualização. Sua tarefa é decompor um pedido complexo num plano de ação passo a passo.
        Responda APENAS com um bloco de código JSON contendo uma chave "plan" com uma lista de ações.
        Cada ação na lista deve ter "tool" e "query".
        As ferramentas disponíveis são: "web_search", "shell", "python_code".
        Se o pedido for simples e não necessitar de ferramentas, retorne um JSON com uma lista vazia: {"plan": []}.

        IMPORTANTE: Para dados que precisam de visualização (clima, gráficos, tabelas, estatísticas), use "python_code" e inclua chamadas para as funções de visualização disponíveis:
        - create_weather_visualization(data) - para dados climáticos
        - create_data_table(data) - para tabelas interativas
        - create_line_chart(data, labels) - para gráficos de linha
        - create_bar_chart(data, labels) - para gráficos de barras
        - create_pie_chart(data, labels) - para gráficos de pizza
        - create_dashboard(data) - para dashboards completos

        Exemplos:

        Pedido sobre clima:
        ```json
        {
            "plan": [
                {"tool": "web_search", "query": "clima atual Lisboa temperatura hoje"},
                {"tool": "python_code", "query": "# Dados do clima anterior: previous_step_result\\nclima_data = {'city': 'Lisboa', 'temperature': 22, 'humidity': 65, 'description': previous_step_result}\\ncreate_weather_visualization(clima_data)\\nprint('Visualização do clima criada com sucesso!')"}
            ]
        }
        ```

        Pedido sobre dados/gráficos:
        ```json
        {
            "plan": [
                {"tool": "python_code", "query": "# Criar dados de exemplo\\ndados = [10, 25, 15, 30, 20, 35]\\nlabels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']\\ncreate_line_chart(dados, labels)\\ncreate_bar_chart(dados, labels)\\nprint('Gráficos criados com sucesso!')"}
            ]
        }
        ```

        Pedido sobre análise de arquivos:
        ```json
        {
            "plan": [
                {"tool": "shell", "query": "find . -name '*.py'"},
                {"tool": "python_code", "query": "import os\\nfiles = previous_step_result.split('\\n')\\nresultados = []\\nfor f in files:\\n  if f:\\n    with open(f, 'r') as reader:\\n      linhas = len(reader.readlines())\\n      resultados.append({'arquivo': f, 'linhas': linhas})\\n      print(f'{f}: {linhas} linhas')\\ncreate_data_table(resultados)\\nprint('Tabela de arquivos criada!')"}
            ]
        }
        ```
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto de conversas anteriores:\n{context}\n\nPedido Atual:\n{user_prompt}"}
                ]
            )
            response_text = response.choices[0].message.content

            # CORREÇÃO: Lógica robusta para extrair JSON da resposta do modelo
            match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # Se não encontrar um bloco de código, tenta encontrar um JSON na resposta
                match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    raise json.JSONDecodeError("Nenhum JSON encontrado na resposta.", response_text, 0)

            plan_data = json.loads(json_str)
            plan_list = plan_data.get("plan", [])

            if not isinstance(plan_list, list):
                raise ValueError("O JSON foi analisado, mas a chave 'plan' não contém uma lista.")

            logging.info(f"Plano criado com {len(plan_list)} passos.")
            return plan_list

        except json.JSONDecodeError:
            logging.error(f"Erro de análise JSON no PlannerAgent. Resposta do modelo não era JSON válido: '{response_text}'")
            return []
        except Exception as e:
            logging.error(f"Erro inesperado no PlannerAgent: {e}. Resposta do modelo: '{response_text}'")
            return []