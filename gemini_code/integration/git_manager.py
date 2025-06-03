"""
Gerenciador Git inteligente que automatiza controle de versão.
"""

import asyncio
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import re
import json

from ..core.gemini_client import GeminiClient
from ..execution.command_executor import CommandExecutor, CommandContext


@dataclass
class GitStatus:
    """Status atual do repositório Git."""
    branch: str
    is_clean: bool
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]
    ahead: int
    behind: int
    remote: Optional[str]


@dataclass
class CommitInfo:
    """Informações sobre um commit."""
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]


class GitManager:
    """Gerencia operações Git de forma inteligente."""
    
    def __init__(self, gemini_client: GeminiClient, command_executor: CommandExecutor):
        self.gemini_client = gemini_client
        self.command_executor = command_executor
        self.auto_commit_patterns = self._load_auto_commit_patterns()
    
    def _load_auto_commit_patterns(self) -> Dict[str, str]:
        """Padrões para commits automáticos."""
        return {
            'feat': 'Adiciona nova funcionalidade',
            'fix': 'Corrige erro',
            'docs': 'Atualiza documentação',
            'style': 'Melhora formatação',
            'refactor': 'Refatora código',
            'test': 'Adiciona/atualiza testes',
            'chore': 'Atualiza dependências ou configurações'
        }
    
    async def init_repository(self, project_path: str, remote_url: Optional[str] = None) -> bool:
        """Inicializa repositório Git."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        # Verifica se já é um repositório
        if await self._is_git_repository(project_path):
            return True
        
        # Inicializa repositório
        result = await self.command_executor.execute_command("git init", context)
        if not result.success:
            return False
        
        # Cria .gitignore se não existir
        await self._create_gitignore(project_path)
        
        # Adiciona remote se fornecido
        if remote_url:
            await self.add_remote("origin", remote_url, project_path)
        
        return True
    
    async def _is_git_repository(self, project_path: str) -> bool:
        """Verifica se o diretório é um repositório Git."""
        git_dir = Path(project_path) / '.git'
        return git_dir.exists()
    
    async def _create_gitignore(self, project_path: str) -> None:
        """Cria .gitignore básico."""
        gitignore_path = Path(project_path) / '.gitignore'
        
        if gitignore_path.exists():
            return
        
        # Usa IA para gerar .gitignore apropriado
        try:
            # Detecta tipo de projeto
            project_files = list(Path(project_path).iterdir())
            file_types = [f.suffix for f in project_files if f.is_file()]
            
            prompt = f"""
            Gere um arquivo .gitignore apropriado para este projeto:
            
            Tipos de arquivo encontrados: {', '.join(set(file_types))}
            Estrutura: {[f.name for f in project_files[:10]]}
            
            Retorne apenas o conteúdo do .gitignore, sem explicações.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Remove formatação markdown se houver
            gitignore_content = response.strip()
            if gitignore_content.startswith('```'):
                gitignore_content = '\n'.join(gitignore_content.split('\n')[1:-1])
            
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
                
        except Exception:
            # Fallback para .gitignore básico Python
            basic_gitignore = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment variables
.env
.env.local
"""
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(basic_gitignore.strip())
    
    async def get_status(self, project_path: str) -> GitStatus:
        """Obtém status completo do repositório."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        # Status básico
        result = await self.command_executor.execute_command("git status --porcelain", context)
        
        if not result.success:
            return GitStatus(
                branch="unknown",
                is_clean=False,
                staged_files=[],
                modified_files=[],
                untracked_files=[],
                ahead=0,
                behind=0,
                remote=None
            )
        
        # Parseia output
        staged_files = []
        modified_files = []
        untracked_files = []
        
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            
            status_code = line[:2]
            file_path = line[3:].strip()
            
            if status_code[0] in ['A', 'M', 'D', 'R', 'C']:
                staged_files.append(file_path)
            elif status_code[1] in ['M', 'D']:
                modified_files.append(file_path)
            elif status_code == '??':
                untracked_files.append(file_path)
        
        # Branch atual
        branch_result = await self.command_executor.execute_command("git branch --show-current", context)
        branch = branch_result.stdout.strip() if branch_result.success else "unknown"
        
        # Ahead/behind info
        ahead, behind = await self._get_ahead_behind_count(project_path)
        
        # Remote info
        remote = await self._get_remote_url(project_path)
        
        return GitStatus(
            branch=branch,
            is_clean=len(staged_files) == 0 and len(modified_files) == 0 and len(untracked_files) == 0,
            staged_files=staged_files,
            modified_files=modified_files,
            untracked_files=untracked_files,
            ahead=ahead,
            behind=behind,
            remote=remote
        )
    
    async def _get_ahead_behind_count(self, project_path: str) -> Tuple[int, int]:
        """Obtém contagem de commits ahead/behind."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command(
            "git rev-list --left-right --count HEAD...@{upstream}", context
        )
        
        if result.success and result.stdout.strip():
            try:
                ahead, behind = map(int, result.stdout.strip().split())
                return ahead, behind
            except:
                pass
        
        return 0, 0
    
    async def _get_remote_url(self, project_path: str) -> Optional[str]:
        """Obtém URL do remote origin."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=5.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command("git remote get-url origin", context)
        
        if result.success and result.stdout.strip():
            return result.stdout.strip()
        
        return None
    
    async def add_files(self, files: List[str], project_path: str) -> bool:
        """Adiciona arquivos ao stage."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        if not files:
            # Adiciona todos os arquivos
            result = await self.command_executor.execute_command("git add .", context)
        else:
            # Adiciona arquivos específicos
            files_str = ' '.join(f'"{f}"' for f in files)
            result = await self.command_executor.execute_command(f"git add {files_str}", context)
        
        return result.success
    
    async def commit(self, message: str, project_path: str, auto_add: bool = True) -> bool:
        """Faz commit com mensagem."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        # Adiciona arquivos automaticamente se solicitado
        if auto_add:
            await self.add_files([], project_path)
        
        # Escapa aspas na mensagem
        escaped_message = message.replace('"', '\\"')
        
        result = await self.command_executor.execute_command(
            f'git commit -m "{escaped_message}"', context
        )
        
        return result.success
    
    async def smart_commit(self, project_path: str, description: Optional[str] = None) -> bool:
        """Faz commit inteligente analisando mudanças."""
        # Obtém status
        status = await self.get_status(project_path)
        
        if status.is_clean:
            return True  # Nada para commitar
        
        # Gera mensagem inteligente
        commit_message = await self._generate_commit_message(status, project_path, description)
        
        # Faz commit
        return await self.commit(commit_message, project_path)
    
    async def _generate_commit_message(self, status: GitStatus, project_path: str, description: Optional[str]) -> str:
        """Gera mensagem de commit inteligente."""
        try:
            # Analisa mudanças
            all_files = status.staged_files + status.modified_files + status.untracked_files
            
            # Obtém diff para arquivos modificados
            context = CommandContext(
                working_directory=project_path,
                environment={},
                timeout=10.0,
                safe_mode=True
            )
            
            diff_result = await self.command_executor.execute_command("git diff --cached", context)
            diff_content = diff_result.stdout if diff_result.success else ""
            
            # Se não há diff staged, pega diff working
            if not diff_content:
                diff_result = await self.command_executor.execute_command("git diff", context)
                diff_content = diff_result.stdout if diff_result.success else ""
            
            prompt = f"""
            Gere uma mensagem de commit concisa baseada nestas mudanças:

            Arquivos alterados: {', '.join(all_files[:10])}
            Descrição fornecida: {description or 'Nenhuma'}

            Diff (primeiras linhas):
            {diff_content[:1000]}

            Gere uma mensagem de commit seguindo convenções:
            - Use formato: "tipo: descrição breve"
            - Tipos: feat, fix, docs, style, refactor, test, chore
            - Máximo 50 caracteres
            - Em português

            Retorne apenas a mensagem, sem explicações.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Limpa resposta
            message = response.strip().split('\n')[0]
            if len(message) > 70:
                message = message[:67] + "..."
            
            return message
            
        except Exception:
            # Fallback para mensagem baseada em arquivos
            if status.untracked_files:
                return "feat: adiciona novos arquivos"
            elif status.modified_files:
                return "fix: atualiza arquivos existentes"
            else:
                return "chore: atualiza projeto"
    
    async def push(self, project_path: str, branch: Optional[str] = None, force: bool = False) -> bool:
        """Faz push para o remote."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=60.0,
            safe_mode=True
        )
        
        # Constrói comando
        command = "git push"
        
        if force:
            command += " --force"
        
        if branch:
            command += f" origin {branch}"
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def pull(self, project_path: str, branch: Optional[str] = None) -> bool:
        """Faz pull do remote."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=60.0,
            safe_mode=True
        )
        
        command = "git pull"
        if branch:
            command += f" origin {branch}"
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def create_branch(self, branch_name: str, project_path: str, checkout: bool = True) -> bool:
        """Cria nova branch."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        if checkout:
            command = f"git checkout -b {branch_name}"
        else:
            command = f"git branch {branch_name}"
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def checkout(self, branch_name: str, project_path: str) -> bool:
        """Muda para branch específica."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command(f"git checkout {branch_name}", context)
        return result.success
    
    async def merge(self, branch_name: str, project_path: str) -> bool:
        """Faz merge de branch."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command(f"git merge {branch_name}", context)
        return result.success
    
    async def get_log(self, project_path: str, limit: int = 10) -> List[CommitInfo]:
        """Obtém histórico de commits."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        # Formato: hash|author|date|message
        result = await self.command_executor.execute_command(
            f'git log --oneline --format="%H|%an|%ad|%s" --date=iso -n {limit}', context
        )
        
        if not result.success:
            return []
        
        commits = []
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    hash_val = parts[0]
                    author = parts[1]
                    date_str = parts[2]
                    message = parts[3]
                    
                    # Parse date
                    try:
                        date = datetime.fromisoformat(date_str.replace(' ', 'T', 1))
                    except:
                        date = datetime.now()
                    
                    commits.append(CommitInfo(
                        hash=hash_val,
                        author=author,
                        date=date,
                        message=message,
                        files_changed=[]  # Seria necessário comando adicional
                    ))
            except:
                continue
        
        return commits
    
    async def add_remote(self, name: str, url: str, project_path: str) -> bool:
        """Adiciona remote."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command(f"git remote add {name} {url}", context)
        return result.success
    
    async def clone_repository(self, url: str, destination: str, branch: Optional[str] = None) -> bool:
        """Clona repositório."""
        context = CommandContext(
            working_directory=str(Path(destination).parent),
            environment={},
            timeout=120.0,
            safe_mode=True
        )
        
        command = f"git clone {url} {Path(destination).name}"
        if branch:
            command += f" -b {branch}"
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def stash(self, project_path: str, message: Optional[str] = None) -> bool:
        """Faz stash das mudanças."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        command = "git stash"
        if message:
            command += f' push -m "{message}"'
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def stash_pop(self, project_path: str) -> bool:
        """Aplica último stash."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        result = await self.command_executor.execute_command("git stash pop", context)
        return result.success
    
    async def reset(self, project_path: str, commit_hash: Optional[str] = None, hard: bool = False) -> bool:
        """Faz reset do repositório."""
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=10.0,
            safe_mode=True
        )
        
        command = "git reset"
        if hard:
            command += " --hard"
        
        if commit_hash:
            command += f" {commit_hash}"
        
        result = await self.command_executor.execute_command(command, context)
        return result.success
    
    async def auto_sync(self, project_path: str) -> Dict[str, Any]:
        """Sincronização automática inteligente."""
        sync_result = {
            'success': False,
            'actions_taken': [],
            'conflicts': [],
            'status': 'unknown'
        }
        
        try:
            # 1. Verifica status
            status = await self.get_status(project_path)
            sync_result['status'] = 'clean' if status.is_clean else 'dirty'
            
            # 2. Se há mudanças locais, commita automaticamente
            if not status.is_clean:
                commit_success = await self.smart_commit(project_path, "Auto-sync: salva mudanças locais")
                if commit_success:
                    sync_result['actions_taken'].append('commit_local_changes')
                else:
                    sync_result['conflicts'].append('failed_to_commit')
                    return sync_result
            
            # 3. Faz pull se há remote
            if status.remote:
                pull_success = await self.pull(project_path)
                if pull_success:
                    sync_result['actions_taken'].append('pull_remote')
                else:
                    sync_result['conflicts'].append('pull_conflicts')
                    return sync_result
            
            # 4. Faz push se há commits ahead
            if status.ahead > 0 and status.remote:
                push_success = await self.push(project_path)
                if push_success:
                    sync_result['actions_taken'].append('push_changes')
                else:
                    sync_result['conflicts'].append('push_failed')
                    return sync_result
            
            sync_result['success'] = True
            return sync_result
            
        except Exception as e:
            sync_result['conflicts'].append(f'error: {str(e)}')
            return sync_result
    
    async def generate_git_report(self, project_path: str) -> str:
        """Gera relatório Git detalhado."""
        status = await self.get_status(project_path)
        recent_commits = await self.get_log(project_path, 5)
        
        report = "📋 **Relatório Git**\n\n"
        
        # Status atual
        status_emoji = "✅" if status.is_clean else "📝"
        report += f"{status_emoji} **Status**: {'Limpo' if status.is_clean else 'Modificado'}\n"
        report += f"🌿 **Branch**: {status.branch}\n"
        
        if status.remote:
            report += f"🔗 **Remote**: {status.remote}\n"
        
        if status.ahead > 0 or status.behind > 0:
            report += f"📊 **Sync**: {status.ahead} ahead, {status.behind} behind\n"
        
        report += "\n"
        
        # Arquivos modificados
        if status.modified_files or status.staged_files or status.untracked_files:
            report += "📁 **Mudanças Pendentes**:\n"
            
            if status.staged_files:
                report += f"- ✅ Staged: {len(status.staged_files)} arquivos\n"
            
            if status.modified_files:
                report += f"- 📝 Modificados: {len(status.modified_files)} arquivos\n"
            
            if status.untracked_files:
                report += f"- ❓ Não rastreados: {len(status.untracked_files)} arquivos\n"
            
            report += "\n"
        
        # Commits recentes
        if recent_commits:
            report += "📚 **Commits Recentes**:\n"
            for commit in recent_commits[:3]:
                date_str = commit.date.strftime('%d/%m %H:%M')
                report += f"- `{commit.hash[:7]}` {commit.message} ({commit.author}, {date_str})\n"
        
        return report