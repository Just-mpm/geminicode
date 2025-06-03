"""
Sistema de Injeção de Dependência para Gemini Code
Facilita o gerenciamento e teste de componentes
"""

from typing import Dict, Any, Type, Optional, Callable
from dataclasses import dataclass
import logging
from pathlib import Path


@dataclass
class ServiceConfig:
    """Configuração para um serviço"""
    service_class: Type
    dependencies: Dict[str, str] = None  # nome_param: nome_servico
    singleton: bool = True
    lazy_init: bool = False
    config: Dict[str, Any] = None


class DependencyContainer:
    """Container de injeção de dependência"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self._services: Dict[str, ServiceConfig] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self.logger = logging.getLogger('DependencyContainer')
        
        if config_path and config_path.exists():
            self._load_config(config_path)
    
    def register(self, name: str, service_class: Type, 
                 dependencies: Dict[str, str] = None,
                 singleton: bool = True,
                 config: Dict[str, Any] = None):
        """Registra um serviço"""
        self._services[name] = ServiceConfig(
            service_class=service_class,
            dependencies=dependencies or {},
            singleton=singleton,
            config=config or {}
        )
        self.logger.debug(f"Registered service: {name}")
    
    def register_factory(self, name: str, factory: Callable):
        """Registra uma factory function"""
        self._factories[name] = factory
        self.logger.debug(f"Registered factory: {name}")
    
    def get(self, name: str) -> Any:
        """Obtém uma instância do serviço"""
        # Verifica se é factory
        if name in self._factories:
            return self._factories[name](self)
        
        # Verifica se já existe instância (singleton)
        if name in self._instances:
            return self._instances[name]
        
        # Verifica se o serviço está registrado
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        
        service_config = self._services[name]
        
        # Resolve dependências
        kwargs = {}
        
        # Adiciona configurações
        if service_config.config:
            kwargs.update(service_config.config)
        
        # Resolve dependências registradas
        for param_name, dep_name in service_config.dependencies.items():
            kwargs[param_name] = self.get(dep_name)
        
        # Cria instância
        try:
            instance = service_config.service_class(**kwargs)
            self.logger.debug(f"Created instance of {name}")
            
            # Armazena se for singleton
            if service_config.singleton:
                self._instances[name] = instance
            
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create {name}: {e}", exc_info=True)
            raise
    
    def reset(self):
        """Limpa todas as instâncias (útil para testes)"""
        self._instances.clear()
        self.logger.debug("Container reset")
    
    def _load_config(self, config_path: Path):
        """Carrega configuração de arquivo"""
        import yaml
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            for name, service_config in config.get('services', {}).items():
                # Importa classe dinamicamente
                module_path, class_name = service_config['class'].rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                service_class = getattr(module, class_name)
                
                self.register(
                    name=name,
                    service_class=service_class,
                    dependencies=service_config.get('dependencies', {}),
                    singleton=service_config.get('singleton', True),
                    config=service_config.get('config', {})
                )
                
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}", exc_info=True)


# Container global
_container = None


def get_container() -> DependencyContainer:
    """Obtém o container global"""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def inject(**dependencies):
    """Decorator para injeção automática de dependências"""
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, **kwargs):
            # Injeta dependências não fornecidas
            container = get_container()
            for param, service_name in dependencies.items():
                if param not in kwargs:
                    kwargs[param] = container.get(service_name)
            
            original_init(self, **kwargs)
        
        cls.__init__ = new_init
        return cls
    
    return decorator