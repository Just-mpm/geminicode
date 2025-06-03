"""
Detector de erros inteligente que encontra e corrige problemas automaticamente.
"""

import ast
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess
import json
from dataclasses import dataclass

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem


@dataclass
class Error:
    """Representa um erro encontrado no código."""
    file_path: str
    line_number: int
    column: int
    error_type: str
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    suggestion: Optional[str] = None
    auto_fixable: bool = False


class ErrorDetector:
    """Detecta e corrige erros em código automaticamente."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.error_patterns = self._load_error_patterns()
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """Carrega padrões comuns de erro."""
        return {
            'python': {
                'syntax_errors': [
                    r'SyntaxError: (.+)',
                    r'IndentationError: (.+)',
                    r'TabError: (.+)'
                ],
                'runtime_errors': [
                    r'NameError: (.+)',
                    r'TypeError: (.+)',
                    r'AttributeError: (.+)',
                    r'ImportError: (.+)',
                    r'ModuleNotFoundError: (.+)'
                ],
                'logic_errors': [
                    r'ZeroDivisionError: (.+)',
                    r'IndexError: (.+)',
                    r'KeyError: (.+)',
                    r'ValueError: (.+)'
                ]
            },
            'javascript': {
                'syntax_errors': [
                    r'SyntaxError: (.+)',
                    r'ReferenceError: (.+)'
                ],
                'runtime_errors': [
                    r'TypeError: (.+)',
                    r'RangeError: (.+)'
                ]
            }
        }
    
    async def scan_project(self, project_path: str) -> List[Error]:
        """Escaneia todo o projeto em busca de erros."""
        errors = []
        
        # Detecta sintaxe
        syntax_errors = await self._check_syntax_errors(project_path)
        errors.extend(syntax_errors)
        
        # Detecta imports
        import_errors = await self._check_import_errors(project_path)
        errors.extend(import_errors)
        
        # Detecta lógica com IA
        logic_errors = await self._check_logic_errors(project_path)
        errors.extend(logic_errors)
        
        # Detecta performance
        performance_issues = await self._check_performance_issues(project_path)
        errors.extend(performance_issues)
        
        return sorted(errors, key=lambda x: self._error_priority(x.severity))
    
    async def _check_syntax_errors(self, project_path: str) -> List[Error]:
        """Verifica erros de sintaxe."""
        errors = []
        python_files = list(Path(project_path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verifica sintaxe Python
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    errors.append(Error(
                        file_path=str(file_path),
                        line_number=e.lineno or 0,
                        column=e.offset or 0,
                        error_type="SyntaxError",
                        message=str(e),
                        severity="critical",
                        auto_fixable=True
                    ))
                except Exception as e:
                    errors.append(Error(
                        file_path=str(file_path),
                        line_number=0,
                        column=0,
                        error_type="ParseError",
                        message=str(e),
                        severity="high",
                        auto_fixable=False
                    ))
                    
            except Exception as e:
                print(f"Erro ao ler {file_path}: {e}")
        
        return errors
    
    async def _check_import_errors(self, project_path: str) -> List[Error]:
        """Verifica erros de import."""
        errors = []
        python_files = list(Path(project_path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                # Executa verificação de imports
                result = subprocess.run(
                    ['python', '-m', 'py_compile', str(file_path)],
                    capture_output=True,
                    text=True,
                    cwd=project_path
                )
                
                if result.returncode != 0:
                    error_lines = result.stderr.split('\n')
                    for line in error_lines:
                        if 'ImportError' in line or 'ModuleNotFoundError' in line:
                            errors.append(Error(
                                file_path=str(file_path),
                                line_number=0,
                                column=0,
                                error_type="ImportError",
                                message=line.strip(),
                                severity="high",
                                auto_fixable=True
                            ))
                            
            except Exception as e:
                print(f"Erro ao verificar imports em {file_path}: {e}")
        
        return errors
    
    async def _check_logic_errors(self, project_path: str) -> List[Error]:
        """Usa IA para detectar erros de lógica."""
        errors = []
        python_files = list(Path(project_path).rglob("*.py"))
        
        for file_path in python_files[:5]:  # Limita para não sobrecarregar
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) > 10000:  # Arquivo muito grande
                    continue
                
                # Analisa com IA
                prompt = f"""
                Analise este código Python e identifique possíveis erros de lógica:

                ```python
                {content}
                ```

                Retorne uma lista JSON com erros encontrados no formato:
                [
                  {{
                    "line": número_da_linha,
                    "error_type": "tipo_do_erro",
                    "message": "descrição_do_erro",
                    "severity": "critical|high|medium|low",
                    "suggestion": "sugestão_de_correção"
                  }}
                ]

                Foque em:
                - Variáveis não definidas
                - Loops infinitos possíveis
                - Divisão por zero
                - Índices fora do range
                - Condições sempre falsas/verdadeiras
                """
                
                response = await self.gemini_client.generate_response(prompt)
                
                try:
                    # Extrai JSON da resposta
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        logic_errors = json.loads(json_match.group())
                        
                        for error in logic_errors:
                            errors.append(Error(
                                file_path=str(file_path),
                                line_number=error.get('line', 0),
                                column=0,
                                error_type=error.get('error_type', 'LogicError'),
                                message=error.get('message', ''),
                                severity=error.get('severity', 'medium'),
                                suggestion=error.get('suggestion'),
                                auto_fixable=True
                            ))
                            
                except Exception as e:
                    print(f"Erro ao processar resposta IA para {file_path}: {e}")
                    
            except Exception as e:
                print(f"Erro ao analisar lógica em {file_path}: {e}")
        
        return errors
    
    async def _check_performance_issues(self, project_path: str) -> List[Error]:
        """Detecta problemas de performance."""
        errors = []
        python_files = list(Path(project_path).rglob("*.py"))
        
        performance_patterns = [
            (r'for.*in.*range\(len\(', 'Use enumerate() ao invés de range(len())'),
            (r'\.append\(.*\)\s*\n.*for.*in', 'Considere list comprehension'),
            (r'open\([^)]+\)(?!\s*as\s|\s*with)', 'Use context manager (with) para arquivos'),
            (r'time\.sleep\(.*\)', 'sleep() pode impactar performance'),
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    for pattern, suggestion in performance_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append(Error(
                                file_path=str(file_path),
                                line_number=line_num,
                                column=0,
                                error_type="PerformanceIssue",
                                message=f"Possível problema de performance: {suggestion}",
                                severity="low",
                                suggestion=suggestion,
                                auto_fixable=False
                            ))
                            
            except Exception as e:
                print(f"Erro ao verificar performance em {file_path}: {e}")
        
        return errors
    
    async def auto_fix_error(self, error: Error) -> bool:
        """Tenta corrigir automaticamente um erro."""
        if not error.auto_fixable:
            return False
        
        try:
            with open(error.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Correções específicas por tipo
            if error.error_type == "SyntaxError":
                fixed_content = await self._fix_syntax_error(content, error)
            elif error.error_type == "ImportError":
                fixed_content = await self._fix_import_error(content, error)
            elif error.error_type == "LogicError":
                fixed_content = await self._fix_logic_error(content, error)
            else:
                return False
            
            if fixed_content and fixed_content != content:
                # Faz backup
                backup_path = f"{error.file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Aplica correção
                with open(error.file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                return True
                
        except Exception as e:
            print(f"Erro ao corrigir automaticamente: {e}")
        
        return False
    
    async def _fix_syntax_error(self, content: str, error: Error) -> Optional[str]:
        """Corrige erros de sintaxe usando IA."""
        prompt = f"""
        Corrija este erro de sintaxe Python:

        Arquivo: {error.file_path}
        Linha: {error.line_number}
        Erro: {error.message}

        Código:
        ```python
        {content}
        ```

        Retorne apenas o código corrigido, sem explicações.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai código da resposta
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return None
    
    async def _fix_import_error(self, content: str, error: Error) -> Optional[str]:
        """Corrige erros de import."""
        # Adiciona imports ausentes ou corrige caminhos
        missing_modules = re.findall(r"No module named '([^']+)'", error.message)
        
        if missing_modules:
            # Tenta encontrar import correto
            for module in missing_modules:
                # Lógica para sugerir imports corretos
                if 'numpy' in module:
                    content = f"import numpy as np\n{content}"
                elif 'pandas' in module:
                    content = f"import pandas as pd\n{content}"
                # Adicione mais padrões conforme necessário
        
        return content
    
    async def _fix_logic_error(self, content: str, error: Error) -> Optional[str]:
        """Corrige erros de lógica usando IA."""
        prompt = f"""
        Corrija este erro de lógica Python:

        Erro: {error.message}
        Sugestão: {error.suggestion}
        Linha: {error.line_number}

        Código:
        ```python
        {content}
        ```

        Retorne apenas o código corrigido, mantendo toda a funcionalidade.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai código da resposta
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return None
    
    def _error_priority(self, severity: str) -> int:
        """Retorna prioridade numérica para ordenação."""
        priorities = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        return priorities.get(severity, 4)
    
    async def get_error_summary(self, errors: List[Error]) -> str:
        """Gera resumo dos erros encontrados."""
        if not errors:
            return "✅ Nenhum erro encontrado!"
        
        summary = f"🔍 **Relatório de Erros** ({len(errors)} encontrados)\n\n"
        
        # Agrupa por severidade
        by_severity = {}
        for error in errors:
            if error.severity not in by_severity:
                by_severity[error.severity] = []
            by_severity[error.severity].append(error)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                count = len(by_severity[severity])
                emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '⚡', 'low': '💡'}[severity]
                summary += f"{emoji} **{severity.title()}**: {count} erros\n"
        
        summary += "\n📋 **Detalhes:**\n"
        for error in errors[:10]:  # Mostra primeiros 10
            summary += f"- {Path(error.file_path).name}:{error.line_number} - {error.message}\n"
        
        if len(errors) > 10:
            summary += f"... e mais {len(errors) - 10} erros\n"
        
        # Conta auto-fixable
        auto_fixable = sum(1 for e in errors if e.auto_fixable)
        summary += f"\n🔧 **{auto_fixable}** erros podem ser corrigidos automaticamente"
        
        return summary