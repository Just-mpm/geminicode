"""
Wrapper de configuração para compatibilidade com testes
"""
from typing import Any
from .config import Config as BaseConfig, ConfigManager


class Config:
    """Wrapper que adiciona métodos set/get à configuração."""
    
    def __init__(self):
        self._config = BaseConfig()
        self._custom_values = {}
        self._manager = ConfigManager()
    
    def set(self, key: str, value: Any) -> None:
        """Define um valor de configuração."""
        self._custom_values[key] = value
        
        # Tenta setar em atributos conhecidos
        if key == 'enable_real_execution':
            self._config.behavior.auto_execute = value
        elif key == 'enable_autonomous_mode':
            self._config.project.auto_fix = value
        elif key == 'nlp_confidence_threshold':
            self._custom_values[key] = value  # Apenas armazena
        elif key == 'max_retries':
            self._custom_values[key] = value  # Apenas armazena
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração."""
        # Primeiro verifica valores customizados
        if key in self._custom_values:
            return self._custom_values[key]
        
        # Depois verifica atributos conhecidos
        if key == 'enable_real_execution':
            return self._config.behavior.auto_execute
        elif key == 'enable_autonomous_mode':
            return self._config.project.auto_fix
        
        # Retorna default se não encontrar
        return default
    
    def __getattr__(self, name):
        """Delega atributos não encontrados para a configuração base."""
        return getattr(self._config, name)