"""
Executor de comandos seguro e inteligente.
"""

import asyncio
import subprocess
import shlex
import os
import signal
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
import threading
import queue

from ..core.gemini_client import GeminiClient


@dataclass
class CommandResult:
    """Resultado da execução de um comando."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    success: bool
    pid: Optional[int] = None


@dataclass
class CommandContext:
    """Contexto de execução de um comando."""
    working_directory: str
    environment: Dict[str, str]
    timeout: Optional[float]
    safe_mode: bool = True


class CommandExecutor:
    """Executa comandos de forma segura e inteligente."""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.running_processes: Dict[int, subprocess.Popen] = {}
        self.command_history: List[CommandResult] = []
        self.safe_commands = self._load_safe_commands()
        self.dangerous_commands = self._load_dangerous_commands()
    
    def _load_safe_commands(self) -> List[str]:
        """Lista de comandos considerados seguros."""
        return [
            'ls', 'dir', 'pwd', 'cd', 'cat', 'type', 'head', 'tail',
            'echo', 'python', 'pip', 'node', 'npm', 'git', 'grep',
            'find', 'tree', 'which', 'where', 'ps', 'wc', 'sort',
            'mkdir', 'touch', 'cp', 'copy', 'mv', 'move', 'chmod',
            'pytest', 'python -m', 'pip install', 'pip list',
            'git status', 'git add', 'git commit', 'git push',
            'git pull', 'git log', 'git diff', 'git branch'
        ]
    
    def _load_dangerous_commands(self) -> List[str]:
        """Lista de comandos considerados perigosos."""
        return [
            'rm -rf', 'del /f', 'format', 'fdisk', 'dd if=',
            'shutdown', 'reboot', 'halt', 'poweroff', 'init 0',
            'killall', 'pkill -9', ':(){:|:&};:', 'fork bomb',
            'sudo rm', 'sudo dd', 'sudo chmod 777 /',
            'curl | sh', 'wget | sh', 'eval', 'exec'
        ]
    
    async def execute_command(self, command: str, context: CommandContext) -> CommandResult:
        """Executa um comando com verificações de segurança."""
        # Verifica segurança
        if context.safe_mode and not await self._is_command_safe(command):
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="Comando bloqueado por questões de segurança",
                execution_time=0,
                success=False
            )
        
        start_time = time.time()
        
        try:
            # Prepara ambiente
            env = os.environ.copy()
            env.update(context.environment)
            
            # Executa comando
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.working_directory,
                env=env
            )
            
            # Registra processo
            if process.pid:
                self.running_processes[process.pid] = process
            
            try:
                # Aguarda com timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=context.timeout
                )
                
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Mata processo em timeout
                if process.pid:
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
                
                return CommandResult(
                    command=command,
                    exit_code=-2,
                    stdout="",
                    stderr="Comando excedeu timeout",
                    execution_time=time.time() - start_time,
                    success=False,
                    pid=process.pid
                )
            
            finally:
                # Remove da lista de processos
                if process.pid and process.pid in self.running_processes:
                    del self.running_processes[process.pid]
            
            result = CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout.decode('utf-8', errors='ignore') if stdout else "",
                stderr=stderr.decode('utf-8', errors='ignore') if stderr else "",
                execution_time=time.time() - start_time,
                success=exit_code == 0,
                pid=process.pid
            )
            
            # Adiciona ao histórico
            self.command_history.append(result)
            
            return result
            
        except Exception as e:
            return CommandResult(
                command=command,
                exit_code=-3,
                stdout="",
                stderr=f"Erro na execução: {str(e)}",
                execution_time=time.time() - start_time,
                success=False
            )
    
    async def _is_command_safe(self, command: str) -> bool:
        """Verifica se um comando é seguro para execução."""
        command_lower = command.lower().strip()
        
        # Verifica comandos perigosos
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return False
        
        # Verifica padrões perigosos
        dangerous_patterns = [
            'rm -rf /',
            'del /f /s /q c:',
            '> /dev/sda',
            'chmod 777 /',
            'chown -R root /',
            'dd if=/dev/zero',
            'format c:',
            'curl.*|.*sh',
            'wget.*|.*sh'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        # Usa IA para verificação adicional
        if len(command) > 50 or any(char in command for char in '|&;`$(){}[]'):
            is_safe = await self._ai_safety_check(command)
            return is_safe
        
        return True
    
    async def _ai_safety_check(self, command: str) -> bool:
        """Usa IA para verificar segurança do comando."""
        try:
            prompt = f"""
            Analise este comando e determine se é seguro executar:

            Comando: {command}

            Considere:
            - Comandos destrutivos (rm, del, format, etc.)
            - Execução de código remoto
            - Alterações de permissões perigosas
            - Ataques de injeção
            - Fork bombs ou DoS

            Responda apenas "SEGURO" ou "PERIGOSO"
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            return "SEGURO" in response.upper()
            
        except Exception:
            # Em caso de erro, erra do lado da segurança
            return False
    
    async def execute_batch_commands(self, commands: List[str], context: CommandContext) -> List[CommandResult]:
        """Executa múltiplos comandos em sequência."""
        results = []
        
        for command in commands:
            result = await self.execute_command(command, context)
            results.append(result)
            
            # Para na primeira falha, se configurado
            if not result.success and context.safe_mode:
                break
        
        return results
    
    async def execute_parallel_commands(self, commands: List[str], context: CommandContext) -> List[CommandResult]:
        """Executa múltiplos comandos em paralelo."""
        tasks = []
        
        for command in commands:
            task = asyncio.create_task(
                self.execute_command(command, context)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converte exceções em resultados
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(CommandResult(
                    command=commands[i],
                    exit_code=-4,
                    stdout="",
                    stderr=f"Erro na execução paralela: {str(result)}",
                    execution_time=0,
                    success=False
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def execute_interactive_command(self, command: str, context: CommandContext, 
                                        input_callback: Callable[[str], str] = None) -> CommandResult:
        """Executa comando interativo com callback para input."""
        if context.safe_mode and not await self._is_command_safe(command):
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="Comando interativo bloqueado por questões de segurança",
                execution_time=0,
                success=False
            )
        
        start_time = time.time()
        
        try:
            env = os.environ.copy()
            env.update(context.environment)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.working_directory,
                env=env
            )
            
            if process.pid:
                self.running_processes[process.pid] = process
            
            # Gerencia comunicação interativa
            stdout_data = []
            stderr_data = []
            
            try:
                while process.returncode is None:
                    # Lê output disponível
                    try:
                        stdout_chunk = await asyncio.wait_for(
                            process.stdout.read(1024), timeout=0.1
                        )
                        if stdout_chunk:
                            stdout_data.append(stdout_chunk)
                            
                            # Se há callback, processa input
                            if input_callback:
                                output_str = stdout_chunk.decode('utf-8', errors='ignore')
                                if any(prompt in output_str.lower() for prompt in [':', '?', '>', '$', '#']):
                                    user_input = input_callback(output_str)
                                    if user_input:
                                        process.stdin.write(f"{user_input}\n".encode())
                                        await process.stdin.drain()
                    
                    except asyncio.TimeoutError:
                        pass
                    
                    # Verifica se processo ainda está rodando
                    if process.returncode is not None:
                        break
                
                # Lê output final
                final_stdout, final_stderr = await process.communicate()
                if final_stdout:
                    stdout_data.append(final_stdout)
                if final_stderr:
                    stderr_data.append(final_stderr)
                
            finally:
                if process.pid and process.pid in self.running_processes:
                    del self.running_processes[process.pid]
            
            return CommandResult(
                command=command,
                exit_code=process.returncode,
                stdout=b''.join(stdout_data).decode('utf-8', errors='ignore'),
                stderr=b''.join(stderr_data).decode('utf-8', errors='ignore'),
                execution_time=time.time() - start_time,
                success=process.returncode == 0,
                pid=process.pid
            )
            
        except Exception as e:
            return CommandResult(
                command=command,
                exit_code=-3,
                stdout="",
                stderr=f"Erro na execução interativa: {str(e)}",
                execution_time=time.time() - start_time,
                success=False
            )
    
    def kill_process(self, pid: int) -> bool:
        """Mata um processo específico."""
        if pid in self.running_processes:
            try:
                process = self.running_processes[pid]
                process.kill()
                del self.running_processes[pid]
                return True
            except Exception:
                return False
        return False
    
    def kill_all_processes(self) -> int:
        """Mata todos os processos em execução."""
        killed_count = 0
        
        for pid in list(self.running_processes.keys()):
            if self.kill_process(pid):
                killed_count += 1
        
        return killed_count
    
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Retorna lista de processos em execução."""
        processes = []
        
        for pid, process in self.running_processes.items():
            processes.append({
                'pid': pid,
                'started': time.time(),  # Simplificado
                'command': getattr(process, 'args', 'unknown')
            })
        
        return processes
    
    async def suggest_command(self, description: str, context: CommandContext) -> List[str]:
        """Sugere comandos baseado em descrição natural."""
        try:
            system_info = os.name
            shell_info = os.environ.get('SHELL', 'cmd' if os.name == 'nt' else 'bash')
            
            prompt = f"""
            Baseado nesta descrição, sugira comandos {system_info} apropriados:

            Descrição: {description}
            Diretório atual: {context.working_directory}
            Sistema: {system_info}
            Shell: {shell_info}

            Retorne 1-3 comandos mais apropriados, um por linha.
            Foque em comandos seguros e práticos.
            Não inclique explicações, apenas os comandos.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai comandos da resposta
            commands = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Remove formatação markdown se houver
                    if line.startswith('```'):
                        continue
                    if line.startswith('`') and line.endswith('`'):
                        line = line[1:-1]
                    
                    commands.append(line)
            
            return commands[:3]  # Máximo 3 sugestões
            
        except Exception as e:
            return [f"# Erro ao sugerir comando: {str(e)}"]
    
    async def explain_command(self, command: str) -> str:
        """Explica o que um comando faz."""
        try:
            prompt = f"""
            Explique este comando de forma simples e clara:

            Comando: {command}

            Explique:
            1. O que o comando faz
            2. Principais parâmetros/flags
            3. Quando usar
            4. Possíveis riscos (se houver)

            Use linguagem simples em português.
            """
            
            explanation = await self.gemini_client.generate_response(prompt)
            return explanation
            
        except Exception as e:
            return f"Erro ao explicar comando: {str(e)}"
    
    def get_command_history(self, limit: int = 10) -> List[CommandResult]:
        """Retorna histórico de comandos executados."""
        return self.command_history[-limit:]
    
    def clear_history(self) -> None:
        """Limpa histórico de comandos."""
        self.command_history.clear()
    
    async def test_command_safety(self, command: str) -> Dict[str, Any]:
        """Testa segurança de um comando sem executá-lo."""
        safety_result = {
            'command': command,
            'is_safe': False,
            'risk_level': 'unknown',
            'warnings': [],
            'suggestions': []
        }
        
        # Verifica padrões perigosos
        command_lower = command.lower()
        
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                safety_result['warnings'].append(f"Contém padrão perigoso: {dangerous}")
                safety_result['risk_level'] = 'high'
        
        # Verifica com IA
        is_safe = await self._ai_safety_check(command)
        safety_result['is_safe'] = is_safe
        
        if not is_safe:
            safety_result['risk_level'] = 'high'
            safety_result['suggestions'].append("Considere uma alternativa mais segura")
        else:
            safety_result['risk_level'] = 'low'
        
        return safety_result