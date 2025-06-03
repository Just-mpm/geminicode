"""
Sistema de métricas de negócio com linguagem natural.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importações opcionais para visualização
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    plt = None
    sns = None
    PLOTTING_AVAILABLE = False
    print("Aviso: matplotlib/seaborn não disponível. Funcionalidades de gráficos desabilitadas.")

from ..core.gemini_client import GeminiClient
from ..database.database_manager import DatabaseManager


class BusinessMetrics:
    """Gerencia métricas de negócio com comandos naturais."""
    
    def __init__(self, gemini_client: GeminiClient, db_manager: DatabaseManager):
        self.gemini_client = gemini_client
        self.db_manager = db_manager
        self.metrics_cache = {}
        
    async def process_natural_query(self, query: str) -> Dict[str, Any]:
        """Processa consulta de métricas em linguagem natural."""
        # Identifica tipo de métrica
        metric_type = await self._identify_metric_type(query)
        
        if metric_type == 'sales':
            return await self._process_sales_metrics(query)
        elif metric_type == 'users':
            return await self._process_user_metrics(query)
        elif metric_type == 'performance':
            return await self._process_performance_metrics(query)
        elif metric_type == 'growth':
            return await self._process_growth_metrics(query)
        else:
            return await self._process_generic_metrics(query)
    
    async def _identify_metric_type(self, query: str) -> str:
        """Identifica tipo de métrica pela consulta."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['venda', 'vendeu', 'faturamento', 'receita']):
            return 'sales'
        elif any(word in query_lower for word in ['usuário', 'cliente', 'cadastro', 'ativo']):
            return 'users'
        elif any(word in query_lower for word in ['performance', 'velocidade', 'tempo', 'resposta']):
            return 'performance'
        elif any(word in query_lower for word in ['crescimento', 'aumento', 'evolução', 'comparação']):
            return 'growth'
        else:
            return 'generic'
    
    async def _process_sales_metrics(self, query: str) -> Dict[str, Any]:
        """Processa métricas de vendas."""
        # Extrai período
        period = self._extract_time_period(query)
        
        # Consulta dados
        sales_data = await self._get_sales_data(period)
        
        # Calcula métricas
        metrics = {
            'total_sales': sum(s.get('value', 0) for s in sales_data),
            'sales_count': len(sales_data),
            'average_ticket': sum(s.get('value', 0) for s in sales_data) / len(sales_data) if sales_data else 0,
            'period': period,
            'top_products': self._get_top_products(sales_data),
            'daily_breakdown': self._get_daily_breakdown(sales_data)
        }
        
        # Gera visualização
        chart_path = await self._generate_sales_chart(metrics)
        metrics['chart'] = chart_path
        
        # Gera insights
        insights = await self._generate_sales_insights(metrics)
        metrics['insights'] = insights
        
        return {
            'success': True,
            'metrics': metrics,
            'summary': self._format_sales_summary(metrics)
        }
    
    async def _process_user_metrics(self, query: str) -> Dict[str, Any]:
        """Processa métricas de usuários."""
        period = self._extract_time_period(query)
        
        # Consulta dados
        user_data = await self._get_user_data(period)
        
        metrics = {
            'total_users': len(user_data),
            'new_users': len([u for u in user_data if self._is_new_user(u, period)]),
            'active_users': len([u for u in user_data if u.get('last_active')]),
            'retention_rate': self._calculate_retention(user_data),
            'user_segments': self._segment_users(user_data),
            'period': period
        }
        
        # Gera visualização
        chart_path = await self._generate_user_chart(metrics)
        metrics['chart'] = chart_path
        
        return {
            'success': True,
            'metrics': metrics,
            'summary': self._format_user_summary(metrics)
        }
    
    def _extract_time_period(self, query: str) -> Dict[str, Any]:
        """Extrai período de tempo da consulta."""
        query_lower = query.lower()
        now = datetime.now()
        
        if 'hoje' in query_lower:
            return {
                'start': now.replace(hour=0, minute=0, second=0),
                'end': now,
                'label': 'hoje'
            }
        elif 'ontem' in query_lower:
            yesterday = now - timedelta(days=1)
            return {
                'start': yesterday.replace(hour=0, minute=0, second=0),
                'end': yesterday.replace(hour=23, minute=59, second=59),
                'label': 'ontem'
            }
        elif 'semana' in query_lower:
            return {
                'start': now - timedelta(days=7),
                'end': now,
                'label': 'última semana'
            }
        elif 'mês' in query_lower or 'mes' in query_lower:
            return {
                'start': now - timedelta(days=30),
                'end': now,
                'label': 'último mês'
            }
        else:
            # Default: últimos 30 dias
            return {
                'start': now - timedelta(days=30),
                'end': now,
                'label': 'últimos 30 dias'
            }
    
    async def _get_sales_data(self, period: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtém dados de vendas do período."""
        # Tenta consultar banco de dados
        try:
            result = await self.db_manager.natural_query(
                f"Mostra vendas entre {period['start']} e {period['end']}"
            )
            
            if result['success'] and result.get('data'):
                return result['data']
        except:
            pass
        
        # Dados simulados para demonstração
        import random
        sales = []
        current = period['start']
        
        while current <= period['end']:
            num_sales = random.randint(5, 20)
            for _ in range(num_sales):
                sales.append({
                    'date': current,
                    'value': random.uniform(50, 500),
                    'product': random.choice(['Produto A', 'Produto B', 'Produto C']),
                    'customer_id': random.randint(1, 100)
                })
            current += timedelta(days=1)
        
        return sales
    
    async def _generate_sales_chart(self, metrics: Dict[str, Any]) -> str:
        """Gera gráfico de vendas."""
        if not PLOTTING_AVAILABLE:
            print("Aviso: Gráficos não disponíveis (matplotlib não instalado)")
            return None
        
        try:
            # Prepara dados
            daily_data = metrics['daily_breakdown']
            dates = [d['date'] for d in daily_data]
            values = [d['total'] for d in daily_data]
            
            # Cria gráfico
            plt.figure(figsize=(10, 6))
            plt.plot(dates, values, marker='o', linewidth=2, markersize=8)
            plt.fill_between(dates, values, alpha=0.3)
            
            plt.title(f"Vendas - {metrics['period']['label']}", fontsize=16)
            plt.xlabel('Data')
            plt.ylabel('Valor (R$)')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            
            # Salva gráfico
            chart_dir = Path('.gemini_code/charts')
            chart_dir.mkdir(parents=True, exist_ok=True)
            
            chart_path = chart_dir / f"sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150)
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            print(f"Erro ao gerar gráfico: {e}")
            return None
    
    async def _generate_sales_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """Gera insights sobre vendas usando IA."""
        prompt = f"""
        Analise estas métricas de vendas e gere 3-5 insights acionáveis:
        
        Total de vendas: R$ {metrics['total_sales']:.2f}
        Número de vendas: {metrics['sales_count']}
        Ticket médio: R$ {metrics['average_ticket']:.2f}
        Período: {metrics['period']['label']}
        
        Top produtos:
        {json.dumps(metrics['top_products'], indent=2)}
        
        Gere insights práticos e específicos em português.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai insights
        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                insights.append(line)
        
        return insights[:5]
    
    def _get_top_products(self, sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Obtém produtos mais vendidos."""
        product_sales = {}
        
        for sale in sales_data:
            product = sale.get('product', 'Unknown')
            value = sale.get('value', 0)
            
            if product not in product_sales:
                product_sales[product] = {'count': 0, 'total': 0}
            
            product_sales[product]['count'] += 1
            product_sales[product]['total'] += value
        
        # Ordena por valor total
        top_products = []
        for product, data in product_sales.items():
            top_products.append({
                'product': product,
                'count': data['count'],
                'total': data['total'],
                'average': data['total'] / data['count'] if data['count'] > 0 else 0
            })
        
        return sorted(top_products, key=lambda x: x['total'], reverse=True)[:5]
    
    def _get_daily_breakdown(self, sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Obtém breakdown diário de vendas."""
        daily_sales = {}
        
        for sale in sales_data:
            date = sale['date'].date() if hasattr(sale['date'], 'date') else sale['date']
            value = sale.get('value', 0)
            
            if date not in daily_sales:
                daily_sales[date] = {'count': 0, 'total': 0}
            
            daily_sales[date]['count'] += 1
            daily_sales[date]['total'] += value
        
        # Converte para lista ordenada
        breakdown = []
        for date, data in sorted(daily_sales.items()):
            breakdown.append({
                'date': date,
                'count': data['count'],
                'total': data['total'],
                'average': data['total'] / data['count'] if data['count'] > 0 else 0
            })
        
        return breakdown
    
    def _format_sales_summary(self, metrics: Dict[str, Any]) -> str:
        """Formata resumo de vendas."""
        summary = f"""
📊 **Resumo de Vendas - {metrics['period']['label']}**

💰 **Total**: R$ {metrics['total_sales']:,.2f}
📦 **Quantidade**: {metrics['sales_count']} vendas
🎯 **Ticket Médio**: R$ {metrics['average_ticket']:.2f}

🏆 **Top Produtos**:
"""
        
        for i, product in enumerate(metrics['top_products'][:3], 1):
            summary += f"{i}. {product['product']}: R$ {product['total']:,.2f} ({product['count']} vendas)\n"
        
        if metrics.get('insights'):
            summary += "\n💡 **Insights**:\n"
            for insight in metrics['insights'][:3]:
                summary += f"- {insight}\n"
        
        return summary
    
    async def create_custom_dashboard(self, config: Dict[str, Any]) -> str:
        """Cria dashboard customizado."""
        dashboard = {
            'title': config.get('title', 'Dashboard de Negócios'),
            'widgets': [],
            'created_at': datetime.now()
        }
        
        # Adiciona widgets solicitados
        for widget_config in config.get('widgets', []):
            widget_type = widget_config.get('type')
            
            if widget_type == 'sales':
                widget = await self._create_sales_widget(widget_config)
            elif widget_type == 'users':
                widget = await self._create_users_widget(widget_config)
            elif widget_type == 'kpi':
                widget = await self._create_kpi_widget(widget_config)
            else:
                continue
            
            dashboard['widgets'].append(widget)
        
        # Gera HTML do dashboard
        html = self._generate_dashboard_html(dashboard)
        
        # Salva dashboard
        dashboard_dir = Path('.gemini_code/dashboards')
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        dashboard_path = dashboard_dir / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(dashboard_path)
    
    def _generate_dashboard_html(self, dashboard: Dict[str, Any]) -> str:
        """Gera HTML do dashboard."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{dashboard['title']}</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .widget {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .widget h3 {{ margin-top: 0; color: #333; }}
        .metric {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
        .chart {{ width: 100%; height: 200px; }}
    </style>
</head>
<body>
    <h1>{dashboard['title']}</h1>
    <p>Atualizado em: {dashboard['created_at'].strftime('%d/%m/%Y %H:%M')}</p>
    
    <div class="dashboard">
"""
        
        for widget in dashboard['widgets']:
            html += f"""
        <div class="widget">
            <h3>{widget['title']}</h3>
            <div class="metric">{widget['value']}</div>
            <p>{widget.get('description', '')}</p>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html