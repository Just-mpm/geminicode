"""
Sistema de monitoramento contínuo 24/7 que observa o projeto constantemente.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import psutil
import json

from ..core.gemini_client import GeminiClient
from ..core.memory_system import MemorySystem
from ..analysis.error_detector import ErrorDetector
from ..analysis.health_monitor import HealthMonitor


class ProjectEventHandler(FileSystemEventHandler):
    """Handler para eventos do sistema de arquivos."""
    
    def __init__(self, monitor: 'ContinuousMonitor'):
        self.monitor = monitor
        self.last_event_time = {}
        self.debounce_seconds = 1.0
    
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """Verifica se deve processar evento (com debounce)."""
        # Ignora diretórios e arquivos temporários
        if event.is_directory:
            return False
        
        path = Path(event.src_path)
        
        # Ignora padrões
        ignore_patterns = [
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            '.pyc', '.log', '.tmp', '.swp', '.gemini_code'
        ]
        
        if any(pattern in str(path) for pattern in ignore_patterns):
            return False
        
        # Debounce - evita múltiplos eventos
        current_time = time.time()
        last_time = self.last_event_time.get(event.src_path, 0)
        
        if current_time - last_time < self.debounce_seconds:
            return False
        
        self.last_event_time[event.src_path] = current_time
        return True
    
    def on_modified(self, event):
        """Arquivo modificado."""
        if self._should_process_event(event):
            asyncio.create_task(
                self.monitor._handle_file_change('modified', event.src_path)
            )
    
    def on_created(self, event):
        """Arquivo criado."""
        if self._should_process_event(event):
            asyncio.create_task(
                self.monitor._handle_file_change('created', event.src_path)
            )
    
    def on_deleted(self, event):
        """Arquivo deletado."""
        if self._should_process_event(event):
            asyncio.create_task(
                self.monitor._handle_file_change('deleted', event.src_path)
            )
    
    def on_moved(self, event):
        """Arquivo movido."""
        if self._should_process_event(event):
            asyncio.create_task(
                self.monitor._handle_file_change('moved', event.src_path, event.dest_path)
            )


class ContinuousMonitor:
    """Monitor contínuo 24/7 do projeto."""
    
    def __init__(self, gemini_client: GeminiClient, project_path: str):
        self.gemini_client = gemini_client
        self.project_path = Path(project_path)
        self.memory = MemorySystem(project_path)
        self.error_detector = ErrorDetector(gemini_client, None)
        self.health_monitor = HealthMonitor(gemini_client, None)
        
        # Estado do monitoramento
        self.is_running = False
        self.start_time = None
        self.events_count = 0
        self.issues_found = 0
        self.auto_fixes = 0
        
        # Callbacks
        self.event_callbacks = []
        self.alert_callbacks = []
        
        # Configurações
        self.config = {
            'auto_fix': True,
            'alert_threshold': 3,  # Alertar após N problemas
            'scan_interval': 300,  # 5 minutos
            'performance_check_interval': 600,  # 10 minutos
            'health_check_interval': 1800,  # 30 minutos
            'memory_limit_mb': 500,
            'cpu_limit_percent': 80
        }
        
        # Métricas em tempo real
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'file_changes': [],
            'errors_detected': [],
            'performance_scores': []
        }
    
    async def start_monitoring(self) -> None:
        """Inicia monitoramento contínuo."""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        print(f"🔍 Iniciando monitoramento 24/7 de {self.project_path}")
        
        # Inicia observer de arquivos
        self._start_file_observer()
        
        # Inicia tarefas assíncronas
        tasks = [
            asyncio.create_task(self._periodic_error_scan()),
            asyncio.create_task(self._periodic_performance_check()),
            asyncio.create_task(self._periodic_health_check()),
            asyncio.create_task(self._system_metrics_collector()),
            asyncio.create_task(self._auto_optimizer())
        ]
        
        # Aguarda todas as tarefas (nunca termina em operação normal)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("🛑 Monitoramento interrompido")
    
    def _start_file_observer(self) -> None:
        """Inicia observador de mudanças em arquivos."""
        self.observer = Observer()
        event_handler = ProjectEventHandler(self)
        
        self.observer.schedule(
            event_handler,
            str(self.project_path),
            recursive=True
        )
        
        self.observer.start()
    
    async def _handle_file_change(self, event_type: str, file_path: str, 
                                 dest_path: Optional[str] = None) -> None:
        """Processa mudança em arquivo."""
        self.events_count += 1
        
        # Registra evento
        event = {
            'type': event_type,
            'file': file_path,
            'dest': dest_path,
            'timestamp': datetime.now()
        }
        
        self.metrics['file_changes'].append(event)
        
        # Analisa impacto da mudança
        if event_type in ['modified', 'created']:
            await self._analyze_file_change(file_path)
        
        # Notifica callbacks
        for callback in self.event_callbacks:
            await callback(event)
        
        # Detecta padrões
        self._detect_change_patterns()
    
    async def _analyze_file_change(self, file_path: str) -> None:
        """Analisa mudança em arquivo específico."""
        if not file_path.endswith('.py'):
            return
        
        try:
            # Verifica erros no arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Análise rápida de sintaxe
            import ast
            try:
                ast.parse(content)
            except SyntaxError as e:
                await self._handle_syntax_error(file_path, e)
            
            # Verifica problemas comuns
            issues = self._quick_code_analysis(content, file_path)
            if issues:
                await self._handle_code_issues(file_path, issues)
                
        except Exception as e:
            print(f"Erro ao analisar {file_path}: {e}")
    
    def _quick_code_analysis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Análise rápida de código para problemas comuns."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Imports não usados (simplificado)
            if line.strip().startswith('import ') and not any(
                line.split()[1] in other_line 
                for j, other_line in enumerate(lines) if j != i-1
            ):
                issues.append({
                    'type': 'unused_import',
                    'line': i,
                    'message': f'Import não usado: {line.strip()}',
                    'severity': 'low'
                })
            
            # TODO/FIXME
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    'type': 'todo',
                    'line': i,
                    'message': line.strip(),
                    'severity': 'info'
                })
            
            # Senha hardcoded
            if any(word in line.lower() for word in ['password=', 'api_key=', 'secret=']):
                if any(char in line for char in ['"', "'"]):
                    issues.append({
                        'type': 'security',
                        'line': i,
                        'message': 'Possível senha/chave hardcoded',
                        'severity': 'high'
                    })
        
        return issues
    
    async def _handle_syntax_error(self, file_path: str, error: SyntaxError) -> None:
        """Lida com erro de sintaxe detectado."""
        self.issues_found += 1
        
        alert = {
            'type': 'syntax_error',
            'file': file_path,
            'line': error.lineno,
            'message': str(error),
            'timestamp': datetime.now()
        }
        
        self.metrics['errors_detected'].append(alert)
        
        # Auto-fix se habilitado
        if self.config['auto_fix']:
            fixed = await self._attempt_auto_fix(file_path, error)
            if fixed:
                self.auto_fixes += 1
                alert['auto_fixed'] = True
        
        # Alerta se necessário
        if self.issues_found % self.config['alert_threshold'] == 0:
            await self._send_alert(alert)
    
    async def _handle_code_issues(self, file_path: str, issues: List[Dict[str, Any]]) -> None:
        """Lida com problemas de código detectados."""
        high_severity = [i for i in issues if i['severity'] == 'high']
        
        if high_severity:
            self.issues_found += len(high_severity)
            
            for issue in high_severity:
                alert = {
                    'type': 'code_issue',
                    'file': file_path,
                    'issue': issue,
                    'timestamp': datetime.now()
                }
                
                await self._send_alert(alert)
    
    async def _periodic_error_scan(self) -> None:
        """Scan periódico de erros no projeto."""
        while self.is_running:
            try:
                # Aguarda intervalo
                await asyncio.sleep(self.config['scan_interval'])
                
                # Executa scan
                errors = await self.error_detector.scan_project(str(self.project_path))
                
                critical_errors = [e for e in errors if e.severity == 'critical']
                
                if critical_errors:
                    for error in critical_errors:
                        if self.config['auto_fix'] and error.auto_fixable:
                            fixed = await self.error_detector.auto_fix_error(error)
                            if fixed:
                                self.auto_fixes += 1
                        else:
                            await self._send_alert({
                                'type': 'critical_error',
                                'error': error,
                                'timestamp': datetime.now()
                            })
                
            except Exception as e:
                print(f"Erro no scan periódico: {e}")
    
    async def _periodic_performance_check(self) -> None:
        """Verificação periódica de performance."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['performance_check_interval'])
                
                # Análise de performance
                from ..analysis.performance import PerformanceAnalyzer
                analyzer = PerformanceAnalyzer(self.gemini_client, None)
                
                metrics, issues = await analyzer.analyze_project_performance(
                    str(self.project_path)
                )
                
                # Registra métricas
                self.metrics['performance_scores'].append({
                    'timestamp': datetime.now(),
                    'cpu': metrics.cpu_usage,
                    'memory': metrics.memory_usage,
                    'issues': len(issues)
                })
                
                # Auto-otimiza se necessário
                high_impact = [i for i in issues if i.impact == 'high']
                if high_impact and self.config['auto_fix']:
                    for issue in high_impact[:3]:  # Limita otimizações
                        if issue.auto_optimizable:
                            optimized = await analyzer.optimize_code(issue)
                            if optimized:
                                self.auto_fixes += 1
                
            except Exception as e:
                print(f"Erro na verificação de performance: {e}")
    
    async def _periodic_health_check(self) -> None:
        """Verificação periódica de saúde do projeto."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['health_check_interval'])
                
                health = await self.health_monitor.full_health_check(
                    str(self.project_path)
                )
                
                # Alerta se saúde crítica
                if health.status == 'critical':
                    await self._send_alert({
                        'type': 'health_critical',
                        'health': health,
                        'timestamp': datetime.now()
                    })
                
                # Executa recomendações automáticas
                if self.config['auto_fix'] and health.recommendations:
                    for rec in health.recommendations[:2]:  # Limita ações
                        await self._execute_recommendation(rec)
                
            except Exception as e:
                print(f"Erro na verificação de saúde: {e}")
    
    async def _system_metrics_collector(self) -> None:
        """Coleta métricas do sistema continuamente."""
        while self.is_running:
            try:
                # Coleta métricas
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                metric = {
                    'timestamp': datetime.now(),
                    'cpu': cpu_percent,
                    'memory': memory.percent,
                    'memory_mb': memory.used / 1024 / 1024
                }
                
                self.metrics['cpu_usage'].append(metric['cpu'])
                self.metrics['memory_usage'].append(metric['memory'])
                
                # Limita histórico
                for key in ['cpu_usage', 'memory_usage']:
                    if len(self.metrics[key]) > 1000:
                        self.metrics[key] = self.metrics[key][-500:]
                
                # Alerta se limites excedidos
                if cpu_percent > self.config['cpu_limit_percent']:
                    await self._send_alert({
                        'type': 'high_cpu',
                        'value': cpu_percent,
                        'timestamp': datetime.now()
                    })
                
                if metric['memory_mb'] > self.config['memory_limit_mb']:
                    await self._send_alert({
                        'type': 'high_memory',
                        'value': metric['memory_mb'],
                        'timestamp': datetime.now()
                    })
                
                await asyncio.sleep(10)  # Coleta a cada 10 segundos
                
            except Exception as e:
                print(f"Erro na coleta de métricas: {e}")
                await asyncio.sleep(60)
    
    async def _auto_optimizer(self) -> None:
        """Otimizador automático que melhora o código proativamente."""
        while self.is_running:
            try:
                # Aguarda 1 hora
                await asyncio.sleep(3600)
                
                # Analisa padrões de uso
                patterns = self._analyze_usage_patterns()
                
                if patterns['frequent_errors']:
                    # Cria soluções preventivas
                    await self._create_preventive_solutions(patterns['frequent_errors'])
                
                if patterns['performance_bottlenecks']:
                    # Otimiza gargalos identificados
                    await self._optimize_bottlenecks(patterns['performance_bottlenecks'])
                
                if patterns['repeated_tasks']:
                    # Sugere automações
                    await self._suggest_automations(patterns['repeated_tasks'])
                
            except Exception as e:
                print(f"Erro no auto-otimizador: {e}")
    
    def _detect_change_patterns(self) -> None:
        """Detecta padrões nas mudanças de arquivo."""
        recent_changes = self.metrics['file_changes'][-20:]
        
        if len(recent_changes) < 5:
            return
        
        # Detecta mudanças rápidas (possível problema)
        time_diffs = []
        for i in range(1, len(recent_changes)):
            diff = (recent_changes[i]['timestamp'] - recent_changes[i-1]['timestamp']).total_seconds()
            time_diffs.append(diff)
        
        avg_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        
        if avg_diff < 5:  # Mudanças muito rápidas
            self.memory.detect_pattern(
                'rapid_changes',
                f"Mudanças rápidas detectadas ({avg_diff:.1f}s entre mudanças)",
                "Possível loop de erro ou problema de desenvolvimento"
            )
    
    def _analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analisa padrões de uso do projeto."""
        patterns = {
            'frequent_errors': [],
            'performance_bottlenecks': [],
            'repeated_tasks': [],
            'common_files': []
        }
        
        # Analisa erros frequentes
        error_counts = {}
        for error in self.metrics['errors_detected'][-100:]:
            key = f"{error.get('type')}:{error.get('file', 'unknown')}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        patterns['frequent_errors'] = [
            {'error': k, 'count': v} 
            for k, v in error_counts.items() 
            if v > 3
        ]
        
        # Identifica arquivos mais modificados
        file_counts = {}
        for change in self.metrics['file_changes'][-200:]:
            file_counts[change['file']] = file_counts.get(change['file'], 0) + 1
        
        patterns['common_files'] = sorted(
            file_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return patterns
    
    async def _attempt_auto_fix(self, file_path: str, error: Exception) -> bool:
        """Tenta corrigir erro automaticamente."""
        try:
            prompt = f"""
            Corrija este erro Python automaticamente:
            
            Arquivo: {file_path}
            Erro: {type(error).__name__}: {str(error)}
            Linha: {getattr(error, 'lineno', 'unknown')}
            
            Retorne apenas o código corrigido do arquivo completo.
            Mantenha toda a funcionalidade original.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código
            import re
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1)
                
                # Backup antes de sobrescrever
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(file_path, backup_path)
                
                # Aplica correção
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                
                return True
                
        except Exception as e:
            print(f"Erro ao tentar auto-fix: {e}")
        
        return False
    
    async def _send_alert(self, alert: Dict[str, Any]) -> None:
        """Envia alerta para callbacks registrados."""
        # Adiciona contexto
        alert['project'] = str(self.project_path)
        alert['monitor_uptime'] = str(datetime.now() - self.start_time)
        
        # Notifica callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                print(f"Erro em callback de alerta: {e}")
        
        # Log no sistema
        self.memory.remember_conversation(
            f"ALERTA: {alert['type']}",
            json.dumps(alert, default=str),
            success=False,
            error=alert.get('message', '')
        )
    
    async def _execute_recommendation(self, recommendation: str) -> None:
        """Executa recomendação automática."""
        # Mapeia recomendações para ações
        action_map = {
            'Corrija os erros críticos': self._fix_critical_errors,
            'Otimize os gargalos de performance': self._optimize_performance,
            'Adicione mais testes': self._generate_tests,
            'Documente funções e classes': self._generate_documentation
        }
        
        for key, action in action_map.items():
            if key in recommendation:
                try:
                    await action()
                    break
                except Exception as e:
                    print(f"Erro ao executar recomendação '{recommendation}': {e}")
    
    async def _fix_critical_errors(self) -> None:
        """Corrige erros críticos automaticamente."""
        errors = await self.error_detector.scan_project(str(self.project_path))
        critical = [e for e in errors if e.severity == 'critical' and e.auto_fixable]
        
        for error in critical[:5]:  # Limita
            await self.error_detector.auto_fix_error(error)
            self.auto_fixes += 1
    
    async def _optimize_performance(self) -> None:
        """Otimiza performance automaticamente."""
        from ..analysis.performance import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer(self.gemini_client, None)
        
        _, issues = await analyzer.analyze_project_performance(str(self.project_path))
        
        for issue in issues[:3]:  # Limita
            if issue.auto_optimizable:
                await analyzer.optimize_code(issue)
                self.auto_fixes += 1
    
    async def _generate_tests(self) -> None:
        """Gera testes automaticamente."""
        from ..development.code_generator import CodeGenerator
        generator = CodeGenerator(self.gemini_client, None)
        
        # Encontra arquivos sem testes
        python_files = list(self.project_path.rglob("*.py"))
        
        for file in python_files[:2]:  # Limita
            if 'test' not in file.name:
                test_file = file.parent / f"test_{file.name}"
                if not test_file.exists():
                    with open(file, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    tests = await generator.generate_tests(code)
                    
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(tests)
    
    async def _generate_documentation(self) -> None:
        """Gera documentação automaticamente."""
        from ..development.code_generator import CodeGenerator
        generator = CodeGenerator(self.gemini_client, None)
        
        # Documenta arquivos principais
        main_files = list(self.project_path.glob("*.py"))
        
        for file in main_files[:3]:  # Limita
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if '"""' not in code[:100]:  # Sem docstring
                docs = await generator.generate_documentation(code)
                
                # Adiciona docstring no início
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(f'"""\n{docs}\n"""\n\n{code}')
    
    async def _create_preventive_solutions(self, frequent_errors: List[Dict]) -> None:
        """Cria soluções preventivas para erros frequentes."""
        for error_info in frequent_errors:
            # Analisa padrão do erro
            error_type = error_info['error'].split(':')[0]
            
            # Cria validações preventivas
            if error_type == 'syntax_error':
                # Adiciona pre-commit hooks
                await self._setup_pre_commit_hooks()
            elif error_type == 'import_error':
                # Atualiza requirements
                await self._update_requirements()
    
    async def _optimize_bottlenecks(self, bottlenecks: List[Dict]) -> None:
        """Otimiza gargalos de performance identificados."""
        for bottleneck in bottlenecks:
            # Implementa otimizações específicas
            pass
    
    async def _suggest_automations(self, repeated_tasks: List[Dict]) -> None:
        """Sugere automações para tarefas repetitivas."""
        suggestions = []
        
        for task in repeated_tasks:
            if task['type'] == 'file_creation':
                suggestions.append({
                    'task': 'Criação de arquivos similar',
                    'suggestion': 'Criar template ou generator',
                    'command': 'gemini-code create-template'
                })
        
        if suggestions:
            self.memory.remember_decision(
                'automation_suggestion',
                'Sugestões de automação baseadas em padrões',
                'Tarefas repetitivas detectadas',
                [s['suggestion'] for s in suggestions],
                'pending'
            )
    
    def stop_monitoring(self) -> None:
        """Para o monitoramento."""
        self.is_running = False
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do monitoramento."""
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        return {
            'running': self.is_running,
            'uptime': str(uptime),
            'events_count': self.events_count,
            'issues_found': self.issues_found,
            'auto_fixes': self.auto_fixes,
            'current_metrics': {
                'cpu': self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else 0,
                'memory': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
                'recent_changes': len(self.metrics['file_changes'][-10:])
            }
        }
    
    def register_event_callback(self, callback: Callable) -> None:
        """Registra callback para eventos."""
        self.event_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Registra callback para alertas."""
        self.alert_callbacks.append(callback)