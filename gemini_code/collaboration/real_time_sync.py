"""
Sistema de sincronização em tempo real para colaboração.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import time

from ..core.gemini_client import GeminiClient
from .team_manager import TeamManager


@dataclass
class SyncEvent:
    """Evento de sincronização."""
    id: str
    project_id: str
    member_id: str
    event_type: str  # file_changed, file_added, file_deleted, cursor_moved, etc.
    file_path: str
    timestamp: datetime
    data: Dict[str, Any]
    checksum: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncEvent':
        """Cria evento a partir de dicionário."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ActiveSession:
    """Sessão ativa de colaboração."""
    id: str
    project_id: str
    member_id: str
    file_path: str
    started_at: datetime
    last_activity: datetime
    cursor_position: Dict[str, int]  # line, column
    selected_range: Optional[Dict[str, Any]] = None
    is_editing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    def update_activity(self) -> None:
        """Atualiza última atividade."""
        self.last_activity = datetime.now()


class RealTimeSync:
    """Sistema de sincronização em tempo real."""
    
    def __init__(self, gemini_client: GeminiClient, team_manager: TeamManager):
        self.gemini_client = gemini_client
        self.team_manager = team_manager
        self.active_sessions: Dict[str, ActiveSession] = {}
        self.event_queue: List[SyncEvent] = []
        self.event_callbacks: Dict[str, List[Callable]] = {
            'file_changed': [],
            'file_added': [],
            'file_deleted': [],
            'cursor_moved': [],
            'selection_changed': [],
            'member_joined': [],
            'member_left': []
        }
        self.file_watchers: Dict[str, Any] = {}
        self.running = False
        self.sync_interval = 1.0  # segundos
        self.data_dir = Path('.gemini_code/realtime')
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Inicializa armazenamento."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def start_sync(self) -> None:
        """Inicia sincronização em tempo real."""
        if self.running:
            return
        
        self.running = True
        print("Iniciando sincronização em tempo real...")
        
        # Inicia tasks de sincronização
        await asyncio.gather(
            self._event_processor(),
            self._session_monitor(),
            self._conflict_resolver()
        )
    
    async def stop_sync(self) -> None:
        """Para sincronização."""
        self.running = False
        
        # Limpa sessões ativas
        for session in list(self.active_sessions.values()):
            await self.leave_session(session.id)
        
        print("Sincronização em tempo real parada.")
    
    async def join_session(self, project_id: str, member_id: str, 
                          file_path: str) -> str:
        """Inicia sessão de colaboração."""
        # Verifica se membro existe
        member = self.team_manager.get_member(member_id)
        if not member:
            raise ValueError("Membro não encontrado")
        
        # Cria sessão
        session_id = str(uuid.uuid4())
        session = ActiveSession(
            id=session_id,
            project_id=project_id,
            member_id=member_id,
            file_path=file_path,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            cursor_position={'line': 1, 'column': 1}
        )
        
        self.active_sessions[session_id] = session
        
        # Notifica outros membros
        await self._broadcast_event(SyncEvent(
            id=str(uuid.uuid4()),
            project_id=project_id,
            member_id=member_id,
            event_type='member_joined',
            file_path=file_path,
            timestamp=datetime.now(),
            data={
                'session_id': session_id,
                'member_name': member.name
            }
        ))
        
        # Inicia monitoramento do arquivo
        await self._start_file_watching(file_path, session_id)
        
        return session_id
    
    async def leave_session(self, session_id: str) -> bool:
        """Sai da sessão de colaboração."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Para monitoramento do arquivo
        await self._stop_file_watching(session.file_path)
        
        # Notifica outros membros
        member = self.team_manager.get_member(session.member_id)
        await self._broadcast_event(SyncEvent(
            id=str(uuid.uuid4()),
            project_id=session.project_id,
            member_id=session.member_id,
            event_type='member_left',
            file_path=session.file_path,
            timestamp=datetime.now(),
            data={
                'session_id': session_id,
                'member_name': member.name if member else 'Unknown',
                'duration': (datetime.now() - session.started_at).total_seconds()
            }
        ))
        
        # Remove sessão
        del self.active_sessions[session_id]
        return True
    
    async def update_cursor(self, session_id: str, line: int, column: int) -> bool:
        """Atualiza posição do cursor."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Atualiza posição
        session.cursor_position = {'line': line, 'column': column}
        session.update_activity()
        
        # Broadcast evento
        await self._broadcast_event(SyncEvent(
            id=str(uuid.uuid4()),
            project_id=session.project_id,
            member_id=session.member_id,
            event_type='cursor_moved',
            file_path=session.file_path,
            timestamp=datetime.now(),
            data=session.cursor_position,
            line_number=line,
            column_number=column
        ))
        
        return True
    
    async def update_selection(self, session_id: str, 
                             start_line: int, start_col: int,
                             end_line: int, end_col: int) -> bool:
        """Atualiza seleção de texto."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Atualiza seleção
        session.selected_range = {
            'start': {'line': start_line, 'column': start_col},
            'end': {'line': end_line, 'column': end_col}
        }
        session.update_activity()
        
        # Broadcast evento
        await self._broadcast_event(SyncEvent(
            id=str(uuid.uuid4()),
            project_id=session.project_id,
            member_id=session.member_id,
            event_type='selection_changed',
            file_path=session.file_path,
            timestamp=datetime.now(),
            data=session.selected_range
        ))
        
        return True
    
    async def sync_file_change(self, session_id: str, 
                             changes: List[Dict[str, Any]]) -> bool:
        """Sincroniza mudanças no arquivo."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Marca como editando
        session.is_editing = True
        session.update_activity()
        
        # Calcula checksum do arquivo
        file_path = Path(session.file_path)
        checksum = None
        if file_path.exists():
            with open(file_path, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
        
        # Broadcast mudanças
        for change in changes:
            await self._broadcast_event(SyncEvent(
                id=str(uuid.uuid4()),
                project_id=session.project_id,
                member_id=session.member_id,
                event_type='file_changed',
                file_path=session.file_path,
                timestamp=datetime.now(),
                data=change,
                checksum=checksum
            ))
        
        # Para de editar após delay
        await asyncio.sleep(2)
        session.is_editing = False
        
        return True
    
    async def _start_file_watching(self, file_path: str, session_id: str) -> None:
        """Inicia monitoramento de arquivo."""
        try:
            # Simulação de file watcher
            # Em implementação real, usaria watchdog ou similar
            async def watch_loop():
                last_mtime = 0
                file_path_obj = Path(file_path)
                
                while session_id in self.active_sessions and self.running:
                    try:
                        if file_path_obj.exists():
                            current_mtime = file_path_obj.stat().st_mtime
                            
                            if current_mtime > last_mtime:
                                last_mtime = current_mtime
                                
                                # Arquivo foi modificado externamente
                                if not self.active_sessions[session_id].is_editing:
                                    await self._handle_external_file_change(
                                        session_id, file_path
                                    )
                        
                        await asyncio.sleep(self.sync_interval)
                        
                    except Exception as e:
                        print(f"Erro no monitoramento do arquivo: {e}")
                        await asyncio.sleep(5)
            
            # Inicia task de monitoramento
            self.file_watchers[file_path] = asyncio.create_task(watch_loop())
            
        except Exception as e:
            print(f"Erro ao iniciar monitoramento: {e}")
    
    async def _stop_file_watching(self, file_path: str) -> None:
        """Para monitoramento de arquivo."""
        if file_path in self.file_watchers:
            task = self.file_watchers[file_path]
            if not task.done():
                task.cancel()
            del self.file_watchers[file_path]
    
    async def _handle_external_file_change(self, session_id: str, 
                                         file_path: str) -> None:
        """Trata mudança externa no arquivo."""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Calcula novo checksum
        file_path_obj = Path(file_path)
        checksum = None
        if file_path_obj.exists():
            with open(file_path_obj, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
        
        # Broadcast mudança externa
        await self._broadcast_event(SyncEvent(
            id=str(uuid.uuid4()),
            project_id=session.project_id,
            member_id='system',
            event_type='file_changed',
            file_path=file_path,
            timestamp=datetime.now(),
            data={'external_change': True},
            checksum=checksum
        ))
    
    async def _broadcast_event(self, event: SyncEvent) -> None:
        """Faz broadcast de evento para todos os callbacks."""
        # Adiciona à fila
        self.event_queue.append(event)
        
        # Executa callbacks
        callbacks = self.event_callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Erro no callback de evento: {e}")
        
        # Salva evento
        await self._save_event(event)
    
    async def _save_event(self, event: SyncEvent) -> None:
        """Salva evento em arquivo."""
        try:
            events_file = self.data_dir / f"events_{event.project_id}.jsonl"
            
            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"Erro ao salvar evento: {e}")
    
    async def _event_processor(self) -> None:
        """Processa fila de eventos."""
        while self.running:
            try:
                # Processa eventos pendentes
                while self.event_queue:
                    event = self.event_queue.pop(0)
                    await self._process_event(event)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Erro no processador de eventos: {e}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: SyncEvent) -> None:
        """Processa evento individual."""
        try:
            # Log do evento
            member = self.team_manager.get_member(event.member_id)
            member_name = member.name if member else event.member_id
            
            print(f"Evento: {event.event_type} por {member_name} em {event.file_path}")
            
            # Processamento específico por tipo
            if event.event_type == 'file_changed':
                await self._handle_file_changed(event)
            elif event.event_type == 'member_joined':
                await self._handle_member_joined(event)
            elif event.event_type == 'member_left':
                await self._handle_member_left(event)
            
        except Exception as e:
            print(f"Erro ao processar evento: {e}")
    
    async def _handle_file_changed(self, event: SyncEvent) -> None:
        """Trata evento de mudança de arquivo."""
        # Verifica conflitos
        conflicts = await self._detect_conflicts(event)
        
        if conflicts:
            await self._handle_conflicts(event, conflicts)
        
        # Atualiza estatísticas
        await self._update_collaboration_stats(event)
    
    async def _handle_member_joined(self, event: SyncEvent) -> None:
        """Trata entrada de membro na sessão."""
        print(f"👥 {event.data.get('member_name')} entrou na colaboração em {event.file_path}")
    
    async def _handle_member_left(self, event: SyncEvent) -> None:
        """Trata saída de membro da sessão."""
        duration = event.data.get('duration', 0)
        print(f"👥 {event.data.get('member_name')} saiu da colaboração (duração: {duration:.1f}s)")
    
    async def _session_monitor(self) -> None:
        """Monitora sessões ativas."""
        while self.running:
            try:
                current_time = datetime.now()
                inactive_sessions = []
                
                # Verifica sessões inativas
                for session_id, session in self.active_sessions.items():
                    if (current_time - session.last_activity).total_seconds() > 300:  # 5 minutos
                        inactive_sessions.append(session_id)
                
                # Remove sessões inativas
                for session_id in inactive_sessions:
                    print(f"Removendo sessão inativa: {session_id}")
                    await self.leave_session(session_id)
                
                await asyncio.sleep(60)  # Verifica a cada minuto
                
            except Exception as e:
                print(f"Erro no monitor de sessões: {e}")
                await asyncio.sleep(60)
    
    async def _conflict_resolver(self) -> None:
        """Resolve conflitos de colaboração."""
        while self.running:
            try:
                # Processa resolução de conflitos
                # Em implementação real, aplicaria algoritmos de merge
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Erro no resolvedor de conflitos: {e}")
                await asyncio.sleep(5)
    
    async def _detect_conflicts(self, event: SyncEvent) -> List[Dict[str, Any]]:
        """Detecta conflitos em evento."""
        conflicts = []
        
        try:
            # Verifica se múltiplos usuários estão editando o mesmo arquivo
            same_file_sessions = [
                s for s in self.active_sessions.values()
                if s.file_path == event.file_path and s.is_editing
            ]
            
            if len(same_file_sessions) > 1:
                conflicts.append({
                    'type': 'concurrent_editing',
                    'file_path': event.file_path,
                    'editors': [s.member_id for s in same_file_sessions]
                })
            
        except Exception as e:
            print(f"Erro ao detectar conflitos: {e}")
        
        return conflicts
    
    async def _handle_conflicts(self, event: SyncEvent, 
                              conflicts: List[Dict[str, Any]]) -> None:
        """Trata conflitos detectados."""
        for conflict in conflicts:
            if conflict['type'] == 'concurrent_editing':
                # Notifica editores sobre conflito
                for editor_id in conflict['editors']:
                    print(f"⚠️ Conflito detectado: Múltiplos editores em {conflict['file_path']}")
    
    async def _update_collaboration_stats(self, event: SyncEvent) -> None:
        """Atualiza estatísticas de colaboração."""
        try:
            stats_file = self.data_dir / 'collaboration_stats.json'
            
            # Carrega estatísticas existentes
            stats = {}
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            
            # Atualiza estatísticas
            project_stats = stats.get(event.project_id, {
                'total_events': 0,
                'unique_collaborators': set(),
                'files_edited': set(),
                'last_activity': None
            })
            
            project_stats['total_events'] += 1
            project_stats['unique_collaborators'].add(event.member_id)
            project_stats['files_edited'].add(event.file_path)
            project_stats['last_activity'] = event.timestamp.isoformat()
            
            # Converte sets para listas para JSON
            stats[event.project_id] = {
                'total_events': project_stats['total_events'],
                'unique_collaborators': list(project_stats['unique_collaborators']),
                'files_edited': list(project_stats['files_edited']),
                'last_activity': project_stats['last_activity']
            }
            
            # Salva estatísticas
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """Adiciona callback para tipo de evento."""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable) -> bool:
        """Remove callback."""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)
            return True
        return False
    
    def get_active_sessions(self, project_id: Optional[str] = None) -> List[ActiveSession]:
        """Obtém sessões ativas."""
        sessions = list(self.active_sessions.values())
        
        if project_id:
            sessions = [s for s in sessions if s.project_id == project_id]
        
        return sessions
    
    def get_collaborators_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Obtém colaboradores ativos em arquivo."""
        collaborators = []
        
        for session in self.active_sessions.values():
            if session.file_path == file_path:
                member = self.team_manager.get_member(session.member_id)
                collaborators.append({
                    'session_id': session.id,
                    'member_id': session.member_id,
                    'member_name': member.name if member else 'Unknown',
                    'cursor_position': session.cursor_position,
                    'is_editing': session.is_editing,
                    'last_activity': session.last_activity.isoformat()
                })
        
        return collaborators
    
    async def get_project_events(self, project_id: str, 
                               limit: int = 100) -> List[SyncEvent]:
        """Obtém eventos de projeto."""
        events = []
        
        try:
            events_file = self.data_dir / f"events_{project_id}.jsonl"
            
            if events_file.exists():
                with open(events_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Pega últimas linhas
                    for line in lines[-limit:]:
                        event_data = json.loads(line.strip())
                        events.append(SyncEvent.from_dict(event_data))
                        
        except Exception as e:
            print(f"Erro ao carregar eventos: {e}")
        
        return events
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de sincronização."""
        return {
            'running': self.running,
            'active_sessions': len(self.active_sessions),
            'monitored_files': len(self.file_watchers),
            'events_queued': len(self.event_queue),
            'sync_interval': self.sync_interval,
            'sessions_by_project': self._group_sessions_by_project()
        }
    
    def _group_sessions_by_project(self) -> Dict[str, int]:
        """Agrupa sessões por projeto."""
        project_counts = {}
        
        for session in self.active_sessions.values():
            project_id = session.project_id
            project_counts[project_id] = project_counts.get(project_id, 0) + 1
        
        return project_counts
    
    async def broadcast_message(self, project_id: str, sender_id: str, 
                              message: str) -> None:
        """Envia mensagem para todos os colaboradores do projeto."""
        # Cria evento de mensagem
        message_event = SyncEvent(
            id=str(uuid.uuid4()),
            project_id=project_id,
            member_id=sender_id,
            event_type='message',
            file_path='',
            timestamp=datetime.now(),
            data={
                'message': message,
                'sender_name': self.team_manager.get_member(sender_id).name
            }
        )
        
        await self._broadcast_event(message_event)
    
    async def create_snapshot(self, project_id: str) -> str:
        """Cria snapshot do estado atual do projeto."""
        snapshot_id = str(uuid.uuid4())
        
        snapshot = {
            'id': snapshot_id,
            'project_id': project_id,
            'timestamp': datetime.now().isoformat(),
            'active_sessions': [s.to_dict() for s in self.get_active_sessions(project_id)],
            'recent_events': [e.to_dict() for e in await self.get_project_events(project_id, 50)]
        }
        
        # Salva snapshot
        snapshot_file = self.data_dir / f"snapshot_{snapshot_id}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        return snapshot_id