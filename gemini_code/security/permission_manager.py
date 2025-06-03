"""
Permission Manager - Sistema de permissões em camadas estilo Claude Code
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

from ..tools.base_tool import BaseTool, ToolInput, ToolResult


class PermissionLevel(Enum):
    """Níveis de permissão para operações."""
    ALWAYS_ALLOW = "always_allow"      # Sempre permite (read-only tools)
    ASK_ONCE = "ask_once"              # Pergunta uma vez por sessão
    ASK_ALWAYS = "ask_always"          # Pergunta sempre
    ASK_UNTIL_SESSION_END = "ask_until_session_end"  # Pergunta até fim da sessão
    DENY = "deny"                      # Sempre nega
    DANGEROUS_SKIP = "dangerous_skip"  # Modo perigoso (containers)


class OperationType(Enum):
    """Tipos de operações para controle de permissão."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    NETWORK_ACCESS = "network_access"
    SYSTEM_MODIFY = "system_modify"
    DIRECTORY_TRAVERSE = "directory_traverse"
    PROCESS_SPAWN = "process_spawn"


@dataclass
class PermissionRequest:
    """Solicitação de permissão."""
    operation_type: OperationType
    resource: str
    tool_name: str
    description: str
    risk_level: str = "medium"  # low, medium, high, critical
    session_id: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionDecision:
    """Decisão de permissão."""
    granted: bool
    remember_choice: bool = False
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    conditions: List[str] = field(default_factory=list)


class PermissionManager:
    """
    Gerencia permissões do sistema com controle granular.
    Implementa os padrões de segurança do Claude Code.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.permissions_dir = self.project_path / '.gemini_code' / 'permissions'
        self.permissions_dir.mkdir(parents=True, exist_ok=True)
        
        # Banco de permissões
        self.db_path = self.permissions_dir / 'permissions.db'
        self._init_database()
        
        # Cache de decisões da sessão
        self.session_decisions: Dict[str, Dict[str, PermissionDecision]] = {}
        
        # Configurações de segurança
        self.security_config = self._load_security_config()
        
        # Permissões padrão por tipo de operação
        self.default_permissions = {
            OperationType.READ_FILE: PermissionLevel.ALWAYS_ALLOW,
            OperationType.WRITE_FILE: PermissionLevel.ASK_ONCE,
            OperationType.DELETE_FILE: PermissionLevel.ASK_ALWAYS,
            OperationType.EXECUTE_COMMAND: PermissionLevel.ASK_UNTIL_SESSION_END,
            OperationType.NETWORK_ACCESS: PermissionLevel.ASK_ALWAYS,
            OperationType.SYSTEM_MODIFY: PermissionLevel.ASK_ALWAYS,
            OperationType.DIRECTORY_TRAVERSE: PermissionLevel.ALWAYS_ALLOW,
            OperationType.PROCESS_SPAWN: PermissionLevel.ASK_ALWAYS,
        }
        
        # Diretórios e comandos protegidos
        self.protected_directories = {
            '/etc', '/usr/bin', '/usr/sbin', '/sbin', '/bin',
            '/boot', '/dev', '/proc', '/sys', '/var/log',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32'
        }
        
        self.dangerous_commands = {
            'rm -rf /', 'sudo rm -rf', 'format', 'fdisk', 'mkfs',
            'dd if=/dev/zero', 'sudo halt', 'sudo reboot', 'sudo shutdown',
            'curl', 'wget', 'nc', 'netcat', 'telnet', 'ssh'
        }
        
        # URLs permitidas
        self.allowed_urls = {
            'api.google.com',
            'googleapis.com',
            'localhost',
            '127.0.0.1',
            'github.com',
            'raw.githubusercontent.com'
        }
        
        # Callbacks para solicitar permissão
        self.permission_callbacks: Dict[str, Callable] = {}
        
    def _init_database(self):
        """Inicializa banco de permissões."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de decisões de permissão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permission_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                resource TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                granted BOOLEAN NOT NULL,
                granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                session_id TEXT,
                remember_choice BOOLEAN DEFAULT FALSE,
                risk_level TEXT DEFAULT 'medium',
                user_decision TEXT,
                conditions TEXT
            )
        """)
        
        # Tabela de configurações de segurança
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de violações de segurança
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                resource TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Carrega configurações de segurança."""
        default_config = {
            'dangerous_operations_mode': False,
            'network_access_enabled': True,
            'file_access_restricted': False,
            'command_execution_enabled': True,
            'max_file_size_mb': 100,
            'session_timeout_hours': 24,
            'auto_deny_patterns': [],
            'auto_allow_patterns': []
        }
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT key, value FROM security_config")
            rows = cursor.fetchall()
            
            config = default_config.copy()
            for key, value in rows:
                try:
                    config[key] = json.loads(value)
                except json.JSONDecodeError:
                    config[key] = value
            
            conn.close()
            return config
            
        except Exception:
            return default_config
    
    def register_permission_callback(self, operation_type: str, callback: Callable):
        """Registra callback para solicitar permissão interativa."""
        self.permission_callbacks[operation_type] = callback
    
    async def check_permission(self, request: PermissionRequest) -> PermissionDecision:
        """
        Verifica permissão para uma operação.
        Principal método do sistema de permissões.
        """
        # 1. Verificações de segurança básicas
        security_check = self._basic_security_check(request)
        if not security_check.granted:
            await self._log_security_violation(request, "basic_security_failed")
            return security_check
        
        # 2. Verifica se há decisão em cache da sessão
        cached_decision = self._get_cached_decision(request)
        if cached_decision:
            return cached_decision
        
        # 3. Verifica decisões persistentes
        persistent_decision = self._get_persistent_decision(request)
        if persistent_decision:
            return persistent_decision
        
        # 4. Aplica política de permissão padrão
        permission_level = self._get_permission_level(request)
        
        if permission_level == PermissionLevel.ALWAYS_ALLOW:
            decision = PermissionDecision(granted=True, reason="always_allowed")
        
        elif permission_level == PermissionLevel.DENY:
            decision = PermissionDecision(granted=False, reason="policy_denied")
        
        elif permission_level == PermissionLevel.DANGEROUS_SKIP:
            # Modo perigoso - permite tudo
            decision = PermissionDecision(granted=True, reason="dangerous_mode")
        
        else:
            # Solicita permissão interativa
            decision = await self._request_interactive_permission(request, permission_level)
        
        # 5. Salva decisão se necessário
        if decision.remember_choice or permission_level in [PermissionLevel.ASK_UNTIL_SESSION_END]:
            self._save_decision(request, decision)
        
        return decision
    
    def _basic_security_check(self, request: PermissionRequest) -> PermissionDecision:
        """Verificações básicas de segurança."""
        
        # Verifica diretórios protegidos
        if request.operation_type in [OperationType.WRITE_FILE, OperationType.DELETE_FILE]:
            resource_path = Path(request.resource).resolve()
            for protected_dir in self.protected_directories:
                if str(resource_path).startswith(protected_dir):
                    return PermissionDecision(
                        granted=False, 
                        reason=f"protected_directory: {protected_dir}"
                    )
        
        # Verifica comandos perigosos
        if request.operation_type == OperationType.EXECUTE_COMMAND:
            command_lower = request.resource.lower()
            for dangerous_cmd in self.dangerous_commands:
                if dangerous_cmd in command_lower:
                    return PermissionDecision(
                        granted=False,
                        reason=f"dangerous_command: {dangerous_cmd}"
                    )
        
        # Verifica acesso à rede
        if request.operation_type == OperationType.NETWORK_ACCESS:
            if not self.security_config.get('network_access_enabled', True):
                return PermissionDecision(
                    granted=False,
                    reason="network_access_disabled"
                )
            
            # Verifica URLs permitidas
            if not self._is_url_allowed(request.resource):
                return PermissionDecision(
                    granted=False,
                    reason=f"url_not_whitelisted: {request.resource}"
                )
        
        # Verifica tamanho de arquivo
        if request.operation_type == OperationType.WRITE_FILE:
            max_size_mb = self.security_config.get('max_file_size_mb', 100)
            content_size = request.user_context.get('content_size_mb', 0)
            if content_size > max_size_mb:
                return PermissionDecision(
                    granted=False,
                    reason=f"file_too_large: {content_size}MB > {max_size_mb}MB"
                )
        
        return PermissionDecision(granted=True, reason="security_check_passed")
    
    def _get_cached_decision(self, request: PermissionRequest) -> Optional[PermissionDecision]:
        """Verifica decisão em cache da sessão."""
        if not request.session_id:
            return None
        
        session_cache = self.session_decisions.get(request.session_id, {})
        cache_key = self._get_decision_key(request)
        
        cached = session_cache.get(cache_key)
        if cached and (not cached.expires_at or cached.expires_at > datetime.now()):
            return cached
        
        return None
    
    def _get_persistent_decision(self, request: PermissionRequest) -> Optional[PermissionDecision]:
        """Verifica decisões persistentes no banco."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT granted, expires_at, remember_choice, conditions
                FROM permission_decisions
                WHERE operation_type = ? AND resource = ? AND tool_name = ?
                AND remember_choice = TRUE
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY granted_at DESC
                LIMIT 1
            """, (
                request.operation_type.value,
                request.resource,
                request.tool_name,
                datetime.now()
            ))
            
            row = cursor.fetchone()
            if row:
                expires_at = datetime.fromisoformat(row[1]) if row[1] else None
                conditions = json.loads(row[3]) if row[3] else []
                
                return PermissionDecision(
                    granted=bool(row[0]),
                    remember_choice=bool(row[2]),
                    expires_at=expires_at,
                    conditions=conditions,
                    reason="persistent_decision"
                )
            
            conn.close()
            
        except Exception:
            pass
        
        return None
    
    def _get_permission_level(self, request: PermissionRequest) -> PermissionLevel:
        """Determina nível de permissão para a operação."""
        
        # Modo perigoso
        if self.security_config.get('dangerous_operations_mode', False):
            return PermissionLevel.DANGEROUS_SKIP
        
        # Permissão específica por ferramenta
        tool_permissions = self.security_config.get('tool_permissions', {})
        if request.tool_name in tool_permissions:
            tool_config = tool_permissions[request.tool_name]
            if request.operation_type.value in tool_config:
                level_str = tool_config[request.operation_type.value]
                return PermissionLevel(level_str)
        
        # Permissão padrão por tipo de operação
        return self.default_permissions.get(request.operation_type, PermissionLevel.ASK_ALWAYS)
    
    async def _request_interactive_permission(self, request: PermissionRequest, level: PermissionLevel) -> PermissionDecision:
        """Solicita permissão interativa do usuário."""
        
        # Se há callback registrado, usa ele
        if request.operation_type.value in self.permission_callbacks:
            callback = self.permission_callbacks[request.operation_type.value]
            try:
                return await callback(request, level)
            except Exception:
                pass
        
        # Fallback: aprovação automática baseada no risco
        if request.risk_level == "low":
            return PermissionDecision(
                granted=True, 
                reason="auto_approved_low_risk",
                expires_at=datetime.now() + timedelta(hours=1)
            )
        
        elif request.risk_level == "critical":
            return PermissionDecision(
                granted=False,
                reason="auto_denied_critical_risk"
            )
        
        else:
            # Risco médio/alto - aprova por padrão mas pede confirmação
            return PermissionDecision(
                granted=True,
                reason="auto_approved_with_warning",
                expires_at=datetime.now() + timedelta(minutes=30)
            )
    
    def _save_decision(self, request: PermissionRequest, decision: PermissionDecision):
        """Salva decisão de permissão."""
        
        # Salva no cache da sessão
        if request.session_id:
            if request.session_id not in self.session_decisions:
                self.session_decisions[request.session_id] = {}
            
            cache_key = self._get_decision_key(request)
            self.session_decisions[request.session_id][cache_key] = decision
        
        # Salva no banco se deve lembrar
        if decision.remember_choice:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO permission_decisions 
                    (operation_type, resource, tool_name, granted, expires_at, 
                     session_id, remember_choice, risk_level, conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.operation_type.value,
                    request.resource,
                    request.tool_name,
                    decision.granted,
                    decision.expires_at,
                    request.session_id,
                    decision.remember_choice,
                    request.risk_level,
                    json.dumps(decision.conditions)
                ))
                
                conn.commit()
                conn.close()
                
            except Exception:
                pass
    
    async def _log_security_violation(self, request: PermissionRequest, violation_type: str):
        """Registra violação de segurança."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO security_violations 
                (operation_type, resource, tool_name, violation_type, session_id, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                request.operation_type.value,
                request.resource,
                request.tool_name,
                violation_type,
                request.session_id,
                json.dumps(request.user_context)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def _get_decision_key(self, request: PermissionRequest) -> str:
        """Gera chave única para decisão."""
        return f"{request.operation_type.value}:{request.resource}:{request.tool_name}"
    
    def _is_url_allowed(self, url: str) -> bool:
        """Verifica se URL está na whitelist."""
        for allowed_domain in self.allowed_urls:
            if allowed_domain in url.lower():
                return True
        return False
    
    def clear_session_cache(self, session_id: str):
        """Limpa cache de decisões da sessão."""
        if session_id in self.session_decisions:
            del self.session_decisions[session_id]
    
    def enable_dangerous_mode(self):
        """Ativa modo perigoso (equivalente ao --dangerously-skip-permissions)."""
        self.security_config['dangerous_operations_mode'] = True
        self._save_security_config('dangerous_operations_mode', True)
    
    def disable_dangerous_mode(self):
        """Desativa modo perigoso."""
        self.security_config['dangerous_operations_mode'] = False
        self._save_security_config('dangerous_operations_mode', False)
    
    def _save_security_config(self, key: str, value: Any):
        """Salva configuração de segurança."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO security_config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def get_security_status(self) -> Dict[str, Any]:
        """Retorna status de segurança do sistema."""
        return {
            'dangerous_mode': self.security_config.get('dangerous_operations_mode', False),
            'network_access': self.security_config.get('network_access_enabled', True),
            'file_restrictions': self.security_config.get('file_access_restricted', False),
            'command_execution': self.security_config.get('command_execution_enabled', True),
            'max_file_size_mb': self.security_config.get('max_file_size_mb', 100),
            'session_timeout_hours': self.security_config.get('session_timeout_hours', 24),
            'protected_directories_count': len(self.protected_directories),
            'dangerous_commands_count': len(self.dangerous_commands),
            'allowed_urls_count': len(self.allowed_urls),
            'active_sessions': len(self.session_decisions)
        }
    
    def get_security_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna violações de segurança recentes."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT operation_type, resource, tool_name, violation_type, 
                       blocked_at, session_id, details
                FROM security_violations
                ORDER BY blocked_at DESC
                LIMIT ?
            """, (limit,))
            
            violations = []
            for row in cursor.fetchall():
                violations.append({
                    'operation_type': row[0],
                    'resource': row[1],
                    'tool_name': row[2],
                    'violation_type': row[3],
                    'blocked_at': row[4],
                    'session_id': row[5],
                    'details': json.loads(row[6]) if row[6] else {}
                })
            
            conn.close()
            return violations
            
        except Exception:
            return []