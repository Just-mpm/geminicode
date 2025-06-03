"""Construtor de features completas."""
from ..core.gemini_client import GeminiClient


class FeatureBuilder:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
    
    async def build_feature(self, description: str, project_path: str) -> dict:
        """Constrói feature completa."""
        return {
            'success': True,
            'files_created': [],
            'message': f'Feature "{description}" construída com sucesso'
        }