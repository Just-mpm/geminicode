"""Modo pânico para emergências críticas."""

class PanicMode:
    def __init__(self, recovery_system):
        self.recovery_system = recovery_system
    
    async def activate(self, reason: str):
        """Ativa modo pânico."""
        return await self.recovery_system.handle_emergency(reason, ".")