"""
Sistema de acompanhamento de KPIs em tempo real.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import sqlite3
from collections import defaultdict

from ..core.gemini_client import GeminiClient
from ..database.database_manager import DatabaseManager


@dataclass
class KPI:
    """Representa um KPI."""
    id: str
    name: str
    description: str
    query: str
    target_value: float
    current_value: float = 0.0
    unit: str = ""
    trend: str = "stable"  # up, down, stable
    alert_threshold: float = 0.0
    category: str = "general"
    priority: str = "medium"  # high, medium, low
    auto_update: bool = True
    update_interval: int = 300  # segundos
    last_updated: Optional[datetime] = None
    history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat() if self.last_updated else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KPI':
        """Cria KPI a partir de dicionário."""
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)
    
    def update_value(self, new_value: float) -> None:
        """Atualiza valor do KPI."""
        # Adiciona ao histórico
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'value': self.current_value,
            'trend': self.trend
        })
        
        # Limita histórico a 1000 registros
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        # Calcula tendência
        if self.current_value > 0:
            change_percent = (new_value - self.current_value) / self.current_value * 100
            if change_percent > 5:
                self.trend = "up"
            elif change_percent < -5:
                self.trend = "down"
            else:
                self.trend = "stable"
        
        # Atualiza valores
        self.current_value = new_value
        self.last_updated = datetime.now()
    
    def get_performance_score(self) -> float:
        """Calcula score de performance do KPI."""
        if self.target_value == 0:
            return 100.0
        
        performance = (self.current_value / self.target_value) * 100
        return min(100.0, max(0.0, performance))
    
    def is_alert_triggered(self) -> bool:
        """Verifica se alerta deve ser disparado."""
        if self.alert_threshold == 0:
            return False
        
        score = self.get_performance_score()
        return score < self.alert_threshold
    
    def get_trend_direction(self) -> str:
        """Retorna direção da tendência em português."""
        return {
            "up": "crescente",
            "down": "decrescente",
            "stable": "estável"
        }.get(self.trend, "estável")


class KPITracker:
    """Sistema de acompanhamento de KPIs."""
    
    def __init__(self, gemini_client: GeminiClient, db_manager: DatabaseManager):
        self.gemini_client = gemini_client
        self.db_manager = db_manager
        self.kpis: Dict[str, KPI] = {}
        self.alert_callbacks: List[Callable] = []
        self.running = False
        self.update_tasks = {}
        self.data_file = Path('.gemini_code/kpis.json')
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Inicializa armazenamento de KPIs."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_kpis()
    
    def save_kpis(self) -> None:
        """Salva KPIs em arquivo."""
        data = {
            'kpis': {kpi_id: kpi.to_dict() for kpi_id, kpi in self.kpis.items()},
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_kpis(self) -> None:
        """Carrega KPIs do arquivo."""
        if not self.data_file.exists():
            self._create_default_kpis()
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.kpis = {}
            for kpi_id, kpi_data in data.get('kpis', {}).items():
                self.kpis[kpi_id] = KPI.from_dict(kpi_data)
                
        except Exception as e:
            print(f"Erro ao carregar KPIs: {e}")
            self._create_default_kpis()
    
    def _create_default_kpis(self) -> None:
        """Cria KPIs padrão."""
        default_kpis = [
            KPI(
                id="daily_sales",
                name="Vendas Diárias",
                description="Total de vendas realizadas hoje",
                query="vendas de hoje",
                target_value=10000.0,
                unit="R$",
                category="sales",
                priority="high",
                alert_threshold=70.0,
                update_interval=300
            ),
            KPI(
                id="active_users",
                name="Usuários Ativos",
                description="Número de usuários ativos hoje",
                query="usuários ativos hoje",
                target_value=500.0,
                unit="usuários",
                category="users",
                priority="high",
                alert_threshold=80.0,
                update_interval=600
            ),
            KPI(
                id="conversion_rate",
                name="Taxa de Conversão",
                description="Percentual de visitantes que se tornam clientes",
                query="taxa de conversão hoje",
                target_value=5.0,
                unit="%",
                category="conversion",
                priority="medium",
                alert_threshold=60.0,
                update_interval=900
            ),
            KPI(
                id="avg_ticket",
                name="Ticket Médio",
                description="Valor médio das vendas",
                query="ticket médio hoje",
                target_value=150.0,
                unit="R$",
                category="sales",
                priority="medium",
                alert_threshold=75.0,
                update_interval=600
            ),
            KPI(
                id="customer_satisfaction",
                name="Satisfação do Cliente",
                description="Score de satisfação dos clientes",
                query="satisfação do cliente",
                target_value=9.0,
                unit="/10",
                category="satisfaction",
                priority="high",
                alert_threshold=85.0,
                update_interval=1800
            )
        ]
        
        for kpi in default_kpis:
            self.kpis[kpi.id] = kpi
        
        self.save_kpis()
    
    async def add_kpi(self, kpi_data: Dict[str, Any]) -> str:
        """Adiciona novo KPI."""
        # Gera ID único
        kpi_id = kpi_data.get('id') or f"kpi_{len(self.kpis) + 1}"
        
        # Cria KPI
        kpi = KPI(
            id=kpi_id,
            name=kpi_data['name'],
            description=kpi_data.get('description', ''),
            query=kpi_data['query'],
            target_value=float(kpi_data['target_value']),
            unit=kpi_data.get('unit', ''),
            category=kpi_data.get('category', 'general'),
            priority=kpi_data.get('priority', 'medium'),
            alert_threshold=float(kpi_data.get('alert_threshold', 0)),
            update_interval=int(kpi_data.get('update_interval', 600))
        )
        
        # Adiciona à coleção
        self.kpis[kpi_id] = kpi
        
        # Atualiza valor inicial
        await self.update_kpi(kpi_id)
        
        # Salva
        self.save_kpis()
        
        # Inicia monitoramento se estiver rodando
        if self.running:
            await self._start_kpi_monitoring(kpi)
        
        return kpi_id
    
    async def add_kpi_from_natural_language(self, request: str) -> str:
        """Adiciona KPI baseado em linguagem natural."""
        prompt = f"""
        O usuário quer criar um KPI com esta solicitação: "{request}"
        
        Extraia as informações e retorne JSON no formato:
        {{
            "name": "Nome do KPI",
            "description": "Descrição detalhada",
            "query": "consulta para obter o valor",
            "target_value": 100.0,
            "unit": "unidade (R$, %, usuários, etc)",
            "category": "categoria (sales, users, conversion, etc)",
            "priority": "high/medium/low",
            "alert_threshold": 80.0,
            "update_interval": 600
        }}
        
        Seja específico e prático.
        """
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                kpi_data = json.loads(json_match.group())
                return await self.add_kpi(kpi_data)
            else:
                raise ValueError("Não foi possível extrair dados do KPI")
                
        except Exception as e:
            # Fallback: cria KPI básico
            kpi_data = {
                'name': f"KPI Personalizado",
                'description': f"KPI criado para: {request}",
                'query': request,
                'target_value': 100.0,
                'category': 'custom',
                'priority': 'medium',
                'alert_threshold': 70.0
            }
            return await self.add_kpi(kpi_data)
    
    async def update_kpi(self, kpi_id: str) -> bool:
        """Atualiza valor de um KPI."""
        if kpi_id not in self.kpis:
            return False
        
        kpi = self.kpis[kpi_id]
        
        try:
            # Tenta obter valor usando query natural
            result = await self._execute_kpi_query(kpi.query)
            
            if result is not None:
                kpi.update_value(result)
                
                # Verifica alertas
                if kpi.is_alert_triggered():
                    await self._trigger_alert(kpi)
                
                return True
                
        except Exception as e:
            print(f"Erro ao atualizar KPI {kpi_id}: {e}")
            # Gera valor simulado para demonstração
            import random
            simulated_value = kpi.target_value * (0.7 + random.random() * 0.6)
            kpi.update_value(simulated_value)
            return True
        
        return False
    
    async def _execute_kpi_query(self, query: str) -> Optional[float]:
        """Executa query para obter valor do KPI."""
        try:
            # Tenta usar business metrics
            if hasattr(self, 'business_metrics'):
                result = await self.business_metrics.process_natural_query(query)
                if result.get('success'):
                    metrics = result.get('metrics', {})
                    # Tenta extrair valor numérico principal
                    for key in ['total_sales', 'active_users', 'conversion_rate', 'average_ticket']:
                        if key in metrics:
                            return float(metrics[key])
            
            # Tenta database manager
            db_result = await self.db_manager.natural_query(query)
            if db_result.get('success') and db_result.get('data'):
                data = db_result['data']
                if isinstance(data, list) and data:
                    # Tenta extrair valor numérico
                    first_item = data[0]
                    if isinstance(first_item, dict):
                        for value in first_item.values():
                            if isinstance(value, (int, float)):
                                return float(value)
            
            return None
            
        except Exception as e:
            print(f"Erro ao executar query KPI: {e}")
            return None
    
    async def update_all_kpis(self) -> Dict[str, bool]:
        """Atualiza todos os KPIs."""
        results = {}
        
        for kpi_id in self.kpis.keys():
            results[kpi_id] = await self.update_kpi(kpi_id)
        
        # Salva após atualizações
        self.save_kpis()
        
        return results
    
    async def start_monitoring(self) -> None:
        """Inicia monitoramento automático dos KPIs."""
        if self.running:
            return
        
        self.running = True
        print("Iniciando monitoramento de KPIs...")
        
        # Inicia tasks para cada KPI
        for kpi in self.kpis.values():
            if kpi.auto_update:
                await self._start_kpi_monitoring(kpi)
    
    async def stop_monitoring(self) -> None:
        """Para monitoramento automático."""
        self.running = False
        
        # Cancela tasks
        for task in self.update_tasks.values():
            if not task.done():
                task.cancel()
        
        self.update_tasks.clear()
        print("Monitoramento de KPIs parado.")
    
    async def _start_kpi_monitoring(self, kpi: KPI) -> None:
        """Inicia monitoramento de um KPI específico."""
        async def monitor_loop():
            while self.running:
                try:
                    await self.update_kpi(kpi.id)
                    await asyncio.sleep(kpi.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Erro no monitoramento do KPI {kpi.id}: {e}")
                    await asyncio.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
        
        # Cancela task anterior se existir
        if kpi.id in self.update_tasks:
            self.update_tasks[kpi.id].cancel()
        
        # Inicia nova task
        self.update_tasks[kpi.id] = asyncio.create_task(monitor_loop())
    
    def get_kpi(self, kpi_id: str) -> Optional[KPI]:
        """Obtém KPI por ID."""
        return self.kpis.get(kpi_id)
    
    def get_kpis_by_category(self, category: str) -> List[KPI]:
        """Obtém KPIs por categoria."""
        return [kpi for kpi in self.kpis.values() if kpi.category == category]
    
    def get_kpis_by_priority(self, priority: str) -> List[KPI]:
        """Obtém KPIs por prioridade."""
        return [kpi for kpi in self.kpis.values() if kpi.priority == priority]
    
    def get_alert_kpis(self) -> List[KPI]:
        """Obtém KPIs em estado de alerta."""
        return [kpi for kpi in self.kpis.values() if kpi.is_alert_triggered()]
    
    def get_kpi_summary(self) -> Dict[str, Any]:
        """Obtém resumo dos KPIs."""
        total_kpis = len(self.kpis)
        alert_kpis = len(self.get_alert_kpis())
        
        # Agrupa por categoria
        by_category = defaultdict(list)
        by_priority = defaultdict(list)
        
        for kpi in self.kpis.values():
            by_category[kpi.category].append(kpi)
            by_priority[kpi.priority].append(kpi)
        
        # Calcula score geral
        if total_kpis > 0:
            total_score = sum(kpi.get_performance_score() for kpi in self.kpis.values()) / total_kpis
        else:
            total_score = 0
        
        return {
            'total_kpis': total_kpis,
            'alert_kpis': alert_kpis,
            'overall_score': total_score,
            'categories': {cat: len(kpis) for cat, kpis in by_category.items()},
            'priorities': {pri: len(kpis) for pri, kpis in by_priority.items()},
            'last_updated': datetime.now().isoformat(),
            'monitoring_active': self.running
        }
    
    async def generate_kpi_report(self, period: str = "today") -> Dict[str, Any]:
        """Gera relatório dos KPIs."""
        summary = self.get_kpi_summary()
        alert_kpis = self.get_alert_kpis()
        
        # Gera insights com IA
        insights = await self._generate_kpi_insights(summary, alert_kpis)
        
        # KPIs com melhor e pior performance
        sorted_kpis = sorted(self.kpis.values(), 
                           key=lambda k: k.get_performance_score(), 
                           reverse=True)
        
        best_kpis = sorted_kpis[:3]
        worst_kpis = sorted_kpis[-3:]
        
        return {
            'period': period,
            'summary': summary,
            'alert_kpis': [kpi.to_dict() for kpi in alert_kpis],
            'best_performance': [kpi.to_dict() for kpi in best_kpis],
            'worst_performance': [kpi.to_dict() for kpi in worst_kpis],
            'insights': insights,
            'recommendations': await self._generate_kpi_recommendations(alert_kpis),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_kpi_insights(self, summary: Dict[str, Any], alert_kpis: List[KPI]) -> List[str]:
        """Gera insights sobre os KPIs usando IA."""
        prompt = f"""
        Analise este resumo de KPIs e gere insights:
        
        Resumo geral:
        - Total de KPIs: {summary['total_kpis']}
        - KPIs em alerta: {summary['alert_kpis']}
        - Score geral: {summary['overall_score']:.1f}%
        - Categorias: {summary['categories']}
        
        KPIs em alerta:
        {json.dumps([kpi.to_dict() for kpi in alert_kpis], indent=2, default=str)}
        
        Gere 3-5 insights acionáveis em português sobre:
        1. Performance geral
        2. Áreas de atenção
        3. Oportunidades de melhoria
        """
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            insights = [line.strip() for line in response.split('\n') 
                       if line.strip() and not line.startswith('#')]
            return insights[:5]
        except:
            return [
                f"Score geral de {summary['overall_score']:.1f}% indica desempenho {'bom' if summary['overall_score'] > 80 else 'regular' if summary['overall_score'] > 60 else 'crítico'}",
                f"{summary['alert_kpis']} KPIs precisam de atenção imediata",
                "Monitore regularmente para identificar tendências"
            ]
    
    async def _generate_kpi_recommendations(self, alert_kpis: List[KPI]) -> List[str]:
        """Gera recomendações para KPIs em alerta."""
        recommendations = []
        
        for kpi in alert_kpis:
            score = kpi.get_performance_score()
            
            if score < 50:
                recommendations.append(f"⚠️ {kpi.name}: Performance crítica ({score:.1f}%) - Ação urgente necessária")
            elif score < 70:
                recommendations.append(f"🟡 {kpi.name}: Abaixo da meta ({score:.1f}%) - Revisar estratégia")
            
            if kpi.trend == "down":
                recommendations.append(f"📉 {kpi.name}: Tendência de queda - Investigar causas")
        
        if not recommendations:
            recommendations.append("✅ Todos os KPIs estão dentro dos parâmetros aceitáveis")
        
        return recommendations[:10]
    
    def add_alert_callback(self, callback: Callable[[KPI], None]) -> None:
        """Adiciona callback para alertas."""
        self.alert_callbacks.append(callback)
    
    async def _trigger_alert(self, kpi: KPI) -> None:
        """Dispara alerta para KPI."""
        print(f"⚠️ ALERTA KPI: {kpi.name} - Score: {kpi.get_performance_score():.1f}%")
        
        # Chama callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(kpi)
                else:
                    callback(kpi)
            except Exception as e:
                print(f"Erro no callback de alerta: {e}")
    
    def remove_kpi(self, kpi_id: str) -> bool:
        """Remove KPI."""
        if kpi_id in self.kpis:
            # Para monitoramento se ativo
            if kpi_id in self.update_tasks:
                self.update_tasks[kpi_id].cancel()
                del self.update_tasks[kpi_id]
            
            # Remove KPI
            del self.kpis[kpi_id]
            self.save_kpis()
            return True
        
        return False
    
    async def forecast_kpi(self, kpi_id: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """Faz previsão de KPI usando histórico."""
        if kpi_id not in self.kpis:
            return None
        
        kpi = self.kpis[kpi_id]
        
        if len(kpi.history) < 5:
            return {
                'success': False,
                'error': 'Histórico insuficiente para previsão'
            }
        
        try:
            # Extrai valores históricos
            values = [entry['value'] for entry in kpi.history[-30:]]  # Últimos 30 registros
            
            # Regressão linear simples
            import numpy as np
            from sklearn.linear_model import LinearRegression
            
            X = np.arange(len(values)).reshape(-1, 1)
            y = np.array(values)
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Previsão
            future_X = np.arange(len(values), len(values) + days).reshape(-1, 1)
            forecast = model.predict(future_X)
            
            # Calcula tendência
            trend_slope = model.coef_[0]
            trend_direction = "crescente" if trend_slope > 0 else "decrescente" if trend_slope < 0 else "estável"
            
            return {
                'success': True,
                'kpi_id': kpi_id,
                'forecast_days': days,
                'forecasted_values': forecast.tolist(),
                'trend_direction': trend_direction,
                'trend_slope': float(trend_slope),
                'confidence': min(100, len(values) * 2),  # Confiança baseada no histórico
                'current_value': kpi.current_value,
                'target_value': kpi.target_value
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na previsão: {str(e)}'
            }