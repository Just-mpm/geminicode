"""
Bash Tool - Execução de comandos shell estilo Claude Code
"""

import asyncio
import subprocess
import shlex
import os
from typing import Dict, Any, List, Optional
import tempfile
from pathlib import Path

from .base_tool import BaseTool, ToolInput, ToolResult, tool_decorator, ToolCategory, ToolPermission


@tool_decorator(
    name="bash",
    description="Executa comandos shell com segurança e controle",
    category=ToolCategory.SYSTEM,
    permission=ToolPermission.EXECUTE,
    requires_confirmation=True
)
class BashTool(BaseTool):
    """
    Ferramenta para execução de comandos shell.
    Replica o comportamento do BashTool do Claude Code.
    """
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Executa comandos shell no sistema operacional"
        )
        
        # Configurações de segurança
        self.allowed_commands = set()  # Se vazio, permite tudo
        self.blocked_commands = {
            'rm -rf /', 'sudo rm -rf /', 'format', 'fdisk',
            'mkfs', 'dd if=/dev/zero', 'sudo halt', 'sudo reboot',
            'sudo shutdown', 'curl', 'wget', 'nc', 'netcat'
        }
        
        # Diretórios permitidos
        self.allowed_directories = set()  # Se vazio, usa diretório atual
        self.blocked_directories = {
            '/etc', '/usr/bin', '/usr/sbin', '/sbin', '/bin',
            '/boot', '/dev', '/proc', '/sys', '/var/log'
        }
        
        # Configurações de execução
        self.timeout_seconds = 30
        self.max_output_size = 1024 * 1024  # 1MB
        self.working_directory = None
        self.environment_vars = {}
        
        # Histórico de comandos
        self.command_history = []
        self.max_history = 100
        
        self.configure(
            requires_confirmation=True,
            timeout_seconds=30,
            metadata={
                'category': 'system',
                'version': '1.0',
                'tags': ['shell', 'command', 'execution'],
                'dependencies': []
            }
        )
    
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Valida comando antes da execução."""
        command = tool_input.command.strip()
        
        if not command:
            return False
        
        # Verifica comandos bloqueados
        command_lower = command.lower()
        for blocked_cmd in self.blocked_commands:
            if blocked_cmd in command_lower:
                return False
        
        # Se há lista de comandos permitidos, verifica
        if self.allowed_commands:
            first_word = command.split()[0]
            if first_word not in self.allowed_commands:
                return False
        
        # Valida diretório de trabalho
        if self.working_directory:
            work_dir = Path(self.working_directory).resolve()
            for blocked_dir in self.blocked_directories:
                if str(work_dir).startswith(blocked_dir):
                    return False
        
        return True
    
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Executa comando bash."""
        command = tool_input.command.strip()
        
        # Adiciona ao histórico
        self._add_to_history(command)
        
        try:
            # Configura ambiente
            env = os.environ.copy()
            env.update(self.environment_vars)
            
            # Configura diretório de trabalho
            cwd = self.working_directory or os.getcwd()
            
            # Executa comando
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Comando timeout após {self.timeout_seconds} segundos"
                )
            
            # Decodifica saídas
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Limita tamanho da saída
            if len(stdout_text) > self.max_output_size:
                stdout_text = stdout_text[:self.max_output_size] + "\\n... (saída truncada)"
            
            if len(stderr_text) > self.max_output_size:
                stderr_text = stderr_text[:self.max_output_size] + "\\n... (erro truncado)"
            
            # Resultado
            success = process.returncode == 0
            
            result_data = {
                'stdout': stdout_text,
                'stderr': stderr_text,
                'returncode': process.returncode,
                'command': command,
                'working_directory': cwd
            }
            
            return ToolResult(
                success=success,
                data=result_data,
                error=stderr_text if not success else None,
                metadata={
                    'command': command,
                    'returncode': process.returncode,
                    'working_directory': cwd
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro executando comando: {str(e)}",
                metadata={'command': command}
            )
    
    def _add_to_history(self, command: str):
        """Adiciona comando ao histórico."""
        self.command_history.append({
            'command': command,
            'timestamp': self._get_timestamp()
        })
        
        # Mantém histórico limitado
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de comandos."""
        return self.command_history[-limit:]
    
    def clear_history(self):
        """Limpa histórico de comandos."""
        self.command_history.clear()
    
    def set_working_directory(self, directory: str):
        """Define diretório de trabalho."""
        path = Path(directory)
        if path.exists() and path.is_dir():
            self.working_directory = str(path.resolve())
            return True
        return False
    
    def add_environment_var(self, key: str, value: str):
        """Adiciona variável de ambiente."""
        self.environment_vars[key] = value
    
    def remove_environment_var(self, key: str):
        """Remove variável de ambiente."""
        if key in self.environment_vars:
            del self.environment_vars[key]
    
    def add_allowed_command(self, command: str):
        """Adiciona comando à lista permitida."""
        self.allowed_commands.add(command)
    
    def remove_allowed_command(self, command: str):
        """Remove comando da lista permitida."""
        self.allowed_commands.discard(command)
    
    def add_blocked_command(self, command: str):
        """Adiciona comando à lista bloqueada."""
        self.blocked_commands.add(command)
    
    def remove_blocked_command(self, command: str):
        """Remove comando da lista bloqueada."""
        self.blocked_commands.discard(command)
    
    def is_command_safe(self, command: str) -> bool:
        """Verifica se comando é seguro para execução."""
        mock_input = ToolInput(command=command)
        return self.validate_input(mock_input)
    
    def _get_usage_examples(self) -> str:
        return """
bash "ls -la"
bash "python --version"
bash "git status"
bash "npm install"
        """.strip()
    
    def _get_parameters_help(self) -> str:
        return """
**command** (obrigatório): Comando shell para executar

**Opções de contexto:**
- working_directory: Diretório para execução
- timeout: Timeout em segundos (padrão: 30)
- env_vars: Variáveis de ambiente adicionais
        """.strip()
    
    def _get_examples(self) -> str:
        return """
# Listar arquivos
bash "ls -la"

# Verificar versão do Python
bash "python --version"

# Status do Git
bash "git status"

# Instalar dependências
bash "npm install"

# Executar testes
bash "python -m pytest tests/"
        """.strip()


class SafeBashTool(BashTool):
    """
    Versão mais segura do BashTool com restrições extras.
    """
    
    def __init__(self):
        super().__init__()
        
        # Lista de comandos seguros permitidos
        self.allowed_commands = {
            'ls', 'pwd', 'echo', 'cat', 'head', 'tail', 'grep',
            'find', 'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
            'python', 'python3', 'pip', 'pip3', 'node', 'npm',
            'git', 'docker', 'kubectl', 'terraform', 'ansible',
            'pytest', 'jest', 'cargo', 'go', 'rustc', 'javac'
        }
        
        # Comandos adicionais bloqueados
        self.blocked_commands.update({
            'sudo', 'su', 'chmod 777', 'chown root',
            'systemctl', 'service', 'mount', 'umount',
            'iptables', 'ufw', 'firewall-cmd'
        })
        
        self.configure(
            requires_confirmation=True,
            timeout_seconds=15,  # Timeout menor
            metadata={
                'category': 'system',
                'version': '1.0-safe',
                'tags': ['shell', 'command', 'execution', 'safe'],
                'dependencies': []
            }
        )


class BashSession:
    """
    Sessão bash persistente para comandos sequenciais.
    """
    
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or os.getcwd()
        self.process: Optional[asyncio.subprocess.Process] = None
        self.environment_vars = {}
        self.is_active = False
    
    async def start(self):
        """Inicia sessão bash."""
        if self.is_active:
            return
        
        env = os.environ.copy()
        env.update(self.environment_vars)
        
        self.process = await asyncio.create_subprocess_shell(
            '/bin/bash',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_directory,
            env=env
        )
        
        self.is_active = True
    
    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Executa comando na sessão ativa."""
        if not self.is_active or not self.process:
            await self.start()
        
        # Envia comando
        self.process.stdin.write(f"{command}\\n".encode())
        await self.process.stdin.drain()
        
        # Lê resultado (implementação simplificada)
        # Em produção, precisaria de parsing mais sofisticado
        try:
            stdout, stderr = await asyncio.wait_for(
                self.process.communicate(),
                timeout=timeout
            )
            
            return {
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace'),
                'success': True
            }
        except asyncio.TimeoutError:
            return {
                'stdout': '',
                'stderr': 'Timeout',
                'success': False
            }
    
    async def close(self):
        """Fecha sessão bash."""
        if self.process and self.is_active:
            self.process.terminate()
            await self.process.wait()
        
        self.is_active = False
        self.process = None