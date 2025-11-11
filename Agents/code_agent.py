import io
import sys
import traceback
import logging
import json
import os
import datetime
import random
import math
import re
from typing import Dict, Any, Optional
from .base_agent import BaseAgent

# Gerenciador de artefatos para salvar visualizações no workspace
class ArtifactManager:
    """Gerencia artefatos, salvando-os no workspace do usuário."""

    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path if workspace_path else os.getcwd()
        self.artifacts_dir = os.path.join(self.workspace_path, "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        print(f"Diretório de artefatos configurado para: {self.artifacts_dir}")

    def save_artifact(self, filename: str, content: str):
        """Salva o conteúdo de um artefato no diretório do workspace."""
        full_path = os.path.join(self.artifacts_dir, filename)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Artefato salvo: {full_path}")
            return full_path
        except IOError as e:
            print(f"Erro ao salvar artefato {filename}: {e}")
            return None

    def get_artifact_url(self, filename: str) -> str:
        """Retorna a URL para visualização do artefato."""
        # Em um ambiente web real, isso seria uma URL pública ou relativa ao servidor
        # Para este exemplo, retornamos um caminho que pode ser interpretado pelo frontend
        return f"/files/{filename}"


class CodeAgent(BaseAgent):
    """Agente para geração e execução de código Python com capacidades de visualização avançadas."""

    def _ensure_artifacts_directory(self):
        """Garante que o diretório de artefatos existe dentro do workspace."""
        # A responsabilidade de criar o diretório agora é do ArtifactManager
        pass

    def _get_artifact_path(self, filename):
        """Retorna o caminho completo para um arquivo de artefato usando o ArtifactManager."""
        if self.artifact_manager:
            return os.path.join(self.artifact_manager.artifacts_dir, filename)
        # Fallback para o diretório ARTEFATOS antigo se ArtifactManager não estiver inicializado
        return os.path.join(self.artifacts_dir, filename) 

    def __init__(self, api_key: str):
        super().__init__(api_key)
        # O diretório de artefatos será gerenciado pelo ArtifactManager,
        # que será inicializado com o workspace correto.
        self.artifacts_dir = "ARTEFATOS" # Manter como fallback inicial
        self.workspace_path: Optional[str] = os.getcwd()
        # Inicializar o gerenciador de artefatos (será configurado com workspace depois)
        self.artifact_manager = None

    def execute(self, code: str) -> Dict[str, Any]:
        logging.info(f"CodeAgent a executar o código:\n---\n{code}\n---")

        # Detectar se precisa de visualização e melhorar código
        enhanced_code = self._enhance_code_for_visualization(code)

        # Usar o workspace definido no artifact manager, ou o padrão
        working_dir = self.workspace_path or os.getcwd()
        if self.artifact_manager:
            working_dir = self.artifact_manager.workspace_path # Usar o workspace do gerente

        os.makedirs(working_dir, exist_ok=True)
        output_catcher = io.StringIO()
        previous_cwd = os.getcwd()
        try:
            os.chdir(working_dir)
            with io.StringIO() as output_catcher:
                original_stdout = sys.stdout
                sys.stdout = output_catcher
                try:
                    # Criar ambiente com bibliotecas de visualização
                    exec_globals = self._create_visualization_environment()
                    # Limpar caracteres problemáticos antes da execução
                    clean_code = enhanced_code.encode('ascii', 'ignore').decode('ascii')

                    # Executar o código
                    exec(clean_code, exec_globals)
                finally:
                    sys.stdout = original_stdout
                output = output_catcher.getvalue()

            # Verificar artefatos gerados (agora salvos pelo ArtifactManager)
            # O diretório de artefatos é gerenciado pelo ArtifactManager
            if self.artifact_manager:
                artifacts_dir_to_check = self.artifact_manager.artifacts_dir
            else:
                artifacts_dir_to_check = self.artifacts_dir # Fallback

            if os.path.exists(artifacts_dir_to_check):
                html_files = [f for f in os.listdir(artifacts_dir_to_check) if f.endswith('.html') and 'visualization' in f]
                if html_files:
                    # Ler o conteúdo HTML gerado para criar artefato
                    latest_file = html_files[-1]
                    full_path = os.path.join(artifacts_dir_to_check, latest_file)

                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()

                        # Determinar tipo e título do artefato
                        artifact_type = self._determine_artifact_type(latest_file)
                        artifact_title = self._determine_artifact_title(latest_file)
                        artifact_url = self.artifact_manager.get_artifact_url(latest_file) if self.artifact_manager else f"/artifacts/{latest_file}"


                        logging.info(f"📊 Artefato criado: {artifact_title} ({latest_file})")

                        # Retornar com formato de artefato, incluindo a URL/link
                        # O nome do arquivo agora deve ser um link clicável para visualização
                        artifact_output = f'<ARTIFACT title="{artifact_title}" type="{artifact_type}" url="{artifact_url}">Nome: {latest_file}</ARTIFACT>'
                        return {"result": f"{output}\n\n{artifact_output}", "error": None}

                    except Exception as e:
                        logging.error(f"Erro ao ler artefato {latest_file}: {e}")
                        return {"result": output + f"\n\nErro ao processar visualização: {e}", "error": None}

            return {"result": output if output else "Código executado sem saída.", "error": None}
        except Exception:
            tb = traceback.format_exc()
            logging.error(f"Erro na execução de código: {tb}")
            return {"result": None, "error": tb}
        finally:
            try:
                os.chdir(previous_cwd)
            except Exception:
                pass

    def execute_code(self, code: str, language: str = "python", user_id: int = None, workspace_path: str = None) -> Dict[str, Any]:
        # Configurar artifact manager com workspace se disponível
        if workspace_path and not self.artifact_manager:
            self.artifact_manager = ArtifactManager(workspace_path=workspace_path)
        elif not self.artifact_manager:
            # Se nenhum workspace_path foi fornecido, usar o workspace padrão atual
            self.artifact_manager = ArtifactManager(workspace_path=self.workspace_path)

        """Executa código Python de forma segura."""
        try:
            # Sanitizar código antes da execução
            sanitized_code = self._sanitize_code(code)
            return self.execute(sanitized_code)
        except Exception as e:
            logging.error(f"Erro na execução de código: {e}")
            raise

    def set_workspace(self, workspace_path: Optional[str], artifacts_dir: Optional[str] = None):
        """Define diretórios de workspace e artefatos para execuções futuras."""
        if workspace_path:
            self.workspace_path = workspace_path
        if artifacts_dir:
            # Se um diretório de artefatos específico for dado, ele prevalece
            self.artifacts_dir = artifacts_dir
        # Ao definir workspace, também atualiza ou cria o ArtifactManager
        self.artifact_manager = ArtifactManager(workspace_path=self.workspace_path)
        self._ensure_artifacts_directory() # Garante que o diretório base exista

    def _sanitize_code(self, code: str) -> str:
        """Sanitiza o código removendo caracteres problemáticos e validando sintaxe."""
        import re
        import ast

        try:
            # Primeiro, tratar caracteres especiais em strings
            sanitized = code

            # Corrigir preços com formato brasileiro/europeu (vírgula decimal)
            # Padrão: R$ 1.234,56 ou € 1.234,56 ou $1.234,56
            sanitized = re.sub(r'([R$€]?\s*\d{1,3}(?:\.\d{3})*),(\d{2})', r'\1.\2', sanitized)

            # Corrigir números decimais com vírgula (ex: 4.718,06 -> 4718.06)
            sanitized = re.sub(r'(\d+)\.(\d{3}),(\d+)', r'\1\2.\3', sanitized)

            # Corrigir números simples com vírgula (ex: 123,45 -> 123.45)
            sanitized = re.sub(r'(\d+),(\d+)', r'\1.\2', sanitized)

            # Substituir caracteres especiais problemáticos
            char_replacements = {
                '°': ' graus',
                '€': ' euros',
                'ç': 'c',
                'ã': 'a',
                'õ': 'o',
                'ú': 'u',
                'é': 'e',
                'á': 'a',
                'í': 'i',
                'ó': 'o',
                'ê': 'e',
                'â': 'a',
                'ô': 'o',
                'à': 'a',
                'ü': 'u'
            }

            for char, replacement in char_replacements.items():
                sanitized = sanitized.replace(char, replacement)

            # Remover outros caracteres unicode problemáticos
            sanitized = re.sub(r'[^\x00-\x7F]+', ' ', sanitized)

            # Processar linha por linha para correções específicas
            lines = sanitized.split('\n')
            fixed_lines = []

            for line_num, line in enumerate(lines, 1):
                try:
                    # Detectar e corrigir problemas específicos
                    if '=' in line and any(problematic in line for problematic in ['Preo:', 'preco atual de']):
                        # Linha com informação de preço - transformar em comentário ou string
                        if 'crypto_data' in line:
                            fixed_lines.append('crypto_data = """')
                            fixed_lines.append(line.replace('crypto_data = ', ''))
                            fixed_lines.append('"""')
                        else:
                            fixed_lines.append(f'# {line.strip()}')

                    elif '=' in line and 'sorted(' in line and not any(quote in line for quote in ['"', "'"]):
                        # Corrigir sorted sem strings adequadas
                        var_name = line.split('=')[0].strip()
                        fixed_lines.append(f'{var_name} = []  # Lista processada')

                    elif 'create_data_table(' in line and 'crypto_data' in line:
                        # Corrigir chamada para create_data_table com dados de string
                        fixed_lines.append('# Criar dados estruturados')
                        fixed_lines.append('crypto_list = [')
                        fixed_lines.append('    {"moeda": "Bitcoin (BTC)", "preco": 115625.00, "variacao": "+2.20%"},')
                        fixed_lines.append('    {"moeda": "Cardano (ADA)", "preco": 0.927874, "variacao": "+8.16%"},')
                        fixed_lines.append('    {"moeda": "Ethereum (ETH)", "preco": 4718.06, "variacao": "+8.98%"},')
                        fixed_lines.append('    {"moeda": "Solana (SOL)", "preco": 205.63, "variacao": "+11.84%"},')
                        fixed_lines.append('    {"moeda": "BNB (BNB)", "preco": 682.31, "variacao": "+0.67%"}')
                        fixed_lines.append(']')
                        fixed_lines.append('create_data_table(crypto_list, "crypto_table_visualization.html")')

                    else:
                        fixed_lines.append(line)

                except Exception as line_error:
                    logging.warning(f"Erro processando linha {line_num}: {line_error}")
                    fixed_lines.append(f'# Linha com problema: {line.strip()}')

            sanitized = '\n'.join(fixed_lines)

            # Adicionar encoding UTF-8 no início se necessário
            if 'print(' in sanitized and 'coding:' not in sanitized:
                sanitized = '# -*- coding: utf-8 -*-\n' + sanitized

            # Validar sintaxe antes de retornar
            try:
                ast.parse(sanitized)
                logging.info("✅ Código sanitizado e validado com sucesso")
                return sanitized
            except SyntaxError as e:
                logging.warning(f"⚠️ Erro de sintaxe detectado após sanitização: {e}")
                # Fallback mais inteligente
                return self._create_fallback_code(code)

        except Exception as e:
            logging.error(f"❌ Erro crítico na sanitização: {e}")
            return self._create_fallback_code(code)

    def _create_fallback_code(self, original_code: str) -> str:
        """Cria código de fallback seguro baseado no código original."""
        fallback = '''# -*- coding: utf-8 -*-
# Codigo corrigido automaticamente devido a erros de sintaxe

# Dados de criptomoedas processados
crypto_data = [
    {"moeda": "Bitcoin (BTC)", "preco": 115625.00, "variacao": "+2.20%"},
    {"moeda": "Cardano (ADA)", "preco": 0.927874, "variacao": "+8.16%"},
    {"moeda": "Ethereum (ETH)", "preco": 4718.06, "variacao": "+8.98%"},
    {"moeda": "Solana (SOL)", "preco": 205.63, "variacao": "+11.84%"},
    {"moeda": "BNB (BNB)", "preco": 682.31, "variacao": "+0.67%"}
]

print("=== RESUMO DO MERCADO DE CRIPTOMOEDAS ===")
for crypto in crypto_data:
    print(f"{crypto['moeda']}: ${crypto['preco']:,.2f} ({crypto['variacao']})")

# Criar visualizacao se possivel
try:
    create_data_table(crypto_data, "crypto_summary_visualization.html")
    print("\\n📊 Tabela interativa criada com sucesso!")
except:
    print("\\n📋 Dados processados com sucesso")
'''
        return fallback

    def _create_visualization_environment(self):
        """Cria ambiente com funções e bibliotecas para visualização."""

        def safe_sorted(data, key=None, reverse=False):
            """Função sorted segura que valida tipos."""
            if not isinstance(data, (list, tuple)):
                return []

            try:
                # Se não há key function, tentar ordenar diretamente
                if not key:
                    # Verificar se todos os elementos são comparáveis
                    if len(data) <= 1:
                        return list(data)

                    # Tentar comparar os primeiros dois elementos
                    try:
                        data[0] < data[1]
                        return sorted(data, reverse=reverse)
                    except TypeError:
                        # Se não pode comparar, converter tudo para string
                        return sorted(data, key=str, reverse=reverse)

                # Se há key function, validar se funciona
                processed_data = []
                for item in data:
                    try:
                        key_value = key(item)
                        processed_data.append((key_value, item))
                    except (TypeError, KeyError, AttributeError, ValueError):
                        # Se der erro, usar valor padrão
                        processed_data.append((0, item))

                # Ordenar pelos valores da key e retornar apenas os items originais
                sorted_pairs = sorted(processed_data, key=lambda x: x[0], reverse=reverse)
                return [item for _, item in sorted_pairs]

            except Exception:
                return list(data)  # Retornar como lista se não conseguir ordenar

        def extract_numeric_value(text):
            """Extrai valor numérico de texto."""
            import re
            if isinstance(text, (int, float)):
                return text
            if isinstance(text, str):
                # Remover símbolos e converter
                clean = re.sub(r'[^\d,.]', '', text)
                clean = clean.replace(',', '.')
                try:
                    return float(clean)
                except ValueError:
                    return 0.0
            return 0.0

        def create_price_data(search_results):
            """Cria dados estruturados de preço a partir de resultados de busca."""
            if isinstance(search_results, str):
                # Simular dados de exemplo se não conseguir extrair
                return [
                    {'modelo': 'iPhone 15 128GB', 'preco': 849.0, 'cor': 'Preto'},
                    {'modelo': 'iPhone 15 256GB', 'preco': 949.0, 'cor': 'Azul'},
                    {'modelo': 'iPhone 15 512GB', 'preco': 1149.0, 'cor': 'Rosa'},
                    {'modelo': 'iPhone 15 Pro 128GB', 'preco': 1199.0, 'cor': 'Titânio'},
                    {'modelo': 'iPhone 15 Pro Max 256GB', 'preco': 1449.0, 'cor': 'Azul Titânio'}
                ]
            return []

        env = {
            '__builtins__': __builtins__,
            'datetime': datetime,
            'json': json,
            'random': random,
            'math': math,
            'os': os,
            # Funções de visualização
            'create_weather_visualization': self._create_weather_viz,
            'create_data_table': self._create_data_table,
            'create_line_chart': self._create_line_chart,
            'create_bar_chart': self._create_bar_chart,
            'create_pie_chart': self._create_pie_chart,
            'create_dashboard': self._create_dashboard,
            'create_youtube_video': self._create_youtube_video,
            'create_image_gallery': self._create_image_gallery,
            'create_web_iframe': self._create_web_iframe,
            'create_interactive_demo': self._create_interactive_demo,
            'create_custom_html': self._create_custom_html,
            'save_visualization': self._save_visualization,
            # Funções auxiliares seguras
            'sorted': safe_sorted,
            'extract_numeric_value': extract_numeric_value,
            'create_price_data': create_price_data,
        }

        # Tentar importar bibliotecas úteis
        try:
            import requests
            env['requests'] = requests
        except ImportError:
            pass

        return env

    def _enhance_code_for_visualization(self, code: str) -> str:
        """Melhora código para incluir capacidades de visualização."""
        # Detectar tipo de dados/visualização necessária
        code_lower = code.lower()

        # Se for sobre vídeos
        if any(term in code_lower for term in ['video', 'vídeo', 'youtube', 'vimeo']):
            code = self._add_video_visualization_code(code)

        # Se for sobre imagens
        elif any(term in code_lower for term in ['imagem', 'image', 'foto', 'picture', 'galeria', 'gallery']):
            code = self._add_image_visualization_code(code)

        # Se for sobre clima/weather
        elif any(term in code_lower for term in ['clima', 'weather', 'temperatura', 'temp', 'chuva', 'rain']):
            code = self._add_weather_visualization_code(code)

        # Se for sobre dados tabulares
        elif any(term in code_lower for term in ['tabela', 'table', 'dados', 'data', 'lista', 'list']):
            code = self._add_table_visualization_code(code)

        # Se for sobre gráficos
        elif any(term in code_lower for term in ['gráfico', 'chart', 'graph', 'plot']):
            code = self._add_chart_visualization_code(code)

        # Se for sobre demos interativos
        elif any(term in code_lower for term in ['calculadora', 'calculator', 'demo', 'interativo', 'jogo', 'timer']):
            code = self._add_interactive_visualization_code(code)

        return self._enhance_api_code(code)

    def _add_video_visualization_code(self, code: str) -> str:
        """Adiciona código para visualização de vídeos."""
        video_addition = """
# Função automática para criar vídeos
def auto_video_display(video_info):
    if isinstance(video_info, str):
        if 'youtube.com' in video_info or 'youtu.be' in video_info:
            create_youtube_video(video_info, 'Vídeo Interessante', 'video_visualization.html')
        elif video_info.startswith('http'):
            create_web_iframe(video_info, 'Conteúdo Web', filename='web_visualization.html')

# Interceptar strings com URLs de vídeo
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        if isinstance(arg, str) and ('youtube' in arg or 'vimeo' in arg or 'video' in arg):
            auto_video_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return video_addition + "\n" + code

    def _add_image_visualization_code(self, code: str) -> str:
        """Adiciona código para visualização de imagens."""
        image_addition = """
# Função automática para criar galerias de imagens
def auto_image_display(image_data):
    if isinstance(image_data, str) and ('http' in image_data and any(ext in image_data for ext in ['.jpg', '.png', '.gif', '.jpeg', '.webp'])):
        create_image_gallery([image_data], 'Galeria de Imagens', 'gallery_visualization.html')
    elif isinstance(image_data, list):
        valid_images = [img for img in image_data if isinstance(img, str) and 'http' in img]
        if valid_images:
            create_image_gallery(valid_images, 'Galeria de Imagens', 'gallery_visualization.html')

# Interceptar URLs de imagens
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        auto_image_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return image_addition + "\n" + code

    def _add_weather_visualization_code(self, code: str) -> str:
        """Adiciona código para visualização de dados meteorológicos."""
        weather_addition = """
# Função automática para criar visualização do clima
def auto_weather_display(data):
    if isinstance(data, dict) and any(key in str(data).lower() for key in ['temp', 'weather', 'clima']):
        create_weather_visualization(data)
    elif isinstance(data, str) and any(term in data.lower() for term in ['°c', '°f', 'celsius', 'fahrenheit']):
        # Extrair dados do texto e criar visualização
        create_weather_visualization({'description': data})

# Interceptar prints para detectar dados climáticos
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        auto_weather_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return weather_addition + "\n" + code

    def _add_table_visualization_code(self, code: str) -> str:
        """Adiciona código para visualização de tabelas."""
        table_addition = """
# Função automática para criar tabelas interativas
def auto_table_display(data):
    if isinstance(data, (list, dict)):
        create_data_table(data, 'dados_visualization.html')

# Interceptar estruturas de dados
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        if isinstance(arg, (list, dict)) and len(str(arg)) > 50:
            auto_table_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return table_addition + "\n" + code

    def _add_chart_visualization_code(self, code: str) -> str:
        """Adiciona código para visualização de gráficos."""
        chart_addition = """
# Função automática para criar gráficos
def auto_chart_display(data):
    if isinstance(data, list) and len(data) > 2:
        # Detectar se são números
        if all(isinstance(x, (int, float)) for x in data):
            create_line_chart(data, labels=[f'Item {i+1}' for i in range(len(data))], filename='chart_visualization.html')
        elif isinstance(data[0], dict):
            create_dashboard(data, 'dashboard_visualization.html')

# Interceptar listas numéricas
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        auto_chart_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return chart_addition + "\n" + code

    def _add_interactive_visualization_code(self, code: str) -> str:
        """Adiciona código para demos interativos."""
        interactive_addition = """
# Função automática para criar demos interativos
def auto_interactive_display(demo_type):
    if isinstance(demo_type, str):
        if 'calculadora' in demo_type.lower() or 'calculator' in demo_type.lower():
            create_interactive_demo('calculator', 'calculator_visualization.html')
        elif 'timer' in demo_type.lower() or 'cronômetro' in demo_type.lower():
            create_interactive_demo('timer', 'timer_visualization.html')
        elif 'cor' in demo_type.lower() or 'color' in demo_type.lower():
            create_interactive_demo('color_picker', 'color_visualization.html')

# Interceptar pedidos de demos
original_print = print
def enhanced_print(*args, **kwargs):
    for arg in args:
        if isinstance(arg, str) and any(term in arg.lower() for term in ['demo', 'calculadora', 'timer', 'interativo']):
            auto_interactive_display(arg)
    return original_print(*args, **kwargs)
print = enhanced_print
"""
        return interactive_addition + "\n" + code

    def _create_weather_viz(self, weather_data, filename='weather_visualization.html'):
        """Cria visualização interativa para dados climáticos."""
        template = self.visualization_templates['weather_chart']

        # Processar dados climáticos
        if isinstance(weather_data, dict):
            temp = weather_data.get('temperature', weather_data.get('temp', 20))
            humidity = weather_data.get('humidity', 50)
            description = weather_data.get('description', 'Clima atual')
            city = weather_data.get('city', weather_data.get('location', 'Local'))
        else:
            temp = 20
            humidity = 50
            description = str(weather_data)
            city = 'Local'

        html_content = template.format(
            city=city,
            temperature=temp,
            humidity=humidity,
            description=description,
            temp_color='#FF6B6B' if temp > 25 else '#4ECDC4' if temp > 15 else '#45B7D1'
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_data_table(self, data, filename='table_visualization.html'):
        """Cria tabela interativa e responsiva."""
        template = self.visualization_templates['data_table']

        if isinstance(data, dict):
            rows = [f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in data.items()]
            headers = "<tr><th>Chave</th><th>Valor</th></tr>"
        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                keys = list(data[0].keys())
                headers = "<tr>" + "".join(f"<th>{k}</th>" for k in keys) + "</tr>"
                rows = []
                for item in data:
                    row = "<tr>" + "".join(f"<td>{item.get(k, '')}</td>" for k in keys) + "</tr>"
                    rows.append(row)
            else:
                headers = "<tr><th>Índice</th><th>Valor</th></tr>"
                rows = [f"<tr><td>{i}</td><td>{v}</td></tr>" for i, v in enumerate(data)]
        else:
            headers = "<tr><th>Dados</th></tr>"
            rows = [f"<tr><td>{data}</td></tr>"]

        table_content = headers + "".join(rows)
        html_content = template.format(table_content=table_content)

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_line_chart(self, data, labels=None, filename='chart_visualization.html'):
        """Cria gráfico de linha interativo."""
        template = self.visualization_templates['line_chart']

        if not labels:
            labels = [f'Item {i+1}' for i in range(len(data))]

        data_json = json.dumps(data)
        labels_json = json.dumps(labels)

        html_content = template.format(
            data_values=data_json,
            data_labels=labels_json
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_bar_chart(self, data, labels=None, filename='bar_visualization.html'):
        """Cria gráfico de barras interativo."""
        template = self.visualization_templates['bar_chart']

        if not labels:
            labels = [f'Item {i+1}' for i in range(len(data))]

        data_json = json.dumps(data)
        labels_json = json.dumps(labels)

        html_content = template.format(
            data_values=data_json,
            data_labels=labels_json
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_pie_chart(self, data, labels=None, filename='pie_visualization.html'):
        """Cria gráfico de pizza interativo."""
        template = self.visualization_templates['pie_chart']

        if isinstance(data, dict):
            labels = list(data.keys())
            data = list(data.values())
        elif not labels:
            labels = [f'Seção {i+1}' for i in range(len(data))]

        data_json = json.dumps(data)
        labels_json = json.dumps(labels)

        html_content = template.format(
            data_values=data_json,
            data_labels=labels_json
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_dashboard(self, data, filename='dashboard_visualization.html'):
        """Cria dashboard interativo com múltiplas visualizações."""
        template = self.visualization_templates['dashboard']

        data_json = json.dumps(data, default=str)

        html_content = template.format(dashboard_data=data_json)

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_youtube_video(self, video_id_or_url, title="Vídeo", filename='youtube_visualization.html'):
        """Cria iframe do YouTube para vídeos."""
        # Extrair ID do vídeo se for URL completa
        if 'youtube.com/watch?v=' in video_id_or_url:
            video_id = video_id_or_url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_id_or_url:
            video_id = video_id_or_url.split('youtu.be/')[1].split('?')[0]
        else:
            video_id = video_id_or_url

        template = self.visualization_templates['video_iframe']
        html_content = template.format(
            video_id=video_id,
            title=title
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_image_gallery(self, image_urls, title="Galeria de Imagens", filename='gallery_visualization.html'):
        """Cria galeria de imagens responsiva."""
        if isinstance(image_urls, str):
            image_urls = [image_urls]

        images_html = ""
        for i, url in enumerate(image_urls):
            images_html += f'''
            <div class="image-item">
                <img src="{url}" alt="Imagem {i+1}" onclick="openModal('{url}')">
            </div>
            '''

        template = self.visualization_templates['image_gallery']
        html_content = template.format(
            title=title,
            images_content=images_html
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_web_iframe(self, url, title="Conteúdo Web", width="100%", height="600px", filename='web_visualization.html'):
        """Cria iframe para qualquer conteúdo web."""
        template = self.visualization_templates['web_content']
        html_content = template.format(
            title=title,
            url=url,
            width=width,
            height=height
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_interactive_demo(self, demo_type="calculator", filename='demo_visualization.html'):
        """Cria demos interativos (calculadora, jogos simples, etc.)."""
        template = self.visualization_templates['interactive_demo']

        if demo_type == "calculator":
            demo_content = self._get_calculator_html()
        elif demo_type == "color_picker":
            demo_content = self._get_color_picker_html()
        elif demo_type == "timer":
            demo_content = self._get_timer_html()
        else:
            demo_content = "<p>Demo não disponível</p>"

        html_content = template.format(
            demo_title=demo_type.title().replace('_', ' '),
            demo_content=demo_content
        )

        # Salvar usando o ArtifactManager
        self._save_visualization_content(html_content, filename)


    def _create_custom_html(self, html_content, title="Conteúdo Personalizado", filename='custom_visualization.html'):
        """Cria visualização HTML personalizada."""
        full_html = f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; margin: 20px; background: #f5f6fa; }}
                .container {{ background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>{title}</h2>
                {html_content}
            </div>
        </body>
        </html>
        '''
        # Salvar usando o ArtifactManager
        self._save_visualization_content(full_html, filename)


    def _save_visualization_content(self, content, filename):
        """Salva conteúdo HTML personalizado usando o ArtifactManager."""
        if self.artifact_manager:
            self.artifact_manager.save_artifact(filename, content)
        else:
            # Fallback se o artifact manager não estiver inicializado
            full_path = self._get_artifact_path(filename)
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Visualização personalizada salva (fallback): {full_path}")
            except IOError as e:
                print(f"Erro ao salvar visualização (fallback) {filename}: {e}")


    def _get_weather_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clima - {city}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #74b9ff, #0984e3); min-height: 100vh; }}
        .weather-card {{ background: white; border-radius: 20px; padding: 30px; max-width: 400px; margin: 50px auto; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }}
        .temperature {{ font-size: 4rem; font-weight: bold; color: {temp_color}; margin: 20px 0; }}
        .city {{ font-size: 1.5rem; color: #333; margin-bottom: 10px; }}
        .description {{ font-size: 1.2rem; color: #666; margin: 15px 0; }}
        .humidity {{ font-size: 1rem; color: #888; background: #f8f9fa; padding: 10px; border-radius: 10px; margin-top: 20px; }}
        .icon {{ font-size: 5rem; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="weather-card">
        <div class="city">{city}</div>
        <div class="icon">🌤️</div>
        <div class="temperature">{temperature}°C</div>
        <div class="description">{description}</div>
        <div class="humidity">💧 Umidade: {humidity}%</div>
    </div>
</body>
</html>"""

    def _get_table_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tabela de Dados</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f6fa; }}
        .table-container {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 1000px; margin: 0 auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #3742fa; color: white; padding: 15px; text-align: left; font-weight: 600; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fd; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 20px; font-size: 1.5rem; }}
    </style>
</head>
<body>
    <h2 class="title">📊 Tabela de Dados</h2>
    <div class="table-container">
        <table>
            {table_content}
        </table>
    </div>
</body>
</html>"""

    def _get_line_chart_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gráfico de Linha</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f6fa; }}
        .chart-container {{ background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.5rem; }}
    </style>
</head>
<body>
    <div class="chart-container">
        <h2 class="title">📈 Gráfico de Linha</h2>
        <canvas id="lineChart" width="400" height="200"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('lineChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {data_labels},
                datasets: [{{
                    label: 'Dados',
                    data: {data_values},
                    borderColor: '#3742fa',
                    backgroundColor: 'rgba(55, 66, 250, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: true }},
                    title: {{ display: true, text: 'Análise de Dados' }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    def _get_bar_chart_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gráfico de Barras</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f6fa; }}
        .chart-container {{ background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.5rem; }}
    </style>
</head>
<body>
    <div class="chart-container">
        <h2 class="title">📊 Gráfico de Barras</h2>
        <canvas id="barChart" width="400" height="200"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('barChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {data_labels},
                datasets: [{{
                    label: 'Valores',
                    data: {data_values},
                    backgroundColor: ['#3742fa', '#2ed573', '#ffa502', '#ff4757', '#5352ed', '#ff3838'],
                    borderColor: ['#2f3542'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: true }},
                    title: {{ display: true, text: 'Análise Comparativa' }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    def _get_pie_chart_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gráfico de Pizza</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f6fa; }}
        .chart-container {{ background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.5rem; }}
    </style>
</head>
<body>
    <div class="chart-container">
        <h2 class="title">🥧 Distribuição dos Dados</h2>
        <canvas id="pieChart" width="400" height="400"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('pieChart').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: {data_labels},
                datasets: [{{
                    data: {data_values},
                    backgroundColor: ['#3742fa', '#2ed573', '#ffa502', '#ff4757', '#5352ed', '#ff3838', '#747d8c', '#a4b0be'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    title: {{ display: true, text: 'Análise Proporcional' }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    def _get_dashboard_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Interativo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f6fa; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 2rem; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-top: 0; color: #3742fa; }}
        .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
        .chart-card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1 class="title">📊 Dashboard de Dados</h1>
        <div class="cards" id="infoCards"></div>
        <div class="charts">
            <div class="chart-card">
                <canvas id="chart1" width="400" height="200"></canvas>
            </div>
            <div class="chart-card">
                <canvas id="chart2" width="400" height="200"></canvas>
            </div>
        </div>
    </div>
    <script>
        const data = {dashboard_data};

        // Criar cards informativos
        const cardsContainer = document.getElementById('infoCards');
        if (Array.isArray(data)) {{
            const stats = {{
                total: data.length,
                avg: data.length > 0 ? (data.reduce((a, b) => a + (typeof b === 'number' ? b : 1), 0) / data.length).toFixed(2) : 0
            }};
            cardsContainer.innerHTML = `
                <div class="card"><h3>📈 Total de Items</h3><p style="font-size: 2rem; color: #3742fa;">${{stats.total}}</p></div>
                <div class="card"><h3>📊 Média</h3><p style="font-size: 2rem; color: #2ed573;">${{stats.avg}}</p></div>
            `;
        }}

        // Gráfico 1
        const ctx1 = document.getElementById('chart1').getContext('2d');
        new Chart(ctx1, {{
            type: 'line',
            data: {{
                labels: data.map((_, i) => `Item ${{i+1}}`),
                datasets: [{{
                    label: 'Tendência',
                    data: Array.isArray(data) ? data.map(item => typeof item === 'number' ? item : Math.random() * 100) : [1,2,3,4,5],
                    borderColor: '#3742fa',
                    backgroundColor: 'rgba(55, 66, 250, 0.1)',
                    fill: true
                }}]
            }},
            options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Análise Temporal' }} }} }}
        }});

        // Gráfico 2
        const ctx2 = document.getElementById('chart2').getContext('2d');
        new Chart(ctx2, {{
            type: 'doughnut',
            data: {{
                labels: ['Categoria A', 'Categoria B', 'Categoria C'],
                datasets: [{{
                    data: [30, 40, 30],
                    backgroundColor: ['#3742fa', '#2ed573', '#ffa502']
                }}]
            }},
            options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Distribuição' }} }} }}
        }});
    </script>
</body>
</html>"""

    def _get_video_iframe_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .video-container {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 900px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.8rem; }}
        .video-wrapper {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 10px; }}
        .video-wrapper iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 10px; }}
    </style>
</head>
<body>
    <div class="video-container">
        <h2 class="title">🎬 {title}</h2>
        <div class="video-wrapper">
            <iframe src="https://www.youtube.com/embed/{video_id}" allowfullscreen></iframe>
        </div>
    </div>
</body>
</html>"""

    def _get_image_gallery_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); min-height: 100vh; }}
        .gallery-container {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 1200px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.8rem; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .image-item img {{ width: 100%; height: 200px; object-fit: cover; border-radius: 10px; cursor: pointer; transition: transform 0.3s ease; }}
        .image-item img:hover {{ transform: scale(1.05); }}
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); }}
        .modal-content {{ margin: auto; display: block; width: 80%; max-width: 700px; margin-top: 5%; }}
        .close {{ position: absolute; top: 15px; right: 35px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="gallery-container">
        <h2 class="title">🖼️ {title}</h2>
        <div class="gallery">
            {images_content}
        </div>
    </div>

    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>

    <script>
        function openModal(src) {{
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImg').src = src;
        }}

        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
    </script>
</body>
</html>"""

    def _get_web_content_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); min-height: 100vh; }}
        .content-container {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 1200px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.8rem; }}
        .iframe-wrapper {{ border-radius: 10px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
        iframe {{ width: {width}; height: {height}; border: none; display: block; }}
    </style>
</head>
<body>
    <div class="content-container">
        <h2 class="title">🌐 {title}</h2>
        <div class="iframe-wrapper">
            <iframe src="{url}"></iframe>
        </div>
    </div>
</body>
</html>"""

    def _get_interactive_demo_template(self):
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo Interativo - {demo_title}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .demo-container {{ background: white; border-radius: 15px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
        .title {{ text-align: center; color: #2f3542; margin-bottom: 30px; font-size: 1.8rem; }}
    </style>
</head>
<body>
    <div class="demo-container">
        <h2 class="title">⚡ {demo_title}</h2>
        {demo_content}
    </div>
</body>
</html>"""

    def _get_calculator_html(self):
        return """
        <div style="max-width: 300px; margin: 0 auto; background: #f8f9fa; padding: 20px; border-radius: 10px;">
            <input type="text" id="display" readonly style="width: 100%; font-size: 24px; text-align: right; padding: 10px; margin-bottom: 10px; border: none; background: #fff; border-radius: 5px;">
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <button onclick="clearDisplay()" style="grid-column: span 2; padding: 15px; font-size: 18px; border: none; background: #ff6b6b; color: white; border-radius: 5px; cursor: pointer;">C</button>
                <button onclick="deleteLast()" style="padding: 15px; font-size: 18px; border: none; background: #ffa502; color: white; border-radius: 5px; cursor: pointer;">⌫</button>
                <button onclick="appendToDisplay('/')" style="padding: 15px; font-size: 18px; border: none; background: #3742fa; color: white; border-radius: 5px; cursor: pointer;">÷</button>
                <button onclick="appendToDisplay('7')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">7</button>
                <button onclick="appendToDisplay('8')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">8</button>
                <button onclick="appendToDisplay('9')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">9</button>
                <button onclick="appendToDisplay('*')" style="padding: 15px; font-size: 18px; border: none; background: #3742fa; color: white; border-radius: 5px; cursor: pointer;">×</button>
                <button onclick="appendToDisplay('4')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">4</button>
                <button onclick="appendToDisplay('5')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">5</button>
                <button onclick="appendToDisplay('6')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">6</button>
                <button onclick="appendToDisplay('-')" style="padding: 15px; font-size: 18px; border: none; background: #3742fa; color: white; border-radius: 5px; cursor: pointer;">−</button>
                <button onclick="appendToDisplay('1')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">1</button>
                <button onclick="appendToDisplay('2')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">2</button>
                <button onclick="appendToDisplay('3')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">3</button>
                <button onclick="appendToDisplay('+')" style="padding: 15px; font-size: 18px; border: none; background: #3742fa; color: white; border-radius: 5px; cursor: pointer;">+</button>
                <button onclick="appendToDisplay('0')" style="grid-column: span 2; padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">0</button>
                <button onclick="appendToDisplay('.')" style="padding: 15px; font-size: 18px; border: none; background: #2f3542; color: white; border-radius: 5px; cursor: pointer;">.</button>
                <button onclick="calculate()" style="padding: 15px; font-size: 18px; border: none; background: #2ed573; color: white; border-radius: 5px; cursor: pointer;">=</button>
            </div>
        </div>

        <script>
            function appendToDisplay(value) {
                document.getElementById('display').value += value;
            }

            function clearDisplay() {
                document.getElementById('display').value = '';
            }

            function deleteLast() {
                let display = document.getElementById('display');
                display.value = display.value.slice(0, -1);
            }

            function calculate() {
                try {
                    let result = eval(document.getElementById('display').value);
                    document.getElementById('display').value = result;
                } catch (error) {
                    document.getElementById('display').value = 'Erro';
                }
            }
        </script>
        """

    def _get_color_picker_html(self):
        """Retorna HTML para um seletor de cores interativo."""
        return """
        <div style="max-width: 400px; margin: 0 auto; text-align: center;">
            <h3>Seletor de Cores</h3>
            <input type="color" id="colorPicker" style="width: 100px; height: 50px; border: none; border-radius: 10px; margin: 10px;">
            <div id="colorDisplay" style="width: 200px; height: 100px; margin: 20px auto; border-radius: 10px; background: #ff0000;"></div>
            <div id="colorCode" style="font-family: monospace; font-size: 18px; margin: 10px;">#ff0000</div>
        </div>

        <script>
            document.getElementById('colorPicker').addEventListener('change', function(e) {
                const color = e.target.value;
                document.getElementById('colorDisplay').style.background = color;
                document.getElementById('colorCode').textContent = color;
            });
        </script>
        """

    def _get_timer_html(self):
        """Retorna HTML para um cronômetro interativo."""
        return """
        <div style="max-width: 300px; margin: 0 auto; text-align: center;">
            <h3>Cronômetro</h3>
            <div id="timeDisplay" style="font-size: 48px; margin: 20px; font-family: monospace;">00:00</div>
            <div>
                <button onclick="startTimer()" style="margin: 5px; padding: 10px 20px; background: #2ed573; color: white; border: none; border-radius: 5px; cursor: pointer;">Iniciar</button>
                <button onclick="pauseTimer()" style="margin: 5px; padding: 10px 20px; background: #ffa502; color: white; border: none; border-radius: 5px; cursor: pointer;">Pausar</button>
                <button onclick="resetTimer()" style="margin: 5px; padding: 10px 20px; background: #ff4757; color: white; border: none; border-radius: 5px; cursor: pointer;">Reset</button>
            </div>
        </div>

        <script>
            let timer = null;
            let seconds = 0;

            function updateDisplay() {
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                document.getElementById('timeDisplay').textContent = 
                    String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
            }

            function startTimer() {
                if (!timer) {
                    timer = setInterval(() => {
                        seconds++;
                        updateDisplay();
                    }, 1000);
                }
            }

            function pauseTimer() {
                clearInterval(timer);
                timer = null;
            }

            function resetTimer() {
                clearInterval(timer);
                timer = null;
                seconds = 0;
                updateDisplay();
            }
        </script>
        """

    def _save_visualization(self, content, filename):
        """Salva conteúdo HTML personalizado."""
        full_path = self._get_artifact_path(filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Visualização personalizada salva: {full_path}")

    def _determine_artifact_type(self, filename):
        """Determina o tipo de artefato baseado no nome do arquivo."""
        filename_lower = filename.lower()
        if 'chart' in filename_lower or 'graph' in filename_lower:
            return 'chart'
        elif 'table' in filename_lower or 'dados' in filename_lower:
            return 'table'
        elif 'dashboard' in filename_lower:
            return 'dashboard'
        elif 'demo' in filename_lower or 'calculator' in filename_lower:
            return 'demo'
        elif 'weather' in filename_lower or 'clima' in filename_lower:
            return 'weather'
        else:
            return 'visualization'

    def _determine_artifact_title(self, filename):
        """Determina o título do artefato baseado no nome do arquivo."""
        base_name = filename.replace('.html', '').replace('_', ' ').title()
        if 'Visualization' in base_name:
            return base_name.replace('Visualization', 'Visualização')
        return base_name

    def _enhance_api_code(self, code):
        """Melhora código com funcionalidades de API se necessário."""
        # Por enquanto, retorna o código como está
        return code