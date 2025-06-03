"""
Analisador de Complexidade - Análise profunda de complexidade de código
"""

import ast
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from pathlib import Path
import math

from ..core.gemini_client import GeminiClient
from ..core.project_manager import ProjectManager
from ..utils.logger import Logger


class ComplexityLevel(Enum):
    """Níveis de complexidade."""
    TRIVIAL = "trivial"      # 1-5
    SIMPLE = "simple"        # 6-10
    MODERATE = "moderate"    # 11-20
    COMPLEX = "complex"      # 21-50
    VERY_COMPLEX = "very_complex"  # 50+


@dataclass
class ComplexityMetrics:
    """Métricas de complexidade para código."""
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_metrics: Dict[str, float]
    lines_of_code: int
    logical_lines_of_code: int
    max_nesting_depth: int
    parameter_count: int
    return_count: int
    complexity_level: ComplexityLevel
    maintainability_index: float


@dataclass
class ComplexityIssue:
    """Problema de complexidade identificado."""
    type: str
    severity: str
    location: str
    description: str
    suggestion: str
    metrics: Dict[str, Any]


class ComplexityAnalyzer:
    """
    Analisador avançado de complexidade de código.
    Calcula múltiplas métricas e sugere melhorias.
    """
    
    def __init__(self, gemini_client: GeminiClient, project_manager: ProjectManager):
        self.gemini = gemini_client
        self.project = project_manager
        self.logger = Logger()
        
        # Thresholds de complexidade
        self.thresholds = {
            'cyclomatic': {
                'simple': 10,
                'moderate': 20,
                'complex': 50
            },
            'cognitive': {
                'simple': 7,
                'moderate': 15,
                'complex': 25
            },
            'nesting': {
                'simple': 3,
                'moderate': 5,
                'complex': 7
            },
            'parameters': {
                'simple': 3,
                'moderate': 5,
                'complex': 7
            }
        }
        
        # Cache de análises
        self.complexity_cache = {}
    
    async def analyze_file_complexity(self, file_path: str) -> Dict[str, Any]:
        """
        Analisa complexidade de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Análise completa de complexidade
        """
        # Verifica cache
        if file_path in self.complexity_cache:
            return self.complexity_cache[file_path]
        
        try:
            # Lê conteúdo do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detecta linguagem
            language = self._detect_language(file_path)
            
            # Análise específica por linguagem
            if language == 'python':
                metrics = await self._analyze_python_complexity(content, file_path)
            elif language in ['javascript', 'typescript']:
                metrics = await self._analyze_javascript_complexity(content, file_path)
            else:
                metrics = await self._analyze_generic_complexity(content, file_path)
            
            # Identifica issues
            issues = self._identify_complexity_issues(metrics)
            
            # Análise com IA para casos complexos
            ai_analysis = {}
            if metrics.get('cyclomatic_complexity', 0) > 20:
                ai_analysis = await self._ai_complexity_analysis(content, metrics, language)
            
            result = {
                'file_path': file_path,
                'language': language,
                'metrics': metrics,
                'issues': issues,
                'ai_analysis': ai_analysis,
                'summary': self._generate_complexity_summary(metrics, issues)
            }
            
            # Cacheia resultado
            self.complexity_cache[file_path] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar complexidade de {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'metrics': {},
                'issues': []
            }
    
    def _detect_language(self, file_path: str) -> str:
        """Detecta linguagem do arquivo."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        return language_map.get(ext, 'unknown')
    
    async def _analyze_python_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analisa complexidade de código Python."""
        try:
            tree = ast.parse(content)
            
            analyzer = PythonComplexityVisitor()
            analyzer.visit(tree)
            
            # Calcula métricas
            metrics = {
                'cyclomatic_complexity': analyzer.cyclomatic_complexity,
                'cognitive_complexity': analyzer.cognitive_complexity,
                'lines_of_code': len(content.splitlines()),
                'logical_lines_of_code': analyzer.logical_lines,
                'max_nesting_depth': analyzer.max_nesting,
                'functions': analyzer.function_complexities,
                'classes': analyzer.class_complexities,
                'halstead_metrics': self._calculate_halstead_metrics(content),
                'maintainability_index': 0  # Será calculado depois
            }
            
            # Calcula Maintainability Index
            metrics['maintainability_index'] = self._calculate_maintainability_index(metrics)
            
            # Determina nível de complexidade
            metrics['complexity_level'] = self._determine_complexity_level(
                metrics['cyclomatic_complexity']
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar Python: {e}")
            return self._empty_metrics()
    
    async def _analyze_javascript_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analisa complexidade de código JavaScript/TypeScript."""
        # Análise simplificada usando regex e heurísticas
        metrics = {
            'cyclomatic_complexity': 1,  # Base
            'cognitive_complexity': 0,
            'lines_of_code': len(content.splitlines()),
            'logical_lines_of_code': 0,
            'max_nesting_depth': 0,
            'functions': {},
            'halstead_metrics': self._calculate_halstead_metrics(content)
        }
        
        # Conta estruturas de controle para complexidade ciclomática
        control_structures = [
            r'\bif\s*\(',
            r'\belse\s+if\s*\(',
            r'\bfor\s*\(',
            r'\bwhile\s*\(',
            r'\bdo\s*\{',
            r'\bswitch\s*\(',
            r'\bcase\s+',
            r'\bcatch\s*\(',
            r'\?\s*[^:]+\s*:',  # Operador ternário
        ]
        
        for pattern in control_structures:
            matches = re.findall(pattern, content)
            metrics['cyclomatic_complexity'] += len(matches)
        
        # Conta logical lines (linhas não vazias e sem apenas comentários)
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('//') and not line.startswith('/*'):
                metrics['logical_lines_of_code'] += 1
        
        # Estima nesting depth
        metrics['max_nesting_depth'] = self._estimate_nesting_depth(content)
        
        # Calcula índices
        metrics['maintainability_index'] = self._calculate_maintainability_index(metrics)
        metrics['complexity_level'] = self._determine_complexity_level(
            metrics['cyclomatic_complexity']
        )
        
        return metrics
    
    async def _analyze_generic_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Análise genérica de complexidade para outras linguagens."""
        metrics = {
            'cyclomatic_complexity': 1,
            'lines_of_code': len(content.splitlines()),
            'logical_lines_of_code': 0,
            'max_nesting_depth': 0,
            'halstead_metrics': {}
        }
        
        # Conta linhas lógicas
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                metrics['logical_lines_of_code'] += 1
        
        # Estima complexidade baseada em palavras-chave
        keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', 'except']
        for keyword in keywords:
            pattern = rf'\b{keyword}\b'
            matches = re.findall(pattern, content, re.IGNORECASE)
            metrics['cyclomatic_complexity'] += len(matches)
        
        metrics['complexity_level'] = self._determine_complexity_level(
            metrics['cyclomatic_complexity']
        )
        
        return metrics
    
    def _calculate_halstead_metrics(self, content: str) -> Dict[str, float]:
        """Calcula métricas de Halstead."""
        # Tokeniza código (simplificado)
        import tokenize
        import io
        
        operators = set()
        operands = set()
        total_operators = 0
        total_operands = 0
        
        try:
            tokens = tokenize.generate_tokens(io.StringIO(content).readline)
            
            operator_types = {
                tokenize.OP, tokenize.PLUS, tokenize.MINUS,
                tokenize.STAR, tokenize.SLASH, tokenize.PERCENT,
                tokenize.DOUBLESTAR, tokenize.LEFTSHIFT, tokenize.RIGHTSHIFT,
                tokenize.AMPER, tokenize.VBAR, tokenize.CIRCUMFLEX,
                tokenize.TILDE, tokenize.LESS, tokenize.GREATER,
                tokenize.EQEQUAL, tokenize.NOTEQUAL, tokenize.LESSEQUAL,
                tokenize.GREATEREQUAL
            }
            
            for token in tokens:
                if token.type in operator_types:
                    operators.add(token.string)
                    total_operators += 1
                elif token.type in [tokenize.NAME, tokenize.NUMBER, tokenize.STRING]:
                    operands.add(token.string)
                    total_operands += 1
        except:
            # Fallback para análise simples
            pass
        
        # Calcula métricas
        n1 = len(operators)  # Operadores únicos
        n2 = len(operands)   # Operandos únicos
        N1 = total_operators # Total de operadores
        N2 = total_operands  # Total de operandos
        
        # Métricas de Halstead
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = volume * difficulty
        time = effort / 18  # Segundos
        bugs = volume / 3000  # Bugs estimados
        
        return {
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort,
            'time_to_program': time,
            'delivered_bugs': bugs
        }
    
    def _calculate_maintainability_index(self, metrics: Dict[str, Any]) -> float:
        """
        Calcula Maintainability Index.
        MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        """
        V = metrics.get('halstead_metrics', {}).get('volume', 1)
        CC = metrics.get('cyclomatic_complexity', 1)
        LOC = metrics.get('logical_lines_of_code', 1)
        
        # Evita log de 0
        V = max(V, 1)
        LOC = max(LOC, 1)
        
        MI = 171 - 5.2 * math.log(V) - 0.23 * CC - 16.2 * math.log(LOC)
        
        # Normaliza para 0-100
        return max(0, min(100, MI))
    
    def _estimate_nesting_depth(self, content: str) -> int:
        """Estima profundidade máxima de aninhamento."""
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _determine_complexity_level(self, cyclomatic_complexity: int) -> ComplexityLevel:
        """Determina nível de complexidade baseado na complexidade ciclomática."""
        if cyclomatic_complexity <= 5:
            return ComplexityLevel.TRIVIAL
        elif cyclomatic_complexity <= 10:
            return ComplexityLevel.SIMPLE
        elif cyclomatic_complexity <= 20:
            return ComplexityLevel.MODERATE
        elif cyclomatic_complexity <= 50:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
    
    def _identify_complexity_issues(self, metrics: Dict[str, Any]) -> List[ComplexityIssue]:
        """Identifica problemas de complexidade."""
        issues = []
        
        # Complexidade ciclomática alta
        cc = metrics.get('cyclomatic_complexity', 0)
        if cc > self.thresholds['cyclomatic']['moderate']:
            severity = 'high' if cc > self.thresholds['cyclomatic']['complex'] else 'medium'
            issues.append(ComplexityIssue(
                type='high_cyclomatic_complexity',
                severity=severity,
                location='file',
                description=f'Cyclomatic complexity is {cc} (threshold: {self.thresholds["cyclomatic"]["moderate"]})',
                suggestion='Consider breaking down into smaller functions',
                metrics={'cyclomatic_complexity': cc}
            ))
        
        # Nesting profundo
        nesting = metrics.get('max_nesting_depth', 0)
        if nesting > self.thresholds['nesting']['moderate']:
            severity = 'high' if nesting > self.thresholds['nesting']['complex'] else 'medium'
            issues.append(ComplexityIssue(
                type='deep_nesting',
                severity=severity,
                location='file',
                description=f'Maximum nesting depth is {nesting}',
                suggestion='Reduce nesting by extracting functions or using early returns',
                metrics={'nesting_depth': nesting}
            ))
        
        # Funções complexas
        if 'functions' in metrics:
            for func_name, func_metrics in metrics['functions'].items():
                func_cc = func_metrics.get('cyclomatic_complexity', 0)
                if func_cc > self.thresholds['cyclomatic']['simple']:
                    issues.append(ComplexityIssue(
                        type='complex_function',
                        severity='medium',
                        location=f'function: {func_name}',
                        description=f'Function has cyclomatic complexity of {func_cc}',
                        suggestion='Break down into smaller functions',
                        metrics={'cyclomatic_complexity': func_cc}
                    ))
        
        # Maintainability Index baixo
        mi = metrics.get('maintainability_index', 100)
        if mi < 50:
            severity = 'high' if mi < 25 else 'medium'
            issues.append(ComplexityIssue(
                type='low_maintainability',
                severity=severity,
                location='file',
                description=f'Maintainability index is {mi:.1f} (poor)',
                suggestion='Refactor to improve code structure and reduce complexity',
                metrics={'maintainability_index': mi}
            ))
        
        return issues
    
    async def _ai_complexity_analysis(self, content: str, metrics: Dict[str, Any], 
                                    language: str) -> Dict[str, Any]:
        """Análise de complexidade usando IA para casos complexos."""
        prompt = f"""
Analyze this {language} code with high complexity:

Metrics:
- Cyclomatic Complexity: {metrics.get('cyclomatic_complexity')}
- Lines of Code: {metrics.get('lines_of_code')}
- Nesting Depth: {metrics.get('max_nesting_depth')}
- Maintainability Index: {metrics.get('maintainability_index', 0):.1f}

Code snippet (first 50 lines):
```{language}
{self._get_code_snippet(content, 50)}
```

Provide:
1. Main complexity drivers
2. Specific refactoring suggestions
3. Design pattern recommendations
4. Estimated effort to refactor

Be specific and actionable.
"""
        
        try:
            response = await self.gemini.generate_response(
                prompt,
                thinking_budget=16384
            )
            
            return {
                'analysis': response,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_code_snippet(self, content: str, max_lines: int) -> str:
        """Obtém snippet de código."""
        lines = content.splitlines()
        return '\n'.join(lines[:max_lines])
    
    def _generate_complexity_summary(self, metrics: Dict[str, Any], 
                                   issues: List[ComplexityIssue]) -> Dict[str, Any]:
        """Gera resumo da análise de complexidade."""
        return {
            'complexity_level': metrics.get('complexity_level', ComplexityLevel.SIMPLE).value,
            'cyclomatic_complexity': metrics.get('cyclomatic_complexity', 0),
            'maintainability_index': metrics.get('maintainability_index', 0),
            'issue_count': len(issues),
            'critical_issues': len([i for i in issues if i.severity == 'high']),
            'recommendations': self._generate_recommendations(metrics, issues)
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any], 
                                issues: List[ComplexityIssue]) -> List[str]:
        """Gera recomendações baseadas na análise."""
        recommendations = []
        
        # Baseado no nível de complexidade
        level = metrics.get('complexity_level', ComplexityLevel.SIMPLE)
        
        if level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
            recommendations.append("Consider major refactoring to reduce complexity")
            recommendations.append("Break down large functions into smaller, focused ones")
            recommendations.append("Apply design patterns like Strategy or Command")
        elif level == ComplexityLevel.MODERATE:
            recommendations.append("Look for opportunities to simplify logic")
            recommendations.append("Extract complex conditions into well-named functions")
        
        # Baseado em issues específicas
        if any(i.type == 'deep_nesting' for i in issues):
            recommendations.append("Use early returns to reduce nesting")
            recommendations.append("Consider using guard clauses")
        
        if any(i.type == 'low_maintainability' for i in issues):
            recommendations.append("Add comprehensive documentation")
            recommendations.append("Improve naming conventions")
            recommendations.append("Add unit tests to ensure safe refactoring")
        
        return recommendations[:5]  # Top 5 recomendações
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Retorna métricas vazias."""
        return {
            'cyclomatic_complexity': 0,
            'cognitive_complexity': 0,
            'lines_of_code': 0,
            'logical_lines_of_code': 0,
            'max_nesting_depth': 0,
            'functions': {},
            'classes': {},
            'halstead_metrics': {},
            'maintainability_index': 0,
            'complexity_level': ComplexityLevel.SIMPLE
        }
    
    async def analyze_project_complexity(self) -> Dict[str, Any]:
        """Analisa complexidade de todo o projeto."""
        self.logger.info("📊 Analisando complexidade do projeto...")
        
        if not self.project.structure:
            self.project.scan_project()
        
        results = {
            'total_files': 0,
            'analyzed_files': 0,
            'total_complexity': 0,
            'average_complexity': 0,
            'complex_files': [],
            'distribution': {level.value: 0 for level in ComplexityLevel},
            'summary_metrics': {},
            'top_issues': []
        }
        
        all_issues = []
        
        # Analisa cada arquivo
        for file_path in self.project.structure.files:
            # Filtra apenas arquivos de código
            if not self._is_code_file(file_path):
                continue
            
            results['total_files'] += 1
            
            try:
                analysis = await self.analyze_file_complexity(file_path)
                
                if 'error' not in analysis:
                    results['analyzed_files'] += 1
                    
                    metrics = analysis['metrics']
                    cc = metrics.get('cyclomatic_complexity', 0)
                    results['total_complexity'] += cc
                    
                    # Adiciona à distribuição
                    level = metrics.get('complexity_level', ComplexityLevel.SIMPLE)
                    results['distribution'][level.value] += 1
                    
                    # Rastreia arquivos complexos
                    if level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
                        results['complex_files'].append({
                            'path': file_path,
                            'complexity': cc,
                            'level': level.value,
                            'maintainability': metrics.get('maintainability_index', 0)
                        })
                    
                    # Coleta issues
                    all_issues.extend(analysis.get('issues', []))
                    
            except Exception as e:
                self.logger.error(f"Erro ao analisar {file_path}: {e}")
        
        # Calcula médias
        if results['analyzed_files'] > 0:
            results['average_complexity'] = results['total_complexity'] / results['analyzed_files']
        
        # Ordena arquivos complexos
        results['complex_files'].sort(key=lambda x: x['complexity'], reverse=True)
        results['complex_files'] = results['complex_files'][:20]  # Top 20
        
        # Top issues
        issue_counts = {}
        for issue in all_issues:
            key = (issue.type, issue.severity)
            if key not in issue_counts:
                issue_counts[key] = {'count': 0, 'example': issue}
            issue_counts[key]['count'] += 1
        
        results['top_issues'] = sorted(
            [{'type': k[0], 'severity': k[1], 'count': v['count'], 'example': v['example']} 
             for k, v in issue_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        # Resumo
        results['summary_metrics'] = {
            'health_score': self._calculate_project_health_score(results),
            'refactoring_priority': self._determine_refactoring_priority(results)
        }
        
        return results
    
    def _is_code_file(self, file_path: str) -> bool:
        """Verifica se é um arquivo de código."""
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
        }
        
        return Path(file_path).suffix.lower() in code_extensions
    
    def _calculate_project_health_score(self, results: Dict[str, Any]) -> float:
        """Calcula score de saúde do projeto baseado em complexidade."""
        score = 100.0
        
        # Penaliza por média de complexidade
        avg_complexity = results.get('average_complexity', 0)
        if avg_complexity > 10:
            score -= min(30, (avg_complexity - 10) * 2)
        
        # Penaliza por arquivos muito complexos
        complex_ratio = len(results['complex_files']) / max(results['analyzed_files'], 1)
        score -= complex_ratio * 50
        
        # Penaliza por distribuição ruim
        dist = results['distribution']
        bad_files = dist.get('complex', 0) + dist.get('very_complex', 0)
        bad_ratio = bad_files / max(results['analyzed_files'], 1)
        score -= bad_ratio * 30
        
        return max(0, min(100, score))
    
    def _determine_refactoring_priority(self, results: Dict[str, Any]) -> str:
        """Determina prioridade de refatoração."""
        health_score = results['summary_metrics']['health_score']
        
        if health_score < 30:
            return "critical"
        elif health_score < 50:
            return "high"
        elif health_score < 70:
            return "medium"
        else:
            return "low"


class PythonComplexityVisitor(ast.NodeVisitor):
    """Visitor AST para calcular complexidade de código Python."""
    
    def __init__(self):
        self.cyclomatic_complexity = 1
        self.cognitive_complexity = 0
        self.logical_lines = 0
        self.max_nesting = 0
        self.current_nesting = 0
        self.function_complexities = {}
        self.class_complexities = {}
        self.current_function = None
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        # Salva contexto anterior
        prev_function = self.current_function
        prev_cc = self.cyclomatic_complexity
        
        # Inicia nova função
        self.current_function = node.name
        function_cc = 1
        
        # Visita corpo
        self.generic_visit(node)
        
        # Salva complexidade da função
        self.function_complexities[node.name] = {
            'cyclomatic_complexity': self.cyclomatic_complexity - prev_cc + 1,
            'parameters': len(node.args.args),
            'lines': node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        }
        
        # Restaura contexto
        self.current_function = prev_function
    
    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        
        self.generic_visit(node)
        
        # Salva informações da classe
        self.class_complexities[node.name] = {
            'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
            'lines': node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        }
        
        self.current_class = prev_class
    
    def visit_If(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.current_nesting
        
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        
        self.generic_visit(node)
        
        self.current_nesting -= 1
        
        # Conta elif como complexidade adicional
        if hasattr(node, 'orelse') and node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self.cyclomatic_complexity += 1
    
    def visit_For(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.current_nesting
        
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        
        self.generic_visit(node)
        
        self.current_nesting -= 1
    
    def visit_While(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.current_nesting
        
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        
        self.generic_visit(node)
        
        self.current_nesting -= 1
    
    def visit_ExceptHandler(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.cognitive_complexity += 1
        self.generic_visit(node)
    
    def visit_Assert(self, node):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        # and/or adicionam complexidade
        if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
            self.cyclomatic_complexity += len(node.values) - 1
            self.cognitive_complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_Lambda(self, node):
        self.cognitive_complexity += 1
        self.generic_visit(node)
    
    def generic_visit(self, node):
        # Conta linhas lógicas
        if hasattr(node, 'lineno'):
            self.logical_lines += 1
        
        super().generic_visit(node)