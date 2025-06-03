"""
Sistema de debugging inteligente que encontra e corrige problemas.
"""

import ast
import sys
import traceback
import inspect
import pdb
import asyncio
import re
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from io import StringIO
import linecache

from ..core.gemini_client import GeminiClient
from .command_executor import CommandExecutor, CommandContext


@dataclass
class DebugSession:
    """Sessão de debugging."""
    session_id: str
    file_path: str
    error_type: str
    error_message: str
    traceback_info: List[Dict[str, Any]]
    variables: Dict[str, Any]
    suggestions: List[str]
    fixed_code: Optional[str] = None


@dataclass
class BreakpointInfo:
    """Informação sobre um breakpoint."""
    file_path: str
    line_number: int
    condition: Optional[str] = None
    enabled: bool = True
    hit_count: int = 0


class DebugManager:
    """Gerencia debugging inteligente de código."""
    
    def __init__(self, gemini_client: GeminiClient, command_executor: CommandExecutor):
        self.gemini_client = gemini_client
        self.command_executor = command_executor
        self.active_sessions: Dict[str, DebugSession] = {}
        self.breakpoints: List[BreakpointInfo] = []
        self.debug_history: List[DebugSession] = []
    
    async def debug_error(self, error_info: Dict[str, Any], project_path: str) -> DebugSession:
        """Analisa e debug um erro específico."""
        session_id = f"debug_{len(self.active_sessions)}"
        
        # Extrai informações do erro
        error_type = error_info.get('type', 'Unknown')
        error_message = error_info.get('message', '')
        file_path = error_info.get('file', '')
        line_number = error_info.get('line', 0)
        
        # Analisa traceback
        traceback_info = await self._parse_traceback(error_info.get('traceback', ''))
        
        # Obtém código relevante
        code_context = await self._get_code_context(file_path, line_number, project_path)
        
        # Analisa variáveis no ponto do erro
        variables = await self._analyze_variables(code_context, line_number)
        
        # Gera sugestões usando IA
        suggestions = await self._generate_debug_suggestions(
            error_type, error_message, code_context, traceback_info
        )
        
        # Tenta gerar código corrigido
        fixed_code = await self._suggest_fix(code_context, error_type, error_message, suggestions)
        
        session = DebugSession(
            session_id=session_id,
            file_path=file_path,
            error_type=error_type,
            error_message=error_message,
            traceback_info=traceback_info,
            variables=variables,
            suggestions=suggestions,
            fixed_code=fixed_code
        )
        
        self.active_sessions[session_id] = session
        self.debug_history.append(session)
        
        return session
    
    async def _parse_traceback(self, traceback_str: str) -> List[Dict[str, Any]]:
        """Analisa traceback e extrai informações úteis."""
        if not traceback_str:
            return []
        
        frames = []
        lines = traceback_str.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Procura por "File "..."
            if line.startswith('File '):
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match:
                    file_path = file_match.group(1)
                    line_num = int(file_match.group(2))
                    
                    # Próxima linha geralmente contém o código
                    code_line = ""
                    if i + 1 < len(lines):
                        code_line = lines[i + 1].strip()
                    
                    frames.append({
                        'file': file_path,
                        'line': line_num,
                        'code': code_line,
                        'function': self._extract_function_name(line)
                    })
            
            i += 1
        
        return frames
    
    def _extract_function_name(self, line: str) -> str:
        """Extrai nome da função do traceback."""
        if ', in ' in line:
            return line.split(', in ')[-1]
        return 'unknown'
    
    async def _get_code_context(self, file_path: str, line_number: int, project_path: str) -> Dict[str, Any]:
        """Obtém contexto do código em torno do erro."""
        if not file_path or not Path(file_path).exists():
            # Tenta resolver path relativo
            full_path = Path(project_path) / file_path
            if not full_path.exists():
                return {'lines': [], 'focus_line': line_number}
        else:
            full_path = Path(file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Pega contexto (5 linhas antes e depois)
            start_line = max(0, line_number - 6)
            end_line = min(len(all_lines), line_number + 5)
            
            context_lines = []
            for i in range(start_line, end_line):
                context_lines.append({
                    'number': i + 1,
                    'content': all_lines[i].rstrip(),
                    'is_error_line': i + 1 == line_number
                })
            
            return {
                'file_path': str(full_path),
                'lines': context_lines,
                'focus_line': line_number,
                'total_lines': len(all_lines)
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'lines': [],
                'focus_line': line_number,
                'error': str(e)
            }
    
    async def _analyze_variables(self, code_context: Dict[str, Any], line_number: int) -> Dict[str, Any]:
        """Analisa variáveis que podem estar causando o problema."""
        if not code_context.get('lines'):
            return {}
        
        variables = {}
        
        # Analisa código antes da linha do erro
        for line_info in code_context['lines']:
            if line_info['number'] >= line_number:
                break
            
            content = line_info['content']
            
            # Procura por atribuições de variáveis
            var_patterns = [
                r'(\w+)\s*=\s*([^=\n]+)',  # var = value
                r'for\s+(\w+)\s+in',       # for var in
                r'def\s+\w+\([^)]*(\w+)',  # function parameters
            ]
            
            for pattern in var_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        var_name = match[0]
                        var_value = match[1] if len(match) > 1 else 'unknown'
                    else:
                        var_name = match
                        var_value = 'unknown'
                    
                    variables[var_name] = {
                        'value': var_value.strip(),
                        'line': line_info['number'],
                        'type': self._guess_variable_type(var_value)
                    }
        
        return variables
    
    def _guess_variable_type(self, value_str: str) -> str:
        """Tenta adivinhar o tipo da variável."""
        value_str = value_str.strip()
        
        if value_str.startswith('"') or value_str.startswith("'"):
            return 'string'
        elif value_str.startswith('['):
            return 'list'
        elif value_str.startswith('{'):
            return 'dict'
        elif value_str.startswith('('):
            return 'tuple'
        elif value_str.isdigit():
            return 'int'
        elif '.' in value_str and value_str.replace('.', '').isdigit():
            return 'float'
        elif value_str.lower() in ['true', 'false']:
            return 'bool'
        elif value_str.lower() == 'none':
            return 'None'
        else:
            return 'unknown'
    
    async def _generate_debug_suggestions(self, error_type: str, error_message: str, 
                                        code_context: Dict[str, Any], traceback_info: List[Dict[str, Any]]) -> List[str]:
        """Gera sugestões de debug usando IA."""
        try:
            # Prepara contexto para IA
            context_str = ""
            if code_context.get('lines'):
                for line in code_context['lines']:
                    marker = " -> " if line['is_error_line'] else "    "
                    context_str += f"{marker}{line['number']}: {line['content']}\n"
            
            traceback_str = ""
            for frame in traceback_info:
                traceback_str += f"File {frame['file']}, line {frame['line']}: {frame['code']}\n"
            
            prompt = f"""
            Analise este erro Python e forneça sugestões de debug:

            Erro: {error_type}: {error_message}

            Código (linha com erro marcada com ->):
            {context_str}

            Traceback:
            {traceback_str}

            Forneça 3-5 sugestões específicas de debug em uma lista JSON:
            ["sugestão1", "sugestão2", "sugestão3"]

            Foque em:
            1. Possíveis causas do erro
            2. Variáveis para verificar
            3. Correções específicas
            4. Prints/logs úteis para debug
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON da resposta
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions[:5]  # Máximo 5 sugestões
            
        except Exception as e:
            print(f"Erro ao gerar sugestões: {e}")
        
        # Fallback para sugestões baseadas no tipo de erro
        return self._get_fallback_suggestions(error_type, error_message)
    
    def _get_fallback_suggestions(self, error_type: str, error_message: str) -> List[str]:
        """Sugestões fallback baseadas no tipo de erro."""
        suggestions_map = {
            'NameError': [
                "Verifique se a variável foi definida antes de usar",
                "Confira se não há erro de digitação no nome",
                "Verifique se a variável está no escopo correto"
            ],
            'TypeError': [
                "Verifique os tipos das variáveis envolvidas",
                "Confira se está chamando métodos corretos",
                "Verifique se os argumentos estão corretos"
            ],
            'IndexError': [
                "Verifique se o índice está dentro dos limites",
                "Confira o tamanho da lista/string",
                "Use len() para verificar tamanhos"
            ],
            'KeyError': [
                "Verifique se a chave existe no dicionário",
                "Use get() com valor padrão",
                "Confira se não há erro de digitação na chave"
            ],
            'AttributeError': [
                "Verifique se o objeto tem esse atributo/método",
                "Confira se o objeto não é None",
                "Verifique a documentação do objeto"
            ],
            'ZeroDivisionError': [
                "Verifique se o denominador não é zero",
                "Adicione verificação antes da divisão",
                "Use try/except para tratar o erro"
            ]
        }
        
        return suggestions_map.get(error_type, [
            "Verifique o código linha por linha",
            "Adicione prints para debug",
            "Teste com dados diferentes"
        ])
    
    async def _suggest_fix(self, code_context: Dict[str, Any], error_type: str, 
                          error_message: str, suggestions: List[str]) -> Optional[str]:
        """Sugere código corrigido usando IA."""
        if not code_context.get('lines'):
            return None
        
        try:
            # Reconstrói código completo
            code_lines = []
            error_line_num = None
            
            for line in code_context['lines']:
                code_lines.append(line['content'])
                if line['is_error_line']:
                    error_line_num = len(code_lines) - 1
            
            original_code = '\n'.join(code_lines)
            
            prompt = f"""
            Corrija este código Python que está causando erro:

            Erro: {error_type}: {error_message}
            Linha com erro: {error_line_num + 1 if error_line_num is not None else 'unknown'}

            Código original:
            ```python
            {original_code}
            ```

            Sugestões de debug:
            {chr(10).join(f"- {s}" for s in suggestions)}

            Retorne o código corrigido mantendo a mesma funcionalidade.
            Adicione comentários explicando as correções.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
        except Exception as e:
            print(f"Erro ao sugerir correção: {e}")
        
        return None
    
    async def run_with_debugging(self, file_path: str, project_path: str) -> Dict[str, Any]:
        """Executa arquivo com debugging automático."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        # Executa o arquivo
        command = f"python {file_path}"
        result = await self.command_executor.execute_command(command, context)
        
        debug_info = {
            'execution_successful': result.success,
            'exit_code': result.exit_code,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        # Se houve erro, analisa automaticamente
        if not result.success and result.stderr:
            error_info = self._parse_error_from_stderr(result.stderr)
            if error_info:
                session = await self.debug_error(error_info, project_path)
                debug_info['debug_session'] = session
        
        return debug_info
    
    def _parse_error_from_stderr(self, stderr: str) -> Optional[Dict[str, Any]]:
        """Extrai informações de erro do stderr."""
        if not stderr:
            return None
        
        lines = stderr.strip().split('\n')
        
        # Procura pela linha final com o tipo de erro
        error_line = lines[-1] if lines else ""
        
        # Extrai tipo e mensagem do erro
        if ':' in error_line:
            parts = error_line.split(':', 1)
            error_type = parts[0].strip()
            error_message = parts[1].strip()
        else:
            error_type = "Unknown"
            error_message = error_line
        
        # Procura por informações de arquivo
        file_info = {}
        for line in lines:
            if line.strip().startswith('File '):
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match:
                    file_info = {
                        'file': file_match.group(1),
                        'line': int(file_match.group(2))
                    }
        
        return {
            'type': error_type,
            'message': error_message,
            'traceback': stderr,
            **file_info
        }
    
    async def add_debug_prints(self, file_path: str, variables: List[str]) -> str:
        """Adiciona prints de debug ao código."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Usa IA para adicionar prints estratégicos
            prompt = f"""
            Adicione prints de debug a este código Python para monitorar estas variáveis: {', '.join(variables)}

            ```python
            {content}
            ```

            Adicione prints estratégicos que mostrem:
            1. Valores das variáveis especificadas
            2. Pontos de execução importantes
            3. Entrada e saída de funções

            Retorne o código modificado com prints de debug.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
        except Exception as e:
            print(f"Erro ao adicionar debug prints: {e}")
        
        return content
    
    def add_breakpoint(self, file_path: str, line_number: int, condition: Optional[str] = None) -> str:
        """Adiciona breakpoint ao código."""
        breakpoint_id = f"bp_{len(self.breakpoints)}"
        
        breakpoint = BreakpointInfo(
            file_path=file_path,
            line_number=line_number,
            condition=condition
        )
        
        self.breakpoints.append(breakpoint)
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """Remove breakpoint."""
        try:
            index = int(breakpoint_id.split('_')[1])
            if 0 <= index < len(self.breakpoints):
                self.breakpoints.pop(index)
                return True
        except:
            pass
        return False
    
    def list_breakpoints(self) -> List[Dict[str, Any]]:
        """Lista todos os breakpoints."""
        return [
            {
                'id': f"bp_{i}",
                'file': bp.file_path,
                'line': bp.line_number,
                'condition': bp.condition,
                'enabled': bp.enabled,
                'hit_count': bp.hit_count
            }
            for i, bp in enumerate(self.breakpoints)
        ]
    
    async def generate_debug_report(self, session: DebugSession) -> str:
        """Gera relatório de debug."""
        report = f"🐛 **Relatório de Debug**\n\n"
        
        # Informações do erro
        report += f"❌ **Erro**: {session.error_type}\n"
        report += f"📝 **Mensagem**: {session.error_message}\n"
        report += f"📄 **Arquivo**: {Path(session.file_path).name}\n\n"
        
        # Traceback resumido
        if session.traceback_info:
            report += "📍 **Traceback**:\n"
            for frame in session.traceback_info[-3:]:  # Últimos 3 frames
                report += f"- {Path(frame['file']).name}:{frame['line']} em {frame['function']}\n"
            report += "\n"
        
        # Variáveis relevantes
        if session.variables:
            report += "🔍 **Variáveis Detectadas**:\n"
            for var_name, var_info in list(session.variables.items())[:5]:
                report += f"- `{var_name}` = {var_info['value']} ({var_info['type']})\n"
            report += "\n"
        
        # Sugestões
        if session.suggestions:
            report += "💡 **Sugestões de Debug**:\n"
            for i, suggestion in enumerate(session.suggestions, 1):
                report += f"{i}. {suggestion}\n"
            report += "\n"
        
        # Código corrigido se disponível
        if session.fixed_code:
            report += "🔧 **Código Sugerido**:\n"
            report += f"```python\n{session.fixed_code[:500]}...\n```\n"
        
        return report
    
    def get_debug_history(self, limit: int = 5) -> List[DebugSession]:
        """Retorna histórico de sessões de debug."""
        return self.debug_history[-limit:]