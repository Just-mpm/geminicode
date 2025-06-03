"""
Módulo de execução do Gemini Code.
Responsável por execução de comandos, testes e debugging.
"""

from .command_executor import CommandExecutor
from .test_runner import TestRunner
from .debugger import DebugManager

__all__ = [
    'CommandExecutor',
    'TestRunner',
    'DebugManager'
]