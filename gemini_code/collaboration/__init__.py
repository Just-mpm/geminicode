"""
Sistema de colaboração em equipe do Gemini Code.
"""

from .team_manager import TeamManager, TeamMember
from .project_sharing import ProjectSharing, SharedProject
from .real_time_sync import RealTimeSync
from .code_review import CodeReview, ReviewRequest

__all__ = [
    'TeamManager',
    'TeamMember', 
    'ProjectSharing',
    'SharedProject',
    'RealTimeSync',
    'CodeReview',
    'ReviewRequest'
]