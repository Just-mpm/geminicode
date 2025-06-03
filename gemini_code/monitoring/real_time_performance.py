"""
Sistema de monitoramento de performance em tempo real.
"""

import asyncio
import time
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import json
from pathlib import Path

from ..utils.performance_optimizer import performance_monitor
from ..core.memory_system import MemorySystem


@dataclass
class SystemMetrics:
    """Métricas do sistema."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_threads: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'active_threads': self.active_threads
        }


@dataclass
class ApplicationMetrics:
    """Métricas da aplicação."""
    timestamp: datetime
    active_conversations: int
    memory_records: int
    cache_hit_rate: float
    average_response_time: float
    errors_last_hour: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'active_conversations': self.active_conversations,
            'memory_records': self.memory_records,
            'cache_hit_rate': self.cache_hit_rate,
            'average_response_time': self.average_response_time,
            'errors_last_hour': self.errors_last_hour
        }


class RealTimePerformanceMonitor:
    """Monitor de performance em tempo real."""
    
    def __init__(self, memory_system: Optional[MemorySystem] = None):
        self.memory_system = memory_system
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Métricas históricas (últimas 24 horas)
        self.system_metrics_history = deque(maxlen=24*60)  # 1 por minuto
        self.app_metrics_history = deque(maxlen=24*60)
        
        # Callbacks para alertas
        self.alert_callbacks: List[Callable] = []
        
        # Thresholds para alertas
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'average_response_time': 5.0,  # segundos
            'errors_per_hour': 10
        }
        
        # Contadores de erro
        self.error_timestamps = deque(maxlen=1000)
        
        # Cache de conversas ativas
        self.active_conversations = set()
    
    def start_monitoring(self, interval: float = 60.0):
        """Inicia monitoramento em tempo real."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        print(f"🔍 Monitoramento de performance iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("🛑 Monitoramento de performance parado")
    
    def _monitoring_loop(self, interval: float):
        """Loop principal de monitoramento."""
        while self.is_monitoring:
            try:
                # Coletar métricas do sistema
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Coletar métricas da aplicação
                app_metrics = self._collect_application_metrics()
                self.app_metrics_history.append(app_metrics)
                
                # Verificar alertas
                self._check_alerts(system_metrics, app_metrics)
                
                # Salvar métricas se necessário
                self._save_metrics_if_needed()
                
            except Exception as e:
                print(f"⚠️ Erro no monitoramento: {e}")
            
            time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Coleta métricas do sistema."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            active_threads = threading.active_count()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                active_threads=active_threads
            )
        except Exception as e:
            print(f"⚠️ Erro ao coletar métricas do sistema: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                memory_used_mb=0,
                disk_usage_percent=0,
                active_threads=0
            )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Coleta métricas da aplicação."""
        try:
            # Obter métricas do performance monitor
            perf_report = performance_monitor.get_performance_report()
            
            # Calcular tempo médio de resposta
            avg_response_time = 0.0
            if 'summary' in perf_report and 'average_execution_time' in perf_report['summary']:
                avg_response_time = perf_report['summary']['average_execution_time']
            
            # Contar erros na última hora
            current_time = time.time()
            errors_last_hour = sum(
                1 for timestamp in self.error_timestamps
                if current_time - timestamp < 3600
            )
            
            # Obter dados da memória se disponível
            memory_records = 0
            if self.memory_system:
                try:
                    # Contar registros na memória
                    import sqlite3
                    conn = sqlite3.connect(str(self.memory_system.db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM conversations")
                    memory_records = cursor.fetchone()[0]
                    conn.close()
                except Exception:
                    memory_records = 0
            
            # Taxa de hit do cache (simulada se não disponível)
            cache_hit_rate = 0.75  # Valor padrão
            
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_conversations=len(self.active_conversations),
                memory_records=memory_records,
                cache_hit_rate=cache_hit_rate,
                average_response_time=avg_response_time,
                errors_last_hour=errors_last_hour
            )
        except Exception as e:
            print(f"⚠️ Erro ao coletar métricas da aplicação: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_conversations=0,
                memory_records=0,
                cache_hit_rate=0.0,
                average_response_time=0.0,
                errors_last_hour=0
            )
    
    def _check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Verifica e dispara alertas se necessário."""
        alerts = []
        
        # Alertas de sistema
        if system_metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"CPU alta: {system_metrics.cpu_percent:.1f}%",
                'severity': 'warning' if system_metrics.cpu_percent < 90 else 'critical'
            })
        
        if system_metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f"Memória alta: {system_metrics.memory_percent:.1f}%",
                'severity': 'warning' if system_metrics.memory_percent < 95 else 'critical'
            })
        
        # Alertas de aplicação
        if app_metrics.average_response_time > self.thresholds['average_response_time']:
            alerts.append({
                'type': 'response_time_high',
                'message': f"Tempo de resposta alto: {app_metrics.average_response_time:.2f}s",
                'severity': 'warning'
            })
        
        if app_metrics.errors_last_hour > self.thresholds['errors_per_hour']:
            alerts.append({
                'type': 'errors_high',
                'message': f"Muitos erros: {app_metrics.errors_last_hour} na última hora",
                'severity': 'critical'
            })
        
        # Disparar callbacks de alerta
        for alert in alerts:
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """Dispara alerta para callbacks registrados."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️ Erro no callback de alerta: {e}")
    
    def _save_metrics_if_needed(self):
        """Salva métricas periodicamente."""
        # Salvar a cada 10 minutos
        if len(self.system_metrics_history) % 10 == 0:
            self._save_metrics_to_file()
    
    def _save_metrics_to_file(self):
        """Salva métricas em arquivo."""
        try:
            metrics_dir = Path('.gemini_code/metrics')
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            metrics_file = metrics_dir / f'performance_metrics_{timestamp}.json'
            
            # Preparar dados para salvar (últimas 60 métricas)
            recent_system = list(self.system_metrics_history)[-60:]
            recent_app = list(self.app_metrics_history)[-60:]
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': [metric.to_dict() for metric in recent_system],
                'application_metrics': [metric.to_dict() for metric in recent_app]
            }
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar métricas: {e}")
    
    def register_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Registra callback para alertas."""
        self.alert_callbacks.append(callback)
    
    def record_error(self):
        """Registra ocorrência de erro."""
        self.error_timestamps.append(time.time())
    
    def register_conversation(self, conversation_id: str):
        """Registra conversa ativa."""
        self.active_conversations.add(conversation_id)
    
    def unregister_conversation(self, conversation_id: str):
        """Remove conversa ativa."""
        self.active_conversations.discard(conversation_id)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Obtém status atual detalhado."""
        if not self.system_metrics_history or not self.app_metrics_history:
            return {"status": "No data available"}
        
        latest_system = self.system_metrics_history[-1]
        latest_app = self.app_metrics_history[-1]
        
        # Calcular tendências (últimos 5 minutos vs anteriores)
        system_trend = self._calculate_trend([m.cpu_percent for m in list(self.system_metrics_history)[-10:]])
        memory_trend = self._calculate_trend([m.memory_percent for m in list(self.system_metrics_history)[-10:]])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": latest_system.cpu_percent,
                "memory_percent": latest_system.memory_percent,
                "memory_used_mb": latest_system.memory_used_mb,
                "disk_usage_percent": latest_system.disk_usage_percent,
                "active_threads": latest_system.active_threads,
                "trends": {
                    "cpu": system_trend,
                    "memory": memory_trend
                }
            },
            "application": {
                "active_conversations": latest_app.active_conversations,
                "memory_records": latest_app.memory_records,
                "cache_hit_rate": latest_app.cache_hit_rate,
                "average_response_time": latest_app.average_response_time,
                "errors_last_hour": latest_app.errors_last_hour
            },
            "health_status": self._calculate_health_status(latest_system, latest_app),
            "recommendations": self._generate_recommendations(latest_system, latest_app)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendência dos valores."""
        if len(values) < 2:
            return "stable"
        
        # Comparar média das últimas 3 com as 3 anteriores
        recent_avg = sum(values[-3:]) / len(values[-3:])
        previous_avg = sum(values[-6:-3]) / len(values[-6:-3]) if len(values) >= 6 else recent_avg
        
        if recent_avg > previous_avg * 1.1:
            return "increasing"
        elif recent_avg < previous_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_health_status(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics) -> str:
        """Calcula status geral de saúde."""
        issues = 0
        
        if system_metrics.cpu_percent > 80:
            issues += 1
        if system_metrics.memory_percent > 85:
            issues += 1
        if app_metrics.average_response_time > 3:
            issues += 1
        if app_metrics.errors_last_hour > 5:
            issues += 1
        
        if issues == 0:
            return "excellent"
        elif issues == 1:
            return "good"
        elif issues == 2:
            return "warning"
        else:
            return "critical"
    
    def _generate_recommendations(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics) -> List[str]:
        """Gera recomendações baseadas nas métricas."""
        recommendations = []
        
        if system_metrics.cpu_percent > 80:
            recommendations.append("⚡ CPU alta detectada - considere otimizar algoritmos ou reduzir carga")
        
        if system_metrics.memory_percent > 85:
            recommendations.append("🧠 Memória alta - revisar vazamentos de memória ou aumentar limite")
        
        if app_metrics.average_response_time > 3:
            recommendations.append("🚀 Tempo de resposta alto - otimizar cache ou melhorar prompts")
        
        if app_metrics.errors_last_hour > 5:
            recommendations.append("🔧 Muitos erros detectados - revisar logs e corrigir problemas")
        
        if app_metrics.cache_hit_rate < 0.7:
            recommendations.append("💾 Taxa de cache baixa - revisar estratégia de caching")
        
        if not recommendations:
            recommendations.append("✨ Sistema funcionando perfeitamente!")
        
        return recommendations
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório completo de performance."""
        current_status = self.get_current_status()
        
        # Estatísticas históricas
        if self.system_metrics_history:
            cpu_values = [m.cpu_percent for m in self.system_metrics_history]
            memory_values = [m.memory_percent for m in self.system_metrics_history]
            
            historical_stats = {
                "cpu": {
                    "average": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "average": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                }
            }
        else:
            historical_stats = {}
        
        return {
            "current_status": current_status,
            "historical_stats": historical_stats,
            "monitoring_duration": len(self.system_metrics_history),
            "last_updated": datetime.now().isoformat()
        }


# Instância global
global_performance_monitor = None


def get_performance_monitor(memory_system: Optional[MemorySystem] = None) -> RealTimePerformanceMonitor:
    """Obtém instância global do monitor de performance."""
    global global_performance_monitor
    
    if global_performance_monitor is None:
        global_performance_monitor = RealTimePerformanceMonitor(memory_system)
    
    return global_performance_monitor


def start_monitoring(memory_system: Optional[MemorySystem] = None, interval: float = 60.0):
    """Inicia monitoramento global."""
    monitor = get_performance_monitor(memory_system)
    monitor.start_monitoring(interval)
    return monitor