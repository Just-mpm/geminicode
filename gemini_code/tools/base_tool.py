"""
Base Tool - Classe abstrata para todas as ferramentas do sistema
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid


@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0
    tool_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time_ms': self.execution_time_ms,
            'tool_name': self.tool_name,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ToolInput:
    """Input padronizado para ferramentas."""
    command: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class BaseTool(ABC):
    """
    Classe base para todas as ferramentas do Gemini Code.
    Implementa interface similar ao Claude Code.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tool_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.execution_count = 0
        self.total_execution_time = 0
        
        # Configurações da ferramenta
        self.requires_confirmation = False
        self.is_destructive = False
        self.timeout_seconds = 30
        self.max_retries = 3
        
        # Metadados
        self.metadata = {
            'version': '1.0',
            'category': 'general',
            'tags': [],
            'dependencies': []
        }
    
    @abstractmethod
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """
        Executa a ferramenta com o input fornecido.
        Deve ser implementado por cada ferramenta específica.
        """
        pass
    
    @abstractmethod
    def validate_input(self, tool_input: ToolInput) -> bool:
        """
        Valida o input antes da execução.
        Deve ser implementado por cada ferramenta específica.
        """
        pass
    
    def get_help(self) -> str:
        """Retorna texto de ajuda da ferramenta."""
        return f"""
# {self.name}

{self.description}

**Categoria:** {self.metadata.get('category', 'general')}
**Versão:** {self.metadata.get('version', '1.0')}

## Uso
{self._get_usage_examples()}

## Parâmetros
{self._get_parameters_help()}

## Exemplos
{self._get_examples()}
        """.strip()
    
    def _get_usage_examples(self) -> str:
        """Retorna exemplos de uso (deve ser sobrescrito)."""
        return f"Use a ferramenta {self.name} com os parâmetros apropriados."
    
    def _get_parameters_help(self) -> str:
        """Retorna ajuda dos parâmetros (deve ser sobrescrito)."""
        return "Parâmetros específicos dependem da ferramenta."
    
    def _get_examples(self) -> str:
        """Retorna exemplos práticos (deve ser sobrescrito)."""
        return f"Exemplo: {self.name} --help"
    
    async def run_with_validation(self, tool_input: ToolInput) -> ToolResult:
        """
        Executa ferramenta com validação completa.
        """
        start_time = datetime.now()
        
        try:
            # Validação de input
            if not self.validate_input(tool_input):
                return ToolResult(
                    success=False,
                    error="Input inválido para a ferramenta",
                    tool_name=self.name,
                    execution_time_ms=0
                )
            
            # Execução
            result = await self.execute(tool_input)
            
            # Calcula tempo de execução
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            result.tool_name = self.name
            
            # Atualiza estatísticas
            self.execution_count += 1
            self.total_execution_time += execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolResult(
                success=False,
                error=f"Erro executando {self.name}: {str(e)}",
                tool_name=self.name,
                execution_time_ms=execution_time,
                metadata={'exception_type': type(e).__name__}
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso da ferramenta."""
        avg_execution_time = 0
        if self.execution_count > 0:
            avg_execution_time = self.total_execution_time / self.execution_count
        
        return {
            'tool_name': self.name,
            'tool_id': self.tool_id,
            'execution_count': self.execution_count,
            'total_execution_time_ms': self.total_execution_time,
            'average_execution_time_ms': avg_execution_time,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    def configure(self, **kwargs):
        """Configura parâmetros da ferramenta."""
        if 'requires_confirmation' in kwargs:
            self.requires_confirmation = kwargs['requires_confirmation']
        
        if 'timeout_seconds' in kwargs:
            self.timeout_seconds = kwargs['timeout_seconds']
        
        if 'max_retries' in kwargs:
            self.max_retries = kwargs['max_retries']
        
        if 'metadata' in kwargs:
            self.metadata.update(kwargs['metadata'])
    
    def reset_stats(self):
        """Reseta estatísticas de execução."""
        self.execution_count = 0
        self.total_execution_time = 0
    
    def __str__(self) -> str:
        return f"Tool({self.name})"
    
    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', executions={self.execution_count})"


class ToolCategory:
    """Categorias padrão de ferramentas."""
    SYSTEM = "system"
    FILE = "file"
    SEARCH = "search"
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    GIT = "git"
    SECURITY = "security"
    MONITORING = "monitoring"
    AI = "ai"
    UTILITY = "utility"


class ToolPermission:
    """Níveis de permissão para ferramentas."""
    READ_ONLY = "read_only"
    WRITE = "write"
    EXECUTE = "execute"
    DESTRUCTIVE = "destructive"
    ADMIN = "admin"


def tool_decorator(
    name: str,
    description: str,
    category: str = ToolCategory.UTILITY,
    permission: str = ToolPermission.READ_ONLY,
    requires_confirmation: bool = False
):
    """
    Decorator para registrar ferramentas automaticamente.
    """
    def decorator(cls):
        # Adiciona metadados à classe
        cls._tool_name = name
        cls._tool_description = description
        cls._tool_category = category
        cls._tool_permission = permission
        cls._requires_confirmation = requires_confirmation
        
        return cls
    
    return decorator