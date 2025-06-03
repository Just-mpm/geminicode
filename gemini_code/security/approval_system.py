"""
Approval System - Sistema de aprovação interativa estilo Claude Code
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.table import Table

from .permission_manager import PermissionRequest, PermissionDecision, PermissionLevel, OperationType


class ApprovalResponse(Enum):
    """Respostas possíveis para solicitação de aprovação."""
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_ONCE = "allow_once"
    ALLOW_SESSION = "allow_session"
    ALLOW_FOREVER = "allow_forever"
    DENY_FOREVER = "deny_forever"


class InteractiveApprovalSystem:
    """
    Sistema de aprovação interativa que replica o comportamento do Claude Code.
    """
    
    def __init__(self):
        self.console = Console()
        self.approval_history: List[Dict[str, Any]] = []
        
        # Templates de mensagens por tipo de operação
        self.approval_messages = {
            OperationType.EXECUTE_COMMAND: "executar comando shell",
            OperationType.WRITE_FILE: "escrever arquivo",
            OperationType.DELETE_FILE: "deletar arquivo",
            OperationType.NETWORK_ACCESS: "acessar rede",
            OperationType.SYSTEM_MODIFY: "modificar sistema",
            OperationType.PROCESS_SPAWN: "criar novo processo"
        }
        
        # Ícones de risco
        self.risk_icons = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴"
        }
    
    async def request_approval(self, request: PermissionRequest, level: PermissionLevel) -> PermissionDecision:
        """
        Solicita aprovação interativa do usuário.
        """
        
        # Mostra informações da solicitação
        self._show_permission_request(request)
        
        # Determina opções disponíveis baseado no nível
        options = self._get_approval_options(level, request)
        
        # Solicita decisão do usuário
        response = await self._get_user_response(options, request)
        
        # Converte resposta em decisão
        decision = self._convert_response_to_decision(response, request)
        
        # Registra no histórico
        self._log_approval(request, decision, response)
        
        return decision
    
    def _show_permission_request(self, request: PermissionRequest):
        """Exibe solicitação de permissão de forma clara."""
        
        # Cabeçalho
        risk_icon = self.risk_icons.get(request.risk_level, "⚪")
        operation_desc = self.approval_messages.get(request.operation_type, "executar operação")
        
        title = f"{risk_icon} Solicitação de Permissão - {request.tool_name}"
        
        # Conteúdo da solicitação
        content_lines = [
            f"**Operação:** {operation_desc}",
            f"**Recurso:** `{request.resource}`",
            f"**Descrição:** {request.description}",
            f"**Nível de Risco:** {request.risk_level.upper()} {risk_icon}",
        ]
        
        # Adiciona contexto se disponível
        if request.user_context:
            if 'file_size' in request.user_context:
                content_lines.append(f"**Tamanho:** {request.user_context['file_size']} bytes")
            if 'command_args' in request.user_context:
                content_lines.append(f"**Argumentos:** {request.user_context['command_args']}")
        
        content = "\\n".join(content_lines)
        
        # Avisos especiais baseados no risco
        if request.risk_level == "critical":
            content += "\\n\\n⚠️  **ATENÇÃO: Operação de alto risco detectada!**"
        elif request.risk_level == "high":
            content += "\\n\\n⚠️  **Cuidado: Esta operação pode ser perigosa**"
        
        # Mostra painel
        panel = Panel(
            content,
            title=title,
            border_style="yellow" if request.risk_level in ["high", "critical"] else "blue",
            padding=(1, 2)
        )
        
        self.console.print("\\n")
        self.console.print(panel)
    
    def _get_approval_options(self, level: PermissionLevel, request: PermissionRequest) -> List[ApprovalResponse]:
        """Determina opções de aprovação baseado no nível de permissão."""
        
        base_options = [ApprovalResponse.ALLOW, ApprovalResponse.DENY]
        
        if level == PermissionLevel.ASK_ONCE:
            return base_options + [ApprovalResponse.ALLOW_FOREVER, ApprovalResponse.DENY_FOREVER]
        
        elif level == PermissionLevel.ASK_UNTIL_SESSION_END:
            return base_options + [ApprovalResponse.ALLOW_SESSION]
        
        elif level == PermissionLevel.ASK_ALWAYS:
            if request.risk_level in ["low", "medium"]:
                return base_options + [ApprovalResponse.ALLOW_SESSION, ApprovalResponse.ALLOW_FOREVER]
            else:
                return base_options + [ApprovalResponse.ALLOW_ONCE]
        
        return base_options
    
    async def _get_user_response(self, options: List[ApprovalResponse], request: PermissionRequest) -> ApprovalResponse:
        """Solicita resposta do usuário."""
        
        # Cria tabela de opções
        table = Table(title="Opções Disponíveis", show_header=True, header_style="bold blue")
        table.add_column("Opção", style="cyan", width=12)
        table.add_column("Descrição", style="white")
        table.add_column("Duração", style="green")
        
        option_map = {
            ApprovalResponse.ALLOW: ("✅ Permitir", "Permite esta operação", "Uma vez"),
            ApprovalResponse.DENY: ("❌ Negar", "Nega esta operação", "Uma vez"),
            ApprovalResponse.ALLOW_ONCE: ("🟢 Permitir", "Permite apenas desta vez", "Uma vez"),
            ApprovalResponse.ALLOW_SESSION: ("🔵 Permitir", "Permite até fim da sessão", "Sessão atual"),
            ApprovalResponse.ALLOW_FOREVER: ("✅ Sempre", "Sempre permite para este recurso", "Permanente"),
            ApprovalResponse.DENY_FOREVER: ("❌ Nunca", "Nunca permite para este recurso", "Permanente")
        }
        
        # Mapeia opções para números
        option_numbers = {}
        for i, option in enumerate(options, 1):
            desc, explanation, duration = option_map[option]
            table.add_row(f"[{i}]", desc, explanation, duration)
            option_numbers[str(i)] = option
        
        self.console.print(table)
        self.console.print()
        
        # Solicita escolha
        while True:
            try:
                choice = Prompt.ask(
                    "Escolha uma opção",
                    choices=list(option_numbers.keys()),
                    default="1"
                )
                
                return option_numbers[choice]
                
            except KeyboardInterrupt:
                return ApprovalResponse.DENY
            except Exception:
                self.console.print("[red]Opção inválida. Tente novamente.[/red]")
                continue
    
    def _convert_response_to_decision(self, response: ApprovalResponse, request: PermissionRequest) -> PermissionDecision:
        """Converte resposta do usuário em decisão de permissão."""
        
        if response == ApprovalResponse.ALLOW:
            return PermissionDecision(
                granted=True,
                reason="user_approved"
            )
        
        elif response == ApprovalResponse.DENY:
            return PermissionDecision(
                granted=False,
                reason="user_denied"
            )
        
        elif response == ApprovalResponse.ALLOW_ONCE:
            return PermissionDecision(
                granted=True,
                reason="user_approved_once",
                expires_at=datetime.now() + timedelta(minutes=5)
            )
        
        elif response == ApprovalResponse.ALLOW_SESSION:
            return PermissionDecision(
                granted=True,
                reason="user_approved_session",
                expires_at=datetime.now() + timedelta(hours=24)  # Duração da sessão
            )
        
        elif response == ApprovalResponse.ALLOW_FOREVER:
            return PermissionDecision(
                granted=True,
                remember_choice=True,
                reason="user_approved_forever"
            )
        
        elif response == ApprovalResponse.DENY_FOREVER:
            return PermissionDecision(
                granted=False,
                remember_choice=True,
                reason="user_denied_forever"
            )
        
        else:
            # Fallback - nega por segurança
            return PermissionDecision(
                granted=False,
                reason="unknown_response"
            )
    
    def _log_approval(self, request: PermissionRequest, decision: PermissionDecision, response: ApprovalResponse):
        """Registra aprovação no histórico."""
        log_entry = {
            'timestamp': datetime.now(),
            'operation_type': request.operation_type.value,
            'resource': request.resource,
            'tool_name': request.tool_name,
            'risk_level': request.risk_level,
            'user_response': response.value,
            'granted': decision.granted,
            'remember_choice': decision.remember_choice,
            'session_id': request.session_id
        }
        
        self.approval_history.append(log_entry)
        
        # Mantém histórico limitado
        if len(self.approval_history) > 100:
            self.approval_history = self.approval_history[-100:]
    
    def show_approval_summary(self, request: PermissionRequest, decision: PermissionDecision):
        """Mostra resumo da decisão tomada."""
        
        if decision.granted:
            icon = "✅"
            status = "[green]PERMITIDO[/green]"
            color = "green"
        else:
            icon = "❌"
            status = "[red]NEGADO[/red]"
            color = "red"
        
        summary_text = f"{icon} {status}"
        
        if decision.remember_choice:
            summary_text += " [dim](salvo permanentemente)[/dim]"
        elif decision.expires_at:
            if decision.expires_at > datetime.now() + timedelta(hours=1):
                summary_text += " [dim](válido até fim da sessão)[/dim]"
            else:
                summary_text += " [dim](válido por alguns minutos)[/dim]"
        
        panel = Panel(
            summary_text,
            title=f"Decisão - {request.tool_name}",
            border_style=color,
            padding=(0, 1)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de aprovações."""
        if not self.approval_history:
            return {
                'total_requests': 0,
                'approvals': 0,
                'denials': 0,
                'approval_rate': 0.0
            }
        
        total = len(self.approval_history)
        approved = sum(1 for entry in self.approval_history if entry['granted'])
        denied = total - approved
        
        # Estatísticas por ferramenta
        tool_stats = {}
        for entry in self.approval_history:
            tool = entry['tool_name']
            if tool not in tool_stats:
                tool_stats[tool] = {'requests': 0, 'approved': 0}
            
            tool_stats[tool]['requests'] += 1
            if entry['granted']:
                tool_stats[tool]['approved'] += 1
        
        # Estatísticas por nível de risco
        risk_stats = {}
        for entry in self.approval_history:
            risk = entry['risk_level']
            if risk not in risk_stats:
                risk_stats[risk] = {'requests': 0, 'approved': 0}
            
            risk_stats[risk]['requests'] += 1
            if entry['granted']:
                risk_stats[risk]['approved'] += 1
        
        return {
            'total_requests': total,
            'approvals': approved,
            'denials': denied,
            'approval_rate': (approved / total) * 100,
            'tool_stats': tool_stats,
            'risk_stats': risk_stats,
            'recent_requests': self.approval_history[-10:]  # Últimas 10
        }
    
    def clear_approval_history(self):
        """Limpa histórico de aprovações."""
        self.approval_history.clear()


class BatchApprovalSystem:
    """
    Sistema para aprovação em lote de múltiplas operações.
    """
    
    def __init__(self, interactive_system: InteractiveApprovalSystem):
        self.interactive = interactive_system
        self.console = Console()
    
    async def request_batch_approval(self, requests: List[PermissionRequest]) -> List[PermissionDecision]:
        """Solicita aprovação para múltiplas operações."""
        
        # Mostra resumo das operações
        self._show_batch_summary(requests)
        
        # Opções de aprovação em lote
        batch_options = [
            "approve_all", "deny_all", "approve_safe", "review_each"
        ]
        
        choice = Prompt.ask(
            "Como deseja proceder?",
            choices=batch_options,
            default="review_each"
        )
        
        if choice == "approve_all":
            return [PermissionDecision(granted=True, reason="batch_approved") for _ in requests]
        
        elif choice == "deny_all":
            return [PermissionDecision(granted=False, reason="batch_denied") for _ in requests]
        
        elif choice == "approve_safe":
            decisions = []
            for request in requests:
                if request.risk_level in ["low", "medium"]:
                    decisions.append(PermissionDecision(granted=True, reason="batch_safe_approved"))
                else:
                    decision = await self.interactive.request_approval(request, PermissionLevel.ASK_ALWAYS)
                    decisions.append(decision)
            return decisions
        
        else:  # review_each
            decisions = []
            for i, request in enumerate(requests, 1):
                self.console.print(f"\\n[bold]Operação {i} de {len(requests)}:[/bold]")
                decision = await self.interactive.request_approval(request, PermissionLevel.ASK_ALWAYS)
                decisions.append(decision)
            return decisions
    
    def _show_batch_summary(self, requests: List[PermissionRequest]):
        """Mostra resumo das operações em lote."""
        table = Table(title=f"Aprovação em Lote - {len(requests)} operações", show_header=True)
        table.add_column("Ferramenta", style="cyan")
        table.add_column("Operação", style="white")
        table.add_column("Recurso", style="yellow")
        table.add_column("Risco", style="red")
        
        for request in requests:
            risk_icon = self.interactive.risk_icons.get(request.risk_level, "⚪")
            table.add_row(
                request.tool_name,
                request.operation_type.value,
                request.resource[:50] + "..." if len(request.resource) > 50 else request.resource,
                f"{request.risk_level} {risk_icon}"
            )
        
        self.console.print("\\n")
        self.console.print(table)
        self.console.print()


# Instância global do sistema de aprovação
_global_approval_system: Optional[InteractiveApprovalSystem] = None


def get_approval_system() -> InteractiveApprovalSystem:
    """Obtém instância global do sistema de aprovação."""
    global _global_approval_system
    
    if _global_approval_system is None:
        _global_approval_system = InteractiveApprovalSystem()
    
    return _global_approval_system