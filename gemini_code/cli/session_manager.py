"""
Session Manager - Gerenciamento de sessões estilo Claude Code
"""

import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib


class SessionManager:
    """
    Gerencia sessões do REPL, permitindo salvar, carregar e alternar entre sessões.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.sessions_dir = project_path / '.gemini_code' / 'sessions'
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Banco de sessões
        self.db_path = self.sessions_dir / 'sessions.db'
        self._init_database()
        
        # Sessão atual
        self.current_session_id: Optional[str] = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def _init_database(self):
        """Inicializa banco de dados de sessões."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de sessões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                command_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                metadata TEXT,
                context_size INTEGER DEFAULT 0,
                project_path TEXT,
                user_preferences TEXT
            )
        """)
        
        # Tabela de contexto de sessões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_type TEXT, -- 'user', 'assistant', 'system'
                content TEXT,
                metadata TEXT,
                token_count INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Tabela de comandos executados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT,
                command_type TEXT, -- 'slash', 'natural'
                result TEXT,
                execution_time_ms INTEGER,
                success BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_session_timestamp ON session_context(session_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_session_timestamp ON session_commands(session_id, timestamp)")
        
        conn.commit()
        conn.close()
    
    async def create_session(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Cria nova sessão."""
        session_id = str(uuid.uuid4())
        
        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"session_{timestamp}"
        
        session_data = {
            'id': session_id,
            'name': name,
            'created_at': datetime.now(),
            'last_active': datetime.now(),
            'command_count': 0,
            'status': 'active',
            'context': [],
            'metadata': {
                'project_path': str(self.project_path),
                'created_by': 'repl',
                'version': '1.0'
            }
        }
        
        # Salva no banco
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (id, name, created_at, last_active, project_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            name,
            session_data['created_at'],
            session_data['last_active'],
            str(self.project_path),
            json.dumps(session_data['metadata'])
        ))
        
        conn.commit()
        conn.close()
        
        # Adiciona às sessões ativas
        self.active_sessions[session_id] = session_data
        self.current_session_id = session_id
        
        return session_data
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega sessão existente."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Carrega dados da sessão
        cursor.execute("""
            SELECT id, name, created_at, last_active, command_count, status, metadata, context_size
            FROM sessions WHERE id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        session_data = {
            'id': row[0],
            'name': row[1],
            'created_at': datetime.fromisoformat(row[2]),
            'last_active': datetime.fromisoformat(row[3]),
            'command_count': row[4],
            'status': row[5],
            'metadata': json.loads(row[6]) if row[6] else {},
            'context_size': row[7],
            'context': []
        }
        
        # Carrega contexto da sessão
        cursor.execute("""
            SELECT timestamp, message_type, content, metadata, token_count
            FROM session_context 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        context_rows = cursor.fetchall()
        for ctx_row in context_rows:
            session_data['context'].append({
                'timestamp': datetime.fromisoformat(ctx_row[0]),
                'type': ctx_row[1],
                'content': ctx_row[2],
                'metadata': json.loads(ctx_row[3]) if ctx_row[3] else {},
                'token_count': ctx_row[4]
            })
        
        conn.close()
        
        # Adiciona às sessões ativas
        self.active_sessions[session_id] = session_data
        
        return session_data
    
    async def save_session(self, session_id: str, context: List[Dict[str, Any]]):
        """Salva contexto da sessão."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Atualiza dados da sessão
        cursor.execute("""
            UPDATE sessions 
            SET last_active = ?, command_count = ?, context_size = ?
            WHERE id = ?
        """, (
            datetime.now(),
            session['command_count'],
            len(context),
            session_id
        ))
        
        # Remove contexto antigo
        cursor.execute("DELETE FROM session_context WHERE session_id = ?", (session_id,))
        
        # Salva novo contexto
        for item in context:
            cursor.execute("""
                INSERT INTO session_context (session_id, timestamp, message_type, content, metadata, token_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                item.get('timestamp', datetime.now()),
                item.get('type', 'unknown'),
                item.get('input') or item.get('output') or item.get('content', ''),
                json.dumps(item.get('metadata', {})),
                item.get('token_count', 0)
            ))
        
        conn.commit()
        conn.close()
        
        return True
    
    async def switch_session(self, session_id: str) -> bool:
        """Alterna para sessão específica."""
        # Carrega sessão se não estiver em memória
        if session_id not in self.active_sessions:
            session = await self.load_session(session_id)
            if not session:
                return False
        
        self.current_session_id = session_id
        
        # Atualiza last_active
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions SET last_active = ? WHERE id = ?
        """, (datetime.now(), session_id))
        conn.commit()
        conn.close()
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Remove sessão."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Remove contexto
        cursor.execute("DELETE FROM session_context WHERE session_id = ?", (session_id,))
        
        # Remove comandos
        cursor.execute("DELETE FROM session_commands WHERE session_id = ?", (session_id,))
        
        # Remove sessão
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        # Remove da memória
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Se era a sessão atual, limpa
        if self.current_session_id == session_id:
            self.current_session_id = None
        
        return True
    
    async def list_sessions(self, limit: int = 20, active_only: bool = False) -> List[Dict[str, Any]]:
        """Lista sessões disponíveis."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = """
            SELECT id, name, created_at, last_active, command_count, status, context_size
            FROM sessions
        """
        params = []
        
        if active_only:
            query += " WHERE status = 'active'"
        
        query += " ORDER BY last_active DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'name': row[1],
                'created_at': datetime.fromisoformat(row[2]),
                'last_active': datetime.fromisoformat(row[3]),
                'command_count': row[4],
                'status': row[5],
                'context_size': row[6],
                'is_current': row[0] == self.current_session_id
            })
        
        return sessions
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas de uma sessão."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Dados básicos da sessão
        cursor.execute("""
            SELECT name, created_at, last_active, command_count, context_size
            FROM sessions WHERE id = ?
        """, (session_id,))
        
        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            return None
        
        # Estatísticas de comandos
        cursor.execute("""
            SELECT 
                command_type,
                COUNT(*) as count,
                AVG(execution_time_ms) as avg_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
            FROM session_commands 
            WHERE session_id = ?
            GROUP BY command_type
        """, (session_id,))
        
        command_stats = {}
        for row in cursor.fetchall():
            command_stats[row[0]] = {
                'count': row[1],
                'avg_time_ms': row[2] or 0,
                'success_rate': (row[3] / row[1]) * 100 if row[1] > 0 else 0
            }
        
        # Atividade por hora
        cursor.execute("""
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as count
            FROM session_commands 
            WHERE session_id = ?
            GROUP BY hour
            ORDER BY hour
        """, (session_id,))
        
        activity_by_hour = dict(cursor.fetchall())
        
        conn.close()
        
        created_at = datetime.fromisoformat(session_row[1])
        last_active = datetime.fromisoformat(session_row[2])
        duration = last_active - created_at
        
        return {
            'session_id': session_id,
            'name': session_row[0],
            'created_at': created_at,
            'last_active': last_active,
            'duration_minutes': duration.total_seconds() / 60,
            'total_commands': session_row[3],
            'context_size': session_row[4],
            'command_stats': command_stats,
            'activity_by_hour': activity_by_hour
        }
    
    async def export_session(self, session_id: str, format: str = 'json') -> Optional[Dict[str, Any]]:
        """Exporta dados de uma sessão."""
        session = await self.load_session(session_id)
        if not session:
            return None
        
        # Busca comandos executados
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, command, command_type, result, execution_time_ms, success
            FROM session_commands 
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        commands = []
        for row in cursor.fetchall():
            commands.append({
                'timestamp': row[0],
                'command': row[1],
                'type': row[2],
                'result': row[3],
                'execution_time_ms': row[4],
                'success': bool(row[5])
            })
        
        conn.close()
        
        export_data = {
            'export_info': {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'format': format
            },
            'session': {
                'id': session['id'],
                'name': session['name'],
                'created_at': session['created_at'].isoformat(),
                'last_active': session['last_active'].isoformat(),
                'command_count': session['command_count'],
                'metadata': session['metadata']
            },
            'context': [
                {
                    'timestamp': item['timestamp'].isoformat(),
                    'type': item['type'],
                    'content': item['content'],
                    'metadata': item['metadata']
                }
                for item in session['context']
            ],
            'commands': commands
        }
        
        return export_data
    
    async def cleanup_old_sessions(self, days: int = 30):
        """Remove sessões antigas."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca sessões antigas
        cursor.execute("""
            SELECT id FROM sessions 
            WHERE last_active < ? AND status != 'pinned'
        """, (cutoff_date,))
        
        old_session_ids = [row[0] for row in cursor.fetchall()]
        
        # Remove cada sessão antiga
        for session_id in old_session_ids:
            cursor.execute("DELETE FROM session_context WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM session_commands WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        return len(old_session_ids)
    
    async def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca sessões por conteúdo."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca em nomes de sessões e contexto
        cursor.execute("""
            SELECT DISTINCT s.id, s.name, s.created_at, s.last_active, s.command_count
            FROM sessions s
            LEFT JOIN session_context sc ON s.id = sc.session_id
            WHERE s.name LIKE ? OR sc.content LIKE ?
            ORDER BY s.last_active DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'created_at': datetime.fromisoformat(row[2]),
                'last_active': datetime.fromisoformat(row[3]),
                'command_count': row[4]
            })
        
        conn.close()
        return results
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Retorna sessão atual."""
        if self.current_session_id and self.current_session_id in self.active_sessions:
            return self.active_sessions[self.current_session_id]
        return None
    
    async def log_command(self, session_id: str, command: str, command_type: str, 
                         result: str, execution_time_ms: int, success: bool):
        """Registra comando executado."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO session_commands 
            (session_id, command, command_type, result, execution_time_ms, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, command, command_type, result, execution_time_ms, success))
        
        # Atualiza contador de comandos da sessão
        cursor.execute("""
            UPDATE sessions 
            SET command_count = command_count + 1, last_active = ?
            WHERE id = ?
        """, (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
        
        # Atualiza em memória
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['command_count'] += 1
            self.active_sessions[session_id]['last_active'] = datetime.now()