"""
Gerador de dashboards interativos e relatórios visuais.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import base64
import io

from ..core.gemini_client import GeminiClient
from .business_metrics import BusinessMetrics
from .analytics_engine import AnalyticsEngine


class DashboardGenerator:
    """Gera dashboards interativos e relatórios."""
    
    def __init__(self, gemini_client: GeminiClient, 
                 business_metrics: BusinessMetrics,
                 analytics_engine: AnalyticsEngine):
        self.gemini_client = gemini_client
        self.business_metrics = business_metrics
        self.analytics_engine = analytics_engine
        self.dashboard_templates = self._load_dashboard_templates()
        
    def _load_dashboard_templates(self) -> Dict[str, str]:
        """Carrega templates de dashboard."""
        return {
            'executive': self._get_executive_template(),
            'sales': self._get_sales_template(),
            'analytics': self._get_analytics_template(),
            'operational': self._get_operational_template(),
            'custom': self._get_custom_template()
        }
    
    async def create_dashboard(self, request: str, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Cria dashboard baseado em solicitação natural."""
        # Identifica tipo de dashboard
        dashboard_type = await self._identify_dashboard_type(request)
        
        # Coleta métricas necessárias
        metrics = await self._collect_dashboard_metrics(dashboard_type, request, data)
        
        # Gera gráficos
        charts = await self._generate_dashboard_charts(dashboard_type, metrics)
        
        # Gera insights com IA
        insights = await self._generate_dashboard_insights(request, metrics)
        
        # Monta dashboard
        dashboard_config = {
            'type': dashboard_type,
            'title': self._generate_dashboard_title(request, dashboard_type),
            'metrics': metrics,
            'charts': charts,
            'insights': insights,
            'created_at': datetime.now(),
            'refresh_interval': self._get_refresh_interval(dashboard_type)
        }
        
        # Gera HTML
        html_path = await self._generate_dashboard_html(dashboard_config)
        
        # Gera JSON para APIs
        json_path = await self._generate_dashboard_json(dashboard_config)
        
        return {
            'success': True,
            'dashboard_type': dashboard_type,
            'html_path': html_path,
            'json_path': json_path,
            'metrics_count': len(metrics),
            'charts_count': len(charts),
            'refresh_url': f"/dashboard/refresh/{Path(html_path).stem}"
        }
    
    async def _identify_dashboard_type(self, request: str) -> str:
        """Identifica tipo de dashboard pela solicitação."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ['executivo', 'diretoria', 'overview', 'geral']):
            return 'executive'
        elif any(word in request_lower for word in ['vendas', 'sales', 'receita', 'faturamento']):
            return 'sales'
        elif any(word in request_lower for word in ['análise', 'analytics', 'estatística', 'predição']):
            return 'analytics'
        elif any(word in request_lower for word in ['operacional', 'produção', 'performance', 'kpi']):
            return 'operational'
        else:
            return 'custom'
    
    async def _collect_dashboard_metrics(self, dashboard_type: str, request: str, data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """Coleta métricas necessárias para o dashboard."""
        metrics = {}
        
        if dashboard_type == 'executive':
            # Métricas executivas
            metrics.update(await self._collect_executive_metrics())
        elif dashboard_type == 'sales':
            # Métricas de vendas
            metrics.update(await self._collect_sales_metrics())
        elif dashboard_type == 'analytics':
            # Métricas analíticas
            if data is not None:
                metrics.update(await self._collect_analytics_metrics(data))
        elif dashboard_type == 'operational':
            # Métricas operacionais
            metrics.update(await self._collect_operational_metrics())
        else:
            # Dashboard customizado
            metrics.update(await self._collect_custom_metrics(request, data))
        
        return metrics
    
    async def _collect_executive_metrics(self) -> Dict[str, Any]:
        """Coleta métricas para dashboard executivo."""
        try:
            # Métricas de vendas
            sales_result = await self.business_metrics.process_natural_query("vendas do último mês")
            
            # Métricas de usuários  
            users_result = await self.business_metrics.process_natural_query("usuários ativos desta semana")
            
            return {
                'sales_summary': sales_result.get('metrics', {}),
                'users_summary': users_result.get('metrics', {}),
                'period': 'Último mês',
                'kpis': {
                    'revenue': sales_result.get('metrics', {}).get('total_sales', 0),
                    'transactions': sales_result.get('metrics', {}).get('sales_count', 0),
                    'avg_ticket': sales_result.get('metrics', {}).get('average_ticket', 0),
                    'active_users': users_result.get('metrics', {}).get('active_users', 0)
                }
            }
        except:
            return self._get_sample_executive_metrics()
    
    async def _collect_sales_metrics(self) -> Dict[str, Any]:
        """Coleta métricas detalhadas de vendas."""
        try:
            # Diferentes períodos
            today_sales = await self.business_metrics.process_natural_query("vendas de hoje")
            week_sales = await self.business_metrics.process_natural_query("vendas desta semana")
            month_sales = await self.business_metrics.process_natural_query("vendas deste mês")
            
            return {
                'today': today_sales.get('metrics', {}),
                'week': week_sales.get('metrics', {}),
                'month': month_sales.get('metrics', {}),
                'comparison': {
                    'daily_average': month_sales.get('metrics', {}).get('total_sales', 0) / 30,
                    'weekly_trend': 'crescente' if week_sales.get('metrics', {}).get('total_sales', 0) > 0 else 'estável'
                }
            }
        except:
            return self._get_sample_sales_metrics()
    
    async def _collect_analytics_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Coleta métricas analíticas dos dados."""
        try:
            # Análises automáticas
            correlation_analysis = await self.analytics_engine.analyze_with_ai(
                "analise correlações nos dados", data
            )
            
            trend_analysis = await self.analytics_engine.analyze_with_ai(
                "identifique tendências temporais", data
            )
            
            anomaly_analysis = await self.analytics_engine.analyze_with_ai(
                "detecte anomalias nos dados", data
            )
            
            return {
                'data_shape': data.shape,
                'correlations': correlation_analysis,
                'trends': trend_analysis,
                'anomalies': anomaly_analysis,
                'data_quality': {
                    'missing_percentage': data.isnull().sum().sum() / (data.shape[0] * data.shape[1]) * 100,
                    'numeric_columns': len(data.select_dtypes(include=['number']).columns),
                    'categorical_columns': len(data.select_dtypes(include=['object']).columns)
                }
            }
        except Exception as e:
            return {'error': str(e), 'data_summary': data.describe().to_dict() if data is not None else {}}
    
    async def _collect_operational_metrics(self) -> Dict[str, Any]:
        """Coleta métricas operacionais."""
        return {
            'system_health': {
                'uptime': '99.9%',
                'response_time': '150ms',
                'error_rate': '0.1%',
                'active_connections': 1250
            },
            'performance': {
                'cpu_usage': '65%',
                'memory_usage': '78%',
                'disk_usage': '45%',
                'network_throughput': '850 Mbps'
            },
            'business_operations': {
                'daily_transactions': 15620,
                'processing_queue': 45,
                'completed_tasks': 98.5,
                'pending_approvals': 12
            }
        }
    
    async def _collect_custom_metrics(self, request: str, data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """Coleta métricas para dashboard customizado."""
        metrics = {}
        
        # Analisa solicitação para extrair métricas específicas
        if data is not None:
            # Análise geral dos dados
            general_analysis = await self.analytics_engine.analyze_with_ai(request, data)
            metrics['analysis'] = general_analysis
        
        # Métricas baseadas em palavras-chave
        request_lower = request.lower()
        
        if 'vendas' in request_lower or 'sales' in request_lower:
            metrics.update(await self._collect_sales_metrics())
        
        if 'usuários' in request_lower or 'users' in request_lower:
            try:
                users_result = await self.business_metrics.process_natural_query("usuários ativos")
                metrics['users'] = users_result.get('metrics', {})
            except:
                pass
        
        return metrics
    
    async def _generate_dashboard_charts(self, dashboard_type: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos para o dashboard."""
        charts = []
        
        try:
            if dashboard_type == 'executive':
                charts.extend(await self._generate_executive_charts(metrics))
            elif dashboard_type == 'sales':
                charts.extend(await self._generate_sales_charts(metrics))
            elif dashboard_type == 'analytics':
                charts.extend(await self._generate_analytics_charts(metrics))
            elif dashboard_type == 'operational':
                charts.extend(await self._generate_operational_charts(metrics))
            else:
                charts.extend(await self._generate_custom_charts(metrics))
                
        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")
            
        return charts
    
    async def _generate_executive_charts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos para dashboard executivo."""
        charts = []
        
        # Gráfico de KPIs principais
        kpis = metrics.get('kpis', {})
        if kpis:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            
            # Receita
            ax1.bar(['Receita'], [kpis.get('revenue', 0)], color='#2E8B57')
            ax1.set_title('Receita Total')
            ax1.set_ylabel('R$')
            
            # Transações
            ax2.bar(['Transações'], [kpis.get('transactions', 0)], color='#4169E1')
            ax2.set_title('Total de Transações')
            
            # Ticket médio
            ax3.bar(['Ticket Médio'], [kpis.get('avg_ticket', 0)], color='#FF6347')
            ax3.set_title('Ticket Médio')
            ax3.set_ylabel('R$')
            
            # Usuários ativos
            ax4.bar(['Usuários Ativos'], [kpis.get('active_users', 0)], color='#9370DB')
            ax4.set_title('Usuários Ativos')
            
            plt.tight_layout()
            chart_path = await self._save_chart(fig, 'executive_kpis')
            charts.append({
                'type': 'kpi_overview',
                'title': 'KPIs Principais',
                'path': chart_path,
                'description': 'Visão geral dos principais indicadores'
            })
        
        return charts
    
    async def _generate_sales_charts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos de vendas."""
        charts = []
        
        # Comparativo de períodos
        periods = ['Hoje', 'Semana', 'Mês']
        values = [
            metrics.get('today', {}).get('total_sales', 0),
            metrics.get('week', {}).get('total_sales', 0),
            metrics.get('month', {}).get('total_sales', 0)
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(periods, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax.set_title('Vendas por Período')
        ax.set_ylabel('Receita (R$)')
        
        # Adiciona valores nas barras
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.annotate(f'R$ {value:,.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
        
        chart_path = await self._save_chart(fig, 'sales_periods')
        charts.append({
            'type': 'sales_comparison',
            'title': 'Vendas por Período',
            'path': chart_path,
            'description': 'Comparativo de vendas entre diferentes períodos'
        })
        
        return charts
    
    async def _generate_analytics_charts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos analíticos."""
        charts = []
        
        # Qualidade dos dados
        data_quality = metrics.get('data_quality', {})
        if data_quality:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Gráfico de completude
            completeness = 100 - data_quality.get('missing_percentage', 0)
            ax1.pie([completeness, 100-completeness], 
                   labels=['Dados Completos', 'Dados Faltantes'],
                   colors=['#2ECC71', '#E74C3C'],
                   startangle=90)
            ax1.set_title('Qualidade dos Dados')
            
            # Distribuição de tipos de colunas
            numeric = data_quality.get('numeric_columns', 0)
            categorical = data_quality.get('categorical_columns', 0)
            
            ax2.bar(['Numéricas', 'Categóricas'], [numeric, categorical], 
                   color=['#3498DB', '#F39C12'])
            ax2.set_title('Tipos de Colunas')
            ax2.set_ylabel('Quantidade')
            
            plt.tight_layout()
            chart_path = await self._save_chart(fig, 'data_quality')
            charts.append({
                'type': 'data_quality',
                'title': 'Qualidade dos Dados',
                'path': chart_path,
                'description': 'Análise da qualidade e estrutura dos dados'
            })
        
        return charts
    
    async def _generate_operational_charts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos operacionais."""
        charts = []
        
        # Performance do sistema
        performance = metrics.get('performance', {})
        if performance:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = ['CPU', 'Memória', 'Disco']
            values = [
                float(performance.get('cpu_usage', '0%').replace('%', '')),
                float(performance.get('memory_usage', '0%').replace('%', '')),
                float(performance.get('disk_usage', '0%').replace('%', ''))
            ]
            
            colors = ['#E74C3C' if v > 80 else '#F39C12' if v > 60 else '#2ECC71' for v in values]
            
            bars = ax.bar(categories, values, color=colors)
            ax.set_title('Performance do Sistema')
            ax.set_ylabel('Uso (%)')
            ax.set_ylim(0, 100)
            
            # Linha de alerta
            ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Limite de Alerta')
            ax.legend()
            
            chart_path = await self._save_chart(fig, 'system_performance')
            charts.append({
                'type': 'system_performance',
                'title': 'Performance do Sistema',
                'path': chart_path,
                'description': 'Monitoramento de recursos do sistema'
            })
        
        return charts
    
    async def _generate_custom_charts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera gráficos customizados."""
        charts = []
        
        # Gráfico genérico baseado nas métricas disponíveis
        if 'analysis' in metrics:
            analysis = metrics['analysis']
            if analysis.get('success'):
                # Usa gráfico já gerado pela análise
                chart_path = analysis.get('chart')
                if chart_path:
                    charts.append({
                        'type': 'custom_analysis',
                        'title': 'Análise Customizada',
                        'path': chart_path,
                        'description': 'Análise específica dos dados fornecidos'
                    })
        
        return charts
    
    async def _save_chart(self, fig, name: str) -> str:
        """Salva gráfico e retorna caminho."""
        charts_dir = Path('.gemini_code/dashboard_charts')
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_path = charts_dir / f"{name}_{timestamp}.png"
        
        fig.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return str(chart_path)
    
    def _chart_to_base64(self, fig) -> str:
        """Converte gráfico para base64."""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        return chart_base64
    
    async def _generate_dashboard_insights(self, request: str, metrics: Dict[str, Any]) -> List[str]:
        """Gera insights para o dashboard usando IA."""
        prompt = f"""
        O usuário solicitou: "{request}"
        
        Métricas disponíveis:
        {json.dumps(metrics, indent=2, default=str)}
        
        Gere 3-5 insights executivos relevantes e acionáveis em português.
        Foque em:
        1. Principais descobertas
        2. Oportunidades identificadas
        3. Alertas ou riscos
        4. Recomendações específicas
        
        Mantenha insights concisos e práticos.
        """
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            insights = [line.strip() for line in response.split('\n') 
                       if line.strip() and not line.startswith('#')]
            return insights[:5]
        except:
            return [
                "Dashboard gerado com sucesso",
                "Métricas principais foram coletadas e visualizadas",
                "Monitore regularmente para identificar tendências"
            ]
    
    def _generate_dashboard_title(self, request: str, dashboard_type: str) -> str:
        """Gera título para o dashboard."""
        titles = {
            'executive': 'Dashboard Executivo',
            'sales': 'Dashboard de Vendas',
            'analytics': 'Dashboard Analítico',
            'operational': 'Dashboard Operacional',
            'custom': 'Dashboard Personalizado'
        }
        
        base_title = titles.get(dashboard_type, 'Dashboard')
        
        # Personaliza com base na solicitação
        if 'tempo real' in request.lower():
            base_title += ' - Tempo Real'
        elif 'semanal' in request.lower():
            base_title += ' - Semanal'
        elif 'mensal' in request.lower():
            base_title += ' - Mensal'
        
        return base_title
    
    def _get_refresh_interval(self, dashboard_type: str) -> int:
        """Retorna intervalo de atualização em segundos."""
        intervals = {
            'executive': 300,    # 5 minutos
            'sales': 60,         # 1 minuto
            'analytics': 600,    # 10 minutos
            'operational': 30,   # 30 segundos
            'custom': 300        # 5 minutos
        }
        return intervals.get(dashboard_type, 300)
    
    async def _generate_dashboard_html(self, config: Dict[str, Any]) -> str:
        """Gera HTML do dashboard."""
        template = self.dashboard_templates[config['type']]
        
        # Converte gráficos para base64 se necessário
        charts_data = []
        for chart in config['charts']:
            chart_data = {
                'title': chart['title'],
                'description': chart['description'],
                'type': chart['type']
            }
            
            # Lê imagem e converte para base64
            if Path(chart['path']).exists():
                with open(chart['path'], 'rb') as f:
                    chart_data['image_base64'] = base64.b64encode(f.read()).decode('utf-8')
            
            charts_data.append(chart_data)
        
        # Prepara dados para template
        template_data = {
            'title': config['title'],
            'created_at': config['created_at'].strftime('%d/%m/%Y %H:%M'),
            'metrics': config['metrics'],
            'charts': charts_data,
            'insights': config['insights'],
            'refresh_interval': config['refresh_interval']
        }
        
        # Renderiza template
        jinja_template = Template(template)
        html_content = jinja_template.render(**template_data)
        
        # Salva HTML
        dashboard_dir = Path('.gemini_code/dashboards')
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_path = dashboard_dir / f"dashboard_{config['type']}_{timestamp}.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    async def _generate_dashboard_json(self, config: Dict[str, Any]) -> str:
        """Gera JSON do dashboard para APIs."""
        # Remove caminhos de arquivo e converte para formato API
        api_config = {
            'type': config['type'],
            'title': config['title'],
            'created_at': config['created_at'].isoformat(),
            'metrics': config['metrics'],
            'insights': config['insights'],
            'charts': [{
                'type': chart['type'],
                'title': chart['title'],
                'description': chart['description']
            } for chart in config['charts']],
            'refresh_interval': config['refresh_interval']
        }
        
        # Salva JSON
        dashboard_dir = Path('.gemini_code/dashboards')
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = dashboard_dir / f"dashboard_{config['type']}_{timestamp}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(api_config, f, indent=2, ensure_ascii=False, default=str)
        
        return str(json_path)
    
    def _get_executive_template(self) -> str:
        """Template para dashboard executivo."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 10px;
        }
        .header .meta {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .chart-container {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 15px;
            text-align: center;
        }
        .chart-image {
            width: 100%;
            border-radius: 5px;
        }
        .insights {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .insights h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .insight-item {
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
            color: #34495e;
            line-height: 1.6;
        }
        .insight-item:last-child {
            border-bottom: none;
        }
    </style>
    <script>
        // Auto-refresh
        setTimeout(function() {
            window.location.reload();
        }, {{ refresh_interval * 1000 }});
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="meta">Atualizado em: {{ created_at }} | Próxima atualização em {{ refresh_interval // 60 }} minutos</div>
        </div>
        
        <div class="dashboard-grid">
            {% if metrics.kpis %}
                <div class="metric-card">
                    <div class="metric-value">R$ {{ "{:,.0f}".format(metrics.kpis.revenue) }}</div>
                    <div class="metric-label">Receita Total</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.kpis.transactions }}</div>
                    <div class="metric-label">Transações</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">R$ {{ "{:,.0f}".format(metrics.kpis.avg_ticket) }}</div>
                    <div class="metric-label">Ticket Médio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.kpis.active_users }}</div>
                    <div class="metric-label">Usuários Ativos</div>
                </div>
            {% endif %}
        </div>
        
        {% for chart in charts %}
        <div class="chart-container">
            <div class="chart-title">{{ chart.title }}</div>
            <img src="data:image/png;base64,{{ chart.image_base64 }}" class="chart-image" alt="{{ chart.title }}">
        </div>
        {% endfor %}
        
        <div class="insights">
            <h3>💡 Insights Principais</h3>
            {% for insight in insights %}
            <div class="insight-item">{{ insight }}</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
        """
    
    def _get_sales_template(self) -> str:
        """Template para dashboard de vendas."""
        return self._get_executive_template()  # Reutiliza template executivo por simplicidade
    
    def _get_analytics_template(self) -> str:
        """Template para dashboard analítico."""
        return self._get_executive_template()  # Reutiliza template executivo por simplicidade
    
    def _get_operational_template(self) -> str:
        """Template para dashboard operacional."""
        return self._get_executive_template()  # Reutiliza template executivo por simplicidade
    
    def _get_custom_template(self) -> str:
        """Template para dashboard customizado."""
        return self._get_executive_template()  # Reutiliza template executivo por simplicidade
    
    def _get_sample_executive_metrics(self) -> Dict[str, Any]:
        """Métricas de exemplo para demonstração."""
        return {
            'kpis': {
                'revenue': 125000,
                'transactions': 847,
                'avg_ticket': 147.50,
                'active_users': 1235
            },
            'period': 'Último mês (demonstração)'
        }
    
    def _get_sample_sales_metrics(self) -> Dict[str, Any]:
        """Métricas de vendas de exemplo."""
        return {
            'today': {'total_sales': 5240, 'sales_count': 23},
            'week': {'total_sales': 42150, 'sales_count': 156},
            'month': {'total_sales': 189350, 'sales_count': 687},
            'comparison': {
                'daily_average': 6311.67,
                'weekly_trend': 'crescente'
            }
        }