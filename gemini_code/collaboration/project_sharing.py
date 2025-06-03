"""
Sistema de compartilhamento de projetos entre equipes.
"""

import json
import uuid
import shutil
import zipfile
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.gemini_client import GeminiClient
from .team_manager import TeamManager, Permission


class ShareLevel(Enum):
    """Níveis de compartilhamento."""
    READ_ONLY = "read_only"
    COLLABORATE = "collaborate"
    FULL_ACCESS = "full_access"
    ADMIN = "admin"


class ProjectStatus(Enum):
    """Status do projeto compartilhado."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    PRIVATE = "private"


@dataclass
class SharedProject:
    """Representa um projeto compartilhado."""
    id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    status: ProjectStatus
    share_level: ShareLevel
    collaborators: Dict[str, ShareLevel]  # member_id -> share_level
    project_path: str
    backup_path: Optional[str] = None
    version: str = "1.0.0"
    tags: List[str] = None
    language: str = "python"
    framework: str = ""
    size_mb: float = 0.0
    file_count: int = 0
    last_sync: Optional[datetime] = None
    sync_conflicts: List[Dict[str, Any]] = None
    access_log: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.sync_conflicts is None:
            self.sync_conflicts = []
        if self.access_log is None:
            self.access_log = []
        if isinstance(self.status, str):
            self.status = ProjectStatus(self.status)
        if isinstance(self.share_level, str):
            self.share_level = ShareLevel(self.share_level)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_sync'] = self.last_sync.isoformat() if self.last_sync else None
        data['status'] = self.status.value
        data['share_level'] = self.share_level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedProject':
        """Cria projeto a partir de dicionário."""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_sync'):
            data['last_sync'] = datetime.fromisoformat(data['last_sync'])
        data['status'] = ProjectStatus(data['status'])
        data['share_level'] = ShareLevel(data['share_level'])
        return cls(**data)
    
    def add_collaborator(self, member_id: str, share_level: ShareLevel) -> None:
        """Adiciona colaborador ao projeto."""
        self.collaborators[member_id] = share_level
        self.updated_at = datetime.now()
    
    def remove_collaborator(self, member_id: str) -> bool:
        """Remove colaborador do projeto."""
        if member_id in self.collaborators:
            del self.collaborators[member_id]
            self.updated_at = datetime.now()
            return True
        return False
    
    def update_collaborator_access(self, member_id: str, share_level: ShareLevel) -> bool:
        """Atualiza nível de acesso de colaborador."""
        if member_id in self.collaborators:
            self.collaborators[member_id] = share_level
            self.updated_at = datetime.now()
            return True
        return False
    
    def can_access(self, member_id: str, required_level: ShareLevel) -> bool:
        """Verifica se membro pode acessar com nível requerido."""
        if member_id == self.owner_id:
            return True
        
        member_level = self.collaborators.get(member_id)
        if not member_level:
            return False
        
        # Hierarquia de permissões
        level_hierarchy = {
            ShareLevel.READ_ONLY: 1,
            ShareLevel.COLLABORATE: 2,
            ShareLevel.FULL_ACCESS: 3,
            ShareLevel.ADMIN: 4
        }
        
        return level_hierarchy[member_level] >= level_hierarchy[required_level]
    
    def log_access(self, member_id: str, action: str, details: str = "") -> None:
        """Registra acesso ao projeto."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'member_id': member_id,
            'action': action,
            'details': details
        }
        
        self.access_log.append(log_entry)
        
        # Mantém apenas últimos 100 registros
        if len(self.access_log) > 100:
            self.access_log = self.access_log[-100:]


class ProjectSharing:
    """Sistema de compartilhamento de projetos."""
    
    def __init__(self, gemini_client: GeminiClient, team_manager: TeamManager):
        self.gemini_client = gemini_client
        self.team_manager = team_manager
        self.shared_projects: Dict[str, SharedProject] = {}
        self.data_file = Path('.gemini_code/shared_projects.json')
        self.projects_dir = Path('.gemini_code/shared_projects')
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Inicializa armazenamento de projetos compartilhados."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.load_projects()
    
    def save_projects(self) -> None:
        """Salva dados dos projetos compartilhados."""
        data = {
            'projects': {proj_id: proj.to_dict() for proj_id, proj in self.shared_projects.items()},
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_projects(self) -> None:
        """Carrega dados dos projetos compartilhados."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.shared_projects = {}
            for proj_id, proj_data in data.get('projects', {}).items():
                self.shared_projects[proj_id] = SharedProject.from_dict(proj_data)
                
        except Exception as e:
            print(f"Erro ao carregar projetos compartilhados: {e}")
    
    async def share_project(self, project_path: str, owner_id: str, 
                          share_config: Dict[str, Any]) -> str:
        """Compartilha projeto existente."""
        # Verifica se usuário existe
        owner = self.team_manager.get_member(owner_id)
        if not owner:
            raise ValueError("Proprietário não encontrado na equipe")
        
        # Verifica se projeto existe
        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError("Caminho do projeto não encontrado")
        
        # Cria ID do projeto
        project_id = str(uuid.uuid4())
        
        # Analisa projeto para extrair metadados
        project_metadata = await self._analyze_project(project_path)
        
        # Cria backup do projeto
        backup_path = await self._create_project_backup(project_path, project_id)
        
        # Cria projeto compartilhado
        shared_project = SharedProject(
            id=project_id,
            name=share_config.get('name', project_path.name),
            description=share_config.get('description', ''),
            owner_id=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=ProjectStatus(share_config.get('status', 'active')),
            share_level=ShareLevel(share_config.get('share_level', 'collaborate')),
            collaborators={},
            project_path=str(project_path),
            backup_path=backup_path,
            tags=share_config.get('tags', []),
            language=project_metadata.get('language', 'python'),
            framework=project_metadata.get('framework', ''),
            size_mb=project_metadata.get('size_mb', 0.0),
            file_count=project_metadata.get('file_count', 0)
        )
        
        # Adiciona colaboradores iniciais
        for member_email, access_level in share_config.get('collaborators', {}).items():
            member = self.team_manager.get_member_by_email(member_email)
            if member:
                shared_project.add_collaborator(member.id, ShareLevel(access_level))
        
        # Registra compartilhamento
        shared_project.log_access(owner_id, 'project_shared', f"Projeto '{shared_project.name}' compartilhado")
        
        # Salva projeto
        self.shared_projects[project_id] = shared_project
        self.save_projects()
        
        # Gera notificação
        await self._notify_collaborators(shared_project, 'project_shared')
        
        return project_id
    
    async def _analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analisa projeto para extrair metadados."""
        metadata = {
            'language': 'unknown',
            'framework': '',
            'size_mb': 0.0,
            'file_count': 0,
            'dependencies': []
        }
        
        try:
            # Calcula tamanho
            total_size = 0
            file_count = 0
            
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            metadata['size_mb'] = total_size / (1024 * 1024)
            metadata['file_count'] = file_count
            
            # Detecta linguagem principal
            language_files = {
                'python': list(project_path.rglob('*.py')),
                'javascript': list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts')),
                'java': list(project_path.rglob('*.java')),
                'csharp': list(project_path.rglob('*.cs')),
                'cpp': list(project_path.rglob('*.cpp')) + list(project_path.rglob('*.c')),
                'go': list(project_path.rglob('*.go')),
                'rust': list(project_path.rglob('*.rs'))
            }
            
            max_files = 0
            detected_language = 'unknown'
            
            for lang, files in language_files.items():
                if len(files) > max_files:
                    max_files = len(files)
                    detected_language = lang
            
            metadata['language'] = detected_language
            
            # Detecta framework
            if detected_language == 'python':
                if (project_path / 'requirements.txt').exists():
                    with open(project_path / 'requirements.txt', 'r') as f:
                        deps = f.read().lower()
                        if 'django' in deps:
                            metadata['framework'] = 'Django'
                        elif 'flask' in deps:
                            metadata['framework'] = 'Flask'
                        elif 'fastapi' in deps:
                            metadata['framework'] = 'FastAPI'
                
                if (project_path / 'manage.py').exists():
                    metadata['framework'] = 'Django'
            
            elif detected_language == 'javascript':
                if (project_path / 'package.json').exists():
                    with open(project_path / 'package.json', 'r') as f:
                        package_data = json.load(f)
                        deps = package_data.get('dependencies', {})
                        
                        if 'react' in deps:
                            metadata['framework'] = 'React'
                        elif 'vue' in deps:
                            metadata['framework'] = 'Vue.js'
                        elif 'angular' in deps:
                            metadata['framework'] = 'Angular'
                        elif 'express' in deps:
                            metadata['framework'] = 'Express.js'
            
            # Usa IA para análise mais detalhada
            ai_analysis = await self._ai_project_analysis(project_path, metadata)
            metadata.update(ai_analysis)
            
        except Exception as e:
            print(f"Erro ao analisar projeto: {e}")
        
        return metadata
    
    async def _ai_project_analysis(self, project_path: Path, 
                                 initial_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de projeto usando IA."""
        try:
            # Lê alguns arquivos principais para contexto
            context_files = []
            
            # Arquivo README
            for readme in ['README.md', 'README.txt', 'readme.md']:
                readme_path = project_path / readme
                if readme_path.exists():
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        context_files.append(f"README:\n{f.read()[:1000]}")
                    break
            
            # Arquivo principal
            main_files = ['main.py', 'app.py', 'index.js', 'main.js', 'App.js']
            for main_file in main_files:
                main_path = project_path / main_file
                if main_path.exists():
                    with open(main_path, 'r', encoding='utf-8') as f:
                        context_files.append(f"{main_file}:\n{f.read()[:500]}")
                    break
            
            if not context_files:
                return {}
            
            prompt = f"""
            Analise este projeto e extraia metadados:
            
            Metadados iniciais:
            {json.dumps(initial_metadata, indent=2)}
            
            Arquivos do projeto:
            {chr(10).join(context_files)}
            
            Retorne JSON com:
            {{
                "framework": "framework/biblioteca principal",
                "project_type": "web app/api/desktop/mobile/cli/etc",
                "description_summary": "resumo do que o projeto faz",
                "complexity": "simple/medium/complex",
                "technologies": ["lista", "de", "tecnologias"]
            }}
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"Erro na análise IA do projeto: {e}")
        
        return {}
    
    async def _create_project_backup(self, project_path: Path, project_id: str) -> str:
        """Cria backup do projeto."""
        backup_dir = self.projects_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"{project_id}_backup.zip"
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
        
        return str(backup_file)
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Verifica se arquivo deve ser ignorado no backup."""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            '.DS_Store', '*.pyc', '*.pyo', '*.log', '.env'
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in ignore_patterns)
    
    def add_collaborator(self, project_id: str, member_id: str, 
                        share_level: ShareLevel, added_by: str) -> bool:
        """Adiciona colaborador ao projeto."""
        project = self.shared_projects.get(project_id)
        if not project:
            return False
        
        # Verifica permissões
        if not project.can_access(added_by, ShareLevel.ADMIN) and project.owner_id != added_by:
            raise PermissionError("Sem permissão para adicionar colaboradores")
        
        # Verifica se membro existe
        member = self.team_manager.get_member(member_id)
        if not member:
            raise ValueError("Membro não encontrado")
        
        # Adiciona colaborador
        project.add_collaborator(member_id, share_level)
        project.log_access(added_by, 'collaborator_added', f"Adicionado {member.name} com acesso {share_level.value}")
        
        self.save_projects()
        
        # Notificação (usar try/except para evitar problemas de asyncio)
        try:
            import asyncio
            asyncio.create_task(
                self._notify_collaborator_added(project, member_id, share_level)
            )
        except Exception as e:
            print(f"Aviso: Notificação não enviada: {e}")
        
        return True
    
    def remove_collaborator(self, project_id: str, member_id: str, 
                          removed_by: str) -> bool:
        """Remove colaborador do projeto."""
        project = self.shared_projects.get(project_id)
        if not project:
            return False
        
        # Verifica permissões
        if not project.can_access(removed_by, ShareLevel.ADMIN) and project.owner_id != removed_by:
            raise PermissionError("Sem permissão para remover colaboradores")
        
        # Não pode remover owner
        if member_id == project.owner_id:
            raise PermissionError("Não é possível remover o proprietário")
        
        # Remove colaborador
        if project.remove_collaborator(member_id):
            member = self.team_manager.get_member(member_id)
            project.log_access(removed_by, 'collaborator_removed', 
                             f"Removido {member.name if member else member_id}")
            self.save_projects()
            return True
        
        return False
    
    def get_user_projects(self, member_id: str) -> List[SharedProject]:
        """Obtém projetos acessíveis pelo usuário."""
        user_projects = []
        
        for project in self.shared_projects.values():
            if (project.owner_id == member_id or 
                member_id in project.collaborators or
                project.status == ProjectStatus.ACTIVE):
                user_projects.append(project)
        
        return user_projects
    
    def get_project(self, project_id: str, member_id: str) -> Optional[SharedProject]:
        """Obtém projeto se usuário tiver acesso."""
        project = self.shared_projects.get(project_id)
        if not project:
            return None
        
        if project.can_access(member_id, ShareLevel.READ_ONLY):
            project.log_access(member_id, 'project_accessed')
            return project
        
        return None
    
    async def clone_project(self, project_id: str, member_id: str, 
                          destination: str) -> str:
        """Clona projeto para diretório local."""
        project = self.get_project(project_id, member_id)
        if not project:
            raise PermissionError("Acesso negado ao projeto")
        
        if not project.can_access(member_id, ShareLevel.READ_ONLY):
            raise PermissionError("Sem permissão para clonar projeto")
        
        destination_path = Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)
        
        # Copia arquivos do projeto original
        source_path = Path(project.project_path)
        if source_path.exists():
            shutil.copytree(source_path, destination_path / project.name, 
                          dirs_exist_ok=True, ignore=shutil.ignore_patterns(
                              '.git', '__pycache__', 'node_modules', '.venv'
                          ))
        
        # Ou extrai do backup
        elif project.backup_path and Path(project.backup_path).exists():
            with zipfile.ZipFile(project.backup_path, 'r') as zipf:
                zipf.extractall(destination_path / project.name)
        
        else:
            raise FileNotFoundError("Arquivos do projeto não encontrados")
        
        project.log_access(member_id, 'project_cloned', f"Clonado para {destination}")
        self.save_projects()
        
        return str(destination_path / project.name)
    
    async def sync_project(self, project_id: str, member_id: str, 
                         local_path: str) -> Dict[str, Any]:
        """Sincroniza projeto local com versão compartilhada."""
        project = self.get_project(project_id, member_id)
        if not project:
            raise PermissionError("Acesso negado ao projeto")
        
        if not project.can_access(member_id, ShareLevel.COLLABORATE):
            raise PermissionError("Sem permissão para sincronizar projeto")
        
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError("Caminho local não encontrado")
        
        # Detecta conflitos
        conflicts = await self._detect_sync_conflicts(project, local_path)
        
        if conflicts:
            # Salva conflitos no projeto
            project.sync_conflicts.extend(conflicts)
            self.save_projects()
            
            return {
                'success': False,
                'conflicts': conflicts,
                'message': 'Conflitos detectados. Resolva antes de sincronizar.'
            }
        
        # Realiza sincronização
        sync_result = await self._perform_sync(project, local_path, member_id)
        
        # Atualiza timestamp
        project.last_sync = datetime.now()
        project.log_access(member_id, 'project_synced')
        self.save_projects()
        
        return sync_result
    
    async def _detect_sync_conflicts(self, project: SharedProject, 
                                   local_path: Path) -> List[Dict[str, Any]]:
        """Detecta conflitos de sincronização."""
        conflicts = []
        
        try:
            source_path = Path(project.project_path)
            if not source_path.exists():
                return conflicts
            
            # Compara arquivos modificados
            for local_file in local_path.rglob('*'):
                if local_file.is_file() and not self._should_ignore_file(local_file):
                    relative_path = local_file.relative_to(local_path)
                    source_file = source_path / relative_path
                    
                    if source_file.exists():
                        local_mtime = local_file.stat().st_mtime
                        source_mtime = source_file.stat().st_mtime
                        
                        # Se ambos foram modificados após última sync
                        if (project.last_sync and 
                            local_mtime > project.last_sync.timestamp() and
                            source_mtime > project.last_sync.timestamp()):
                            
                            conflicts.append({
                                'file': str(relative_path),
                                'type': 'modified_conflict',
                                'local_modified': datetime.fromtimestamp(local_mtime).isoformat(),
                                'source_modified': datetime.fromtimestamp(source_mtime).isoformat()
                            })
            
        except Exception as e:
            print(f"Erro ao detectar conflitos: {e}")
        
        return conflicts
    
    async def _perform_sync(self, project: SharedProject, 
                          local_path: Path, member_id: str) -> Dict[str, Any]:
        """Realiza sincronização de projeto."""
        try:
            source_path = Path(project.project_path)
            
            files_updated = 0
            files_added = 0
            files_deleted = 0
            
            # Copia arquivos do source para local
            if source_path.exists():
                for source_file in source_path.rglob('*'):
                    if source_file.is_file() and not self._should_ignore_file(source_file):
                        relative_path = source_file.relative_to(source_path)
                        local_file = local_path / relative_path
                        
                        # Cria diretórios se necessário
                        local_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        if local_file.exists():
                            files_updated += 1
                        else:
                            files_added += 1
                        
                        shutil.copy2(source_file, local_file)
            
            # Cria novo backup
            new_backup = await self._create_project_backup(local_path, project.id)
            if project.backup_path and Path(project.backup_path).exists():
                Path(project.backup_path).unlink()  # Remove backup antigo
            project.backup_path = new_backup
            
            return {
                'success': True,
                'files_updated': files_updated,
                'files_added': files_added,
                'files_deleted': files_deleted,
                'message': f'Sincronização concluída: {files_updated} atualizados, {files_added} adicionados'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro durante sincronização'
            }
    
    async def _notify_collaborators(self, project: SharedProject, event: str) -> None:
        """Notifica colaboradores sobre eventos do projeto."""
        try:
            # Em implementação real, enviaria notificações
            for member_id in project.collaborators.keys():
                member = self.team_manager.get_member(member_id)
                if member:
                    print(f"Notificação para {member.name}: {event} no projeto {project.name}")
        except Exception as e:
            print(f"Erro ao enviar notificações: {e}")
    
    async def _notify_collaborator_added(self, project: SharedProject, 
                                       member_id: str, share_level: ShareLevel) -> None:
        """Notifica sobre adição de colaborador."""
        member = self.team_manager.get_member(member_id)
        if member:
            print(f"Notificação para {member.name}: Você foi adicionado ao projeto {project.name} com acesso {share_level.value}")
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos projetos compartilhados."""
        total_projects = len(self.shared_projects)
        active_projects = len([p for p in self.shared_projects.values() if p.status == ProjectStatus.ACTIVE])
        
        # Distribuição por linguagem
        language_dist = {}
        for project in self.shared_projects.values():
            lang = project.language
            language_dist[lang] = language_dist.get(lang, 0) + 1
        
        # Total de colaboradores únicos
        all_collaborators = set()
        for project in self.shared_projects.values():
            all_collaborators.add(project.owner_id)
            all_collaborators.update(project.collaborators.keys())
        
        # Tamanho total
        total_size_mb = sum(p.size_mb for p in self.shared_projects.values())
        
        return {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'archived_projects': total_projects - active_projects,
            'unique_collaborators': len(all_collaborators),
            'language_distribution': language_dist,
            'total_size_mb': total_size_mb,
            'total_files': sum(p.file_count for p in self.shared_projects.values())
        }
    
    async def generate_sharing_report(self) -> Dict[str, Any]:
        """Gera relatório de compartilhamento."""
        stats = self.get_project_stats()
        
        # Projetos mais ativos
        most_active = sorted(
            self.shared_projects.values(),
            key=lambda p: len(p.access_log),
            reverse=True
        )[:5]
        
        # Gera insights
        insights = await self._generate_sharing_insights(stats)
        
        return {
            'stats': stats,
            'most_active_projects': [{
                'name': p.name,
                'collaborators': len(p.collaborators),
                'access_events': len(p.access_log),
                'last_activity': p.access_log[-1]['timestamp'] if p.access_log else None
            } for p in most_active],
            'insights': insights,
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_sharing_insights(self, stats: Dict[str, Any]) -> List[str]:
        """Gera insights sobre compartilhamento."""
        insights = []
        
        if stats['total_projects'] == 0:
            insights.append("Nenhum projeto compartilhado ainda")
        else:
            insights.append(f"{stats['total_projects']} projetos compartilhados com {stats['unique_collaborators']} colaboradores")
            
            if stats['active_projects'] < stats['total_projects']:
                archived = stats['total_projects'] - stats['active_projects']
                insights.append(f"{archived} projetos arquivados - considere reativá-los se necessário")
            
            # Linguagem dominante
            if stats['language_distribution']:
                top_lang = max(stats['language_distribution'].items(), key=lambda x: x[1])
                insights.append(f"Linguagem mais usada: {top_lang[0]} ({top_lang[1]} projetos)")
            
            # Tamanho
            if stats['total_size_mb'] > 1000:
                insights.append(f"Total de {stats['total_size_mb']:.1f} MB compartilhados - monitore espaço")
        
        return insights