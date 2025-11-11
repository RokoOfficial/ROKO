
"""
Templates profissionais para diferentes tipos de visualizações.
Cada template é uma obra de arte funcional e responsiva.
"""

class VisualizationTemplates:
    
    @staticmethod
    def get_financial_dashboard(data):
        """Dashboard financeiro profissional com gráficos em tempo real."""
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Financeiro Profissional</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
            color: #ffffff;
        }}
        
        .dashboard {{
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .crypto-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .crypto-card {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .crypto-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .crypto-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
        }}
        
        .crypto-name {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        
        .crypto-icon {{
            width: 40px;
            height: 40px;
            margin-right: 15px;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #1e3c72;
        }}
        
        .crypto-price {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            color: #ffd700;
        }}
        
        .crypto-change {{
            font-size: 1.2rem;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 12px;
            display: inline-block;
        }}
        
        .positive {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
        .negative {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        
        .chart-section {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
            border-radius: 20px;
            padding: 40px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 30px;
        }}
        
        .chart-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        .pulse {{ animation: pulse 2s infinite; }}
        
        @keyframes slideInUp {{
            from {{
                opacity: 0;
                transform: translateY(50px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .animate-slide {{ animation: slideInUp 0.8s ease-out; }}
        
        @media (max-width: 768px) {{
            .dashboard {{ padding: 20px; }}
            .crypto-grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 2rem; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard animate-slide">
        <div class="header">
            <h1><i class="fas fa-coins"></i> Dashboard Criptomoedas</h1>
            <p>Análise em Tempo Real - Top 5 Performances</p>
        </div>
        
        <div class="crypto-grid">
            {self._generate_crypto_cards(data)}
        </div>
        
        <div class="chart-section">
            <h3 class="chart-title"><i class="fas fa-chart-line"></i> Comparativo de Performance 24h</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
    </div>

    <script>
        // Dados das criptomoedas
        const cryptoData = {data};
        
        // Configuração do gráfico
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        const gradient1 = ctx.createLinearGradient(0, 0, 0, 400);
        gradient1.addColorStop(0, 'rgba(255, 215, 0, 0.8)');
        gradient1.addColorStop(1, 'rgba(255, 215, 0, 0.1)');
        
        const gradient2 = ctx.createLinearGradient(0, 0, 0, 400);
        gradient2.addColorStop(0, 'rgba(34, 197, 94, 0.8)');
        gradient2.addColorStop(1, 'rgba(34, 197, 94, 0.1)');
        
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: cryptoData.map(crypto => crypto.name),
                datasets: [{{
                    label: 'Variação 24h (%)',
                    data: cryptoData.map(crypto => crypto.change_24h),
                    backgroundColor: cryptoData.map(crypto => 
                        crypto.change_24h > 0 ? gradient2 : 'rgba(239, 68, 68, 0.8)'
                    ),
                    borderColor: cryptoData.map(crypto => 
                        crypto.change_24h > 0 ? '#22c55e' : '#ef4444'
                    ),
                    borderWidth: 2,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: '#ffd700',
                        borderWidth: 1,
                        cornerRadius: 12
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: 'white', font: {{ family: 'Inter', size: 14 }} }}
                    }},
                    y: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: 'white', font: {{ family: 'Inter', size: 14 }} }}
                    }}
                }},
                animation: {{
                    duration: 2000,
                    easing: 'easeOutBounce'
                }}
            }}
        }});
        
        // Efeito de atualização em tempo real simulado
        setInterval(() => {{
            document.querySelectorAll('.crypto-price').forEach(price => {{
                price.classList.add('pulse');
                setTimeout(() => price.classList.remove('pulse'), 1000);
            }});
        }}, 5000);
    </script>
</body>
</html>"""
    
    @staticmethod
    def _generate_crypto_cards(data):
        """Gera cards para cada criptomoeda."""
        cards = ""
        for crypto in data:
            change_class = "positive" if crypto['change_24h'] > 0 else "negative"
            change_icon = "fa-arrow-up" if crypto['change_24h'] > 0 else "fa-arrow-down"
            
            cards += f"""
            <div class="crypto-card">
                <div class="crypto-name">
                    <div class="crypto-icon">{crypto['name'][0]}</div>
                    {crypto['name']}
                </div>
                <div class="crypto-price">${crypto['price']:,.2f}</div>
                <div class="crypto-change {change_class}">
                    <i class="fas {change_icon}"></i> {abs(crypto['change_24h']):.2f}%
                </div>
            </div>
            """
        return cards
    
    @staticmethod
    def get_data_table_professional(data, title="Dados Profissionais"):
        """Tabela de dados profissional e interativa."""
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 30px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #e2e8f0;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        
        .table-container {{
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }}
        
        td {{
            padding: 20px;
            border-bottom: 1px solid #f1f5f9;
            transition: all 0.3s ease;
        }}
        
        tr:hover {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            transform: scale(1.01);
        }}
        
        .number {{
            font-weight: 600;
            color: #1e293b;
        }}
        
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
        
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .badge-success {{ background: #dcfce7; color: #15803d; }}
        .badge-warning {{ background: #fef3c7; color: #d97706; }}
        .badge-danger {{ background: #fee2e2; color: #dc2626; }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .animate-in {{ animation: slideIn 0.6s ease-out; }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 20px; }}
            table {{ font-size: 0.9rem; }}
            th, td {{ padding: 15px 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container animate-in">
        <div class="header">
            <h1><i class="fas fa-table"></i> {title}</h1>
            <p>Dados organizados de forma profissional e interativa</p>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th><i class="fas fa-coins"></i> Criptomoeda</th>
                        <th><i class="fas fa-dollar-sign"></i> Preço (USD)</th>
                        <th><i class="fas fa-chart-line"></i> Variação 24h</th>
                        <th><i class="fas fa-volume-up"></i> Volume 24h</th>
                        <th><i class="fas fa-crown"></i> Market Cap</th>
                    </tr>
                </thead>
                <tbody>
                    {VisualizationTemplates._generate_table_rows(data)}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    
    @staticmethod
    def _generate_table_rows(data):
        """Gera linhas da tabela com formatação profissional."""
        rows = ""
        for crypto in data:
            change_class = "positive" if crypto['change_24h'] > 0 else "negative"
            change_icon = "fa-arrow-up" if crypto['change_24h'] > 0 else "fa-arrow-down"
            
            volume = f"${crypto['volume_24h']:,}" if crypto.get('volume_24h') else "N/A"
            market_cap = f"${crypto['market_cap']:,}" if crypto.get('market_cap') else "N/A"
            
            rows += f"""
            <tr>
                <td><strong>{crypto['name']}</strong></td>
                <td class="number">${crypto['price']:,.2f}</td>
                <td class="number {change_class}">
                    <i class="fas {change_icon}"></i> {abs(crypto['change_24h']):.2f}%
                </td>
                <td class="number">{volume}</td>
                <td class="number">{market_cap}</td>
            </tr>
            """
        return rows
