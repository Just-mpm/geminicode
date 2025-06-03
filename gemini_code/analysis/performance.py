"""
Analisador de performance que identifica gargalos e otimiza código.
"""

import ast
import time
import psutil
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
from dataclasses import dataclass
import subprocess
import json

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem


@dataclass
class PerformanceIssue:
    """Representa um problema de performance."""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    suggestion: str
    auto_optimizable: bool = False
    estimated_improvement: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Métricas de performance do projeto."""
    cpu_usage: float
    memory_usage: float
    file_count: int
    total_lines: int
    complexity_score: float
    load_time: float
    bottlenecks: List[str]


class PerformanceAnalyzer:
    """Analisa e otimiza performance de código."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.performance_patterns = self._load_performance_patterns()
    
    def _load_performance_patterns(self) -> Dict[str, Any]:
        """Carrega padrões de performance conhecidos."""
        return {
            'python': {
                'slow_patterns': [
                    {
                        'pattern': r'for\s+\w+\s+in\s+range\(len\([^)]+\)\)',
                        'issue': 'Uso de range(len()) ao invés de enumerate()',
                        'suggestion': 'Use enumerate() para melhor performance',
                        'impact': 'medium'
                    },
                    {
                        'pattern': r'\.append\([^)]+\)\s*\n.*for.*in',
                        'issue': 'Loop com append pode ser substituído por list comprehension',
                        'suggestion': 'Use list comprehension quando possível',
                        'impact': 'medium'
                    },
                    {
                        'pattern': r'open\([^)]+\)(?!\s*as\s|\s*with)',
                        'issue': 'Arquivo aberto sem context manager',
                        'suggestion': 'Use "with open()" para gerenciamento automático',
                        'impact': 'low'
                    },
                    {
                        'pattern': r'time\.sleep\(\d+\)',
                        'issue': 'sleep() bloqueia thread principal',
                        'suggestion': 'Considere asyncio.sleep() para código assíncrono',
                        'impact': 'high'
                    },
                    {
                        'pattern': r'\.join\(\)\s*for.*in.*\.split\(',
                        'issue': 'Múltiplas operações string desnecessárias',
                        'suggestion': 'Optimize operações de string',
                        'impact': 'medium'
                    },
                    {
                        'pattern': r'if\s+.*\s+in\s+\[.*\]',
                        'issue': 'Busca em lista pode ser lenta',
                        'suggestion': 'Use set() para buscas frequentes',
                        'impact': 'medium'
                    },
                    {
                        'pattern': r'\.find\(.*\)\s*!=\s*-1',
                        'issue': 'find() é mais lento que "in"',
                        'suggestion': 'Use "substring in string"',
                        'impact': 'low'
                    }
                ],
                'memory_patterns': [
                    {
                        'pattern': r'pd\.read_csv\([^)]*\)(?!\s*\.head\(|\s*\.sample\()',
                        'issue': 'Carregamento completo de CSV pode consumir muita memória',
                        'suggestion': 'Use chunksize ou read específicas colunas',
                        'impact': 'high'
                    },
                    {
                        'pattern': r'\[\s*.*\s*for\s+.*\s+in\s+.*\s*\]',
                        'issue': 'List comprehension pode usar muita memória',
                        'suggestion': 'Considere generator expression',
                        'impact': 'medium'
                    }
                ]
            }
        }
    
    async def analyze_project_performance(self, project_path: str) -> Tuple[PerformanceMetrics, List[PerformanceIssue]]:
        """Analisa performance completa do projeto."""
        start_time = time.time()
        
        # Coleta métricas do sistema
        metrics = await self._collect_system_metrics(project_path)
        
        # Encontra problemas de performance
        issues = await self._find_performance_issues(project_path)
        
        # Analisa complexidade
        complexity = await self._analyze_complexity(project_path)
        metrics.complexity_score = complexity
        
        # Calcula tempo de carregamento
        metrics.load_time = time.time() - start_time
        
        return metrics, issues
    
    async def _collect_system_metrics(self, project_path: str) -> PerformanceMetrics:
        """Coleta métricas do sistema e projeto."""
        # Métricas do sistema
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Métricas do projeto
        file_count = 0
        total_lines = 0
        
        for file_path in Path(project_path).rglob("*.py"):
            file_count += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                continue
        
        return PerformanceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            file_count=file_count,
            total_lines=total_lines,
            complexity_score=0.0,  # Será calculada separadamente
            load_time=0.0,  # Será calculada no final
            bottlenecks=[]
        )
    
    async def _find_performance_issues(self, project_path: str) -> List[PerformanceIssue]:
        """Encontra problemas de performance no código."""
        issues = []
        python_files = list(Path(project_path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verifica padrões conhecidos
                file_issues = await self._check_performance_patterns(file_path, content)
                issues.extend(file_issues)
                
                # Análise com IA para problemas complexos
                ai_issues = await self._ai_performance_analysis(file_path, content)
                issues.extend(ai_issues)
                
            except Exception as e:
                print(f"Erro ao analisar {file_path}: {e}")
        
        return issues
    
    async def _check_performance_patterns(self, file_path: Path, content: str) -> List[PerformanceIssue]:
        """Verifica padrões conhecidos de performance."""
        issues = []
        lines = content.split('\n')
        
        patterns = self.performance_patterns['python']['slow_patterns']
        patterns.extend(self.performance_patterns['python']['memory_patterns'])
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in patterns:
                if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                    issues.append(PerformanceIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="PatternIssue",
                        description=pattern_info['issue'],
                        impact=pattern_info['impact'],
                        suggestion=pattern_info['suggestion'],
                        auto_optimizable=pattern_info['impact'] in ['low', 'medium']
                    ))
        
        return issues
    
    async def _ai_performance_analysis(self, file_path: Path, content: str) -> List[PerformanceIssue]:
        """Usa IA para análise avançada de performance."""
        if len(content) > 15000:  # Arquivo muito grande
            return []
        
        issues = []
        
        try:
            prompt = f"""
            Analise este código Python para problemas de performance:

            ```python
            {content}
            ```

            Identifique:
            1. Gargalos de performance
            2. Uso ineficiente de memória
            3. Algoritmos lentos
            4. I/O desnecessário
            5. Loops ineficientes

            Retorne JSON no formato:
            [
              {{
                "line": número_da_linha,
                "issue_type": "tipo_problema",
                "description": "descrição_do_problema",
                "impact": "high|medium|low",
                "suggestion": "como_otimizar",
                "estimated_improvement": "% de melhoria estimada"
              }}
            ]
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON da resposta
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                ai_issues = json.loads(json_match.group())
                
                for issue in ai_issues:
                    issues.append(PerformanceIssue(
                        file_path=str(file_path),
                        line_number=issue.get('line', 0),
                        issue_type=issue.get('issue_type', 'PerformanceIssue'),
                        description=issue.get('description', ''),
                        impact=issue.get('impact', 'medium'),
                        suggestion=issue.get('suggestion', ''),
                        auto_optimizable=issue.get('impact') in ['low', 'medium'],
                        estimated_improvement=issue.get('estimated_improvement')
                    ))
                    
        except Exception as e:
            print(f"Erro na análise IA para {file_path}: {e}")
        
        return issues
    
    async def _analyze_complexity(self, project_path: str) -> float:
        """Calcula complexidade ciclomática do projeto."""
        total_complexity = 0
        file_count = 0
        
        for file_path in Path(project_path).rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Calcula complexidade usando AST
                tree = ast.parse(content)
                complexity = self._calculate_cyclomatic_complexity(tree)
                total_complexity += complexity
                file_count += 1
                
            except Exception:
                continue
        
        return total_complexity / max(file_count, 1)
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calcula complexidade ciclomática de um AST."""
        complexity = 1  # Complexidade base
        
        for node in ast.walk(tree):
            # Conta pontos de decisão
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    async def optimize_code(self, issue: PerformanceIssue) -> Optional[str]:
        """Otimiza código automaticamente."""
        if not issue.auto_optimizable:
            return None
        
        try:
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Otimizações específicas por tipo
            if "range(len())" in issue.description:
                optimized = await self._optimize_range_len(content, issue)
            elif "list comprehension" in issue.suggestion:
                optimized = await self._optimize_to_comprehension(content, issue)
            elif "context manager" in issue.suggestion:
                optimized = await self._optimize_file_handling(content, issue)
            else:
                # Otimização geral com IA
                optimized = await self._ai_optimization(content, issue)
            
            return optimized
            
        except Exception as e:
            print(f"Erro ao otimizar: {e}")
            return None
    
    async def _optimize_range_len(self, content: str, issue: PerformanceIssue) -> str:
        """Otimiza loops range(len()) para enumerate()."""
        lines = content.split('\n')
        line_to_fix = lines[issue.line_number - 1]
        
        # Substitui padrão range(len()) por enumerate()
        pattern = r'for\s+(\w+)\s+in\s+range\(len\(([^)]+)\)\)'
        replacement = r'for \1, item in enumerate(\2)'
        
        fixed_line = re.sub(pattern, replacement, line_to_fix)
        lines[issue.line_number - 1] = fixed_line
        
        return '\n'.join(lines)
    
    async def _optimize_to_comprehension(self, content: str, issue: PerformanceIssue) -> str:
        """Converte loops simples em list comprehensions."""
        prompt = f"""
        Otimize este código Python convertendo para list comprehension:
        
        Linha {issue.line_number}: {issue.description}
        
        Código:
        ```python
        {content}
        ```
        
        Retorne apenas o código otimizado, mantendo toda funcionalidade.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai código da resposta
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return content
    
    async def _optimize_file_handling(self, content: str, issue: PerformanceIssue) -> str:
        """Otimiza abertura de arquivos para usar context managers."""
        lines = content.split('\n')
        line_to_fix = lines[issue.line_number - 1]
        
        # Substitui open() por with open()
        if 'open(' in line_to_fix and 'with' not in line_to_fix:
            # Padrão simples: file = open(...)
            pattern = r'(\s*)(\w+)\s*=\s*open\(([^)]+)\)'
            replacement = r'\1with open(\3) as \2:'
            
            fixed_line = re.sub(pattern, replacement, line_to_fix)
            lines[issue.line_number - 1] = fixed_line
        
        return '\n'.join(lines)
    
    async def _ai_optimization(self, content: str, issue: PerformanceIssue) -> str:
        """Usa IA para otimização geral."""
        prompt = f"""
        Otimize este código Python para melhor performance:
        
        Problema: {issue.description}
        Sugestão: {issue.suggestion}
        Linha: {issue.line_number}
        
        Código:
        ```python
        {content}
        ```
        
        Retorne apenas o código otimizado, preservando funcionalidade.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai código da resposta
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return content
    
    async def benchmark_optimization(self, original_code: str, optimized_code: str) -> Dict[str, Any]:
        """Compara performance entre código original e otimizado."""
        import tempfile
        import timeit
        
        results = {
            'original_time': 0,
            'optimized_time': 0,
            'improvement': 0,
            'success': False
        }
        
        try:
            # Cria arquivos temporários
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
                f1.write(original_code)
                original_file = f1.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                f2.write(optimized_code)
                optimized_file = f2.name
            
            # Executa benchmark (simplificado)
            original_time = timeit.timeit(
                f"exec(open('{original_file}').read())", 
                number=1
            )
            
            optimized_time = timeit.timeit(
                f"exec(open('{optimized_file}').read())", 
                number=1
            )
            
            improvement = ((original_time - optimized_time) / original_time) * 100
            
            results.update({
                'original_time': original_time,
                'optimized_time': optimized_time,
                'improvement': improvement,
                'success': True
            })
            
        except Exception as e:
            print(f"Erro no benchmark: {e}")
        
        return results
    
    async def get_performance_report(self, metrics: PerformanceMetrics, issues: List[PerformanceIssue]) -> str:
        """Gera relatório completo de performance."""
        report = "📊 **Relatório de Performance**\n\n"
        
        # Métricas gerais
        report += "🖥️ **Métricas do Sistema:**\n"
        report += f"- CPU: {metrics.cpu_usage:.1f}%\n"
        report += f"- Memória: {metrics.memory_usage:.1f}%\n"
        report += f"- Arquivos analisados: {metrics.file_count}\n"
        report += f"- Total de linhas: {metrics.total_lines:,}\n"
        report += f"- Complexidade média: {metrics.complexity_score:.1f}\n"
        report += f"- Tempo de análise: {metrics.load_time:.2f}s\n\n"
        
        # Problemas por impacto
        if issues:
            report += f"⚡ **Problemas Encontrados** ({len(issues)} total):\n\n"
            
            by_impact = {}
            for issue in issues:
                if issue.impact not in by_impact:
                    by_impact[issue.impact] = []
                by_impact[issue.impact].append(issue)
            
            for impact in ['high', 'medium', 'low']:
                if impact in by_impact:
                    count = len(by_impact[impact])
                    emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[impact]
                    report += f"{emoji} **{impact.title()}**: {count} problemas\n"
            
            # Top 5 problemas
            report += "\n🔍 **Top 5 Problemas:**\n"
            top_issues = sorted(issues, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x.impact])[:5]
            
            for i, issue in enumerate(top_issues, 1):
                file_name = Path(issue.file_path).name
                report += f"{i}. {file_name}:{issue.line_number} - {issue.description}\n"
                report += f"   💡 {issue.suggestion}\n"
        else:
            report += "✅ **Nenhum problema de performance encontrado!**\n\n"
        
        # Recomendações
        auto_fixable = sum(1 for issue in issues if issue.auto_optimizable)
        if auto_fixable > 0:
            report += f"\n🔧 **{auto_fixable}** problemas podem ser otimizados automaticamente\n"
        
        # Score geral
        total_score = max(0, 100 - len([i for i in issues if i.impact == 'high']) * 20 - 
                         len([i for i in issues if i.impact == 'medium']) * 10 - 
                         len([i for i in issues if i.impact == 'low']) * 5)
        
        report += f"\n📈 **Score de Performance**: {total_score}/100"
        
        return report