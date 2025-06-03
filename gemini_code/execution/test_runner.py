"""
Executor de testes inteligente que roda e analisa resultados.
"""

import asyncio
import subprocess
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..core.gemini_client import GeminiClient
from .command_executor import CommandExecutor, CommandContext


@dataclass
class TestResult:
    """Resultado de um teste específico."""
    name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class TestSuite:
    """Conjunto de testes executados."""
    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage: Optional[float] = None
    results: List[TestResult] = None


@dataclass
class TestSession:
    """Sessão completa de testes."""
    timestamp: datetime
    framework: str
    command: str
    exit_code: int
    total_duration: float
    suites: List[TestSuite]
    overall_status: str
    coverage_report: Optional[Dict[str, Any]] = None


class TestRunner:
    """Executa e analisa testes automaticamente."""
    
    def __init__(self, gemini_client: GeminiClient, command_executor: CommandExecutor):
        self.gemini_client = gemini_client
        self.command_executor = command_executor
        self.test_frameworks = self._detect_test_frameworks()
        self.test_history: List[TestSession] = []
    
    def _detect_test_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Detecta frameworks de teste disponíveis."""
        return {
            'pytest': {
                'command': 'pytest',
                'files': ['pytest.ini', 'pyproject.toml', 'setup.cfg'],
                'patterns': ['test_*.py', '*_test.py', 'tests/'],
                'coverage_command': 'pytest --cov=. --cov-report=json'
            },
            'unittest': {
                'command': 'python -m unittest',
                'files': [],
                'patterns': ['test_*.py', '*_test.py'],
                'coverage_command': 'coverage run -m unittest && coverage json'
            },
            'nose2': {
                'command': 'nose2',
                'files': ['nose2.cfg'],
                'patterns': ['test_*.py', '*_test.py'],
                'coverage_command': 'nose2 --with-coverage'
            },
            'doctest': {
                'command': 'python -m doctest',
                'files': [],
                'patterns': ['*.py'],
                'coverage_command': None
            }
        }
    
    async def detect_test_framework(self, project_path: str) -> Optional[str]:
        """Detecta qual framework de teste está sendo usado."""
        project_path = Path(project_path)
        
        # Verifica arquivos de configuração
        for framework, config in self.test_frameworks.items():
            for config_file in config['files']:
                if (project_path / config_file).exists():
                    return framework
        
        # Verifica padrões de arquivos de teste
        test_files = []
        for pattern in ['test_*.py', '*_test.py']:
            test_files.extend(project_path.rglob(pattern))
        
        if test_files:
            # Verifica imports nos arquivos de teste
            framework_imports = {
                'pytest': ['import pytest', 'from pytest'],
                'unittest': ['import unittest', 'from unittest'],
                'nose2': ['import nose2', 'from nose2']
            }
            
            for test_file in test_files[:5]:  # Verifica apenas alguns arquivos
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for framework, imports in framework_imports.items():
                        if any(imp in content for imp in imports):
                            return framework
                except:
                    continue
            
            # Default para pytest se há arquivos de teste
            return 'pytest'
        
        return None
    
    async def run_tests(self, project_path: str, test_pattern: Optional[str] = None, 
                       with_coverage: bool = True) -> TestSession:
        """Executa todos os testes do projeto."""
        framework = await self.detect_test_framework(project_path)
        
        if not framework:
            return TestSession(
                timestamp=datetime.now(),
                framework='none',
                command='',
                exit_code=-1,
                total_duration=0,
                suites=[],
                overall_status='no_tests'
            )
        
        # Prepara comando
        framework_config = self.test_frameworks[framework]
        
        if with_coverage and framework_config['coverage_command']:
            command = framework_config['coverage_command']
        else:
            command = framework_config['command']
        
        # Adiciona padrão específico se fornecido
        if test_pattern:
            if framework == 'pytest':
                command += f" -k {test_pattern}"
            elif framework == 'unittest':
                command += f" {test_pattern}"
        
        # Adiciona flags úteis
        if framework == 'pytest':
            command += " -v --tb=short"
        elif framework == 'unittest':
            command += " -v"
        
        # Executa testes
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=300.0,  # 5 minutos
            safe_mode=True
        )
        
        start_time = time.time()
        result = await self.command_executor.execute_command(command, context)
        total_duration = time.time() - start_time
        
        # Analisa resultados
        suites = await self._parse_test_output(result.stdout, result.stderr, framework)
        
        # Determina status geral
        overall_status = self._determine_overall_status(result.exit_code, suites)
        
        # Processa cobertura se solicitada
        coverage_report = None
        if with_coverage:
            coverage_report = await self._get_coverage_report(project_path, framework)
        
        session = TestSession(
            timestamp=datetime.now(),
            framework=framework,
            command=command,
            exit_code=result.exit_code,
            total_duration=total_duration,
            suites=suites,
            overall_status=overall_status,
            coverage_report=coverage_report
        )
        
        self.test_history.append(session)
        return session
    
    async def _parse_test_output(self, stdout: str, stderr: str, framework: str) -> List[TestSuite]:
        """Analisa output dos testes baseado no framework."""
        if framework == 'pytest':
            return await self._parse_pytest_output(stdout, stderr)
        elif framework == 'unittest':
            return await self._parse_unittest_output(stdout, stderr)
        else:
            return await self._parse_generic_output(stdout, stderr)
    
    async def _parse_pytest_output(self, stdout: str, stderr: str) -> List[TestSuite]:
        """Analisa output do pytest."""
        suites = []
        
        # Extrai resumo geral
        summary_pattern = r'=+ (\d+) failed,?\s*(\d+) passed,?\s*(\d+) skipped.*in ([\d.]+)s'
        summary_match = re.search(summary_pattern, stdout)
        
        if summary_match:
            failed = int(summary_match.group(1)) if summary_match.group(1) else 0
            passed = int(summary_match.group(2)) if summary_match.group(2) else 0
            skipped = int(summary_match.group(3)) if summary_match.group(3) else 0
            duration = float(summary_match.group(4))
        else:
            # Padrões alternativos
            passed_match = re.search(r'(\d+) passed', stdout)
            failed_match = re.search(r'(\d+) failed', stdout)
            skipped_match = re.search(r'(\d+) skipped', stdout)
            duration_match = re.search(r'in ([\d.]+)s', stdout)
            
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            skipped = int(skipped_match.group(1)) if skipped_match else 0
            duration = float(duration_match.group(1)) if duration_match else 0
        
        # Extrai detalhes dos testes
        test_results = []
        
        # Padrão para testes individuais
        test_pattern = r'(\S+\.py)::\S+ (PASSED|FAILED|SKIPPED|ERROR)'
        for match in re.finditer(test_pattern, stdout):
            file_path = match.group(1)
            status = match.group(2).lower()
            
            test_results.append(TestResult(
                name=f"{file_path}::{match.group(0).split('::')[1].split()[0]}",
                status=status,
                duration=0,  # pytest não mostra duração individual por padrão
                file_path=file_path
            ))
        
        # Extrai erros detalhados
        error_pattern = r'FAILED (\S+) - (.+)'
        for match in re.finditer(error_pattern, stdout):
            test_name = match.group(1)
            error_msg = match.group(2)
            
            # Encontra o teste correspondente
            for test in test_results:
                if test_name in test.name:
                    test.error_message = error_msg
                    break
        
        suite = TestSuite(
            name="pytest",
            total_tests=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=0,  # pytest não distingue errors de failures
            duration=duration,
            results=test_results
        )
        
        suites.append(suite)
        return suites
    
    async def _parse_unittest_output(self, stdout: str, stderr: str) -> List[TestSuite]:
        """Analisa output do unittest."""
        suites = []
        
        # Padrão de resultado do unittest
        result_pattern = r'Ran (\d+) tests? in ([\d.]+)s\n\n(?:FAILED \(failures=(\d+)(?:, errors=(\d+))?\)|OK)'
        match = re.search(result_pattern, stderr)
        
        if match:
            total = int(match.group(1))
            duration = float(match.group(2))
            failures = int(match.group(3)) if match.group(3) else 0
            errors = int(match.group(4)) if match.group(4) else 0
            passed = total - failures - errors
        else:
            total = passed = failures = errors = 0
            duration = 0
        
        suite = TestSuite(
            name="unittest",
            total_tests=total,
            passed=passed,
            failed=failures,
            skipped=0,  # unittest não mostra skipped no resumo padrão
            errors=errors,
            duration=duration
        )
        
        suites.append(suite)
        return suites
    
    async def _parse_generic_output(self, stdout: str, stderr: str) -> List[TestSuite]:
        """Analisa output genérico de testes."""
        # Usa IA para tentar extrair informações
        try:
            prompt = f"""
            Analise este output de testes e extraia as informações:

            STDOUT:
            {stdout[:2000]}

            STDERR:
            {stderr[:1000]}

            Retorne JSON com:
            {{
                "total_tests": número_total,
                "passed": número_passou,
                "failed": número_falhou,
                "skipped": número_pulado,
                "errors": número_erros,
                "duration": tempo_segundos
            }}
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON da resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                suite = TestSuite(
                    name="generic",
                    total_tests=data.get('total_tests', 0),
                    passed=data.get('passed', 0),
                    failed=data.get('failed', 0),
                    skipped=data.get('skipped', 0),
                    errors=data.get('errors', 0),
                    duration=data.get('duration', 0)
                )
                
                return [suite]
        except:
            pass
        
        # Fallback para análise manual básica
        lines = (stdout + stderr).split('\n')
        total = failed = passed = 0
        
        for line in lines:
            if 'test' in line.lower():
                if any(word in line.lower() for word in ['pass', 'ok', 'success']):
                    passed += 1
                elif any(word in line.lower() for word in ['fail', 'error', 'exception']):
                    failed += 1
        
        total = passed + failed
        
        return [TestSuite(
            name="unknown",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=0,
            errors=0,
            duration=0
        )]
    
    def _determine_overall_status(self, exit_code: int, suites: List[TestSuite]) -> str:
        """Determina status geral dos testes."""
        if exit_code != 0:
            return 'failed'
        
        if not suites:
            return 'no_tests'
        
        for suite in suites:
            if suite.failed > 0 or suite.errors > 0:
                return 'failed'
        
        total_tests = sum(suite.total_tests for suite in suites)
        if total_tests == 0:
            return 'no_tests'
        
        return 'passed'
    
    async def _get_coverage_report(self, project_path: str, framework: str) -> Optional[Dict[str, Any]]:
        """Obtém relatório de cobertura."""
        coverage_file = Path(project_path) / 'coverage.json'
        
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    async def run_specific_test(self, project_path: str, test_path: str) -> TestSession:
        """Executa um teste específico."""
        framework = await self.detect_test_framework(project_path)
        
        if not framework:
            return TestSession(
                timestamp=datetime.now(),
                framework='none',
                command='',
                exit_code=-1,
                total_duration=0,
                suites=[],
                overall_status='no_framework'
            )
        
        # Prepara comando para teste específico
        if framework == 'pytest':
            command = f"pytest {test_path} -v"
        elif framework == 'unittest':
            # Converte path para module notation
            module_path = test_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            command = f"python -m unittest {module_path} -v"
        else:
            command = f"{self.test_frameworks[framework]['command']} {test_path}"
        
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=60.0,
            safe_mode=True
        )
        
        start_time = time.time()
        result = await self.command_executor.execute_command(command, context)
        total_duration = time.time() - start_time
        
        suites = await self._parse_test_output(result.stdout, result.stderr, framework)
        overall_status = self._determine_overall_status(result.exit_code, suites)
        
        return TestSession(
            timestamp=datetime.now(),
            framework=framework,
            command=command,
            exit_code=result.exit_code,
            total_duration=total_duration,
            suites=suites,
            overall_status=overall_status
        )
    
    async def analyze_test_failures(self, session: TestSession) -> Dict[str, Any]:
        """Analisa falhas de teste e sugere correções."""
        if session.overall_status == 'passed':
            return {'status': 'all_passed', 'suggestions': []}
        
        failed_tests = []
        for suite in session.suites:
            if suite.results:
                failed_tests.extend([t for t in suite.results if t.status in ['failed', 'error']])
        
        if not failed_tests:
            return {'status': 'no_failures', 'suggestions': []}
        
        # Analisa falhas com IA
        analysis = await self._ai_failure_analysis(failed_tests, session)
        
        return {
            'status': 'has_failures',
            'failed_count': len(failed_tests),
            'analysis': analysis,
            'suggestions': analysis.get('suggestions', [])
        }
    
    async def _ai_failure_analysis(self, failed_tests: List[TestResult], session: TestSession) -> Dict[str, Any]:
        """Usa IA para analisar falhas de teste."""
        try:
            # Prepara contexto das falhas
            failures_text = ""
            for test in failed_tests[:5]:  # Limita a 5 falhas
                failures_text += f"Teste: {test.name}\n"
                if test.error_message:
                    failures_text += f"Erro: {test.error_message}\n"
                failures_text += "---\n"
            
            prompt = f"""
            Analise estas falhas de teste e sugira correções:

            Framework: {session.framework}
            Status: {session.overall_status}

            Falhas:
            {failures_text}

            Retorne análise em JSON:
            {{
                "common_patterns": ["padrão1", "padrão2"],
                "likely_causes": ["causa1", "causa2"],
                "suggestions": ["sugestão1", "sugestão2"],
                "priority": "high|medium|low"
            }}
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            pass
        
        # Fallback para análise simples
        return {
            'common_patterns': ['Falhas de teste detectadas'],
            'likely_causes': ['Erro no código ou nos testes'],
            'suggestions': ['Revisar código e testes falhando'],
            'priority': 'medium'
        }
    
    async def generate_test_report(self, session: TestSession) -> str:
        """Gera relatório detalhado dos testes."""
        status_emoji = {
            'passed': '✅',
            'failed': '❌',
            'no_tests': '⚠️',
            'no_framework': '🚫'
        }
        
        report = f"{status_emoji.get(session.overall_status, '❓')} **Relatório de Testes**\n\n"
        
        # Informações gerais
        report += f"🕐 **Executado em**: {session.timestamp.strftime('%H:%M:%S')}\n"
        report += f"🔧 **Framework**: {session.framework}\n"
        report += f"⏱️ **Duração**: {session.total_duration:.2f}s\n"
        report += f"📝 **Comando**: `{session.command}`\n\n"
        
        # Status geral
        if session.overall_status == 'passed':
            report += "🎉 **Todos os testes passaram!**\n\n"
        elif session.overall_status == 'failed':
            report += "💥 **Alguns testes falharam**\n\n"
        elif session.overall_status == 'no_tests':
            report += "📭 **Nenhum teste encontrado**\n\n"
        
        # Detalhes por suite
        for suite in session.suites:
            report += f"📊 **{suite.name}**:\n"
            report += f"- Total: {suite.total_tests}\n"
            report += f"- ✅ Passou: {suite.passed}\n"
            report += f"- ❌ Falhou: {suite.failed}\n"
            if suite.skipped > 0:
                report += f"- ⏭️ Pulado: {suite.skipped}\n"
            if suite.errors > 0:
                report += f"- 💥 Erros: {suite.errors}\n"
            report += f"- ⏱️ Tempo: {suite.duration:.2f}s\n\n"
        
        # Cobertura se disponível
        if session.coverage_report:
            try:
                total_coverage = session.coverage_report.get('totals', {}).get('percent_covered', 0)
                report += f"📈 **Cobertura de Código**: {total_coverage:.1f}%\n\n"
            except:
                pass
        
        # Análise de falhas se houver
        if session.overall_status == 'failed':
            analysis = await self.analyze_test_failures(session)
            if analysis['suggestions']:
                report += "💡 **Sugestões**:\n"
                for suggestion in analysis['suggestions'][:3]:
                    report += f"- {suggestion}\n"
        
        return report
    
    def get_test_history(self, limit: int = 5) -> List[TestSession]:
        """Retorna histórico de execuções de teste."""
        return self.test_history[-limit:]
    
    async def watch_tests(self, project_path: str, callback=None) -> None:
        """Monitora arquivos e executa testes automaticamente."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class TestWatcher(FileSystemEventHandler):
            def __init__(self, runner: TestRunner):
                self.runner = runner
                self.last_run = 0
                self.debounce_time = 2  # segundos
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                # Só reage a arquivos Python
                if not event.src_path.endswith('.py'):
                    return
                
                # Debounce para evitar múltiplas execuções
                current_time = time.time()
                if current_time - self.last_run < self.debounce_time:
                    return
                
                self.last_run = current_time
                
                # Executa testes em background
                async def run_tests():
                    try:
                        session = await self.runner.run_tests(project_path)
                        if callback:
                            await callback(session)
                    except Exception as e:
                        print(f"Erro ao executar testes: {e}")
                
                asyncio.create_task(run_tests())
        
        observer = Observer()
        event_handler = TestWatcher(self)
        observer.schedule(event_handler, project_path, recursive=True)
        
        observer.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()