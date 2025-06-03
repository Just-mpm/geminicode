"""
Gerenciador de equipes e colaboradores.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.gemini_client import GeminiClient


class Role(Enum):
    """Roles/funções na equipe."""
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """Permissões do sistema."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    REVIEW = "review"
    ADMIN = "admin"
    DEPLOY = "deploy"
    DELETE = "delete"


@dataclass
class TeamMember:
    """Representa um membro da equipe."""
    id: str
    name: str
    email: str
    role: Role
    permissions: Set[Permission]
    joined_at: datetime
    last_active: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = None
    timezone: str = "UTC"
    status: str = "active"  # active, inactive, suspended
    projects: Set[str] = None
    contributions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.projects is None:
            self.projects = set()
        if self.contributions is None:
            self.contributions = {
                'commits': 0,
                'reviews': 0,
                'issues_created': 0,
                'issues_resolved': 0
            }
        if isinstance(self.role, str):
            self.role = Role(self.role)
        if isinstance(self.permissions, list):
            self.permissions = {Permission(p) for p in self.permissions}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['role'] = self.role.value
        data['permissions'] = [p.value for p in self.permissions]
        data['joined_at'] = self.joined_at.isoformat()
        data['last_active'] = self.last_active.isoformat() if self.last_active else None
        data['projects'] = list(self.projects)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Cria membro a partir de dicionário."""
        data = data.copy()
        data['joined_at'] = datetime.fromisoformat(data['joined_at'])
        if data.get('last_active'):
            data['last_active'] = datetime.fromisoformat(data['last_active'])
        data['role'] = Role(data['role'])
        data['permissions'] = {Permission(p) for p in data['permissions']}
        data['projects'] = set(data.get('projects', []))
        return cls(**data)
    
    def has_permission(self, permission: Permission) -> bool:
        """Verifica se tem permissão."""
        return permission in self.permissions
    
    def update_activity(self) -> None:
        """Atualiza última atividade."""
        self.last_active = datetime.now()
    
    def add_contribution(self, contrib_type: str, amount: int = 1) -> None:
        """Adiciona contribuição."""
        if contrib_type in self.contributions:
            self.contributions[contrib_type] += amount
        else:
            self.contributions[contrib_type] = amount


class TeamManager:
    """Gerenciador de equipes."""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.members: Dict[str, TeamMember] = {}
        self.invitations: Dict[str, Dict[str, Any]] = {}
        self.role_permissions = self._init_role_permissions()
        self.data_file = Path('.gemini_code/team.json')
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Inicializa armazenamento da equipe."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_team()
    
    def _init_role_permissions(self) -> Dict[Role, Set[Permission]]:
        """Inicializa permissões por role."""
        return {
            Role.OWNER: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.REVIEW, Permission.ADMIN, Permission.DEPLOY, Permission.DELETE
            },
            Role.ADMIN: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.REVIEW, Permission.DEPLOY
            },
            Role.DEVELOPER: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE
            },
            Role.REVIEWER: {
                Permission.READ, Permission.REVIEW
            },
            Role.VIEWER: {
                Permission.READ
            },
            Role.GUEST: {
                Permission.READ
            }
        }
    
    def save_team(self) -> None:
        """Salva dados da equipe."""
        data = {
            'members': {member_id: member.to_dict() for member_id, member in self.members.items()},
            'invitations': self.invitations,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_team(self) -> None:
        """Carrega dados da equipe."""
        if not self.data_file.exists():
            self._create_default_owner()
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Carrega membros
            self.members = {}
            for member_id, member_data in data.get('members', {}).items():
                self.members[member_id] = TeamMember.from_dict(member_data)
            
            # Carrega convites
            self.invitations = data.get('invitations', {})
            
        except Exception as e:
            print(f"Erro ao carregar equipe: {e}")
            self._create_default_owner()
    
    def _create_default_owner(self) -> None:
        """Cria proprietário padrão."""
        owner = TeamMember(
            id="owner_001",
            name="Proprietário",
            email="owner@geminicode.local",
            role=Role.OWNER,
            permissions=self.role_permissions[Role.OWNER],
            joined_at=datetime.now()
        )
        
        self.members[owner.id] = owner
        self.save_team()
    
    async def invite_member(self, email: str, role: Role, 
                           invited_by: str, message: str = "") -> str:
        """Convida novo membro para a equipe."""
        # Verifica permissões do convidador
        inviter = self.members.get(invited_by)
        if not inviter or not inviter.has_permission(Permission.ADMIN):
            raise PermissionError("Sem permissão para convidar membros")
        
        # Verifica se já é membro
        for member in self.members.values():
            if member.email == email:
                raise ValueError("Usuário já é membro da equipe")
        
        # Cria convite
        invitation_id = str(uuid.uuid4())
        invitation = {
            'id': invitation_id,
            'email': email,
            'role': role.value,
            'invited_by': invited_by,
            'invited_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'message': message,
            'status': 'pending'
        }
        
        self.invitations[invitation_id] = invitation
        self.save_team()
        
        # Gera mensagem de convite
        invite_message = await self._generate_invitation_message(
            inviter.name, email, role, message
        )
        
        # Simula envio de email (em implementação real, enviaria email)
        print(f"Convite enviado para {email}:")
        print(invite_message)
        
        return invitation_id
    
    async def _generate_invitation_message(self, inviter_name: str, 
                                         email: str, role: Role, 
                                         message: str) -> str:
        """Gera mensagem de convite personalizada."""
        prompt = f"""
        Crie uma mensagem de convite para equipe de desenvolvimento:
        
        Convidado por: {inviter_name}
        Email do convidado: {email}
        Função: {role.value}
        Mensagem adicional: {message}
        
        A mensagem deve ser:
        - Profissional e acolhedora
        - Explicar o que é o Gemini Code
        - Mencionar as responsabilidades da função
        - Incluir instruções para aceitar o convite
        
        Escreva em português.
        """
        
        try:
            return await self.gemini_client.generate_response(prompt)
        except:
            return f"""
Olá!

Você foi convidado(a) por {inviter_name} para participar da equipe de desenvolvimento no Gemini Code.

Função: {role.value.title()}

O Gemini Code é um assistente de desenvolvimento avançado que utiliza IA para ajudar equipes a criar e manter projetos de software de forma mais eficiente.

{message}

Para aceitar o convite, responda a este email ou entre em contato com {inviter_name}.

Bem-vindo(a) à equipe!
            """
    
    def accept_invitation(self, invitation_id: str, 
                         member_data: Dict[str, Any]) -> str:
        """Aceita convite e adiciona membro à equipe."""
        if invitation_id not in self.invitations:
            raise ValueError("Convite não encontrado")
        
        invitation = self.invitations[invitation_id]
        
        # Verifica se convite ainda é válido
        expires_at = datetime.fromisoformat(invitation['expires_at'])
        if datetime.now() > expires_at:
            raise ValueError("Convite expirado")
        
        if invitation['status'] != 'pending':
            raise ValueError("Convite já foi processado")
        
        # Cria membro
        member_id = str(uuid.uuid4())
        role = Role(invitation['role'])
        
        member = TeamMember(
            id=member_id,
            name=member_data['name'],
            email=invitation['email'],
            role=role,
            permissions=self.role_permissions[role],
            joined_at=datetime.now(),
            avatar_url=member_data.get('avatar_url'),
            bio=member_data.get('bio', ''),
            skills=member_data.get('skills', []),
            timezone=member_data.get('timezone', 'UTC')
        )
        
        # Adiciona à equipe
        self.members[member_id] = member
        
        # Marca convite como aceito
        invitation['status'] = 'accepted'
        invitation['accepted_at'] = datetime.now().isoformat()
        invitation['member_id'] = member_id
        
        self.save_team()
        
        return member_id
    
    def reject_invitation(self, invitation_id: str, reason: str = "") -> None:
        """Rejeita convite."""
        if invitation_id not in self.invitations:
            raise ValueError("Convite não encontrado")
        
        invitation = self.invitations[invitation_id]
        invitation['status'] = 'rejected'
        invitation['rejected_at'] = datetime.now().isoformat()
        invitation['rejection_reason'] = reason
        
        self.save_team()
    
    def get_member(self, member_id: str) -> Optional[TeamMember]:
        """Obtém membro por ID."""
        return self.members.get(member_id)
    
    def get_member_by_email(self, email: str) -> Optional[TeamMember]:
        """Obtém membro por email."""
        for member in self.members.values():
            if member.email == email:
                return member
        return None
    
    def get_members_by_role(self, role: Role) -> List[TeamMember]:
        """Obtém membros por função."""
        return [member for member in self.members.values() if member.role == role]
    
    def get_active_members(self, hours: int = 24) -> List[TeamMember]:
        """Obtém membros ativos nas últimas N horas."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            member for member in self.members.values()
            if member.last_active and member.last_active > cutoff
        ]
    
    def update_member_role(self, member_id: str, new_role: Role, 
                          updated_by: str) -> bool:
        """Atualiza função de membro."""
        # Verifica permissões
        updater = self.members.get(updated_by)
        if not updater or not updater.has_permission(Permission.ADMIN):
            raise PermissionError("Sem permissão para alterar funções")
        
        member = self.members.get(member_id)
        if not member:
            return False
        
        # Não pode alterar próprio role de OWNER
        if member.role == Role.OWNER and member_id == updated_by:
            raise PermissionError("Proprietário não pode alterar próprio role")
        
        # Atualiza role e permissões
        member.role = new_role
        member.permissions = self.role_permissions[new_role]
        
        self.save_team()
        return True
    
    def remove_member(self, member_id: str, removed_by: str, 
                     reason: str = "") -> bool:
        """Remove membro da equipe."""
        # Verifica permissões
        remover = self.members.get(removed_by)
        if not remover or not remover.has_permission(Permission.ADMIN):
            raise PermissionError("Sem permissão para remover membros")
        
        member = self.members.get(member_id)
        if not member:
            return False
        
        # Não pode remover OWNER
        if member.role == Role.OWNER:
            raise PermissionError("Não é possível remover o proprietário")
        
        # Não pode se remover
        if member_id == removed_by:
            raise PermissionError("Não é possível se remover")
        
        # Remove membro
        del self.members[member_id]
        
        # Log da remoção
        self._log_member_action('removed', {
            'member_id': member_id,
            'member_name': member.name,
            'removed_by': removed_by,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_team()
        return True
    
    def update_member_permissions(self, member_id: str, 
                                permissions: Set[Permission],
                                updated_by: str) -> bool:
        """Atualiza permissões customizadas de membro."""
        # Verifica permissões
        updater = self.members.get(updated_by)
        if not updater or not updater.has_permission(Permission.ADMIN):
            raise PermissionError("Sem permissão para alterar permissões")
        
        member = self.members.get(member_id)
        if not member:
            return False
        
        # Não pode alterar permissões do OWNER
        if member.role == Role.OWNER:
            raise PermissionError("Não é possível alterar permissões do proprietário")
        
        member.permissions = permissions
        self.save_team()
        return True
    
    def get_team_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da equipe."""
        total_members = len(self.members)
        active_members = len(self.get_active_members())
        
        # Distribuição por função
        role_distribution = {}
        for role in Role:
            count = len(self.get_members_by_role(role))
            if count > 0:
                role_distribution[role.value] = count
        
        # Contribuições totais
        total_contributions = {
            'commits': 0,
            'reviews': 0,
            'issues_created': 0,
            'issues_resolved': 0
        }
        
        for member in self.members.values():
            for key, value in member.contributions.items():
                if key in total_contributions:
                    total_contributions[key] += value
        
        # Convites pendentes
        pending_invitations = len([
            inv for inv in self.invitations.values()
            if inv['status'] == 'pending'
        ])
        
        return {
            'total_members': total_members,
            'active_members': active_members,
            'role_distribution': role_distribution,
            'total_contributions': total_contributions,
            'pending_invitations': pending_invitations,
            'team_created': min(member.joined_at for member in self.members.values()).isoformat(),
            'last_activity': max(
                member.last_active for member in self.members.values()
                if member.last_active
            ).isoformat() if any(member.last_active for member in self.members.values()) else None
        }
    
    async def generate_team_report(self) -> Dict[str, Any]:
        """Gera relatório detalhado da equipe."""
        stats = self.get_team_stats()
        active_members = self.get_active_members()
        
        # Top contribuidores
        top_contributors = sorted(
            self.members.values(),
            key=lambda m: sum(m.contributions.values()),
            reverse=True
        )[:5]
        
        # Gera insights com IA
        insights = await self._generate_team_insights(stats, active_members)
        
        return {
            'stats': stats,
            'top_contributors': [{
                'name': member.name,
                'role': member.role.value,
                'total_contributions': sum(member.contributions.values()),
                'contributions': member.contributions
            } for member in top_contributors],
            'active_members': [{
                'name': member.name,
                'role': member.role.value,
                'last_active': member.last_active.isoformat() if member.last_active else None
            } for member in active_members],
            'insights': insights,
            'recommendations': await self._generate_team_recommendations(stats),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_team_insights(self, stats: Dict[str, Any], 
                                    active_members: List[TeamMember]) -> List[str]:
        """Gera insights sobre a equipe usando IA."""
        prompt = f"""
        Analise estas estatísticas de equipe e gere insights:
        
        Estatísticas:
        - Total de membros: {stats['total_members']}
        - Membros ativos (24h): {stats['active_members']}
        - Distribuição por função: {stats['role_distribution']}
        - Contribuições totais: {stats['total_contributions']}
        - Convites pendentes: {stats['pending_invitations']}
        
        Gere 3-5 insights sobre:
        1. Saúde da equipe
        2. Produtividade
        3. Engajamento
        4. Áreas de melhoria
        
        Responda em português com insights práticos.
        """
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            insights = [line.strip() for line in response.split('\n') 
                       if line.strip() and not line.startswith('#')]
            return insights[:5]
        except:
            return [
                f"Equipe de {stats['total_members']} membros com {stats['active_members']} ativos",
                f"Total de {sum(stats['total_contributions'].values())} contribuições registradas",
                "Monitor regularmente atividade da equipe para manter engajamento"
            ]
    
    async def _generate_team_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações para a equipe."""
        recommendations = []
        
        # Análise de atividade
        if stats['active_members'] < stats['total_members'] * 0.7:
            recommendations.append("🟡 Baixa atividade da equipe - considere reuniões regulares")
        
        # Análise de convites
        if stats['pending_invitations'] > 0:
            recommendations.append(f"📬 {stats['pending_invitations']} convites pendentes - acompanhe respostas")
        
        # Análise de distribuição
        if 'developer' not in stats['role_distribution']:
            recommendations.append("👥 Considere adicionar desenvolvedores à equipe")
        
        if 'reviewer' not in stats['role_distribution'] and stats['total_members'] > 2:
            recommendations.append("🔍 Adicione revisores para melhorar qualidade do código")
        
        # Contribuições
        total_contribs = sum(stats['total_contributions'].values())
        if total_contribs < stats['total_members'] * 10:
            recommendations.append("📈 Incentive mais contribuições da equipe")
        
        if not recommendations:
            recommendations.append("✅ Equipe está funcionando bem - continue monitorando")
        
        return recommendations
    
    def _log_member_action(self, action: str, data: Dict[str, Any]) -> None:
        """Registra ação relacionada a membro."""
        log_file = Path('.gemini_code/team_actions.log')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'data': data
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def get_member_activity_summary(self, member_id: str, 
                                  days: int = 30) -> Dict[str, Any]:
        """Obtém resumo de atividade de membro."""
        member = self.members.get(member_id)
        if not member:
            return {}
        
        return {
            'member_id': member_id,
            'name': member.name,
            'role': member.role.value,
            'days_analyzed': days,
            'contributions': member.contributions,
            'total_contributions': sum(member.contributions.values()),
            'last_active': member.last_active.isoformat() if member.last_active else None,
            'days_since_last_activity': (
                datetime.now() - member.last_active
            ).days if member.last_active else None,
            'projects': list(member.projects),
            'skills': member.skills
        }