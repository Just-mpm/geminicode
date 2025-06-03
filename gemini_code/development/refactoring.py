"""Refatoração inteligente de código."""
from ..core.gemini_client import GeminiClient


class RefactoringManager:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
    
    async def extract_method(self, code: str, start_line: int, end_line: int) -> str:
        """Extrai método de código."""
        return await self.gemini_client.generate_response(f"Extraia método das linhas {start_line}-{end_line}: {code}")
    
    async def rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Renomeia variável."""
        return code.replace(old_name, new_name)
    
    async def optimize_imports(self, code: str) -> str:
        """Otimiza imports."""
        return await self.gemini_client.generate_response(f"Otimize imports: {code}")