
"""
Processador HMP específico para criação e renderização de artefatos.
Garante que todas as interfaces sejam renderizadas como artefatos completos.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from .hmp_interpreter import HMPInterpreter

class ArtifactHMPProcessor:
    """
    Processador especializado em criar artefatos renderizáveis via HMP.
    """
    
    def __init__(self):
        self.hmp_interpreter = HMPInterpreter()
        self.artifact_templates = self._load_artifact_templates()
        logging.info("🎨 ArtifactHMPProcessor inicializado")
    
    def process_artifact_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa requisição para criar artefato renderizável."""
        
        # Determinar tipo de artefato baseado na entrada
        artifact_type = self._classify_artifact_type(user_input)
        
        # Executar cadeia HMP apropriada
        if artifact_type == "dashboard":
            return self._create_dashboard_artifact(user_input, context)
        elif artifact_type == "form":
            return self._create_form_artifact(user_input, context)
        elif artifact_type == "visualization":
            return self._create_visualization_artifact(user_input, context)
        elif artifact_type == "interface":
            return self._create_interface_artifact(user_input, context)
        else:
            return self._create_generic_artifact(user_input, context)
    
    def _classify_artifact_type(self, user_input: str) -> str:
        """Classifica o tipo de artefato baseado na entrada do usuário."""
        
        classification_hmp = f"""
SET input_text TO "{user_input}"
SET artifact_type TO "generic"

# ANÁLISE DE PADRÕES PARA ARTEFATOS
IF input_text.contains("dashboard", "painel", "métricas", "analytics") THEN
    SET artifact_type TO "dashboard"
ELSE IF input_text.contains("formulário", "form", "cadastro", "input") THEN
    SET artifact_type TO "form"
ELSE IF input_text.contains("gráfico", "chart", "visualização", "dados") THEN
    SET artifact_type TO "visualization"
ELSE IF input_text.contains("interface", "app", "aplicativo", "página") THEN
    SET artifact_type TO "interface"
ELSE IF input_text.contains("tabela", "table", "lista") THEN
    SET artifact_type TO "table"
ELSE
    SET artifact_type TO "generic"
ENDIF

RETURN artifact_type
"""
        
        result = self.hmp_interpreter.execute_hmp(classification_hmp)
        return result.get('variables', {}).get('artifact_type', 'generic')
    
    def _create_dashboard_artifact(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria artefato de dashboard completo."""
        
        dashboard_hmp = f"""
SET dashboard_request TO "{user_input}"
SET dashboard_config TO empty_dict

# FASE 1: ANÁLISE DE REQUISITOS
CALL analyze_dashboard_requirements WITH request = dashboard_request
SET required_metrics TO analysis_result.metrics
SET layout_type TO analysis_result.layout
SET data_sources TO analysis_result.data_sources

# FASE 2: GERAÇÃO DE ESTRUTURA
CALL generate_dashboard_structure WITH
    metrics = required_metrics,
    layout = layout_type,
    responsive = true

# FASE 3: ADIÇÃO DE COMPONENTES INTERATIVOS
CALL add_interactive_components WITH
    structure = dashboard_structure,
    components = ["charts", "filters", "export_buttons"]

# FASE 4: STYLING E RESPONSIVIDADE
CALL apply_professional_styling WITH
    dashboard = interactive_dashboard,
    theme = "modern_professional"

# FASE 5: VALIDAÇÃO E FINALIZAÇÃO
CALL validate_dashboard_functionality WITH dashboard = styled_dashboard
CALL generate_complete_html WITH validated_dashboard = final_dashboard

RETURN complete_dashboard_artifact
"""
        
        result = self.hmp_interpreter.execute_hmp(dashboard_hmp, context)
        
        # Gerar HTML do dashboard
        html_content = self._generate_dashboard_html(user_input, result)
        
        return {
            'type': 'dashboard',
            'title': 'Dashboard Interativo',
            'content': html_content,
            'is_complete': True,
            'interactive': True
        }
    
    def _create_visualization_artifact(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria artefato de visualização de dados."""
        
        viz_hmp = f"""
SET viz_request TO "{user_input}"
SET visualization_config TO empty_dict

# FASE 1: ANÁLISE DE DADOS E TIPO DE GRÁFICO
CALL analyze_data_requirements WITH request = viz_request
SET chart_type TO determine_optimal_chart_type(data_analysis)
SET data_structure TO analysis_result.structure

# FASE 2: GERAÇÃO DE DADOS DE EXEMPLO (SE NECESSÁRIO)
IF data_structure.has_real_data == false THEN
    CALL generate_sample_data WITH
        type = chart_type,
        records = 20,
        realistic = true
ENDIF

# FASE 3: CRIAÇÃO DO GRÁFICO INTERATIVO
CALL create_interactive_chart WITH
    data = processed_data,
    chart_type = chart_type,
    library = "Chart.js"

# FASE 4: ADIÇÃO DE CONTROLES
CALL add_chart_controls WITH
    chart = interactive_chart,
    controls = ["zoom", "filter", "export", "animation"]

RETURN complete_visualization_artifact
"""
        
        result = self.hmp_interpreter.execute_hmp(viz_hmp, context)
        
        # Gerar HTML da visualização
        html_content = self._generate_visualization_html(user_input, result)
        
        return {
            'type': 'visualization',
            'title': 'Visualização Interativa',
            'content': html_content,
            'is_complete': True,
            'interactive': True
        }
    
    def _create_interface_artifact(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria artefato de interface completa."""
        
        interface_hmp = f"""
SET interface_request TO "{user_input}"
SET interface_config TO empty_dict

# FASE 1: ANÁLISE DE REQUISITOS DA INTERFACE
CALL analyze_interface_requirements WITH request = interface_request
SET ui_components TO analysis_result.components
SET layout_style TO analysis_result.layout
SET functionality TO analysis_result.functionality

# FASE 2: GERAÇÃO DE LAYOUT RESPONSIVO
CALL generate_responsive_layout WITH
    components = ui_components,
    style = layout_style,
    mobile_first = true

# FASE 3: IMPLEMENTAÇÃO DE FUNCIONALIDADES
CALL implement_interactive_features WITH
    layout = responsive_layout,
    features = functionality

# FASE 4: OTIMIZAÇÃO E POLISH
CALL optimize_interface_performance WITH interface = functional_interface
CALL apply_modern_styling WITH optimized_interface = polished_interface

RETURN complete_interface_artifact
"""
        
        result = self.hmp_interpreter.execute_hmp(interface_hmp, context)
        
        # Gerar HTML da interface
        html_content = self._generate_interface_html(user_input, result)
        
        return {
            'type': 'interface',
            'title': 'Interface Interativa',
            'content': html_content,
            'is_complete': True,
            'interactive': True
        }
    
    def _create_form_artifact(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria artefato de formulário interativo."""
        
        form_hmp = f"""
SET form_request TO "{user_input}"
SET form_config TO empty_dict

# FASE 1: ANÁLISE DE CAMPOS NECESSÁRIOS
CALL analyze_form_requirements WITH request = form_request
SET required_fields TO analysis_result.fields
SET validation_rules TO analysis_result.validation
SET submission_action TO analysis_result.action

# FASE 2: GERAÇÃO DE ESTRUTURA DO FORMULÁRIO
CALL generate_form_structure WITH
    fields = required_fields,
    validation = validation_rules,
    responsive = true

# FASE 3: IMPLEMENTAÇÃO DE VALIDAÇÃO
CALL implement_form_validation WITH
    form = form_structure,
    rules = validation_rules,
    real_time = true

# FASE 4: STYLING E UX
CALL apply_modern_form_styling WITH
    form = validated_form,
    style = "clean_professional"

RETURN complete_form_artifact
"""
        
        result = self.hmp_interpreter.execute_hmp(form_hmp, context)
        
        # Gerar HTML do formulário
        html_content = self._generate_form_html(user_input, result)
        
        return {
            'type': 'form',
            'title': 'Formulário Interativo',
            'content': html_content,
            'is_complete': True,
            'interactive': True
        }
    
    def _create_generic_artifact(self, user_input: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria artefato genérico baseado na entrada."""
        
        generic_hmp = f"""
SET generic_request TO "{user_input}"
SET artifact_config TO empty_dict

# FASE 1: ANÁLISE GERAL
CALL analyze_generic_requirements WITH request = generic_request
SET content_type TO analysis_result.type
SET required_features TO analysis_result.features

# FASE 2: GERAÇÃO DE CONTEÚDO
CALL generate_appropriate_content WITH
    type = content_type,
    features = required_features,
    interactive = true

# FASE 3: ESTRUTURAÇÃO E STYLING
CALL structure_content_professionally WITH content = generated_content
CALL apply_universal_styling WITH structured_content = professional_content

RETURN complete_generic_artifact
"""
        
        result = self.hmp_interpreter.execute_hmp(generic_hmp, context)
        
        # Gerar HTML genérico
        html_content = self._generate_generic_html(user_input, result)
        
        return {
            'type': 'generic',
            'title': 'Artefato Interativo',
            'content': html_content,
            'is_complete': True,
            'interactive': True
        }
    
    def _generate_dashboard_html(self, user_input: str, hmp_result: Dict) -> str:
        """Gera HTML completo para dashboard."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Interativo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .dashboard {{ 
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }}
        .header {{ 
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .metrics-grid {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{ transform: translateY(-5px); }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; margin-top: 5px; }}
        .chart-container {{ 
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid #e2e8f0;
        }}
        .controls {{ 
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        button {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        button:hover {{ background: linear-gradient(135deg, #5a6fd8, #6a4190); }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Dashboard Interativo</h1>
            <p>Baseado em: {user_input}</p>
        </div>
        
        <div class="controls">
            <button onclick="refreshData()">🔄 Atualizar</button>
            <button onclick="exportData()">📊 Exportar</button>
            <button onclick="toggleView()">👁️ Alternar Visualização</button>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="metric1">1,234</div>
                <div class="metric-label">Total de Visualizações</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="metric2">89.5%</div>
                <div class="metric-label">Taxa de Conversão</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="metric3">R$ 45.6K</div>
                <div class="metric-label">Receita Total</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="metric4">156</div>
                <div class="metric-label">Novos Usuários</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="mainChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <canvas id="secondaryChart" width="400" height="200"></canvas>
        </div>
    </div>
    
    <script>
        // Configuração dos gráficos
        const ctx1 = document.getElementById('mainChart').getContext('2d');
        const ctx2 = document.getElementById('secondaryChart').getContext('2d');
        
        const mainChart = new Chart(ctx1, {{
            type: 'line',
            data: {{
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                datasets: [{{
                    label: 'Vendas',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Evolução das Vendas'
                    }}
                }}
            }}
        }});
        
        const secondaryChart = new Chart(ctx2, {{
            type: 'doughnut',
            data: {{
                labels: ['Desktop', 'Mobile', 'Tablet'],
                datasets: [{{
                    data: [55, 35, 10],
                    backgroundColor: [
                        'rgb(102, 126, 234)',
                        'rgb(118, 75, 162)',
                        'rgb(255, 99, 132)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Dispositivos de Acesso'
                    }}
                }}
            }}
        }});
        
        // Funções interativas
        function refreshData() {{
            // Simular atualização de dados
            document.getElementById('metric1').textContent = Math.floor(Math.random() * 2000 + 1000).toLocaleString();
            document.getElementById('metric2').textContent = (Math.random() * 100).toFixed(1) + '%';
            document.getElementById('metric3').textContent = 'R$ ' + (Math.random() * 100 + 20).toFixed(1) + 'K';
            document.getElementById('metric4').textContent = Math.floor(Math.random() * 300 + 100);
        }}
        
        function exportData() {{
            alert('Exportando dados do dashboard...');
        }}
        
        function toggleView() {{
            const charts = document.querySelectorAll('.chart-container');
            charts.forEach(chart => {{
                chart.style.display = chart.style.display === 'none' ? 'block' : 'none';
            }});
        }}
        
        // Auto-refresh dos dados a cada 30 segundos
        setInterval(refreshData, 30000);
    </script>
</body>
</html>"""
    
    def _generate_visualization_html(self, user_input: str, hmp_result: Dict) -> str:
        """Gera HTML completo para visualização."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualização Interativa</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }}
        .chart-controls {{ 
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        button {{ 
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        .chart-wrapper {{ 
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        .data-table {{ 
            margin-top: 30px;
            background: #f8fafc;
            border-radius: 10px;
            padding: 20px;
        }}
        table {{ 
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{ 
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{ 
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Visualização Interativa</h1>
        <p>Baseado em: {user_input}</p>
        
        <div class="chart-controls">
            <button onclick="changeChartType('line')">📈 Linha</button>
            <button onclick="changeChartType('bar')">📊 Barras</button>
            <button onclick="changeChartType('pie')">🥧 Pizza</button>
            <button onclick="toggleAnimation()">✨ Animação</button>
            <button onclick="exportChart()">💾 Exportar</button>
        </div>
        
        <div class="chart-wrapper">
            <canvas id="mainChart"></canvas>
        </div>
        
        <div class="data-table">
            <h3>Dados da Visualização</h3>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>Categoria</th>
                        <th>Valor</th>
                        <th>Percentual</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let currentChart;
        const data = {{
            labels: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho'],
            datasets: [{{
                label: 'Dados',
                data: [65, 59, 80, 81, 56, 55],
                backgroundColor: [
                    'rgba(116, 185, 255, 0.7)',
                    'rgba(9, 132, 227, 0.7)',
                    'rgba(255, 107, 107, 0.7)',
                    'rgba(255, 177, 66, 0.7)',
                    'rgba(72, 219, 251, 0.7)',
                    'rgba(29, 209, 161, 0.7)'
                ],
                borderColor: [
                    'rgb(116, 185, 255)',
                    'rgb(9, 132, 227)',
                    'rgb(255, 107, 107)',
                    'rgb(255, 177, 66)',
                    'rgb(72, 219, 251)',
                    'rgb(29, 209, 161)'
                ],
                borderWidth: 2
            }}]
        }};
        
        function createChart(type = 'line') {{
            const ctx = document.getElementById('mainChart').getContext('2d');
            
            if (currentChart) {{
                currentChart.destroy();
            }}
            
            currentChart = new Chart(ctx, {{
                type: type,
                data: data,
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Visualização de Dados Interativa'
                        }},
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }},
                    scales: type !== 'pie' ? {{
                        y: {{
                            beginAtZero: true
                        }}
                    }} : {{}},
                    animation: {{
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }}
                }}
            }});
            
            updateTable();
        }}
        
        function changeChartType(type) {{
            createChart(type);
        }}
        
        function toggleAnimation() {{
            currentChart.options.animation.duration = 
                currentChart.options.animation.duration === 0 ? 1000 : 0;
            currentChart.update();
        }}
        
        function exportChart() {{
            const link = document.createElement('a');
            link.download = 'chart.png';
            link.href = currentChart.toBase64Image();
            link.click();
        }}
        
        function updateTable() {{
            const tableBody = document.getElementById('tableBody');
            tableBody.innerHTML = '';
            
            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
            
            data.labels.forEach((label, index) => {{
                const value = data.datasets[0].data[index];
                const percentage = ((value / total) * 100).toFixed(1);
                
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = label;
                row.insertCell(1).textContent = value;
                row.insertCell(2).textContent = percentage + '%';
            }});
        }}
        
        // Inicializar o gráfico
        createChart();
    </script>
</body>
</html>"""
    
    def _generate_interface_html(self, user_input: str, hmp_result: Dict) -> str:
        """Gera HTML completo para interface."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interface Interativa</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .app-container {{ 
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav {{ 
            background: #f8fafc;
            padding: 15px 30px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .nav-items {{ 
            display: flex;
            gap: 20px;
        }}
        .nav-item {{ 
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .nav-item.active {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        .content {{ 
            padding: 30px;
            min-height: 400px;
        }}
        .card {{ 
            background: #f8fafc;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border: 1px solid #e2e8f0;
            transition: transform 0.3s ease;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .grid {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        button {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        button:hover {{ transform: translateY(-2px); }}
        input, textarea, select {{ 
            width: 100%;
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            margin: 8px 0;
        }}
        .modal {{ 
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }}
        .modal-content {{ 
            background: white;
            margin: 5% auto;
            padding: 30px;
            width: 80%;
            max-width: 600px;
            border-radius: 15px;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1>Interface Interativa</h1>
            <div>
                <button onclick="showModal()">⚙️ Configurações</button>
                <button onclick="exportData()">📊 Exportar</button>
            </div>
        </div>
        
        <div class="nav">
            <div class="nav-items">
                <div class="nav-item active" onclick="showSection('dashboard')">📊 Dashboard</div>
                <div class="nav-item" onclick="showSection('data')">📋 Dados</div>
                <div class="nav-item" onclick="showSection('settings')">⚙️ Configurações</div>
            </div>
        </div>
        
        <div class="content">
            <div id="dashboard-section">
                <h2>Dashboard</h2>
                <p>Baseado em: {user_input}</p>
                
                <div class="grid">
                    <div class="card">
                        <h3>📈 Métricas</h3>
                        <p>Visualização de dados em tempo real</p>
                        <button onclick="refreshMetrics()">Atualizar</button>
                    </div>
                    <div class="card">
                        <h3>👥 Usuários</h3>
                        <p>Gestão de usuários ativos</p>
                        <button onclick="manageUsers()">Gerenciar</button>
                    </div>
                    <div class="card">
                        <h3>⚡ Performance</h3>
                        <p>Monitoramento de performance</p>
                        <button onclick="checkPerformance()">Verificar</button>
                    </div>
                </div>
            </div>
            
            <div id="data-section" style="display: none;">
                <h2>Dados</h2>
                <div class="card">
                    <input type="text" placeholder="Buscar dados..." onkeyup="searchData(this.value)">
                    <table style="width: 100%; margin-top: 15px;">
                        <thead>
                            <tr style="background: #f8fafc;">
                                <th>ID</th>
                                <th>Nome</th>
                                <th>Status</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody id="dataTable">
                            <tr><td>001</td><td>Item 1</td><td>Ativo</td><td><button>Editar</button></td></tr>
                            <tr><td>002</td><td>Item 2</td><td>Inativo</td><td><button>Editar</button></td></tr>
                            <tr><td>003</td><td>Item 3</td><td>Ativo</td><td><button>Editar</button></td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="settings-section" style="display: none;">
                <h2>Configurações</h2>
                <div class="card">
                    <h3>Preferências</h3>
                    <label>Tema:</label>
                    <select onchange="changeTheme(this.value)">
                        <option value="light">Claro</option>
                        <option value="dark">Escuro</option>
                    </select>
                    
                    <label>Notificações:</label>
                    <input type="checkbox" checked> Ativar notificações
                    
                    <button onclick="saveSettings()">Salvar Configurações</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <h2>Configurações Avançadas</h2>
            <p>Configure suas preferências avançadas aqui.</p>
            <button onclick="closeModal()">Fechar</button>
        </div>
    </div>
    
    <script>
        function showSection(section) {{
            // Esconder todas as seções
            document.getElementById('dashboard-section').style.display = 'none';
            document.getElementById('data-section').style.display = 'none';
            document.getElementById('settings-section').style.display = 'none';
            
            // Mostrar seção selecionada
            document.getElementById(section + '-section').style.display = 'block';
            
            // Atualizar navegação
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.remove('active');
            }});
            event.target.classList.add('active');
        }}
        
        function showModal() {{
            document.getElementById('modal').style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('modal').style.display = 'none';
        }}
        
        function refreshMetrics() {{
            alert('Métricas atualizadas!');
        }}
        
        function manageUsers() {{
            alert('Abrindo gerenciamento de usuários...');
        }}
        
        function checkPerformance() {{
            alert('Performance: Excelente!');
        }}
        
        function searchData(query) {{
            const rows = document.querySelectorAll('#dataTable tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
            }});
        }}
        
        function changeTheme(theme) {{
            if (theme === 'dark') {{
                document.body.style.background = 'linear-gradient(135deg, #2c3e50, #34495e)';
            }} else {{
                document.body.style.background = 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)';
            }}
        }}
        
        function saveSettings() {{
            alert('Configurações salvas!');
        }}
        
        function exportData() {{
            alert('Exportando dados...');
        }}
        
        // Fechar modal clicando fora
        window.onclick = function(event) {{
            const modal = document.getElementById('modal');
            if (event.target === modal) {{
                modal.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>"""
    
    def _generate_form_html(self, user_input: str, hmp_result: Dict) -> str:
        """Gera HTML completo para formulário."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulário Interativo</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .form-container {{ 
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }}
        .form-group {{ 
            margin-bottom: 20px;
        }}
        label {{ 
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #374151;
        }}
        input, textarea, select {{ 
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }}
        input:focus, textarea:focus, select:focus {{ 
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        .error {{ 
            color: #ef4444;
            font-size: 14px;
            margin-top: 5px;
        }}
        .success {{ 
            color: #10b981;
            font-size: 14px;
            margin-top: 5px;
        }}
        button {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }}
        button:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }}
        .progress-bar {{ 
            width: 100%;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            margin-bottom: 30px;
            overflow: hidden;
        }}
        .progress-fill {{ 
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }}
        .step-indicator {{ 
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .step {{ 
            flex: 1;
            text-align: center;
            padding: 10px;
            background: #f8fafc;
            margin: 0 5px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        .step.active {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>Formulário Interativo</h1>
        <p>Baseado em: {user_input}</p>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        
        <div class="step-indicator">
            <div class="step active">1. Dados Pessoais</div>
            <div class="step">2. Informações</div>
            <div class="step">3. Confirmação</div>
        </div>
        
        <form id="dynamicForm">
            <div id="step1" class="form-step">
                <div class="form-group">
                    <label for="name">Nome Completo *</label>
                    <input type="text" id="name" name="name" required>
                    <div class="error" id="nameError"></div>
                </div>
                
                <div class="form-group">
                    <label for="email">E-mail *</label>
                    <input type="email" id="email" name="email" required>
                    <div class="error" id="emailError"></div>
                </div>
                
                <div class="form-group">
                    <label for="phone">Telefone</label>
                    <input type="tel" id="phone" name="phone">
                </div>
                
                <button type="button" onclick="nextStep(2)">Próximo →</button>
            </div>
            
            <div id="step2" class="form-step" style="display: none;">
                <div class="form-group">
                    <label for="company">Empresa</label>
                    <input type="text" id="company" name="company">
                </div>
                
                <div class="form-group">
                    <label for="position">Cargo</label>
                    <input type="text" id="position" name="position">
                </div>
                
                <div class="form-group">
                    <label for="message">Mensagem</label>
                    <textarea id="message" name="message" rows="4"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button type="button" onclick="prevStep(1)" style="width: 50%; background: #6b7280;">← Anterior</button>
                    <button type="button" onclick="nextStep(3)" style="width: 50%;">Próximo →</button>
                </div>
            </div>
            
            <div id="step3" class="form-step" style="display: none;">
                <h3>Confirmação dos Dados</h3>
                <div id="confirmationData"></div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="terms" required>
                        Aceito os termos e condições *
                    </label>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button type="button" onclick="prevStep(2)" style="width: 50%; background: #6b7280;">← Anterior</button>
                    <button type="submit" style="width: 50%;">Enviar ✓</button>
                </div>
            </div>
        </form>
    </div>
    
    <script>
        let currentStep = 1;
        
        function nextStep(step) {{
            if (validateCurrentStep()) {{
                document.getElementById('step' + currentStep).style.display = 'none';
                document.getElementById('step' + step).style.display = 'block';
                
                // Atualizar indicadores
                document.querySelectorAll('.step').forEach((el, index) => {{
                    el.classList.toggle('active', index < step);
                }});
                
                currentStep = step;
                updateProgress();
                
                if (step === 3) {{
                    showConfirmation();
                }}
            }}
        }}
        
        function prevStep(step) {{
            document.getElementById('step' + currentStep).style.display = 'none';
            document.getElementById('step' + step).style.display = 'block';
            
            // Atualizar indicadores
            document.querySelectorAll('.step').forEach((el, index) => {{
                el.classList.toggle('active', index < step);
            }});
            
            currentStep = step;
            updateProgress();
        }}
        
        function validateCurrentStep() {{
            let isValid = true;
            
            if (currentStep === 1) {{
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                
                if (!name.trim()) {{
                    showError('nameError', 'Nome é obrigatório');
                    isValid = false;
                }} else {{
                    clearError('nameError');
                }}
                
                if (!email.trim()) {{
                    showError('emailError', 'E-mail é obrigatório');
                    isValid = false;
                }} else if (!isValidEmail(email)) {{
                    showError('emailError', 'E-mail inválido');
                    isValid = false;
                }} else {{
                    clearError('emailError');
                }}
            }}
            
            return isValid;
        }}
        
        function showError(elementId, message) {{
            document.getElementById(elementId).textContent = message;
        }}
        
        function clearError(elementId) {{
            document.getElementById(elementId).textContent = '';
        }}
        
        function isValidEmail(email) {{
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }}
        
        function updateProgress() {{
            const progress = (currentStep / 3) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }}
        
        function showConfirmation() {{
            const formData = new FormData(document.getElementById('dynamicForm'));
            let confirmationHtml = '<div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">';
            
            for (let [key, value] of formData.entries()) {{
                if (value && key !== 'terms') {{
                    confirmationHtml += `<p><strong>${{getFieldLabel(key)}}:</strong> ${{value}}</p>`;
                }}
            }}
            
            confirmationHtml += '</div>';
            document.getElementById('confirmationData').innerHTML = confirmationHtml;
        }}
        
        function getFieldLabel(fieldName) {{
            const labels = {{
                'name': 'Nome',
                'email': 'E-mail',
                'phone': 'Telefone',
                'company': 'Empresa',
                'position': 'Cargo',
                'message': 'Mensagem'
            }};
            return labels[fieldName] || fieldName;
        }}
        
        document.getElementById('dynamicForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            if (!document.getElementById('terms').checked) {{
                alert('Você deve aceitar os termos e condições');
                return;
            }}
            
            // Simular envio
            alert('Formulário enviado com sucesso!');
        }});
        
        // Validação em tempo real
        document.getElementById('email').addEventListener('input', function() {{
            if (this.value && !isValidEmail(this.value)) {{
                showError('emailError', 'E-mail inválido');
            }} else {{
                clearError('emailError');
            }}
        }});
        
        // Máscara para telefone
        document.getElementById('phone').addEventListener('input', function() {{
            let value = this.value.replace(/\\D/g, '');
            value = value.replace(/(\\d{{{{2}}}})(\\d)/, '($1) $2');
            value = value.replace(/(\\d{{{{5}}}})(\\d)/, '$1-$2');
            this.value = value;
        }});
    </script>
</body>
</html>"""
    
    def _generate_generic_html(self, user_input: str, hmp_result: Dict) -> str:
        """Gera HTML genérico interativo."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artefato Interativo</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }}
        .content {{ 
            line-height: 1.6;
            color: #374151;
        }}
        .interactive-section {{ 
            background: #f8fafc;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #e2e8f0;
        }}
        button {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Artefato Interativo</h1>
        <p><strong>Baseado em:</strong> {user_input}</p>
        
        <div class="content">
            <div class="interactive-section">
                <h3>🎯 Conteúdo Principal</h3>
                <p>Este artefato foi gerado automaticamente baseado na sua solicitação. Ele contém funcionalidades interativas para melhor experiência do usuário.</p>
                
                <button onclick="showDetails()">📋 Ver Detalhes</button>
                <button onclick="toggleMode()">🌓 Alternar Modo</button>
                <button onclick="exportContent()">💾 Exportar</button>
            </div>
            
            <div id="details" style="display: none;" class="interactive-section">
                <h3>📊 Detalhes Expandidos</h3>
                <p>Informações adicionais sobre o artefato:</p>
                <ul>
                    <li>Criado automaticamente pelo sistema HMP</li>
                    <li>Interface responsiva e interativa</li>
                    <li>Funcionalidades de exportação</li>
                    <li>Compatível com dispositivos móveis</li>
                </ul>
            </div>
            
            <div class="interactive-section">
                <h3>⚙️ Configurações</h3>
                <label>Tema: </label>
                <select onchange="changeTheme(this.value)">
                    <option value="light">Claro</option>
                    <option value="dark">Escuro</option>
                </select>
                
                <br><br>
                <label>Tamanho da fonte: </label>
                <input type="range" min="12" max="24" value="16" onchange="changeFontSize(this.value)">
            </div>
        </div>
    </div>
    
    <script>
        function showDetails() {{
            const details = document.getElementById('details');
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }}
        
        function toggleMode() {{
            document.body.classList.toggle('dark-mode');
        }}
        
        function exportContent() {{
            const content = document.querySelector('.container').innerHTML;
            const blob = new Blob([content], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'artefato.html';
            a.click();
        }}
        
        function changeTheme(theme) {{
            if (theme === 'dark') {{
                document.body.style.background = 'linear-gradient(135deg, #2c3e50, #34495e)';
                document.querySelector('.container').style.background = '#1a202c';
                document.querySelector('.container').style.color = 'white';
            }} else {{
                document.body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                document.querySelector('.container').style.background = 'white';
                document.querySelector('.container').style.color = 'black';
            }}
        }}
        
        function changeFontSize(size) {{
            document.querySelector('.content').style.fontSize = size + 'px';
        }}
    </script>
</body>
</html>"""
    
    def _load_artifact_templates(self) -> Dict[str, str]:
        """Carrega templates pré-definidos para artefatos."""
        return {
            "dashboard": "template_dashboard",
            "form": "template_form",
            "visualization": "template_viz",
            "interface": "template_interface"
        }
