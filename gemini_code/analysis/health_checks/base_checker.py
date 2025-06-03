"""
Base class for health checkers.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ...core.gemini_client import GeminiClient
from ...core.file_manager import FileManagementSystem


@dataclass
class CheckResult:
    """Result of a health check."""
    name: str
    score: float  # 0-100
    status: str  # 'good', 'warning', 'critical'
    details: Dict[str, Any]
    recommendations: List[str]
    execution_time: float


class BaseHealthChecker(ABC):
    """Base class for all health checkers."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def check(self, project_path: str) -> CheckResult:
        """Perform the health check."""
        pass
    
    @abstractmethod
    def get_threshold_config(self) -> Dict[str, float]:
        """Get threshold configuration for this checker."""
        pass
    
    def _calculate_status(self, score: float, thresholds: Dict[str, float]) -> str:
        """Calculate status based on score and thresholds."""
        if score >= thresholds.get('good', 80):
            return 'good'
        elif score >= thresholds.get('warning', 50):
            return 'warning'
        else:
            return 'critical'
    
    def _filter_valid_python_files(self, project_path: str) -> List[Path]:
        """Filter valid Python files applying exclusion patterns."""
        all_python_files = list(Path(project_path).rglob("*.py"))
        valid_python_files = []
        
        excluded_patterns = [
            '*/__pycache__/*',
            '*/venv/*',
            '*/.venv/*',
            '*/env/*',
            '*/.env/*',
            '*/migrations/*',
            '*/node_modules/*',
            '*/.git/*',
            '*/temp*',
            '*/.pytest_cache/*',
            '*/.mypy_cache/*',
            '*/test_*',
            '*_test.py'
        ]
        
        for f in all_python_files:
            if not f.is_file():
                continue
                
            file_str = str(f)
            should_exclude = False
            
            for pattern in excluded_patterns:
                import fnmatch
                if fnmatch.fnmatch(file_str, pattern) or fnmatch.fnmatch(f.name, pattern):
                    should_exclude = True
                    break
            
            if not should_exclude and not f.name.startswith('.'):
                valid_python_files.append(f)
        
        return valid_python_files
    
    async def _analyze_with_gemini(self, prompt: str, context: str = "") -> str:
        """Use Gemini for analysis if available."""
        try:
            full_prompt = f"{prompt}\n\nContext: {context}" if context else prompt
            response = await self.gemini_client.generate_response(full_prompt)
            return response
        except Exception:
            return "Análise automática não disponível"