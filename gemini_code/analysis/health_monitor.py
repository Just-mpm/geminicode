"""
Monitor de saúde do projeto que acompanha qualidade e estado geral.
"""

import json
import time
import asyncio
import ast
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem
from .error_detector import ErrorDetector
from .performance import PerformanceAnalyzer


@dataclass
class HealthMetric:
    """Métrica de saúde do projeto."""
    name: str
    value: float
    threshold: float
    status: str  # 'good', 'warning', 'critical'
    description: str
    trend: str  # 'improving', 'stable', 'declining'
    last_updated: datetime


@dataclass
class ProjectHealth:
    """Estado geral de saúde do projeto."""
    overall_score: float
    status: str  # 'healthy', 'needs_attention', 'critical'
    metrics: List[HealthMetric]
    recommendations: List[str]
    last_scan: datetime
    scan_duration: float


class HealthMonitor:
    """Monitora saúde contínua do projeto."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.error_detector = ErrorDetector(gemini_client, file_manager)
        self.performance_analyzer = PerformanceAnalyzer(gemini_client, file_manager)
        self.health_history: List[ProjectHealth] = []
        self.monitoring_config = self._load_monitoring_config()
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Carrega configuração de monitoramento."""
        return {
            'error_threshold': 5,  # Máximo de erros aceitáveis
            'complexity_threshold': 10.0,  # Complexidade máxima por função
            'file_size_threshold': 1000,  # Linhas máximas por arquivo
            'performance_threshold': 100,  # ms máximo para operações
            'test_coverage_threshold': 80.0,  # % mínimo de cobertura
            'code_quality_threshold': 7.0,  # Score mínimo de qualidade (0-10)
            'security_threshold': 0,  # Vulnerabilidades máximas
            'documentation_threshold': 60.0,  # % mínimo de documentação
            'scan_interval': 300,  # Segundos entre scans automáticos
            'alert_on_decline': True,  # Alerta quando métricas pioram
            'auto_fix_enabled': True  # Correção automática ativada
        }
    
    async def full_health_check(self, project_path: str) -> ProjectHealth:
        """Executa verificação completa de saúde."""
        start_time = time.time()
        
        print("🔍 Iniciando verificação de saúde do projeto...")
        
        # Coleta todas as métricas
        metrics = []
        
        # 1. Erros e problemas
        error_metric = await self._check_errors(project_path)
        metrics.append(error_metric)
        
        # 2. Performance
        performance_metric = await self._check_performance(project_path)
        metrics.append(performance_metric)
        
        # 3. Qualidade de código
        quality_metric = await self._check_code_quality(project_path)
        metrics.append(quality_metric)
        
        # 4. Complexidade
        complexity_metric = await self._check_complexity(project_path)
        metrics.append(complexity_metric)
        
        # 5. Cobertura de testes
        test_metric = await self._check_test_coverage(project_path)
        metrics.append(test_metric)
        
        # 6. Segurança
        security_metric = await self._check_security(project_path)
        metrics.append(security_metric)
        
        # 7. Documentação
        docs_metric = await self._check_documentation(project_path)
        metrics.append(docs_metric)
        
        # 8. Estrutura do projeto
        structure_metric = await self._check_project_structure(project_path)
        metrics.append(structure_metric)
        
        # Calcula score geral e gera recomendações
        overall_score = self._calculate_overall_score(metrics)
        status = self._determine_status(overall_score)
        recommendations = await self._generate_recommendations(metrics, project_path)
        
        # Atualiza tendências
        self._update_trends(metrics)
        
        health = ProjectHealth(
            overall_score=overall_score,
            status=status,
            metrics=metrics,
            recommendations=recommendations,
            last_scan=datetime.now(),
            scan_duration=time.time() - start_time
        )
        
        # Salva no histórico
        self.health_history.append(health)
        await self._save_health_report(health, project_path)
        
        return health
    
    async def _check_errors(self, project_path: str) -> HealthMetric:
        """Verifica erros no projeto."""
        try:
            errors = await self.error_detector.scan_project(project_path)
            
            critical_errors = len([e for e in errors if e.severity == 'critical'])
            high_errors = len([e for e in errors if e.severity == 'high'])
            total_errors = len(errors)
            
            # Score baseado na severidade dos erros
            error_score = max(0, 100 - (critical_errors * 30 + high_errors * 15 + (total_errors - critical_errors - high_errors) * 5))
            
            status = 'good' if total_errors <= self.monitoring_config['error_threshold'] else ('warning' if total_errors <= self.monitoring_config['error_threshold'] * 2 else 'critical')
            
            return HealthMetric(
                name="Erros",
                value=error_score,
                threshold=self.monitoring_config['error_threshold'],
                status=status,
                description=f"{total_errors} erros encontrados ({critical_errors} críticos, {high_errors} altos)",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Erros",
                value=0,
                threshold=self.monitoring_config['error_threshold'],
                status="critical",
                description=f"Erro ao verificar: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_performance(self, project_path: str) -> HealthMetric:
        """Verifica performance do projeto."""
        try:
            metrics, issues = await self.performance_analyzer.analyze_project_performance(project_path)
            
            high_impact = len([i for i in issues if i.impact == 'high'])
            medium_impact = len([i for i in issues if i.impact == 'medium'])
            
            # Score baseado em problemas de performance
            perf_score = max(0, 100 - (high_impact * 20 + medium_impact * 10))
            
            status = 'good' if perf_score >= 80 else ('warning' if perf_score >= 60 else 'critical')
            
            return HealthMetric(
                name="Performance",
                value=perf_score,
                threshold=80,
                status=status,
                description=f"{len(issues)} problemas de performance ({high_impact} alto impacto)",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Performance",
                value=50,
                threshold=80,
                status="warning",
                description=f"Erro ao verificar performance: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_code_quality(self, project_path: str) -> HealthMetric:
        """Verifica qualidade de código usando IA."""
        try:
            # Analisa qualidade com IA (amostra de arquivos)
            python_files = list(Path(project_path).rglob("*.py"))[:5]  # Limita amostra
            
            quality_scores = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) > 5000:  # Arquivo muito grande
                        continue
                    
                    prompt = f"""
                    Analise a qualidade deste código Python e dê uma nota de 0 a 10:

                    ```python
                    {content}
                    ```

                    Considere:
                    - Legibilidade e clareza
                    - Boas práticas
                    - Estrutura e organização
                    - Nomes de variáveis/funções
                    - Comentários e documentação

                    Retorne apenas o número da nota (ex: 7.5)
                    """
                    
                    response = await self.gemini_client.generate_response(prompt)
                    
                    # Extrai nota da resposta
                    import re
                    score_match = re.search(r'(\d+\.?\d*)', response)
                    if score_match:
                        score = float(score_match.group(1))
                        quality_scores.append(min(10, max(0, score)))
                        
                except Exception:
                    continue
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5.0
            quality_score = (avg_quality / 10) * 100  # Converte para escala 0-100
            
            status = 'good' if avg_quality >= self.monitoring_config['code_quality_threshold'] else ('warning' if avg_quality >= 5.0 else 'critical')
            
            return HealthMetric(
                name="Qualidade de Código",
                value=quality_score,
                threshold=self.monitoring_config['code_quality_threshold'] * 10,
                status=status,
                description=f"Qualidade média: {avg_quality:.1f}/10 (baseado em {len(quality_scores)} arquivos)",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Qualidade de Código",
                value=50,
                threshold=70,
                status="warning",
                description=f"Erro ao verificar qualidade: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_complexity(self, project_path: str) -> HealthMetric:
        """Verifica complexidade do código."""
        try:
            total_complexity = 0
            function_count = 0
            high_complexity_functions = 0
            
            for file_path in Path(project_path).rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import ast
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            complexity = self._calculate_function_complexity(node)
                            total_complexity += complexity
                            function_count += 1
                            
                            if complexity > self.monitoring_config['complexity_threshold']:
                                high_complexity_functions += 1
                                
                except Exception:
                    continue
            
            avg_complexity = total_complexity / max(function_count, 1)
            
            # Score baseado na complexidade média
            complexity_score = max(0, 100 - (avg_complexity - 5) * 10)
            
            status = 'good' if avg_complexity <= self.monitoring_config['complexity_threshold'] else ('warning' if avg_complexity <= 15 else 'critical')
            
            return HealthMetric(
                name="Complexidade",
                value=complexity_score,
                threshold=self.monitoring_config['complexity_threshold'],
                status=status,
                description=f"Complexidade média: {avg_complexity:.1f} ({high_complexity_functions} funções complexas)",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Complexidade",
                value=50,
                threshold=10,
                status="warning",
                description=f"Erro ao calcular complexidade: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complexidade ciclomática de uma função."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    async def _check_test_coverage(self, project_path: str) -> HealthMetric:
        """Verifica cobertura de testes."""
        try:
            # Conta arquivos de teste
            test_files = list(Path(project_path).rglob("test_*.py"))
            test_files.extend(Path(project_path).rglob("*_test.py"))
            test_files.extend(Path(project_path).rglob("tests/*.py"))
            
            # Conta arquivos de código
            code_files = [f for f in Path(project_path).rglob("*.py") 
                         if not any(test_pattern in str(f) for test_pattern in ['test_', '_test', '/tests/'])]
            
            # Estima cobertura baseada na proporção de arquivos de teste
            if code_files:
                coverage_ratio = len(test_files) / len(code_files)
                estimated_coverage = min(100, coverage_ratio * 80)  # Estimativa conservadora
            else:
                estimated_coverage = 0
            
            status = 'good' if estimated_coverage >= self.monitoring_config['test_coverage_threshold'] else ('warning' if estimated_coverage >= 50 else 'critical')
            
            return HealthMetric(
                name="Cobertura de Testes",
                value=estimated_coverage,
                threshold=self.monitoring_config['test_coverage_threshold'],
                status=status,
                description=f"~{estimated_coverage:.1f}% cobertura estimada ({len(test_files)} arquivos de teste)",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Cobertura de Testes",
                value=0,
                threshold=80,
                status="critical",
                description=f"Erro ao verificar testes: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_security(self, project_path: str) -> HealthMetric:
        """Verifica vulnerabilidades de segurança."""
        try:
            vulnerabilities = []
            
            # Padrões de segurança conhecidos
            security_patterns = [
                (r'eval\s*\(', 'Uso de eval() é perigoso'),
                (r'exec\s*\(', 'Uso de exec() é perigoso'),
                (r'shell=True', 'subprocess com shell=True pode ser vulnerável'),
                (r'password\s*=\s*["\'][^"\']+["\']', 'Senha hardcoded no código'),
                (r'api_key\s*=\s*["\'][^"\']+["\']', 'API key hardcoded no código'),
                (r'SECRET_KEY\s*=\s*["\'][^"\']+["\']', 'Secret key hardcoded no código'),
                (r'input\s*\(', 'input() pode ser vulnerável a injection'),
            ]
            
            for file_path in Path(project_path).rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for pattern, description in security_patterns:
                        import re
                        if re.search(pattern, content, re.IGNORECASE):
                            vulnerabilities.append({
                                'file': str(file_path),
                                'issue': description,
                                'pattern': pattern
                            })
                            
                except Exception:
                    continue
            
            vuln_count = len(vulnerabilities)
            security_score = max(0, 100 - vuln_count * 20)
            
            status = 'good' if vuln_count <= self.monitoring_config['security_threshold'] else ('warning' if vuln_count <= 3 else 'critical')
            
            return HealthMetric(
                name="Segurança",
                value=security_score,
                threshold=self.monitoring_config['security_threshold'],
                status=status,
                description=f"{vuln_count} possíveis vulnerabilidades encontradas",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Segurança",
                value=50,
                threshold=0,
                status="warning",
                description=f"Erro ao verificar segurança: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_documentation(self, project_path: str) -> HealthMetric:
        """Verifica qualidade da documentação."""
        try:
            total_functions = 0
            documented_functions = 0
            
            for file_path in Path(project_path).rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import ast
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            total_functions += 1
                            if ast.get_docstring(node):
                                documented_functions += 1
                                
                except Exception:
                    continue
            
            if total_functions > 0:
                doc_percentage = (documented_functions / total_functions) * 100
            else:
                doc_percentage = 100  # Sem funções = sem problema de documentação
            
            status = 'good' if doc_percentage >= self.monitoring_config['documentation_threshold'] else ('warning' if doc_percentage >= 30 else 'critical')
            
            return HealthMetric(
                name="Documentação",
                value=doc_percentage,
                threshold=self.monitoring_config['documentation_threshold'],
                status=status,
                description=f"{doc_percentage:.1f}% funções documentadas ({documented_functions}/{total_functions})",
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Documentação",
                value=0,
                threshold=60,
                status="critical",
                description=f"Erro ao verificar documentação: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    async def _check_project_structure(self, project_path: str) -> HealthMetric:
        """Verifica estrutura do projeto."""
        try:
            score = 100
            issues = []
            
            # Verifica arquivos essenciais
            essential_files = ['README.md', 'requirements.txt', '.gitignore']
            for file_name in essential_files:
                if not Path(project_path, file_name).exists():
                    score -= 15
                    issues.append(f"Falta {file_name}")
            
            # Verifica estrutura de pastas
            if not any(Path(project_path).iterdir()):
                score -= 30
                issues.append("Projeto vazio")
            
            # Verifica se há arquivos Python
            python_files = list(Path(project_path).rglob("*.py"))
            if not python_files:
                score -= 40
                issues.append("Nenhum arquivo Python encontrado")
            
            # Verifica tamanho dos arquivos
            large_files = []
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = len(f.readlines())
                    
                    if line_count > self.monitoring_config['file_size_threshold']:
                        large_files.append((file_path.name, line_count))
                        score -= 5
                        
                except Exception:
                    continue
            
            if large_files:
                issues.append(f"{len(large_files)} arquivos muito grandes")
            
            status = 'good' if score >= 80 else ('warning' if score >= 60 else 'critical')
            
            description = f"Score estrutural: {score}/100"
            if issues:
                description += f" ({', '.join(issues)})"
            
            return HealthMetric(
                name="Estrutura do Projeto",
                value=score,
                threshold=80,
                status=status,
                description=description,
                trend="stable",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            return HealthMetric(
                name="Estrutura do Projeto",
                value=50,
                threshold=80,
                status="warning",
                description=f"Erro ao verificar estrutura: {e}",
                trend="stable",
                last_updated=datetime.now()
            )
    
    def _calculate_overall_score(self, metrics: List[HealthMetric]) -> float:
        """Calcula score geral ponderado."""
        weights = {
            'Erros': 0.25,
            'Performance': 0.20,
            'Qualidade de Código': 0.15,
            'Complexidade': 0.10,
            'Cobertura de Testes': 0.10,
            'Segurança': 0.15,
            'Documentação': 0.05,
            'Estrutura do Projeto': 0.05
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for metric in metrics:
            weight = weights.get(metric.name, 0.1)
            weighted_sum += metric.value * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _determine_status(self, score: float) -> str:
        """Determina status geral baseado no score."""
        if score >= 80:
            return 'healthy'
        elif score >= 60:
            return 'needs_attention'
        else:
            return 'critical'
    
    async def _generate_recommendations(self, metrics: List[HealthMetric], project_path: str) -> List[str]:
        """Gera recomendações baseadas nas métricas."""
        recommendations = []
        
        for metric in metrics:
            if metric.status == 'critical':
                if metric.name == 'Erros':
                    recommendations.append("🚨 Corrija os erros críticos imediatamente")
                elif metric.name == 'Performance':
                    recommendations.append("⚡ Otimize os gargalos de performance")
                elif metric.name == 'Segurança':
                    recommendations.append("🔒 Resolva as vulnerabilidades de segurança")
                elif metric.name == 'Estrutura do Projeto':
                    recommendations.append("📁 Melhore a estrutura do projeto")
            
            elif metric.status == 'warning':
                if metric.name == 'Qualidade de Código':
                    recommendations.append("✨ Refatore código para melhorar legibilidade")
                elif metric.name == 'Complexidade':
                    recommendations.append("🔧 Simplifique funções complexas")
                elif metric.name == 'Cobertura de Testes':
                    recommendations.append("🧪 Adicione mais testes")
                elif metric.name == 'Documentação':
                    recommendations.append("📖 Documente funções e classes")
        
        # Recomendações gerais baseadas no score
        overall_score = self._calculate_overall_score(metrics)
        if overall_score < 70:
            recommendations.append("📋 Execute correções automáticas disponíveis")
            recommendations.append("🔄 Monitore mudanças regularmente")
        
        return recommendations[:5]  # Limita a 5 recomendações
    
    def _update_trends(self, current_metrics: List[HealthMetric]) -> None:
        """Atualiza tendências baseadas no histórico."""
        if len(self.health_history) < 2:
            return
        
        previous_health = self.health_history[-1]
        previous_metrics = {m.name: m.value for m in previous_health.metrics}
        
        for metric in current_metrics:
            if metric.name in previous_metrics:
                current_value = metric.value
                previous_value = previous_metrics[metric.name]
                
                if current_value > previous_value + 5:
                    metric.trend = "improving"
                elif current_value < previous_value - 5:
                    metric.trend = "declining"
                else:
                    metric.trend = "stable"
    
    async def _save_health_report(self, health: ProjectHealth, project_path: str) -> None:
        """Salva relatório de saúde em arquivo."""
        try:
            reports_dir = Path(project_path) / '.gemini_code' / 'health_reports'
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Converte para JSON serializável
            health_dict = asdict(health)
            health_dict['last_scan'] = health.last_scan.isoformat()
            
            for metric in health_dict['metrics']:
                metric['last_updated'] = datetime.fromisoformat(metric['last_updated']).isoformat()
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(health_dict, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")
    
    async def get_health_summary(self, health: ProjectHealth) -> str:
        """Gera resumo visual da saúde do projeto."""
        status_emoji = {
            'healthy': '✅',
            'needs_attention': '⚠️',
            'critical': '🚨'
        }
        
        summary = f"{status_emoji[health.status]} **Status Geral: {health.status.replace('_', ' ').title()}**\n"
        summary += f"📊 **Score Geral: {health.overall_score:.1f}/100**\n\n"
        
        # Métricas por status
        summary += "📋 **Métricas Detalhadas:**\n"
        
        for metric in health.metrics:
            emoji = {'good': '✅', 'warning': '⚠️', 'critical': '🚨'}[metric.status]
            trend_emoji = {'improving': '📈', 'stable': '➡️', 'declining': '📉'}[metric.trend]
            
            summary += f"{emoji} {trend_emoji} **{metric.name}**: {metric.value:.1f}\n"
            summary += f"   {metric.description}\n"
        
        summary += f"\n⏱️ **Última verificação**: {health.last_scan.strftime('%H:%M:%S')}\n"
        summary += f"🕐 **Duração**: {health.scan_duration:.1f}s\n"
        
        # Recomendações
        if health.recommendations:
            summary += "\n🎯 **Recomendações Prioritárias:**\n"
            for i, rec in enumerate(health.recommendations[:3], 1):
                summary += f"{i}. {rec}\n"
        
        return summary
    
    async def monitor_continuously(self, project_path: str, callback=None) -> None:
        """Monitora projeto continuamente."""
        print(f"🔄 Iniciando monitoramento contínuo de {project_path}")
        
        while True:
            try:
                health = await self.full_health_check(project_path)
                
                if callback:
                    await callback(health)
                
                # Verifica se precisa alertar
                if health.status == 'critical' and self.monitoring_config['alert_on_decline']:
                    print(f"🚨 ALERTA: Projeto em estado crítico! Score: {health.overall_score:.1f}")
                
                # Aguarda próximo scan
                await asyncio.sleep(self.monitoring_config['scan_interval'])
                
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                await asyncio.sleep(60)  # Retry em 1 minuto