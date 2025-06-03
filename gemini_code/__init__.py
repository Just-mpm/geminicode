"""
Gemini Code - Assistente de Desenvolvimento Total
Sistema completo de desenvolvimento com IA
"""

__version__ = "1.0.0"
__author__ = "Gemini Code Team"

# Core modules
from .core.gemini_client import GeminiClient
from .core.project_manager import ProjectManager
from .core.nlp_enhanced import NLPEnhanced
from .core.file_manager import FileManagementSystem
from .core.workspace_manager import WorkspaceManager

# Analysis modules - Core only for now
try:
    from .analysis.error_detector import ErrorDetector
except ImportError:
    ErrorDetector = None

try:
    from .analysis.performance import PerformanceAnalyzer
except ImportError:
    PerformanceAnalyzer = None

# Database and utilities
try:
    from .database.database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None

# Monitoring and security
try:
    from .security.security_scanner import SecurityScanner
except ImportError:
    SecurityScanner = None

# Metrics and analytics
try:
    from .metrics.business_metrics import BusinessMetrics
except ImportError:
    BusinessMetrics = None

# Collaboration
try:
    from .collaboration.team_manager import TeamManager
except ImportError:
    TeamManager = None

__all__ = [
    # Core modules (always available)
    "GeminiClient",
    "ProjectManager", 
    "NLPEnhanced",
    "FileManagementSystem",
    "WorkspaceManager",
    
    # Optional modules (may be None if import fails)
    "ErrorDetector",
    "PerformanceAnalyzer",
    "DatabaseManager",
    "SecurityScanner",
    "BusinessMetrics",
    "TeamManager"
]