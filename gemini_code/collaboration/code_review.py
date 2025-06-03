"""
Sistema de Code Review assistido por IA
Analisa PRs, sugere melhorias e identifica problemas
"""

import re
import ast
import difflib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging

from ..core.gemini_client import GeminiClient
from ..analysis.error_detector import ErrorDetector
from ..security.security_scanner import SecurityScanner


@dataclass
class ReviewComment:
    """Comentário de revisão"""
    file_path: str
    line_number: int
    severity: str  # info, warning, error, critical
    category: str  # bug, security, performance, style, refactor
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class CodeReviewResult:
    """Resultado da revisão de código"""
    pull_request_id: Optional[str]
    files_reviewed: int
    total_comments: int
    comments: List[ReviewComment]
    summary: str
    score: float  # 0-100
    approved: bool
    timestamp: datetime


class CodeReview:
    """Sistema de revisão de código automatizada"""
    
    def __init__(self, gemini_client: GeminiClient, 
                 error_detector: Optional[ErrorDetector] = None,
                 security_scanner: Optional[SecurityScanner] = None):
        self.gemini = gemini_client
        self.error_detector = error_detector
        self.security_scanner = security_scanner
        self.logger = logging.getLogger('CodeReview')
        
        # Padrões de código
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Carrega padrões de análise"""
        return {
            'python': [
                # Bugs comuns
                {
                    'pattern': r'except\s*:',
                    'severity': 'error',
                    'category': 'bug',
                    'message': 'Bare except clause catches all exceptions',
                    'suggestion': 'Use specific exception types: except Exception as e:'
                },
                {
                    'pattern': r'if\s+.*==\s*True|if\s+.*==\s*False',
                    'severity': 'warning',
                    'category': 'style',
                    'message': 'Redundant comparison to boolean',
                    'suggestion': 'Use: if condition: or if not condition:'
                },
                {
                    'pattern': r'print\s*\(',
                    'severity': 'info',
                    'category': 'style',
                    'message': 'Debug print statement found',
                    'suggestion': 'Use logging instead of print for production code'
                },
                # Security
                {
                    'pattern': r'eval\s*\(',
                    'severity': 'critical',
                    'category': 'security',
                    'message': 'Use of eval() is a security risk',
                    'suggestion': 'Use ast.literal_eval() or find alternative approach'
                },
                {
                    'pattern': r'pickle\.load',
                    'severity': 'error',
                    'category': 'security',
                    'message': 'Unpickling untrusted data is dangerous',
                    'suggestion': 'Use JSON or other safe serialization formats'
                },
                # Performance
                {
                    'pattern': r'for\s+.*\s+in\s+.*\.keys\(\)',
                    'severity': 'info',
                    'category': 'performance',
                    'message': 'Iterating over dict.keys() is redundant',
                    'suggestion': 'Iterate directly over the dictionary'
                },
            ],
            'javascript': [
                {
                    'pattern': r'var\s+',
                    'severity': 'warning',
                    'category': 'style',
                    'message': 'Use of var instead of let/const',
                    'suggestion': 'Use const for immutable values, let for mutable'
                },
                {
                    'pattern': r'==(?!=)',
                    'severity': 'warning',
                    'category': 'bug',
                    'message': 'Use of == instead of ===',
                    'suggestion': 'Use === for strict equality'
                },
            ]
        }
    
    async def review_pull_request(self, pr_data: Dict[str, Any]) -> CodeReviewResult:
        """Revisa um pull request completo"""
        self.logger.info(f"Starting review for PR: {pr_data.get('id', 'unknown')}")
        
        comments = []
        files_reviewed = 0
        
        # Analisa cada arquivo modificado
        for file_change in pr_data.get('files', []):
            file_path = file_change['path']
            
            if self._should_review_file(file_path):
                file_comments = await self._review_file(
                    file_path,
                    file_change.get('content', ''),
                    file_change.get('patch', '')
                )
                comments.extend(file_comments)
                files_reviewed += 1
        
        # Análise geral com IA
        ai_review = await self._ai_review(pr_data, comments)
        
        # Calcula score
        score = self._calculate_score(comments)
        approved = score >= 70 and not any(c.severity == 'critical' for c in comments)
        
        # Gera sumário
        summary = self._generate_summary(comments, ai_review)
        
        result = CodeReviewResult(
            pull_request_id=pr_data.get('id'),
            files_reviewed=files_reviewed,
            total_comments=len(comments),
            comments=comments,
            summary=summary,
            score=score,
            approved=approved,
            timestamp=datetime.now()
        )
        
        self.logger.info(f"Review completed: {files_reviewed} files, {len(comments)} comments, score: {score}")
        
        return result
    
    async def review_file(self, file_path: str, content: str) -> List[ReviewComment]:
        """Revisa um arquivo individual"""
        return await self._review_file(file_path, content, None)
    
    async def _review_file(self, file_path: str, content: str, patch: Optional[str]) -> List[ReviewComment]:
        """Implementação interna de revisão de arquivo"""
        comments = []
        file_ext = Path(file_path).suffix.lower()
        
        # Análise de padrões
        if file_ext == '.py':
            comments.extend(self._check_patterns(file_path, content, 'python'))
            comments.extend(await self._check_python_specific(file_path, content))
        elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
            comments.extend(self._check_patterns(file_path, content, 'javascript'))
        
        # Análise de segurança se disponível
        if self.security_scanner and file_ext in ['.py', '.js']:
            security_issues = await self._check_security(file_path, content)
            comments.extend(security_issues)
        
        # Análise de complexidade
        complexity_issues = self._check_complexity(file_path, content)
        comments.extend(complexity_issues)
        
        # Análise de patch/diff se disponível
        if patch:
            diff_comments = self._analyze_diff(file_path, patch)
            comments.extend(diff_comments)
        
        return comments
    
    def _check_patterns(self, file_path: str, content: str, language: str) -> List[ReviewComment]:
        """Verifica padrões conhecidos"""
        comments = []
        patterns = self.patterns.get(language, [])
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern_config in patterns:
                pattern = pattern_config['pattern']
                if re.search(pattern, line):
                    comments.append(ReviewComment(
                        file_path=file_path,
                        line_number=line_num,
                        severity=pattern_config['severity'],
                        category=pattern_config['category'],
                        message=pattern_config['message'],
                        suggestion=pattern_config.get('suggestion'),
                        code_snippet=line.strip()
                    ))
        
        return comments
    
    async def _check_python_specific(self, file_path: str, content: str) -> List[ReviewComment]:
        """Verificações específicas para Python"""
        comments = []
        
        try:
            # Parse AST
            tree = ast.parse(content)
            
            # Verifica funções muito longas
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        comments.append(ReviewComment(
                            file_path=file_path,
                            line_number=node.lineno,
                            severity='warning',
                            category='refactor',
                            message=f'Function {node.name} is too long ({func_lines} lines)',
                            suggestion='Consider breaking into smaller functions'
                        ))
                    
                    # Verifica muitos parâmetros
                    if len(node.args.args) > 5:
                        comments.append(ReviewComment(
                            file_path=file_path,
                            line_number=node.lineno,
                            severity='warning',
                            category='refactor',
                            message=f'Function {node.name} has too many parameters ({len(node.args.args)})',
                            suggestion='Consider using configuration object or builder pattern'
                        ))
            
            # Verifica imports não utilizados
            # (simplificado - em produção seria mais complexo)
            imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)]
            for imp in imports:
                for alias in imp.names:
                    # Verifica se é usado no código
                    if alias.name not in content[content.find('\n', imp.lineno):]:
                        comments.append(ReviewComment(
                            file_path=file_path,
                            line_number=imp.lineno,
                            severity='info',
                            category='style',
                            message=f'Unused import: {alias.name}',
                            suggestion='Remove unused imports'
                        ))
                        
        except SyntaxError as e:
            comments.append(ReviewComment(
                file_path=file_path,
                line_number=e.lineno or 1,
                severity='error',
                category='bug',
                message=f'Syntax error: {e.msg}',
                suggestion='Fix syntax error before proceeding'
            ))
        
        return comments
    
    async def _check_security(self, file_path: str, content: str) -> List[ReviewComment]:
        """Verifica problemas de segurança"""
        comments = []
        
        # Patterns de segurança básicos
        security_patterns = [
            {
                'pattern': r'password\s*=\s*["\'][^"\']+["\']',
                'message': 'Hardcoded password detected',
                'severity': 'critical'
            },
            {
                'pattern': r'(api_key|secret_key|token)\s*=\s*["\'][^"\']+["\']',
                'message': 'Hardcoded secret/API key detected',
                'severity': 'critical'
            },
            {
                'pattern': r'subprocess.*shell\s*=\s*True',
                'message': 'Shell injection vulnerability',
                'severity': 'error'
            },
            {
                'pattern': r'sql\s*=.*%s|f["\'].*SELECT.*FROM',
                'message': 'Potential SQL injection',
                'severity': 'error'
            }
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for sec_pattern in security_patterns:
                if re.search(sec_pattern['pattern'], line, re.IGNORECASE):
                    comments.append(ReviewComment(
                        file_path=file_path,
                        line_number=line_num,
                        severity=sec_pattern['severity'],
                        category='security',
                        message=sec_pattern['message'],
                        suggestion='Store secrets in environment variables or secure vaults',
                        code_snippet=line.strip()
                    ))
        
        return comments
    
    def _check_complexity(self, file_path: str, content: str) -> List[ReviewComment]:
        """Verifica complexidade do código"""
        comments = []
        
        # Verifica linhas muito longas
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                comments.append(ReviewComment(
                    file_path=file_path,
                    line_number=line_num,
                    severity='info',
                    category='style',
                    message=f'Line too long ({len(line)} characters)',
                    suggestion='Break line to improve readability (max 120 chars)',
                    code_snippet=line[:50] + '...'
                ))
        
        # Verifica aninhamento profundo
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        if max_indent > 20:  # 5 níveis com 4 espaços
            comments.append(ReviewComment(
                file_path=file_path,
                line_number=1,
                severity='warning',
                category='refactor',
                message=f'Deep nesting detected (max indent: {max_indent})',
                suggestion='Refactor to reduce nesting levels'
            ))
        
        return comments
    
    def _analyze_diff(self, file_path: str, patch: str) -> List[ReviewComment]:
        """Analisa o diff/patch"""
        comments = []
        
        # Verifica remoção de testes
        if 'test' in file_path.lower():
            removed_tests = len(re.findall(r'^-\s*def\s+test_', patch, re.MULTILINE))
            if removed_tests > 0:
                comments.append(ReviewComment(
                    file_path=file_path,
                    line_number=1,
                    severity='error',
                    category='bug',
                    message=f'Removed {removed_tests} test(s)',
                    suggestion='Ensure tests are moved, not deleted'
                ))
        
        # Verifica TODOs adicionados
        todos_added = len(re.findall(r'^\+.*TODO', patch, re.MULTILINE))
        if todos_added > 0:
            comments.append(ReviewComment(
                file_path=file_path,
                line_number=1,
                severity='info',
                category='refactor',
                message=f'Added {todos_added} TODO(s)',
                suggestion='Consider creating issues for TODOs'
            ))
        
        return comments
    
    async def _ai_review(self, pr_data: Dict[str, Any], comments: List[ReviewComment]) -> str:
        """Análise adicional com IA"""
        # Prepara contexto para IA
        critical_issues = [c for c in comments if c.severity in ['critical', 'error']]
        
        prompt = f"""
Analise este Pull Request:
- Título: {pr_data.get('title', 'N/A')}
- Descrição: {pr_data.get('description', 'N/A')}
- Arquivos modificados: {len(pr_data.get('files', []))}
- Problemas críticos encontrados: {len(critical_issues)}

Forneça:
1. Avaliação geral da qualidade
2. Principais preocupações
3. Sugestões de melhoria
4. Pontos positivos
"""
        
        try:
            response = await self.gemini.generate_response(prompt)
            return response
        except Exception as e:
            self.logger.error(f"AI review failed: {e}")
            return "AI review not available"
    
    def _calculate_score(self, comments: List[ReviewComment]) -> float:
        """Calcula score baseado nos comentários"""
        if not comments:
            return 100.0
        
        # Pesos por severidade
        weights = {
            'critical': -20,
            'error': -10,
            'warning': -5,
            'info': -2
        }
        
        score = 100.0
        for comment in comments:
            score += weights.get(comment.severity, 0)
        
        return max(0, min(100, score))
    
    def _generate_summary(self, comments: List[ReviewComment], ai_review: str) -> str:
        """Gera sumário da revisão"""
        # Conta por categoria
        by_severity = {}
        by_category = {}
        
        for comment in comments:
            by_severity[comment.severity] = by_severity.get(comment.severity, 0) + 1
            by_category[comment.category] = by_category.get(comment.category, 0) + 1
        
        summary_parts = ["## Code Review Summary\n"]
        
        # Estatísticas
        summary_parts.append("### Issues Found:")
        for severity in ['critical', 'error', 'warning', 'info']:
            if severity in by_severity:
                emoji = {'critical': '🔴', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[severity]
                summary_parts.append(f"- {emoji} {severity.title()}: {by_severity[severity]}")
        
        summary_parts.append("\n### By Category:")
        for category, count in by_category.items():
            summary_parts.append(f"- {category.title()}: {count}")
        
        # Top issues
        critical_issues = [c for c in comments if c.severity in ['critical', 'error']]
        if critical_issues:
            summary_parts.append("\n### Critical Issues:")
            for issue in critical_issues[:5]:
                summary_parts.append(f"- {issue.file_path}:{issue.line_number} - {issue.message}")
        
        # AI insights
        if ai_review and ai_review != "AI review not available":
            summary_parts.append(f"\n### AI Analysis:\n{ai_review}")
        
        return '\n'.join(summary_parts)
    
    def _should_review_file(self, file_path: str) -> bool:
        """Determina se o arquivo deve ser revisado"""
        # Ignora alguns tipos de arquivo
        ignore_patterns = [
            r'\.min\.(js|css)$',
            r'\.lock$',
            r'__pycache__',
            r'\.pyc$',
            r'\.pyo$',
            r'node_modules/',
            r'\.git/',
            r'build/',
            r'dist/',
        ]
        
        for pattern in ignore_patterns:
            if re.search(pattern, file_path):
                return False
        
        # Revisa apenas código
        review_extensions = [
            '.py', '.js', '.jsx', '.ts', '.tsx',
            '.java', '.cpp', '.c', '.cs', '.go',
            '.rb', '.php', '.swift', '.kt', '.scala'
        ]
        
        return any(file_path.endswith(ext) for ext in review_extensions)
    
    def format_github_comment(self, comment: ReviewComment) -> str:
        """Formata comentário para GitHub"""
        severity_emoji = {
            'critical': '🔴',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        parts = [
            f"{severity_emoji.get(comment.severity, '📝')} **{comment.severity.upper()}**: {comment.message}"
        ]
        
        if comment.suggestion:
            parts.append(f"\n💡 **Suggestion**: {comment.suggestion}")
        
        if comment.code_snippet:
            parts.append(f"\n```\n{comment.code_snippet}\n```")
        
        return '\n'.join(parts)