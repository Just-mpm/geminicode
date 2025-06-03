"""
File Tools - Ferramentas de manipulação de arquivos estilo Claude Code
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import yaml
import csv
from datetime import datetime

from .base_tool import BaseTool, ToolInput, ToolResult, tool_decorator, ToolCategory, ToolPermission


@tool_decorator(
    name="read",
    description="Lê conteúdo de arquivos",
    category=ToolCategory.FILE,
    permission=ToolPermission.READ_ONLY
)
class ReadTool(BaseTool):
    """
    Ferramenta para leitura de arquivos.
    Similar ao FileReadTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="read",
            description="Lê e exibe conteúdo de arquivos"
        )
        
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = {
            '.txt', '.py', '.js', '.ts', '.html', '.css', '.md',
            '.json', '.yaml', '.yml', '.xml', '.csv', '.log',
            '.conf', '.cfg', '.ini', '.toml', '.sh', '.bat'
        }
        
        self.configure(
            requires_confirmation=False,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['read', 'file', 'content']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida se arquivo pode ser lido."""
        if not tool_input.command:
            return False
        
        file_path = Path(tool_input.command)
        
        # Verifica se arquivo existe
        if not file_path.exists():
            return False
        
        # Verifica se é arquivo
        if not file_path.is_file():
            return False
        
        # Verifica tamanho
        if file_path.stat().st_size > self.max_file_size:
            return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Lê arquivo."""
        file_path = Path(tool_input.command)
        
        try:
            # Detecta encoding
            encoding = self._detect_encoding(file_path)
            
            # Lê arquivo
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Informações do arquivo
            stat = file_path.stat()
            file_info = {
                'path': str(file_path),
                'size_bytes': stat.st_size,
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'encoding': encoding,
                'lines': len(content.splitlines()),
                'extension': file_path.suffix
            }
            
            # Processa conteúdo baseado no formato
            processed_content = self._process_content(content, file_path.suffix)
            
            return ToolResult(
                success=True,
                data={
                    'content': processed_content,
                    'file_info': file_info,
                    'raw_content': content
                },
                metadata=file_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro lendo arquivo {file_path}: {str(e)}"
            )
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detecta encoding do arquivo."""
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except ImportError:
            # Fallback sem chardet
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(100)
                return 'utf-8'
            except UnicodeDecodeError:
                return 'latin-1'
    
    def _process_content(self, content: str, extension: str) -> Union[str, Dict, List]:
        """Processa conteúdo baseado no tipo de arquivo."""
        if extension in ['.json']:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        
        elif extension in ['.yaml', '.yml']:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return content
        
        elif extension == '.csv':
            try:
                import io
                reader = csv.DictReader(io.StringIO(content))
                return list(reader)
            except Exception:
                return content
        
        return content


@tool_decorator(
    name="write",
    description="Escreve conteúdo em arquivos",
    category=ToolCategory.FILE,
    permission=ToolPermission.WRITE,
    requires_confirmation=True
)
class WriteTool(BaseTool):
    """
    Ferramenta para escrita de arquivos.
    Similar ao FileWriteTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="write",
            description="Cria ou sobrescreve arquivos com conteúdo"
        )
        
        self.backup_enabled = True
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        self.configure(
            requires_confirmation=True,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['write', 'file', 'create']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida parâmetros de escrita."""
        if not tool_input.command:  # file_path
            return False
        
        if 'content' not in tool_input.kwargs:
            return False
        
        content = tool_input.kwargs['content']
        if len(content.encode('utf-8')) > self.max_file_size:
            return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Escreve arquivo."""
        file_path = Path(tool_input.command)
        content = tool_input.kwargs['content']
        encoding = tool_input.kwargs.get('encoding', 'utf-8')
        
        try:
            # Cria diretório se necessário
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup se arquivo existir
            backup_path = None
            if self.backup_enabled and file_path.exists():
                backup_path = self._create_backup(file_path)
            
            # Escreve arquivo
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Informações do resultado
            stat = file_path.stat()
            result_info = {
                'path': str(file_path),
                'size_bytes': stat.st_size,
                'backup_created': backup_path is not None,
                'backup_path': str(backup_path) if backup_path else None,
                'encoding': encoding,
                'lines_written': len(content.splitlines())
            }
            
            return ToolResult(
                success=True,
                data=result_info,
                metadata=result_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro escrevendo arquivo {file_path}: {str(e)}"
            )
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Cria backup do arquivo existente."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = file_path.with_suffix(f'.backup_{timestamp}{file_path.suffix}')
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None


@tool_decorator(
    name="edit",
    description="Edita arquivos com substituições precisas",
    category=ToolCategory.FILE,
    permission=ToolPermission.WRITE,
    requires_confirmation=True
)
class EditTool(BaseTool):
    """
    Ferramenta para edição de arquivos.
    Similar ao FileEditTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="edit",
            description="Edita arquivos fazendo substituições precisas"
        )
        
        self.backup_enabled = True
        
        self.configure(
            requires_confirmation=True,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['edit', 'file', 'replace']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida parâmetros de edição."""
        if not tool_input.command:  # file_path
            return False
        
        required_params = ['old_text', 'new_text']
        for param in required_params:
            if param not in tool_input.kwargs:
                return False
        
        file_path = Path(tool_input.command)
        if not file_path.exists() or not file_path.is_file():
            return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Edita arquivo."""
        file_path = Path(tool_input.command)
        old_text = tool_input.kwargs['old_text']
        new_text = tool_input.kwargs['new_text']
        
        try:
            # Lê arquivo atual
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica se texto existe
            if old_text not in content:
                return ToolResult(
                    success=False,
                    error=f"Texto '{old_text[:50]}...' não encontrado no arquivo"
                )
            
            # Conta ocorrências
            occurrences = content.count(old_text)
            
            # Backup se necessário
            backup_path = None
            if self.backup_enabled:
                backup_path = self._create_backup(file_path)
            
            # Substitui texto
            new_content = content.replace(old_text, new_text)
            
            # Escreve arquivo modificado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            result_info = {
                'path': str(file_path),
                'occurrences_replaced': occurrences,
                'backup_created': backup_path is not None,
                'backup_path': str(backup_path) if backup_path else None,
                'old_text_length': len(old_text),
                'new_text_length': len(new_text),
                'size_change': len(new_content) - len(content)
            }
            
            return ToolResult(
                success=True,
                data=result_info,
                metadata=result_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro editando arquivo {file_path}: {str(e)}"
            )
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Cria backup do arquivo."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = file_path.with_suffix(f'.backup_{timestamp}{file_path.suffix}')
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None


@tool_decorator(
    name="list",
    description="Lista arquivos e diretórios",
    category=ToolCategory.FILE,
    permission=ToolPermission.READ_ONLY
)
class ListTool(BaseTool):
    """
    Ferramenta para listagem de arquivos.
    Similar ao LSTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="list",
            description="Lista arquivos e diretórios"
        )
        
        self.show_hidden = False
        self.max_items = 1000
        
        self.configure(
            requires_confirmation=False,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['list', 'directory', 'files']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida diretório."""
        path = Path(tool_input.command or '.')
        return path.exists() and path.is_dir()
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Lista diretório."""
        directory = Path(tool_input.command or '.')
        
        try:
            items = []
            for item in directory.iterdir():
                if not self.show_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat.st_size if item.is_file() else None,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'permissions': oct(stat.st_mode)[-3:],
                    'extension': item.suffix if item.is_file() else None
                }
                
                items.append(item_info)
                
                if len(items) >= self.max_items:
                    break
            
            # Ordena por nome
            items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            summary = {
                'directory': str(directory),
                'total_items': len(items),
                'files': len([i for i in items if i['type'] == 'file']),
                'directories': len([i for i in items if i['type'] == 'directory']),
                'total_size': sum(i['size'] or 0 for i in items)
            }
            
            return ToolResult(
                success=True,
                data={
                    'items': items,
                    'summary': summary
                },
                metadata=summary
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro listando diretório {directory}: {str(e)}"
            )


@tool_decorator(
    name="copy",
    description="Copia arquivos e diretórios",
    category=ToolCategory.FILE,
    permission=ToolPermission.WRITE,
    requires_confirmation=True
)
class CopyTool(BaseTool):
    """Ferramenta para cópia de arquivos."""
    
    def __init__(self):
        super().__init__(
            name="copy",
            description="Copia arquivos e diretórios"
        )
        
        self.configure(
            requires_confirmation=True,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['copy', 'file', 'duplicate']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida parâmetros de cópia."""
        if not tool_input.command:  # source
            return False
        
        if 'destination' not in tool_input.kwargs:
            return False
        
        source = Path(tool_input.command)
        return source.exists()
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Copia arquivo ou diretório."""
        source = Path(tool_input.command)
        destination = Path(tool_input.kwargs['destination'])
        
        try:
            if source.is_file():
                # Cria diretório de destino se necessário
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                
                result_info = {
                    'source': str(source),
                    'destination': str(destination),
                    'type': 'file',
                    'size': destination.stat().st_size
                }
            
            elif source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
                
                # Conta arquivos copiados
                file_count = sum(1 for _ in destination.rglob('*') if _.is_file())
                
                result_info = {
                    'source': str(source),
                    'destination': str(destination),
                    'type': 'directory',
                    'files_copied': file_count
                }
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Origem {source} não é arquivo nem diretório válido"
                )
            
            return ToolResult(
                success=True,
                data=result_info,
                metadata=result_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro copiando {source} para {destination}: {str(e)}"
            )


@tool_decorator(
    name="delete",
    description="Remove arquivos e diretórios",
    category=ToolCategory.FILE,
    permission=ToolPermission.DESTRUCTIVE,
    requires_confirmation=True
)
class DeleteTool(BaseTool):
    """Ferramenta para remoção de arquivos."""
    
    def __init__(self):
        super().__init__(
            name="delete",
            description="Remove arquivos e diretórios"
        )
        
        self.backup_before_delete = True
        self.protected_paths = {
            '/', '/etc', '/usr', '/var', '/boot', '/sys', '/proc'
        }
        
        self.configure(
            requires_confirmation=True,
            metadata={
                'category': 'file',
                'version': '1.0',
                'tags': ['delete', 'remove', 'destructive']
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida se pode remover."""
        if not tool_input.command:
            return False
        
        path = Path(tool_input.command).resolve()
        
        # Verifica caminhos protegidos
        for protected in self.protected_paths:
            if str(path).startswith(protected):
                return False
        
        return path.exists()
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Remove arquivo ou diretório."""
        path = Path(tool_input.command)
        
        try:
            backup_info = None
            
            # Backup se habilitado
            if self.backup_before_delete:
                backup_info = self._create_backup_before_delete(path)
            
            if path.is_file():
                path.unlink()
                result_info = {
                    'path': str(path),
                    'type': 'file',
                    'backup_created': backup_info is not None
                }
            
            elif path.is_dir():
                shutil.rmtree(path)
                result_info = {
                    'path': str(path),
                    'type': 'directory',
                    'backup_created': backup_info is not None
                }
            
            if backup_info:
                result_info['backup_path'] = backup_info
            
            return ToolResult(
                success=True,
                data=result_info,
                metadata=result_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro removendo {path}: {str(e)}"
            )
    
    def _create_backup_before_delete(self, path: Path) -> Optional[str]:
        """Cria backup antes de deletar."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = path.parent / '.backups'
            backup_dir.mkdir(exist_ok=True)
            
            backup_path = backup_dir / f"{path.name}.backup_{timestamp}"
            
            if path.is_file():
                shutil.copy2(path, backup_path)
            else:
                shutil.copytree(path, backup_path)
            
            return str(backup_path)
        except Exception:
            return None