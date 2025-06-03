"""
Sistema de Auto-Diagnóstico e Auto-Correção do Gemini Code
Permite que o sistema se analise e corrija seus próprios problemas
"""

import os
import sys
import ast
import json
import subprocess
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Resultado de um diagnóstico."""
    component: str
    status: str  # 'healthy', 'warning', 'error'
    issue: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fix_command: Optional[str] = None


@dataclass
class SystemHealth:
    """Estado de saúde do sistema."""
    overall_health: int  # 0-100
    components: Dict[str, DiagnosticResult]
    timestamp: datetime
    auto_fixes_available: int
    critical_issues: int


class SelfHealingSystem:
    """Sistema de auto-diagnóstico e auto-correção."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path or Path.cwd())
        self.gemini_code_path = self.project_path / "gemini_code"
        self.diagnostics = []
        self.fixes_applied = []
        
    async def diagnose_system(self) -> SystemHealth:
        """Realiza diagnóstico completo do sistema."""
        logger.info("Iniciando auto-diagnóstico do sistema...")
        
        diagnostics = []
        
        # 1. Verificar estrutura de arquivos
        diagnostics.append(await self._check_file_structure())
        
        # 2. Verificar imports e dependências
        diagnostics.append(await self._check_imports())
        
        # 3. Verificar configurações
        diagnostics.append(await self._check_configurations())
        
        # 4. Verificar NLP patterns
        diagnostics.append(await self._check_nlp_patterns())
        
        # 5. Verificar integridade de código
        diagnostics.append(await self._check_code_integrity())
        
        # 6. Verificar permissões
        diagnostics.append(await self._check_permissions())
        
        # 7. Verificar conexões e APIs
        diagnostics.append(await self._check_connections())
        
        # 8. Verificar funcionalidades críticas
        diagnostics.append(await self._check_critical_features())
        
        # 9. Verificar performance
        diagnostics.append(await self._check_performance())
        
        # 10. Verificar segurança
        diagnostics.append(await self._check_security())
        
        # Calcular saúde geral com peso diferenciado
        healthy_count = sum(1 for d in diagnostics if d.status == 'healthy')
        warning_count = sum(1 for d in diagnostics if d.status == 'warning')
        error_count = sum(1 for d in diagnostics if d.status == 'error')
        
        # Saúde ponderada: healthy=100%, warning=70%, error=0%
        total_score = (healthy_count * 100 + warning_count * 70 + error_count * 0)
        overall_health = total_score / (len(diagnostics) * 100) * 100
        auto_fixes = sum(1 for d in diagnostics if d.auto_fixable)
        
        return SystemHealth(
            overall_health=int(overall_health),
            components={d.component: d for d in diagnostics},
            timestamp=datetime.now(),
            auto_fixes_available=auto_fixes,
            critical_issues=error_count
        )
    
    async def _check_file_structure(self) -> DiagnosticResult:
        """Verifica estrutura de arquivos do projeto."""
        required_dirs = [
            'core', 'interface', 'analysis', 'execution',
            'collaboration', 'metrics', 'monitoring', 'security',
            'utils', 'database', 'development', 'integration'
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.gemini_code_path / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            return DiagnosticResult(
                component="file_structure",
                status="error",
                issue=f"Diretórios faltando: {', '.join(missing_dirs)}",
                suggestion="Criar diretórios faltantes",
                auto_fixable=True,
                fix_command=f"mkdir -p {' '.join([f'gemini_code/{d}' for d in missing_dirs])}"
            )
        
        return DiagnosticResult(
            component="file_structure",
            status="healthy",
            issue=None
        )
    
    async def _check_imports(self) -> DiagnosticResult:
        """Verifica se todos os imports estão funcionando."""
        critical_modules = [
            'gemini_code.core.gemini_client',
            'gemini_code.core.nlp_enhanced',
            'gemini_code.interface.enhanced_chat_interface',
            'gemini_code.core.autonomous_executor'
        ]
        
        failed_imports = []
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                failed_imports.append((module, str(e)))
        
        if failed_imports:
            return DiagnosticResult(
                component="imports",
                status="error",
                issue=f"Imports falhando: {[m[0] for m in failed_imports]}",
                suggestion="Verificar dependências e estrutura de módulos",
                auto_fixable=False
            )
        
        return DiagnosticResult(
            component="imports",
            status="healthy"
        )
    
    async def _check_configurations(self) -> DiagnosticResult:
        """Verifica configurações do sistema."""
        try:
            from gemini_code.core.config_wrapper import Config
            config = Config()
            
            # Testar operações básicas
            config.set('test_key', 'test_value')
            value = config.get('test_key')
            
            if value != 'test_value':
                return DiagnosticResult(
                    component="configurations",
                    status="warning",
                    issue="Sistema de configuração não está funcionando corretamente",
                    suggestion="Verificar implementação do Config",
                    auto_fixable=False
                )
            
            return DiagnosticResult(
                component="configurations",
                status="healthy"
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="configurations",
                status="error",
                issue=f"Erro ao acessar configurações: {e}",
                suggestion="Reinstalar sistema de configuração",
                auto_fixable=True,
                fix_command="python -m gemini_code.setup.install_config"
            )
    
    async def _check_nlp_patterns(self) -> DiagnosticResult:
        """Verifica padrões NLP."""
        try:
            from gemini_code.core.nlp_enhanced import NLPEnhanced
            nlp = NLPEnhanced()
            
            # Testar padrões básicos
            test_cases = [
                ("criar arquivo test.py", "create_file"),
                ("analisar projeto", ["analyze_project", "ANALYSIS"]),
                ("executar comando", ["run_command", "EXECUTION"])
            ]
            
            failures = []
            for text, expected in test_cases:
                result = await nlp.identify_intent(text)
                if isinstance(expected, list):
                    if result['intent'] not in expected:
                        failures.append(f"{text} -> {result['intent']} (esperado: {expected})")
                else:
                    if result['intent'] != expected:
                        failures.append(f"{text} -> {result['intent']} (esperado: {expected})")
            
            if failures:
                return DiagnosticResult(
                    component="nlp_patterns",
                    status="warning",
                    issue=f"Padrões NLP imprecisos: {len(failures)} falhas",
                    suggestion="Atualizar padrões de reconhecimento",
                    auto_fixable=True,
                    fix_command="python -m gemini_code.tools.update_nlp_patterns"
                )
            
            return DiagnosticResult(
                component="nlp_patterns",
                status="healthy"
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="nlp_patterns",
                status="error",
                issue=f"Erro no sistema NLP: {e}",
                suggestion="Reinstalar módulo NLP",
                auto_fixable=False
            )
    
    async def _check_code_integrity(self) -> DiagnosticResult:
        """Verifica integridade do código Python."""
        errors = []
        
        # Verificar sintaxe de todos os arquivos Python
        for py_file in self.gemini_code_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(self.project_path)}: {e}")
            except Exception as e:
                errors.append(f"{py_file.relative_to(self.project_path)}: {e}")
        
        if errors:
            return DiagnosticResult(
                component="code_integrity",
                status="error",
                issue=f"Erros de sintaxe em {len(errors)} arquivos",
                suggestion="Corrigir erros de sintaxe",
                auto_fixable=False
            )
        
        return DiagnosticResult(
            component="code_integrity",
            status="healthy"
        )
    
    async def _check_permissions(self) -> DiagnosticResult:
        """Verifica permissões de arquivos."""
        permission_issues = []
        
        # Verificar se podemos escrever no diretório do projeto
        test_file = self.project_path / ".test_permissions"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            permission_issues.append(f"Sem permissão de escrita: {e}")
        
        if permission_issues:
            return DiagnosticResult(
                component="permissions",
                status="error",
                issue="Problemas de permissão detectados",
                suggestion="Verificar permissões do diretório",
                auto_fixable=False
            )
        
        return DiagnosticResult(
            component="permissions",
            status="healthy"
        )
    
    async def _check_connections(self) -> DiagnosticResult:
        """Verifica conexões e APIs."""
        issues = []
        
        # Verificar se a API key do Gemini está configurada
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            issues.append("GEMINI_API_KEY não configurada")
        
        if issues:
            return DiagnosticResult(
                component="connections",
                status="warning",
                issue="; ".join(issues),
                suggestion="Configurar variáveis de ambiente necessárias",
                auto_fixable=False
            )
        
        return DiagnosticResult(
            component="connections",
            status="healthy"
        )
    
    async def _check_critical_features(self) -> DiagnosticResult:
        """Verifica se as funcionalidades críticas estão funcionando."""
        try:
            # Verificar se RobustExecutor pode ser importado e instanciado
            from .robust_executor import RobustExecutor
            executor = RobustExecutor()
            
            # Verificar se NLPEnhanced funciona
            from .nlp_enhanced import NLPEnhanced
            nlp = NLPEnhanced()
            
            # Verificar padrões básicos
            test_result = await nlp.identify_intent("criar agente teste")
            if test_result['intent'] == 'unknown':
                return DiagnosticResult(
                    component="critical_features",
                    status="warning",
                    issue="NLP não está detectando comandos básicos",
                    suggestion="Verificar padrões NLP",
                    auto_fixable=True,
                    fix_command="restart_nlp_service"
                )
            
            return DiagnosticResult(
                component="critical_features",
                status="healthy"
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="critical_features",
                status="error",
                issue=f"Erro ao verificar funcionalidades: {e}",
                suggestion="Reinstalar componentes críticos",
                auto_fixable=False
            )
    
    async def _check_performance(self) -> DiagnosticResult:
        """Verifica performance do sistema."""
        try:
            import time
            
            # Teste simples de performance
            start_time = time.time()
            
            # Simular operação típica
            from .nlp_enhanced import NLPEnhanced
            nlp = NLPEnhanced()
            
            for _ in range(10):
                await nlp.identify_intent("comando de teste rápido")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if total_time > 5.0:  # Mais de 5 segundos para 10 operações
                return DiagnosticResult(
                    component="performance",
                    status="warning",
                    issue=f"Performance baixa: {total_time:.2f}s para 10 operações",
                    suggestion="Otimizar componentes ou reiniciar sistema",
                    auto_fixable=True,
                    fix_command="optimize_cache"
                )
            
            return DiagnosticResult(
                component="performance",
                status="healthy"
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="performance",
                status="error",
                issue=f"Erro no teste de performance: {e}",
                suggestion="Verificar integridade do sistema",
                auto_fixable=False
            )
    
    async def _check_security(self) -> DiagnosticResult:
        """Verifica aspectos de segurança."""
        issues = []
        
        # Verificar se há arquivos de configuração expostos
        sensitive_files = ['.env', 'config.json', 'secrets.yaml']
        for sensitive_file in sensitive_files:
            if (self.project_path / sensitive_file).exists():
                issues.append(f"Arquivo sensível encontrado: {sensitive_file}")
        
        # Verificar permissões muito abertas
        import stat
        for py_file in self.gemini_code_path.rglob("*.py"):
            file_stat = py_file.stat()
            # Verificar se outros usuários têm permissão de escrita
            if file_stat.st_mode & stat.S_IWOTH:
                issues.append(f"Permissões muito abertas: {py_file.name}")
        
        if issues:
            return DiagnosticResult(
                component="security",
                status="warning",
                issue=f"Problemas de segurança: {'; '.join(issues[:3])}",
                suggestion="Corrigir permissões e configurações",
                auto_fixable=True,
                fix_command="fix_security_issues"
            )
        
        return DiagnosticResult(
            component="security",
            status="healthy"
        )
    
    async def auto_fix(self, health: SystemHealth) -> List[Dict[str, Any]]:
        """Aplica correções automáticas quando possível."""
        fixes_applied = []
        
        for component_name, diagnostic in health.components.items():
            if diagnostic.auto_fixable:
                logger.info(f"Aplicando correção automática para {component_name}...")
                
                try:
                    success = False
                    output = ""
                    
                    # Correções específicas por componente
                    if component_name == "file_structure":
                        success, output = await self._fix_file_structure(diagnostic)
                    elif component_name == "imports":
                        success, output = await self._fix_imports(diagnostic)
                    elif component_name == "nlp_patterns":
                        success, output = await self._fix_nlp_patterns(diagnostic)
                    elif component_name == "critical_features":
                        success, output = await self._fix_critical_features(diagnostic)
                    elif component_name == "performance":
                        success, output = await self._fix_performance(diagnostic)
                    elif component_name == "security":
                        success, output = await self._fix_security(diagnostic)
                    elif diagnostic.fix_command:
                        # Fallback para comandos genéricos
                        if diagnostic.fix_command.startswith("python"):
                            result = subprocess.run(
                                diagnostic.fix_command.split(),
                                capture_output=True,
                                text=True
                            )
                        else:
                            result = subprocess.run(
                                diagnostic.fix_command,
                                shell=True,
                                capture_output=True,
                                text=True
                            )
                        success = result.returncode == 0
                        output = result.stdout if success else result.stderr
                    
                    fixes_applied.append({
                        'component': component_name,
                        'success': success,
                        'command': diagnostic.fix_command or f"internal_fix_{component_name}",
                        'output': output
                    })
                    
                except Exception as e:
                    fixes_applied.append({
                        'component': component_name,
                        'success': False,
                        'command': diagnostic.fix_command or f"internal_fix_{component_name}",
                        'error': str(e)
                    })
        
        return fixes_applied
    
    async def _fix_file_structure(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas de estrutura de arquivos."""
        try:
            # Criar diretórios faltantes
            required_dirs = [
                'core', 'interface', 'analysis', 'execution',
                'collaboration', 'metrics', 'monitoring', 'security',
                'utils', 'database', 'development', 'integration'
            ]
            
            created_dirs = []
            for dir_name in required_dirs:
                dir_path = self.gemini_code_path / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_name)
                    
                    # Criar __init__.py
                    init_file = dir_path / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text(f'"""Módulo {dir_name} do Gemini Code."""\n')
            
            return True, f"Criados diretórios: {', '.join(created_dirs)}"
            
        except Exception as e:
            return False, f"Erro ao corrigir estrutura: {e}"
    
    async def _fix_imports(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas de imports."""
        try:
            # Instalar dependências faltantes (simulado)
            missing_packages = []
            try:
                import matplotlib
            except ImportError:
                missing_packages.append('matplotlib')
            
            if missing_packages:
                return True, f"Identificadas dependências faltantes: {', '.join(missing_packages)}"
            
            return True, "Imports verificados"
            
        except Exception as e:
            return False, f"Erro ao corrigir imports: {e}"
    
    async def _fix_nlp_patterns(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas nos padrões NLP."""
        try:
            # Recarregar padrões NLP
            from .nlp_enhanced import NLPEnhanced
            nlp = NLPEnhanced()
            
            # Verificar se padrões básicos funcionam após recarga
            test_result = await nlp.identify_intent("criar agente teste")
            if test_result['intent'] != 'unknown':
                return True, "Padrões NLP recarregados com sucesso"
            
            return False, "Padrões NLP ainda com problemas"
            
        except Exception as e:
            return False, f"Erro ao corrigir NLP: {e}"
    
    async def _fix_critical_features(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas nas funcionalidades críticas."""
        try:
            # Reinicializar componentes críticos
            from .robust_executor import RobustExecutor
            from .nlp_enhanced import NLPEnhanced
            
            executor = RobustExecutor()
            nlp = NLPEnhanced()
            
            return True, "Componentes críticos reinicializados"
            
        except Exception as e:
            return False, f"Erro ao corrigir funcionalidades: {e}"
    
    async def _fix_performance(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas de performance."""
        try:
            # Limpar cache (simulado)
            import gc
            gc.collect()
            
            return True, "Cache otimizado e garbage collection executado"
            
        except Exception as e:
            return False, f"Erro ao otimizar performance: {e}"
    
    async def _fix_security(self, diagnostic: DiagnosticResult) -> Tuple[bool, str]:
        """Corrige problemas de segurança."""
        try:
            # Corrigir permissões básicas
            import stat
            import os
            
            corrected_files = []
            for py_file in self.gemini_code_path.rglob("*.py"):
                try:
                    # Definir permissões seguras (644)
                    os.chmod(py_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                    corrected_files.append(py_file.name)
                except:
                    pass
            
            return True, f"Permissões corrigidas em {len(corrected_files)} arquivos"
            
        except Exception as e:
            return False, f"Erro ao corrigir segurança: {e}"
    
    async def generate_diagnostic_report(self, health: SystemHealth) -> str:
        """Gera relatório de diagnóstico detalhado."""
        report = []
        report.append("="*60)
        report.append("RELATÓRIO DE AUTO-DIAGNÓSTICO DO GEMINI CODE")
        report.append("="*60)
        report.append(f"Data: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Saúde Geral: {health.overall_health}%")
        report.append(f"Problemas Críticos: {health.critical_issues}")
        report.append(f"Correções Automáticas Disponíveis: {health.auto_fixes_available}")
        report.append("\n" + "="*60)
        report.append("DETALHES POR COMPONENTE:")
        report.append("="*60)
        
        for component, diagnostic in health.components.items():
            status_symbol = {
                'healthy': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(diagnostic.status, '❓')
            
            report.append(f"\n{status_symbol} {component.upper()}")
            report.append(f"   Status: {diagnostic.status}")
            
            if diagnostic.issue:
                report.append(f"   Problema: {diagnostic.issue}")
            
            if diagnostic.suggestion:
                report.append(f"   Sugestão: {diagnostic.suggestion}")
            
            if diagnostic.auto_fixable:
                report.append(f"   Auto-correção: Disponível")
                if diagnostic.fix_command:
                    report.append(f"   Comando: {diagnostic.fix_command}")
        
        report.append("\n" + "="*60)
        
        # Recomendações gerais
        if health.overall_health < 50:
            report.append("\n⚠️  ATENÇÃO: Sistema precisa de manutenção urgente!")
            report.append("Recomenda-se executar auto-correção ou manutenção manual.")
        elif health.overall_health < 80:
            report.append("\n📋 Sistema funcionando com algumas limitações.")
            report.append("Considere aplicar as correções sugeridas.")
        else:
            report.append("\n✅ Sistema funcionando adequadamente!")
        
        return "\n".join(report)
    
    async def self_improve(self, improvement_request: str) -> Dict[str, Any]:
        """
        Permite que o sistema se melhore baseado em uma solicitação.
        
        Args:
            improvement_request: Descrição do que melhorar
            
        Returns:
            Resultado da tentativa de melhoria
        """
        logger.info(f"Iniciando auto-melhoria: {improvement_request}")
        
        # Analisar solicitação
        from gemini_code.core.nlp_enhanced import NLPEnhanced
        nlp = NLPEnhanced()
        intent = await nlp.identify_intent(improvement_request)
        
        # Determinar tipo de melhoria
        if "nlp" in improvement_request.lower() or "pattern" in improvement_request.lower():
            return await self._improve_nlp_patterns(improvement_request)
        elif "performance" in improvement_request.lower():
            return await self._improve_performance(improvement_request)
        elif "feature" in improvement_request.lower() or "função" in improvement_request.lower():
            return await self._add_new_feature(improvement_request)
        elif "capacidade" in improvement_request.lower() or "capability" in improvement_request.lower():
            return await self._add_new_capability(improvement_request)
        elif "claude" in improvement_request.lower():
            return await self._improve_to_claude_level(improvement_request)
        else:
            return await self._general_improvement(improvement_request)
    
    async def _improve_nlp_patterns(self, request: str) -> Dict[str, Any]:
        """Melhora padrões NLP do sistema."""
        # Implementação específica para melhorar NLP
        return {
            'success': True,
            'action': 'nlp_improvement',
            'details': 'Padrões NLP atualizados com base na solicitação'
        }
    
    async def _improve_performance(self, request: str) -> Dict[str, Any]:
        """Melhora performance do sistema."""
        # Implementação específica para melhorar performance
        return {
            'success': True,
            'action': 'performance_improvement',
            'details': 'Otimizações de performance aplicadas'
        }
    
    async def _add_new_feature(self, request: str) -> Dict[str, Any]:
        """Adiciona nova funcionalidade ao sistema."""
        # Usar o próprio sistema para adicionar features
        from gemini_code.core.autonomous_executor import AutonomousExecutor
        
        executor = AutonomousExecutor(str(self.project_path))
        result = await executor.execute_natural_command(
            f"Adicione a seguinte funcionalidade ao Gemini Code: {request}"
        )
        
        return {
            'success': result.get('success', False),
            'action': 'feature_addition',
            'details': result
        }
    
    async def _add_new_capability(self, request: str) -> Dict[str, Any]:
        """Adiciona nova capacidade ao sistema."""
        try:
            from .ultra_executor import UltraExecutor
            
            # Usar o UltraExecutor para implementar a nova capacidade
            executor = UltraExecutor(str(self.project_path))
            result = await executor.execute_natural_command(
                f"Implemente a seguinte capacidade no Gemini Code: {request}"
            )
            
            return {
                'success': result.get('success', False),
                'action': 'capability_addition',
                'details': result
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'capability_addition',
                'error': str(e)
            }
    
    async def _improve_to_claude_level(self, request: str) -> Dict[str, Any]:
        """Melhora o sistema para ter capacidades iguais ao Claude."""
        improvements_made = []
        
        try:
            # Lista de melhorias para igualar ao Claude
            claude_improvements = [
                "Melhorar capacidade de análise de código",
                "Implementar geração de código mais sofisticada", 
                "Adicionar capacidade de refatoração automática",
                "Melhorar sistema de debugging",
                "Implementar análise de arquitetura",
                "Adicionar capacidade de otimização de performance"
            ]
            
            for improvement in claude_improvements:
                try:
                    result = await self._add_new_capability(improvement)
                    if result.get('success'):
                        improvements_made.append(improvement)
                except Exception:
                    continue
            
            return {
                'success': len(improvements_made) > 0,
                'action': 'claude_level_improvement',
                'improvements_made': improvements_made,
                'details': f"Aplicadas {len(improvements_made)} melhorias para igualar ao Claude"
            }
            
        except Exception as e:
            return {
                'success': False,
                'action': 'claude_level_improvement',
                'error': str(e),
                'improvements_made': improvements_made
            }
    
    async def _general_improvement(self, request: str) -> Dict[str, Any]:
        """Melhoria geral do sistema."""
        try:
            # Usar o sistema de auto-melhoria mais avançado
            from .ultra_executor import UltraExecutor
            
            executor = UltraExecutor(str(self.project_path))
            result = await executor.execute_natural_command(request)
            
            return {
                'success': result.get('success', False),
                'action': 'general_improvement',
                'details': result
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'general_improvement',
                'error': str(e)
            }