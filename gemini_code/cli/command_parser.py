"""
Command Parser - Parse de comandos slash estilo Claude Code
"""

import re
import shlex
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    """Resultado do parsing de um comando."""
    type: str
    action: str
    args: List[str]
    kwargs: Dict[str, Any]
    raw_command: str


class CommandParser:
    """
    Parser para comandos slash que replica o comportamento do Claude Code.
    """
    
    def __init__(self):
        # Mapeamento de comandos slash para funções
        self.slash_commands = {
            'help': self._parse_help,
            'cost': self._parse_cost,
            'clear': self._parse_clear,
            'compact': self._parse_compact,
            'doctor': self._parse_doctor,
            'bug': self._parse_bug,
            'memory': self._parse_memory,
            'config': self._parse_config,
            'sessions': self._parse_sessions,
            'export': self._parse_export,
            'exit': self._parse_exit,
            'quit': self._parse_exit,
            'context': self._parse_context,
            'history': self._parse_history,
            'stats': self._parse_stats,
            'workspace': self._parse_workspace,
            'model': self._parse_model,
            'thinking': self._parse_thinking,
        }
        
        # Aliases para comandos
        self.aliases = {
            'h': 'help',
            '?': 'help',
            'c': 'clear',
            'cls': 'clear',
            'x': 'exit',
            'q': 'quit',
            'mem': 'memory',
            'cfg': 'config',
            'diag': 'doctor',
            'diagnostic': 'doctor',
            'session': 'sessions',
            'exp': 'export',
        }
    
    async def parse_slash_command(self, command: str) -> Dict[str, Any]:
        """
        Parse comando slash e retorna estrutura padronizada.
        """
        if not command.startswith('/'):
            raise ValueError("Comando deve começar com '/'")
        
        # Remove o '/' inicial
        command_body = command[1:].strip()
        
        if not command_body:
            return {'type': 'help', 'error': 'Comando vazio'}
        
        # Split em partes usando shlex para lidar com aspas
        try:
            parts = shlex.split(command_body)
        except ValueError:
            # Se falhar, usa split simples
            parts = command_body.split()
        
        if not parts:
            return {'type': 'help', 'error': 'Comando vazio'}
        
        # Primeiro item é o comando principal
        main_command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Resolve aliases
        if main_command in self.aliases:
            main_command = self.aliases[main_command]
        
        # Verifica se comando existe
        if main_command not in self.slash_commands:
            return {
                'type': 'error',
                'error': f"Comando '/{main_command}' não reconhecido",
                'suggestion': self._suggest_command(main_command)
            }
        
        # Chama parser específico do comando
        try:
            parser_func = self.slash_commands[main_command]
            return await parser_func(main_command, args, command)
        except Exception as e:
            return {
                'type': 'error',
                'command': main_command,
                'error': str(e),
                'args': args
            }
    
    def _suggest_command(self, invalid_command: str) -> Optional[str]:
        """Sugere comando similar usando distância de edição."""
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # Encontra comando mais similar
        min_distance = float('inf')
        best_match = None
        
        all_commands = list(self.slash_commands.keys()) + list(self.aliases.keys())
        
        for cmd in all_commands:
            distance = levenshtein_distance(invalid_command.lower(), cmd.lower())
            if distance < min_distance and distance <= 2:  # Máximo 2 caracteres de diferença
                min_distance = distance
                best_match = cmd
        
        return best_match
    
    # Parsers específicos para cada comando
    
    async def _parse_help(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /help."""
        topic = args[0] if args else None
        
        return {
            'type': 'help',
            'topic': topic,
            'show_all': topic is None
        }
    
    async def _parse_cost(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /cost."""
        period = 'session'  # default
        
        if args:
            if args[0].lower() in ['session', 'today', 'week', 'month', 'total']:
                period = args[0].lower()
        
        return {
            'type': 'cost',
            'period': period,
            'detailed': '--detailed' in args or '-d' in args
        }
    
    async def _parse_clear(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /clear."""
        clear_type = 'session'  # default
        
        if args:
            if args[0].lower() in ['session', 'memory', 'history', 'all']:
                clear_type = args[0].lower()
        
        confirm_required = clear_type in ['memory', 'history', 'all']
        
        return {
            'type': 'clear',
            'clear_type': clear_type,
            'confirm_required': confirm_required,
            'force': '--force' in args or '-f' in args
        }
    
    async def _parse_compact(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /compact."""
        # Extrai instruções personalizadas
        instructions = None
        if args:
            instructions = ' '.join(args)
        
        return {
            'type': 'compact',
            'instructions': instructions,
            'aggressive': '--aggressive' in args,
            'preserve_recent': '--preserve-recent' in args
        }
    
    async def _parse_doctor(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /doctor."""
        check_type = 'all'  # default
        
        if args:
            valid_checks = ['all', 'system', 'memory', 'performance', 'security', 'network']
            if args[0].lower() in valid_checks:
                check_type = args[0].lower()
        
        return {
            'type': 'doctor',
            'check_type': check_type,
            'verbose': '--verbose' in args or '-v' in args,
            'fix': '--fix' in args
        }
    
    async def _parse_bug(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /bug."""
        description = ' '.join(args) if args else None
        
        return {
            'type': 'bug',
            'description': description,
            'include_logs': '--logs' in args,
            'include_config': '--config' in args
        }
    
    async def _parse_memory(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /memory."""
        action = 'show'  # default
        
        if args:
            valid_actions = ['show', 'clear', 'export', 'import', 'search', 'stats']
            if args[0].lower() in valid_actions:
                action = args[0].lower()
        
        # Para ação search, pega o termo
        search_term = None
        if action == 'search' and len(args) > 1:
            search_term = ' '.join(args[1:])
        
        return {
            'type': 'memory',
            'action': action,
            'search_term': search_term,
            'limit': self._extract_limit(args),
            'format': self._extract_format(args)
        }
    
    async def _parse_config(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /config."""
        action = 'show'  # default
        
        if args:
            if args[0].lower() in ['show', 'get', 'set', 'reset', 'list']:
                action = args[0].lower()
                args = args[1:]
        
        # Para set: /config set key value
        key = args[0] if args else None
        value = ' '.join(args[1:]) if len(args) > 1 else None
        
        return {
            'type': 'config',
            'action': action,
            'key': key,
            'value': value,
            'global': '--global' in args,
            'local': '--local' in args
        }
    
    async def _parse_sessions(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /sessions."""
        action = 'list'  # default
        
        if args:
            if args[0].lower() in ['list', 'switch', 'delete', 'export', 'import']:
                action = args[0].lower()
                args = args[1:]
        
        session_id = args[0] if args else None
        
        return {
            'type': 'sessions',
            'action': action,
            'session_id': session_id,
            'limit': self._extract_limit(args),
            'active_only': '--active' in args
        }
    
    async def _parse_export(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /export."""
        export_type = 'session'  # default
        
        if args:
            if args[0].lower() in ['session', 'memory', 'config', 'all']:
                export_type = args[0].lower()
                args = args[1:]
        
        # Arquivo de destino
        filename = args[0] if args else None
        
        return {
            'type': 'export',
            'export_type': export_type,
            'filename': filename,
            'format': self._extract_format(args, default='json'),
            'compress': '--zip' in args or '--compress' in args
        }
    
    async def _parse_exit(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /exit ou /quit."""
        return {
            'type': 'exit',
            'save_session': '--no-save' not in args,
            'force': '--force' in args
        }
    
    async def _parse_context(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /context."""
        action = 'show'  # default
        
        if args:
            if args[0].lower() in ['show', 'size', 'usage', 'optimize']:
                action = args[0].lower()
        
        return {
            'type': 'context',
            'action': action,
            'detailed': '--detailed' in args,
            'tokens': '--tokens' in args
        }
    
    async def _parse_history(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /history."""
        limit = self._extract_limit(args, default=20)
        
        return {
            'type': 'history',
            'limit': limit,
            'search': self._extract_search_term(args),
            'session_only': '--session' in args
        }
    
    async def _parse_stats(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /stats."""
        period = 'today'  # default
        
        if args:
            if args[0].lower() in ['session', 'today', 'week', 'month', 'all']:
                period = args[0].lower()
        
        return {
            'type': 'stats',
            'period': period,
            'detailed': '--detailed' in args
        }
    
    async def _parse_workspace(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /workspace."""
        action = 'info'  # default
        
        if args:
            if args[0].lower() in ['info', 'switch', 'create', 'delete', 'list']:
                action = args[0].lower()
                args = args[1:]
        
        workspace_name = args[0] if args else None
        
        return {
            'type': 'workspace',
            'action': action,
            'workspace_name': workspace_name
        }
    
    async def _parse_model(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /model."""
        action = 'info'  # default
        
        if args:
            if args[0].lower() in ['info', 'switch', 'list', 'config']:
                action = args[0].lower()
                args = args[1:]
        
        model_name = args[0] if args else None
        
        return {
            'type': 'model',
            'action': action,
            'model_name': model_name
        }
    
    async def _parse_thinking(self, command: str, args: List[str], raw: str) -> Dict[str, Any]:
        """Parse comando /thinking."""
        action = 'toggle'  # default
        
        if args:
            if args[0].lower() in ['on', 'off', 'toggle', 'budget', 'show']:
                action = args[0].lower()
                args = args[1:]
        
        budget = None
        if action == 'budget' and args:
            try:
                budget = int(args[0])
            except ValueError:
                pass
        
        return {
            'type': 'thinking',
            'action': action,
            'budget': budget,
            'show_reasoning': '--show' in args
        }
    
    # Métodos utilitários
    
    def _extract_limit(self, args: List[str], default: int = 10) -> int:
        """Extrai parâmetro --limit dos argumentos."""
        for i, arg in enumerate(args):
            if arg == '--limit' and i + 1 < len(args):
                try:
                    return int(args[i + 1])
                except ValueError:
                    pass
            elif arg.startswith('--limit='):
                try:
                    return int(arg.split('=')[1])
                except ValueError:
                    pass
        return default
    
    def _extract_format(self, args: List[str], default: str = 'table') -> str:
        """Extrai parâmetro --format dos argumentos."""
        for i, arg in enumerate(args):
            if arg == '--format' and i + 1 < len(args):
                return args[i + 1]
            elif arg.startswith('--format='):
                return arg.split('=')[1]
        return default
    
    def _extract_search_term(self, args: List[str]) -> Optional[str]:
        """Extrai termo de busca dos argumentos."""
        for i, arg in enumerate(args):
            if arg == '--search' and i + 1 < len(args):
                return args[i + 1]
            elif arg.startswith('--search='):
                return arg.split('=')[1]
        return None
    
    def get_available_commands(self) -> List[str]:
        """Retorna lista de todos os comandos disponíveis."""
        return list(self.slash_commands.keys())
    
    def get_command_help(self, command: str) -> Optional[str]:
        """Retorna ajuda específica para um comando."""
        help_texts = {
            'help': 'Mostra ajuda geral ou específica de um comando\nUso: /help [comando]',
            'cost': 'Mostra informações de custo e uso\nUso: /cost [session|today|week|month|total] [--detailed]',
            'clear': 'Limpa sessão, memória ou histórico\nUso: /clear [session|memory|history|all] [--force]',
            'compact': 'Compacta o contexto atual\nUso: /compact [instruções] [--aggressive] [--preserve-recent]',
            'doctor': 'Executa diagnósticos do sistema\nUso: /doctor [all|system|memory|performance|security] [--verbose] [--fix]',
            'bug': 'Reporta um bug ou problema\nUso: /bug [descrição] [--logs] [--config]',
            'memory': 'Gerencia memória do sistema\nUso: /memory [show|clear|export|search] [termo] [--limit=N]',
            'config': 'Gerencia configurações\nUso: /config [show|get|set|reset] [chave] [valor] [--global|--local]',
            'sessions': 'Gerencia sessões\nUso: /sessions [list|switch|delete|export] [id] [--active] [--limit=N]',
            'export': 'Exporta dados\nUso: /export [session|memory|config|all] [arquivo] [--format=json|yaml] [--zip]',
            'exit': 'Sai do REPL\nUso: /exit [--no-save] [--force]',
            'context': 'Informações sobre contexto\nUso: /context [show|size|usage|optimize] [--detailed] [--tokens]',
            'history': 'Mostra histórico de comandos\nUso: /history [--limit=N] [--search=termo] [--session]',
            'stats': 'Estatísticas de uso\nUso: /stats [session|today|week|month|all] [--detailed]',
            'workspace': 'Gerencia workspaces\nUso: /workspace [info|switch|create|delete|list] [nome]',
            'model': 'Gerencia modelos de IA\nUso: /model [info|switch|list|config] [nome]',
            'thinking': 'Controla modo thinking\nUso: /thinking [on|off|toggle|budget|show] [valor] [--show]'
        }
        
        return help_texts.get(command.lower())