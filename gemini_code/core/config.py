"""
Sistema de configuração do Gemini Code
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import shutil


@dataclass
class ModelConfig:
    name: str = "gemini-2.5-flash-preview-05-20"
    thinking_budget_default: int = 8192
    thinking_budget_max: int = 24576
    temperature: float = 0.3
    max_output_tokens: int = 8192
    context_window: int = 1048576


@dataclass
class UserConfig:
    mode: str = "non-programmer"
    language: str = "portuguese"
    timezone: str = "America/Sao_Paulo"


@dataclass
class ProjectConfig:
    type: str = "continuous_development"
    scan_on_start: bool = True
    auto_fix: bool = True
    preserve_style: bool = True
    backup_before_changes: bool = True
    git_integration: bool = True


@dataclass
class BehaviorConfig:
    natural_language_only: bool = True
    auto_execute: bool = True
    show_progress: bool = True
    explain_simple: bool = True
    ask_only_essential: bool = True
    visual_feedback: bool = True
    auto_commit: bool = False


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    user: UserConfig = field(default_factory=UserConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    
    _config_path: Optional[Path] = None
    _project_root: Optional[Path] = None


class ConfigManager:
    """Gerencia configurações do Gemini Code"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".gemini_code"
        self.config_file = self.config_dir / "config.yaml"
        self.config = self.load_config()
    
    def load_config(self) -> Config:
        """Carrega configuração do projeto ou usa padrão"""
        if self.config_file.exists():
            return self._load_from_file()
        else:
            return self._load_default()
    
    def _load_from_file(self) -> Config:
        """Carrega configuração de arquivo"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            config = Config()
            
            # Atualiza model config
            if 'model' in data:
                for key, value in data['model'].items():
                    if hasattr(config.model, key):
                        setattr(config.model, key, value)
            
            # Atualiza user config
            if 'user' in data:
                for key, value in data['user'].items():
                    if hasattr(config.user, key):
                        setattr(config.user, key, value)
            
            # Atualiza project config
            if 'project' in data:
                for key, value in data['project'].items():
                    if hasattr(config.project, key):
                        setattr(config.project, key, value)
            
            # Atualiza behavior config
            if 'behavior' in data:
                for key, value in data['behavior'].items():
                    if hasattr(config.behavior, key):
                        setattr(config.behavior, key, value)
            
            config._config_path = self.config_file
            config._project_root = self.project_root
            
            return config
            
        except Exception as e:
            print(f"⚠️  Erro ao carregar configuração: {e}")
            return self._load_default()
    
    def _load_default(self) -> Config:
        """Carrega configuração padrão"""
        # Tenta copiar do template
        default_config_path = Path(__file__).parent.parent / "config" / "default_config.yaml"
        
        if default_config_path.exists():
            try:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                config = Config()
                
                # Mesma lógica de atualização
                if 'model' in data:
                    for key, value in data['model'].items():
                        if hasattr(config.model, key):
                            setattr(config.model, key, value)
                
                if 'user' in data:
                    for key, value in data['user'].items():
                        if hasattr(config.user, key):
                            setattr(config.user, key, value)
                
                if 'project' in data:
                    for key, value in data['project'].items():
                        if hasattr(config.project, key):
                            setattr(config.project, key, value)
                
                if 'behavior' in data:
                    for key, value in data['behavior'].items():
                        if hasattr(config.behavior, key):
                            setattr(config.behavior, key, value)
                
                return config
                
            except Exception:
                pass
        
        # Retorna configuração padrão em código
        return Config()
    
    def save_config(self, config: Optional[Config] = None):
        """Salva configuração no projeto"""
        config = config or self.config
        
        # Cria diretório se não existir
        self.config_dir.mkdir(exist_ok=True)
        
        # Converte para dict
        config_dict = {
            'model': {
                'name': config.model.name,
                'thinking_budget_default': config.model.thinking_budget_default,
                'thinking_budget_max': config.model.thinking_budget_max,
                'temperature': config.model.temperature,
                'max_output_tokens': config.model.max_output_tokens,
                'context_window': config.model.context_window,
            },
            'user': {
                'mode': config.user.mode,
                'language': config.user.language,
                'timezone': config.user.timezone,
            },
            'project': {
                'type': config.project.type,
                'scan_on_start': config.project.scan_on_start,
                'auto_fix': config.project.auto_fix,
                'preserve_style': config.project.preserve_style,
                'backup_before_changes': config.project.backup_before_changes,
                'git_integration': config.project.git_integration,
            },
            'behavior': {
                'natural_language_only': config.behavior.natural_language_only,
                'auto_execute': config.behavior.auto_execute,
                'show_progress': config.behavior.show_progress,
                'explain_simple': config.behavior.explain_simple,
                'ask_only_essential': config.behavior.ask_only_essential,
                'visual_feedback': config.behavior.visual_feedback,
                'auto_commit': config.behavior.auto_commit,
            }
        }
        
        # Salva arquivo
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def init_project(self):
        """Inicializa configuração no projeto"""
        if self.config_file.exists():
            return False
        
        self.save_config()
        
        # Cria .gitignore se não existir
        gitignore_path = self.config_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write("memory.db\n*.log\n")
    def migrate_config(self, from_version: str = None) -> bool:
        """Migra configuração entre versões."""
        try:
            current_version = getattr(self.config, 'version', '1.0.0')
            
            if from_version and from_version != current_version:
                self.logger.info(f"Migrando configuração de {from_version} para {current_version}")
                
                # Aplica migrações específicas
                if from_version < '1.0.0':
                    self._migrate_to_v1_0_0()
                
                # Salva versão atualizada
                self.config.version = current_version
                self.save_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na migração: {e}")
            return False
    
    def _migrate_to_v1_0_0(self):
        """Migração específica para v1.0.0."""
        # Adiciona configurações padrão se não existirem
        if not hasattr(self.config, 'advanced'):
            self.config.advanced = type('Advanced', (), {
                'enable_cognition': True,
                'auto_healing': True,
                'learning_enabled': True,
                'massive_context': True
            })()
        
        if not hasattr(self.config, 'security'):
            self.config.security = type('Security', (), {
                'permission_level': 'moderate',
                'auto_approve_safe': True
            })()
    
    def validate_config(self) -> List[str]:
        """Valida configuração atual."""
        issues = []
        
        try:
            # Verifica configurações essenciais
            if not hasattr(self.config, 'model'):
                issues.append("Configuração 'model' ausente")
            
            if not hasattr(self.config, 'user'):
                issues.append("Configuração 'user' ausente")
            
            # Verifica configuração do modelo
            if hasattr(self.config, 'model'):
                if not hasattr(self.config.model, 'name'):
                    issues.append("Nome do modelo não configurado")
                
                if not hasattr(self.config.model, 'temperature'):
                    issues.append("Temperatura do modelo não configurada")
            
            return issues
            
        except Exception as e:
            return [f"Erro na validação: {e}"]
    
    def get_api_key(self) -> Optional[str]:
        """Obtém API key do Gemini"""
        # Tenta de várias fontes
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            # Tenta arquivo .env
            env_file = self.project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
        
        if not api_key:
            # Tenta arquivo de config local
            key_file = self.config_dir / "api_key.txt"
            if key_file.exists():
                with open(key_file, 'r') as f:
                    api_key = f.read().strip()
        
        return api_key
    
    def set_api_key(self, api_key: str):
        """Define API key do Gemini"""
        # Salva no arquivo de config
        self.config_dir.mkdir(exist_ok=True)
        key_file = self.config_dir / "api_key.txt"
        
        with open(key_file, 'w') as f:
            f.write(api_key)
        
        # Adiciona ao .gitignore se não estiver
        gitignore_path = self.config_dir / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            if "api_key.txt" not in content:
                with open(gitignore_path, 'a') as f:
                    f.write("\napi_key.txt\n")
    
    def update_config(self, **kwargs):
        """Atualiza configuração específica"""
        for key, value in kwargs.items():
            if '.' in key:
                # Nested config
                parts = key.split('.')
                obj = self.config
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
            else:
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        self.save_config()