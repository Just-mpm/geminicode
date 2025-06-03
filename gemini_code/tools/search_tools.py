"""
Search Tools - Ferramentas de busca estilo Claude Code
"""

import re
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Pattern
import fnmatch
from datetime import datetime

from .base_tool import BaseTool, ToolInput, ToolResult, tool_decorator, ToolCategory, ToolPermission


@tool_decorator(
    name="glob",
    description="Busca arquivos usando padrões glob",
    category=ToolCategory.SEARCH,
    permission=ToolPermission.READ_ONLY
)
class GlobTool(BaseTool):
    """
    Ferramenta para busca de arquivos usando padrões glob.
    Similar ao GlobTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="glob",
            description="Encontra arquivos usando padrões glob"
        )
        
        self.max_results = 1000
        self.follow_symlinks = False
        
        self.configure(
            requires_confirmation=False,
            metadata={
                'category': 'search',
                'version': '1.0',
                'tags': ['glob', 'find', 'pattern', 'files']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida padrão glob."""
        if not tool_input.command:
            return False
        
        # Verifica se padrão não é perigoso
        pattern = tool_input.command
        dangerous_patterns = ['/', '/*', '/etc/*', '/usr/*']
        
        for dangerous in dangerous_patterns:
            if pattern.startswith(dangerous):
                return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Executa busca glob."""
        pattern = tool_input.command
        base_dir = tool_input.kwargs.get('base_dir', '.')
        
        try:
            base_path = Path(base_dir).resolve()
            results = []
            
            # Se padrão é absoluto, usa como está
            if os.path.isabs(pattern):
                search_pattern = pattern
            else:
                search_pattern = str(base_path / pattern)
            
            # Busca arquivos
            matches = glob.glob(search_pattern, recursive=True)
            
            for match in matches[:self.max_results]:
                path = Path(match)
                
                if not self.follow_symlinks and path.is_symlink():
                    continue
                
                try:
                    stat = path.stat()
                    result_item = {
                        'path': str(path),
                        'relative_path': str(path.relative_to(base_path)) if path.is_relative_to(base_path) else str(path),
                        'name': path.name,
                        'type': 'directory' if path.is_dir() else 'file',
                        'size': stat.st_size if path.is_file() else None,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': path.suffix if path.is_file() else None,
                        'parent': str(path.parent)
                    }
                    results.append(result_item)
                except (OSError, ValueError):
                    # Skip arquivos que não conseguimos acessar
                    continue
            
            # Estatísticas
            summary = {
                'pattern': pattern,
                'base_directory': str(base_path),
                'total_matches': len(results),
                'files': len([r for r in results if r['type'] == 'file']),
                'directories': len([r for r in results if r['type'] == 'directory']),
                'truncated': len(matches) > self.max_results
            }
            
            return ToolResult(
                success=True,
                data={
                    'matches': results,
                    'summary': summary
                },
                metadata=summary
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro na busca glob '{pattern}': {str(e)}"
            )
    
    def _get_usage_examples(self) -> str:
        return """
glob "*.py"
glob "**/*.js"
glob "src/**/*.ts"
glob "tests/**/test_*.py"
        """.strip()
    
    def _get_examples(self) -> str:
        return """
# Buscar todos os arquivos Python
glob "*.py"

# Buscar arquivos JavaScript recursivamente  
glob "**/*.js"

# Buscar arquivos TypeScript em src/
glob "src/**/*.ts"

# Buscar arquivos de teste
glob "tests/**/test_*.py"
        """.strip()


@tool_decorator(
    name="grep",
    description="Busca texto dentro de arquivos",
    category=ToolCategory.SEARCH,
    permission=ToolPermission.READ_ONLY
)
class GrepTool(BaseTool):
    """
    Ferramenta para busca de texto em arquivos.
    Similar ao GrepTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="grep",
            description="Busca texto ou padrões regex em arquivos"
        )
        
        self.max_matches = 500
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.context_lines = 0
        
        self.configure(
            requires_confirmation=False,
            metadata={
                'category': 'search',
                'version': '1.0',
                'tags': ['grep', 'search', 'text', 'regex']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida parâmetros de busca."""
        if not tool_input.command:  # pattern
            return False
        
        # Valida regex se for o caso
        if tool_input.kwargs.get('regex', False):
            try:
                re.compile(tool_input.command)
            except re.error:
                return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Executa busca de texto."""
        pattern = tool_input.command
        target = tool_input.kwargs.get('target', '.')
        case_sensitive = tool_input.kwargs.get('case_sensitive', False)
        use_regex = tool_input.kwargs.get('regex', False)
        file_pattern = tool_input.kwargs.get('include', '*')
        exclude_pattern = tool_input.kwargs.get('exclude', None)
        
        try:
            target_path = Path(target)
            matches = []
            files_searched = 0
            
            # Compila regex se necessário
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                compiled_pattern = re.compile(pattern, flags)
            else:
                compiled_pattern = None
            
            # Determina arquivos para buscar
            if target_path.is_file():
                files_to_search = [target_path]
            else:
                files_to_search = self._get_files_to_search(
                    target_path, file_pattern, exclude_pattern
                )
            
            for file_path in files_to_search:
                if len(matches) >= self.max_matches:
                    break
                
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                    
                    file_matches = self._search_in_file(
                        file_path, pattern, compiled_pattern, case_sensitive
                    )
                    
                    if file_matches:
                        matches.extend(file_matches)
                    
                    files_searched += 1
                    
                except (OSError, UnicodeDecodeError):
                    # Skip arquivos que não conseguimos ler
                    continue
            
            # Ordena por arquivo e linha
            matches.sort(key=lambda x: (x['file'], x['line_number']))
            
            # Estatísticas
            summary = {
                'pattern': pattern,
                'target': str(target_path),
                'total_matches': len(matches),
                'files_with_matches': len(set(m['file'] for m in matches)),
                'files_searched': files_searched,
                'use_regex': use_regex,
                'case_sensitive': case_sensitive,
                'truncated': len(matches) >= self.max_matches
            }
            
            return ToolResult(
                success=True,
                data={
                    'matches': matches[:self.max_matches],
                    'summary': summary
                },
                metadata=summary
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro na busca grep '{pattern}': {str(e)}"
            )
    
    def _get_files_to_search(self, directory: Path, include: str, exclude: Optional[str]) -> List[Path]:
        """Obtém lista de arquivos para buscar."""
        files = []
        
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Verifica padrão de inclusão
            if not fnmatch.fnmatch(file_path.name, include):
                continue
            
            # Verifica padrão de exclusão
            if exclude and fnmatch.fnmatch(file_path.name, exclude):
                continue
            
            # Skip arquivos binários comuns
            if file_path.suffix in {'.exe', '.bin', '.so', '.dll', '.dylib'}:
                continue
            
            files.append(file_path)
        
        return files
    
    def _search_in_file(self, file_path: Path, pattern: str, 
                       compiled_pattern: Optional[Pattern], 
                       case_sensitive: bool) -> List[Dict[str, Any]]:
        """Busca padrão em um arquivo específico."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_number, line in enumerate(f, 1):
                    line = line.rstrip('\\n\\r')
                    
                    # Busca padrão
                    if compiled_pattern:
                        match_result = compiled_pattern.search(line)
                        if match_result:
                            match_info = {
                                'start': match_result.start(),
                                'end': match_result.end(),
                                'groups': match_result.groups()
                            }
                        else:
                            match_info = None
                    else:
                        # Busca simples
                        search_line = line if case_sensitive else line.lower()
                        search_pattern = pattern if case_sensitive else pattern.lower()
                        
                        if search_pattern in search_line:
                            start = search_line.find(search_pattern)
                            match_info = {
                                'start': start,
                                'end': start + len(search_pattern),
                                'groups': []
                            }
                        else:
                            match_info = None
                    
                    if match_info:
                        matches.append({
                            'file': str(file_path),
                            'line_number': line_number,
                            'line_content': line,
                            'match_start': match_info['start'],
                            'match_end': match_info['end'],
                            'match_groups': match_info['groups']
                        })
        
        except Exception:
            # Skip arquivos com problemas de encoding
            pass
        
        return matches
    
    def _get_usage_examples(self) -> str:
        return """
grep "function" --target="src/"
grep "TODO|FIXME" --regex=true
grep "class.*Test" --include="*.py" --regex=true
        """.strip()


@tool_decorator(
    name="find",
    description="Busca arquivos por critérios avançados",
    category=ToolCategory.SEARCH,
    permission=ToolPermission.READ_ONLY
)
class FindTool(BaseTool):
    """
    Ferramenta para busca avançada de arquivos.
    """
    
    def __init__(self):
        super().__init__(
            name="find",
            description="Busca arquivos por nome, tamanho, data, etc."
        )
        
        self.max_results = 1000
        
        self.configure(
            requires_confirmation=False,
            metadata={
                'category': 'search',
                'version': '1.0',
                'tags': ['find', 'search', 'files', 'advanced']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida critérios de busca."""
        target = tool_input.command or '.'
        target_path = Path(target)
        return target_path.exists()
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Executa busca avançada."""
        target = tool_input.command or '.'
        name_pattern = tool_input.kwargs.get('name')
        file_type = tool_input.kwargs.get('type')  # 'file', 'directory'
        min_size = tool_input.kwargs.get('min_size')
        max_size = tool_input.kwargs.get('max_size')
        modified_after = tool_input.kwargs.get('modified_after')
        modified_before = tool_input.kwargs.get('modified_before')
        
        try:
            target_path = Path(target)
            results = []
            
            for item in target_path.rglob('*'):
                if len(results) >= self.max_results:
                    break
                
                try:
                    # Filtro por tipo
                    if file_type == 'file' and not item.is_file():
                        continue
                    elif file_type == 'directory' and not item.is_dir():
                        continue
                    
                    # Filtro por nome
                    if name_pattern and not fnmatch.fnmatch(item.name, name_pattern):
                        continue
                    
                    stat = item.stat()
                    
                    # Filtro por tamanho (apenas para arquivos)
                    if item.is_file():
                        if min_size and stat.st_size < min_size:
                            continue
                        if max_size and stat.st_size > max_size:
                            continue
                    
                    # Filtro por data de modificação
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    if modified_after:
                        after_date = datetime.fromisoformat(modified_after.replace('Z', '+00:00'))
                        if modified_time < after_date:
                            continue
                    
                    if modified_before:
                        before_date = datetime.fromisoformat(modified_before.replace('Z', '+00:00'))
                        if modified_time > before_date:
                            continue
                    
                    # Adiciona aos resultados
                    result_item = {
                        'path': str(item),
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else None,
                        'modified': modified_time.isoformat(),
                        'permissions': oct(stat.st_mode)[-3:],
                        'extension': item.suffix if item.is_file() else None,
                        'parent': str(item.parent)
                    }
                    
                    results.append(result_item)
                
                except (OSError, ValueError):
                    continue
            
            summary = {
                'target': str(target_path),
                'criteria': {
                    'name_pattern': name_pattern,
                    'type': file_type,
                    'min_size': min_size,
                    'max_size': max_size,
                    'modified_after': modified_after,
                    'modified_before': modified_before
                },
                'total_found': len(results),
                'files': len([r for r in results if r['type'] == 'file']),
                'directories': len([r for r in results if r['type'] == 'directory']),
                'truncated': len(results) >= self.max_results
            }
            
            return ToolResult(
                success=True,
                data={
                    'results': results,
                    'summary': summary
                },
                metadata=summary
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro na busca find: {str(e)}"
            )
    
    def _get_usage_examples(self) -> str:
        return """
find . --name="*.py" --type=file
find /project --min_size=1024 --type=file
find . --modified_after="2023-01-01" --name="*.log"
        """.strip()


class SearchRegistry:
    """
    Registry para todas as ferramentas de busca.
    """
    
    def __init__(self):
        self.tools = {
            'glob': GlobTool(),
            'grep': GrepTool(),
            'find': FindTool()
        }
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Obtém ferramenta por nome."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Lista todas as ferramentas disponíveis."""
        return list(self.tools.keys())
    
    async def search_files(self, pattern: str, **kwargs) -> ToolResult:
        """Busca arquivos usando glob."""
        tool_input = ToolInput(command=pattern, kwargs=kwargs)
        return await self.tools['glob'].run_with_validation(tool_input)
    
    async def search_text(self, pattern: str, **kwargs) -> ToolResult:
        """Busca texto usando grep."""
        tool_input = ToolInput(command=pattern, kwargs=kwargs)
        return await self.tools['grep'].run_with_validation(tool_input)
    
    async def find_files(self, target: str = '.', **kwargs) -> ToolResult:
        """Busca arquivos usando find."""
        tool_input = ToolInput(command=target, kwargs=kwargs)
        return await self.tools['find'].run_with_validation(tool_input)