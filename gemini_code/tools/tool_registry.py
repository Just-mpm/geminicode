"""
Tool Registry - Registro e gestão centralizada de todas as ferramentas
"""

import asyncio
from typing import Dict, Any, List, Optional, Type, Callable, Union
from datetime import datetime
import json
from pathlib import Path

from .base_tool import BaseTool, ToolInput, ToolResult, ToolCategory, ToolPermission
from .bash_tool import BashTool, SafeBashTool
from .file_tools import ReadTool, WriteTool, EditTool, ListTool, CopyTool, DeleteTool
from .search_tools import GlobTool, GrepTool, FindTool


class ToolRegistry:
    """
    Registry centralizado para todas as ferramentas do sistema.
    Gerencia registro, execução e permissões de ferramentas.
    """
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or '.')
        self.tools: Dict[str, BaseTool] = {}
        self.tool_categories: Dict[str, List[str]] = {}
        self.permission_manager = None  # Será definido quando implementarmos
        
        # Estatísticas globais
        self.total_executions = 0
        self.total_execution_time = 0
        self.last_reset = datetime.now()
        
        # Configurações
        self.max_concurrent_tools = 5
        self.default_timeout = 30
        
        # Inicializa ferramentas padrão
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Registra todas as ferramentas padrão do sistema."""
        
        # System Tools
        self.register_tool(BashTool())
        self.register_tool('safe_bash', SafeBashTool())
        
        # File Tools
        self.register_tool(ReadTool())
        self.register_tool(WriteTool())
        self.register_tool(EditTool())
        self.register_tool(ListTool())
        self.register_tool(CopyTool())
        self.register_tool(DeleteTool())
        
        # Search Tools
        self.register_tool(GlobTool())
        self.register_tool(GrepTool())
        self.register_tool(FindTool())
    
    def register_tool(self, tool_or_name: Union[BaseTool, str], tool: Optional[BaseTool] = None):
        """
        Registra uma ferramenta no registry.
        """
        if isinstance(tool_or_name, str):
            # Registro com nome customizado
            name = tool_or_name
            if tool is None:
                raise ValueError("Tool instance required when providing custom name")
            tool_instance = tool
        else:
            # Registro com nome da ferramenta
            tool_instance = tool_or_name
            name = tool_instance.name
        
        # Registra ferramenta
        self.tools[name] = tool_instance
        
        # Organiza por categoria
        category = tool_instance.metadata.get('category', ToolCategory.UTILITY)
        if category not in self.tool_categories:
            self.tool_categories[category] = []
        
        if name not in self.tool_categories[category]:
            self.tool_categories[category].append(name)
        
        print(f"🔧 Ferramenta '{name}' registrada (categoria: {category})")
    
    def unregister_tool(self, name: str) -> bool:
        """Remove ferramenta do registry."""
        if name not in self.tools:
            return False
        
        tool = self.tools[name]
        category = tool.metadata.get('category', ToolCategory.UTILITY)
        
        # Remove da categoria
        if category in self.tool_categories:
            self.tool_categories[category].remove(name)
            if not self.tool_categories[category]:
                del self.tool_categories[category]
        
        # Remove ferramenta
        del self.tools[name]
        return True
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Obtém ferramenta por nome."""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """Lista ferramentas disponíveis."""
        if category:
            return self.tool_categories.get(category, [])
        return list(self.tools.keys())
    
    def list_categories(self) -> List[str]:
        """Lista categorias disponíveis."""
        return list(self.tool_categories.keys())
    
    async def execute_tool(self, tool_name: str, tool_input: ToolInput) -> ToolResult:
        """
        Executa ferramenta com validação e logging.
        """
        start_time = datetime.now()
        
        # Verifica se ferramenta existe
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                error=f"Ferramenta '{tool_name}' não encontrada",
                tool_name=tool_name
            )
        
        tool = self.tools[tool_name]
        
        try:
            # Verificação de permissões (placeholder)
            if not await self._check_permissions(tool, tool_input):
                return ToolResult(
                    success=False,
                    error=f"Permissão negada para executar '{tool_name}'",
                    tool_name=tool_name
                )
            
            # Executa ferramenta
            result = await tool.run_with_validation(tool_input)
            
            # Atualiza estatísticas globais
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.total_executions += 1
            self.total_execution_time += execution_time
            
            # Log da execução
            await self._log_execution(tool_name, tool_input, result, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            error_result = ToolResult(
                success=False,
                error=f"Erro executando '{tool_name}': {str(e)}",
                tool_name=tool_name,
                execution_time_ms=execution_time
            )
            
            await self._log_execution(tool_name, tool_input, error_result, execution_time)
            return error_result
    
    async def execute_command_natural(self, command: str, context: Dict[str, Any] = None) -> ToolResult:
        """
        Executa comando em linguagem natural, detectando a ferramenta apropriada.
        """
        # Detecta qual ferramenta usar baseado no comando
        tool_name, tool_input = await self._parse_natural_command(command, context or {})
        
        if not tool_name:
            return ToolResult(
                success=False,
                error=f"Não foi possível determinar ferramenta para: '{command}'"
            )
        
        return await self.execute_tool(tool_name, tool_input)
    
    async def _parse_natural_command(self, command: str, context: Dict[str, Any]) -> tuple[Optional[str], Optional[ToolInput]]:
        """
        Parse comando natural para determinar ferramenta e parâmetros.
        """
        command_lower = command.lower().strip()
        
        # Padrões para diferentes ferramentas
        patterns = {
            # File operations
            'read': [
                r'(?:leia?|mostr[ae]|exib[ae]|visualiz[ae])\s+(?:o\s+)?(?:arquivo\s+)?(.+)',
                r'(?:cat|head|tail)\s+(.+)',
                r'abr[iae]\s+(?:o\s+)?(?:arquivo\s+)?(.+)'
            ],
            'write': [
                r'(?:escrev[ae]|cri[ae]|salv[ae])\s+(?:o\s+)?(?:arquivo\s+)?(.+)',
                r'(?:grav[ae])\s+(.+)',
                r'(?:faz[ae]r?)\s+(?:um\s+)?(?:arquivo\s+)?(.+)'
            ],
            'list': [
                r'(?:list[ae]|mostr[ae])\s+(?:os\s+)?(?:arquivos|diretórios?)\s*(?:em\s+)?(.*)$',
                r'ls\s*(.*)',
                r'dir\s*(.*)'
            ],
            'glob': [
                r'(?:busc[ae]|encontr[ae])\s+(?:arquivos?\s+)?(?:com\s+)?(?:padrão\s+)?(.+)',
                r'find\s+(.+)\s+name',
                r'localiz[ae]\s+(.+)'
            ],
            'grep': [
                r'(?:busc[ae]|encontr[ae])\s+(?:texto\s+)?["\'](.+?)["\'](?:\s+em\s+(.+))?',
                r'grep\s+(.+)',
                r'procur[ae]\s+(?:por\s+)?(.+)(?:\s+em\s+(.+))?'
            ],
            'bash': [
                r'(?:execut[ae]|rod[ae]|run)\s+(?:o\s+comando\s+)?(.+)',
                r'(?:command[oe]|cmd)\s+(.+)',
                r'bash\s+(.+)'
            ]
        }
        
        # Tenta fazer match com cada padrão
        for tool_name, tool_patterns in patterns.items():
            for pattern in tool_patterns:
                import re
                match = re.search(pattern, command_lower)
                if match:
                    groups = match.groups()
                    
                    # Cria ToolInput baseado na ferramenta
                    if tool_name == 'read':
                        file_path = groups[0].strip().strip('"\'')
                        return tool_name, ToolInput(command=file_path, context=context)
                    
                    elif tool_name == 'write':
                        # Precisa de conteúdo - placeholder por enquanto
                        file_path = groups[0].strip().strip('"\'')
                        content = context.get('content', '')
                        return tool_name, ToolInput(
                            command=file_path,
                            kwargs={'content': content},
                            context=context
                        )
                    
                    elif tool_name == 'list':
                        directory = groups[0].strip() if groups[0] else '.'
                        return tool_name, ToolInput(command=directory, context=context)
                    
                    elif tool_name == 'glob':
                        pattern = groups[0].strip().strip('"\'')
                        return tool_name, ToolInput(command=pattern, context=context)
                    
                    elif tool_name == 'grep':
                        search_term = groups[0].strip().strip('"\'')
                        target = groups[1].strip() if len(groups) > 1 and groups[1] else '.'
                        return tool_name, ToolInput(
                            command=search_term,
                            kwargs={'target': target},
                            context=context
                        )
                    
                    elif tool_name == 'bash':
                        bash_command = groups[0].strip()
                        return tool_name, ToolInput(command=bash_command, context=context)
        
        return None, None
    
    async def _check_permissions(self, tool: BaseTool, tool_input: ToolInput) -> bool:
        """
        Verifica permissões para executar ferramenta.
        Placeholder - será implementado no sistema de permissões.
        """
        # Por enquanto, permite tudo exceto operações destrutivas sem confirmação
        if tool.is_destructive and not tool_input.kwargs.get('confirmed', False):
            return False
        
        return True
    
    async def _log_execution(self, tool_name: str, tool_input: ToolInput, 
                           result: ToolResult, execution_time_ms: float):
        """
        Registra execução de ferramenta para auditoria.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'command': tool_input.command,
            'success': result.success,
            'execution_time_ms': execution_time_ms,
            'session_id': tool_input.session_id,
            'user_id': tool_input.user_id
        }
        
        # Salva log (implementação simplificada)
        log_dir = self.project_path / '.gemini_code' / 'tool_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"tools_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Append ao arquivo de log
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            # Silently fail logging
            pass
    
    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtém estatísticas de uso das ferramentas."""
        if tool_name:
            if tool_name not in self.tools:
                return {}
            return self.tools[tool_name].get_stats()
        
        # Estatísticas globais
        stats = {
            'registry_stats': {
                'total_tools': len(self.tools),
                'categories': len(self.tool_categories),
                'total_executions': self.total_executions,
                'total_execution_time_ms': self.total_execution_time,
                'average_execution_time_ms': (
                    self.total_execution_time / self.total_executions 
                    if self.total_executions > 0 else 0
                ),
                'last_reset': self.last_reset.isoformat()
            },
            'tools': {}
        }
        
        # Estatísticas por ferramenta
        for name, tool in self.tools.items():
            stats['tools'][name] = tool.get_stats()
        
        return stats
    
    def get_tool_help(self, tool_name: str) -> Optional[str]:
        """Obtém ajuda de uma ferramenta específica."""
        if tool_name not in self.tools:
            return None
        
        return self.tools[tool_name].get_help()
    
    def list_tools_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Lista ferramentas organizadas por categoria."""
        result = {}
        
        for category, tool_names in self.tool_categories.items():
            result[category] = []
            for tool_name in tool_names:
                tool = self.tools[tool_name]
                result[category].append({
                    'name': tool_name,
                    'description': tool.description,
                    'requires_confirmation': tool.requires_confirmation,
                    'is_destructive': tool.is_destructive,
                    'execution_count': tool.execution_count
                })
        
        return result
    
    def reset_stats(self):
        """Reseta todas as estatísticas."""
        self.total_executions = 0
        self.total_execution_time = 0
        self.last_reset = datetime.now()
        
        for tool in self.tools.values():
            tool.reset_stats()
    
    def export_config(self) -> Dict[str, Any]:
        """Exporta configuração do registry."""
        return {
            'tools': {
                name: {
                    'name': tool.name,
                    'description': tool.description,
                    'metadata': tool.metadata,
                    'requires_confirmation': tool.requires_confirmation,
                    'timeout_seconds': tool.timeout_seconds
                }
                for name, tool in self.tools.items()
            },
            'categories': self.tool_categories,
            'settings': {
                'max_concurrent_tools': self.max_concurrent_tools,
                'default_timeout': self.default_timeout
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todas as ferramentas."""
        health_status = {
            'overall_status': 'healthy',
            'total_tools': len(self.tools),
            'tools_status': {},
            'issues': []
        }
        
        for name, tool in self.tools.items():
            try:
                # Teste básico de validação
                test_input = ToolInput(command="")
                is_valid = tool.validate_input(test_input)
                
                tool_health = {
                    'status': 'healthy',
                    'validation_working': True,
                    'execution_count': tool.execution_count,
                    'last_error': None
                }
                
                health_status['tools_status'][name] = tool_health
                
            except Exception as e:
                tool_health = {
                    'status': 'error',
                    'validation_working': False,
                    'error': str(e)
                }
                
                health_status['tools_status'][name] = tool_health
                health_status['issues'].append(f"Tool '{name}': {str(e)}")
        
        # Determina status geral
        if health_status['issues']:
            health_status['overall_status'] = 'degraded' if len(health_status['issues']) < len(self.tools) / 2 else 'critical'
        
        return health_status


# Instância global do registry
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry(project_path: str = None) -> ToolRegistry:
    """Obtém instância global do tool registry."""
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ToolRegistry(project_path)
    
    return _global_registry


def reset_tool_registry():
    """Reseta instância global do registry."""
    global _global_registry
    _global_registry = None