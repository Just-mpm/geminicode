"""
Gerenciador de múltiplos workspaces/pastas
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .project_manager import ProjectManager
from .file_manager import FileManagementSystem
from .gemini_client import GeminiClient


class WorkspaceManager:
    """Gerencia acesso a múltiplas pastas/projetos"""
    
    def __init__(self, gemini_client, default_root: Optional[Path] = None):
        self.gemini_client = gemini_client
        self.default_root = Path(default_root) if default_root else Path.cwd()
        self.current_workspace = self.default_root
        self.workspaces_history: List[Path] = [self.default_root]
        self.project_managers: Dict[str, ProjectManager] = {}
        self.file_managers: Dict[str, FileManagementSystem] = {}
        
    def change_workspace(self, path: str) -> Dict[str, Any]:
        """Muda para outra pasta/workspace"""
        try:
            # Resolve caminho
            new_path = Path(path)
            
            # Se não for absoluto, tenta relativo ao workspace atual
            if not new_path.is_absolute():
                new_path = self.current_workspace / new_path
            
            # Normaliza caminho
            new_path = new_path.resolve()
            
            # Verifica se existe
            if not new_path.exists():
                return {
                    'success': False,
                    'error': f'Pasta não encontrada: {new_path}',
                    'suggestion': 'Verifique se o caminho está correto'
                }
            
            # Verifica se é diretório
            if not new_path.is_dir():
                return {
                    'success': False,
                    'error': f'O caminho não é uma pasta: {new_path}',
                    'suggestion': 'Forneça o caminho de uma pasta, não um arquivo'
                }
            
            # Muda workspace
            self.current_workspace = new_path
            self.workspaces_history.append(new_path)
            
            # Cria/obtém project manager para este workspace
            workspace_key = str(new_path)
            if workspace_key not in self.project_managers:
                self.project_managers[workspace_key] = ProjectManager(new_path)
                self.file_managers[workspace_key] = FileManagementSystem(
                    self.project_managers[workspace_key]
                )
            
            # Escaneia novo workspace
            pm = self.project_managers[workspace_key]
            structure = pm.scan_project()
            
            return {
                'success': True,
                'workspace': str(new_path),
                'files_found': structure.total_files,
                'size_mb': round(structure.total_size / (1024 * 1024), 2),
                'main_language': pm._detect_main_language(),
                'project_type': pm._detect_project_type()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Tente usar o caminho completo, ex: C:\\Users\\SeuNome\\Pasta'
            }
    
    def get_current_workspace(self) -> Path:
        """Retorna workspace atual"""
        return self.current_workspace
    
    def get_project_manager(self) -> ProjectManager:
        """Retorna project manager do workspace atual"""
        workspace_key = str(self.current_workspace)
        if workspace_key not in self.project_managers:
            self.project_managers[workspace_key] = ProjectManager(self.current_workspace)
        return self.project_managers[workspace_key]
    
    def get_file_manager(self) -> FileManagementSystem:
        """Retorna file manager do workspace atual"""
        workspace_key = str(self.current_workspace)
        if workspace_key not in self.file_managers:
            pm = self.get_project_manager()
            self.file_managers[workspace_key] = FileManagementSystem(pm)
        return self.file_managers[workspace_key]
    
    def list_workspace_contents(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Lista conteúdo de uma pasta"""
        try:
            target_path = Path(path) if path else self.current_workspace
            
            if not target_path.is_absolute():
                target_path = self.current_workspace / target_path
            
            target_path = target_path.resolve()
            
            if not target_path.exists():
                return {'success': False, 'error': 'Pasta não encontrada'}
            
            contents = {
                'path': str(target_path),
                'folders': [],
                'files': []
            }
            
            # Lista conteúdo
            for item in target_path.iterdir():
                if item.is_dir():
                    contents['folders'].append({
                        'name': item.name,
                        'path': str(item)
                    })
                else:
                    size_kb = item.stat().st_size / 1024
                    contents['files'].append({
                        'name': item.name,
                        'path': str(item),
                        'size_kb': round(size_kb, 2),
                        'extension': item.suffix
                    })
            
            # Ordena
            contents['folders'].sort(key=lambda x: x['name'].lower())
            contents['files'].sort(key=lambda x: x['name'].lower())
            
            return {
                'success': True,
                'contents': contents,
                'total_folders': len(contents['folders']),
                'total_files': len(contents['files'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def read_file_from_path(self, file_path: str) -> Dict[str, Any]:
        """Lê arquivo de qualquer caminho"""
        try:
            path = Path(file_path)
            
            if not path.is_absolute():
                path = self.current_workspace / path
            
            path = path.resolve()
            
            if not path.exists():
                return {'success': False, 'error': 'Arquivo não encontrado'}
            
            if not path.is_file():
                return {'success': False, 'error': 'O caminho não é um arquivo'}
            
            # Detecta encoding
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {'success': False, 'error': 'Não foi possível ler o arquivo (encoding)'}
            
            return {
                'success': True,
                'path': str(path),
                'content': content,
                'size_kb': round(path.stat().st_size / 1024, 2),
                'encoding': used_encoding,
                'lines': len(content.splitlines())
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def write_file_to_path(self, file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Escreve arquivo em qualquer caminho"""
        try:
            path = Path(file_path)
            
            if not path.is_absolute():
                path = self.current_workspace / path
            
            path = path.resolve()
            
            # Cria diretórios se necessário
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup se existir
            if path.exists():
                backup_path = path.with_suffix(path.suffix + '.bak')
                shutil.copy2(path, backup_path)
            
            # Escreve arquivo
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'path': str(path),
                'size_kb': round(len(content.encode('utf-8')) / 1024, 2),
                'lines': len(content.splitlines()),
                'created': not path.exists()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Cria diretório em qualquer caminho"""
        try:
            path = Path(dir_path)
            
            if not path.is_absolute():
                path = self.current_workspace / path
            
            path = path.resolve()
            
            if path.exists():
                return {
                    'success': False,
                    'error': 'Diretório já existe',
                    'path': str(path)
                }
            
            path.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'path': str(path),
                'created': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def copy_files(self, source: str, destination: str) -> Dict[str, Any]:
        """Copia arquivos/pastas"""
        try:
            src_path = Path(source)
            dst_path = Path(destination)
            
            # Resolve caminhos
            if not src_path.is_absolute():
                src_path = self.current_workspace / src_path
            if not dst_path.is_absolute():
                dst_path = self.current_workspace / dst_path
            
            src_path = src_path.resolve()
            dst_path = dst_path.resolve()
            
            if not src_path.exists():
                return {'success': False, 'error': 'Origem não encontrada'}
            
            # Copia
            if src_path.is_file():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                copied = 'file'
            else:
                shutil.copytree(src_path, dst_path)
                copied = 'directory'
            
            return {
                'success': True,
                'source': str(src_path),
                'destination': str(dst_path),
                'type': copied
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_path(self, path: str, confirm: bool = True) -> Dict[str, Any]:
        """Deleta arquivo ou pasta"""
        try:
            target_path = Path(path)
            
            if not target_path.is_absolute():
                target_path = self.current_workspace / target_path
            
            target_path = target_path.resolve()
            
            if not target_path.exists():
                return {'success': False, 'error': 'Caminho não encontrado'}
            
            # Cria backup antes de deletar
            backup_name = f"{target_path.name}.deleted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = target_path.parent / backup_name
            
            if target_path.is_file():
                shutil.copy2(target_path, backup_path)
                target_path.unlink()
                deleted = 'file'
            else:
                shutil.copytree(target_path, backup_path)
                shutil.rmtree(target_path)
                deleted = 'directory'
            
            return {
                'success': True,
                'deleted': str(target_path),
                'backup': str(backup_path),
                'type': deleted
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_in_workspace(self, pattern: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Busca em todo workspace"""
        pm = self.get_project_manager()
        results = pm.search_in_files(pattern, file_pattern)
        
        return {
            'success': True,
            'pattern': pattern,
            'workspace': str(self.current_workspace),
            'files_found': len(results),
            'results': results
        }
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Informações do workspace atual"""
        pm = self.get_project_manager()
        stats = pm.get_project_stats() if pm.structure else {}
        
        return {
            'current_workspace': str(self.current_workspace),
            'is_default': self.current_workspace == self.default_root,
            'stats': stats,
            'history': [str(p) for p in self.workspaces_history[-5:]]  # Últimos 5
        }