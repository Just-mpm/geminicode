"""
Módulo de integração do Gemini Code.
Responsável por Git, deploy e CI/CD.
"""

from .git_manager import GitManager
from .deployment import DeploymentManager
from .ci_cd import CICDManager

__all__ = [
    'GitManager',
    'DeploymentManager',
    'CICDManager'
]