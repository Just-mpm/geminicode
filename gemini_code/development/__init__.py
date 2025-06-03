"""
Módulo de desenvolvimento do Gemini Code.
Responsável por geração de código, refatoração e construção de features.
"""

from .code_generator import CodeGenerator
from .refactoring import RefactoringManager
from .feature_builder import FeatureBuilder

__all__ = [
    'CodeGenerator',
    'RefactoringManager',
    'FeatureBuilder'
]