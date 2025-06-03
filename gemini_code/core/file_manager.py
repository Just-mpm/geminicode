"""
Sistema de manipulação inteligente de arquivos
"""
import os
import shutil
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import difflib
from dataclasses import dataclass
import ast
import importlib.util

from .gemini_client import GeminiClient
import logging
import traceback


@dataclass
class FileOperation:
    """Representa uma operação em arquivo"""
    type: str  # create, modify, delete, move, rename
    path: str
    content: Optional[str] = None
    old_path: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FileManagementSystem:
    """Sistema completo de manipulação de arquivos"""
    
    def __init__(self, gemini_client: GeminiClient, project_root: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.gemini_client = gemini_client
        self.project_root = project_root or Path.cwd()
        self.operations_history: List[FileOperation] = []
        self.backup_dir = self.project_root / ".gemini_code" / "backups"
        self.templates_dir = Path(__file__).parent.parent / "templates"
        
        # Configura logger
        self.logger = logger or self._setup_logger()
        
        # Inicializa diretórios
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Backup directory initialized: {self.backup_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create backup directory: {e}", exc_info=True)
            
        self._ensure_templates_dir()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logger padrão"""
        logger = logging.getLogger('FileManagementSystem')
        logger.setLevel(logging.DEBUG)
        
        # Handler para arquivo
        log_dir = self.project_root / ".gemini_code" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "file_manager.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_templates_dir(self) -> None:
        """Garante que o diretório de templates existe."""
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Aviso: Não foi possível criar diretório de templates: {e}")
            # Usa templates inline como fallback
            self.templates_dir = None
        
    def handle_agent_creation(self, natural_command: str, agent_name: str) -> Dict[str, Any]:
        """
        Cria novo agente com todos os arquivos necessários
        """
        agent_name = agent_name.lower()
        agent_class = ''.join(word.capitalize() for word in agent_name.split('_'))
        
        results = {
            'created_files': [],
            'modified_files': [],
            'errors': []
        }
        
        # 1. Cria arquivo principal do agente
        agent_file = self.project_root / "agents" / f"{agent_name}_agent.py"
        agent_content = self._generate_agent_code(agent_name, agent_class)
        
        created = self.create_file(agent_file, agent_content)
        if created:
            results['created_files'].append(str(agent_file))
        else:
            results['errors'].append(f"Erro ao criar {agent_file}")
        
        # 2. Atualiza __init__.py dos agents
        init_file = self.project_root / "agents" / "__init__.py"
        if init_file.exists():
            updated = self._update_agents_init(init_file, agent_name, agent_class)
            if updated:
                results['modified_files'].append(str(init_file))
        
        # 3. Adiciona configuração do agente
        config_file = self.project_root / "config" / "agents_config.yaml"
        if config_file.exists():
            updated = self._update_agents_config(config_file, agent_name)
            if updated:
                results['modified_files'].append(str(config_file))
        
        # 4. Atualiza roteador de mensagens
        router_file = self.project_root / "core" / "message_router.py"
        if router_file.exists():
            updated = self._update_message_router(router_file, agent_name)
            if updated:
                results['modified_files'].append(str(router_file))
        
        # 5. Cria testes para o agente
        test_file = self.project_root / "tests" / f"test_{agent_name}_agent.py"
        test_content = self._generate_agent_test_code(agent_name, agent_class)
        
        created = self.create_file(test_file, test_content)
        if created:
            results['created_files'].append(str(test_file))
        
        # 6. Atualiza documentação
        docs_file = self.project_root / "docs" / "AGENTS.md"
        if docs_file.exists():
            updated = self._update_agents_docs(docs_file, agent_name)
            if updated:
                results['modified_files'].append(str(docs_file))
        
        return results
    
    def _generate_agent_code(self, agent_name: str, agent_class: str) -> str:
        """Gera código do agente"""
        template = f'''"""
{agent_class} Agent - Gerado automaticamente pelo Gemini Code
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base_agent import BaseAgent


class {agent_class}Agent(BaseAgent):
    """Agent gerado automaticamente"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "{agent_name}"
        self.description = "Agent responsável por processamento especializado"
        self.capabilities = ['analyze', 'execute', 'report']
    
    async def _handle_analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Processa análise"""
        self.logger.info(f"{{self.name}} analisando: {{content}}")
        
        try:
            analysis_type = content.get('type', 'general')
            target = content.get('target', '')
            
            # Implementa diferentes tipos de análise
            if analysis_type == 'code':
                result = await self._analyze_code(target)
            elif analysis_type == 'file':
                result = await self._analyze_file(target)
            elif analysis_type == 'project':
                result = await self._analyze_project(target)
            else:
                result = await self._analyze_general(target)
            
            # Atualiza métricas de performance
            self.performance_metrics['messages_processed'] += 1
            
            return {{
                'status': 'success',
                'type': 'analysis_result',
                'result': result,
                'agent': self.name,
                'timestamp': datetime.now().isoformat()
            }}
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {{e}}")
            return {{
                'status': 'error',
                'error': str(e),
                'agent': self.name
            }}
    
    async def _analyze_code(self, code: str) -> Dict[str, Any]:
        """Analisa código específico"""
        return {{
            'complexity': 'medium',
            'issues': [],
            'suggestions': ['Add type hints', 'Improve documentation'],
            'quality_score': 7.5
        }}
    
    async def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analisa arquivo específico"""
        from pathlib import Path
        path = Path(file_path)
        
        return {{
            'file_type': path.suffix,
            'size': path.stat().st_size if path.exists() else 0,
            'exists': path.exists(),
            'is_readable': path.is_file() if path.exists() else False
        }}
    
    async def _analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analisa projeto completo"""
        return {{
            'total_files': 50,
            'code_files': 35,
            'test_files': 10,
            'health_score': 8.2
        }}
    
    async def _analyze_general(self, target: str) -> Dict[str, Any]:
        """Análise geral"""
        return {{
            'type': 'general_analysis',
            'target': target,
            'status': 'completed'
        }}
    
    async def _handle_execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ação"""
        self.logger.info(f"{{self.name}} executando: {{content}}")
        
        # TODO: Implementar lógica de execução
        
        return {{
            'status': 'success',
            'agent': self.name,
            'action': 'execute',
            'result': {{
                'completed': True,
                'output': 'Execução realizada'
            }}
        }}
    
    async def _handle_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório"""
        self.logger.info(f"{{self.name}} gerando relatório")
        
        # TODO: Implementar geração de relatório
        
        return {{
            'status': 'success',
            'agent': self.name,
            'action': 'report',
            'result': {{
                'report': 'Relatório gerado',
                'timestamp': datetime.now().isoformat()
            }}
        }}
    
    async def _handle_default(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handler padrão para mensagens não reconhecidas"""
        self.logger.warning(f"{{self.name}} recebeu tipo de mensagem não reconhecido")
        
        return {{
            'status': 'error',
            'agent': self.name,
            'error': 'Tipo de mensagem não reconhecido'
        }}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do agente"""
        return {{
            'name': self.name,
            'type': self.__class__.__name__,
            'status': 'active',
            'uptime': self.get_uptime(),
            'messages_processed': self.messages_processed,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }}
    
    def get_capabilities(self) -> List[str]:
        """Retorna capacidades do agente"""
        return [
            'analyze',
            'execute',
            'report'
        ]
'''
        return template
    
    def _generate_agent_test_code(self, agent_name: str, agent_class: str) -> str:
        """Gera código de teste do agente"""
        template = f'''"""
Testes para {agent_class}Agent
"""
import pytest
import asyncio
from datetime import datetime

from agents.{agent_name}_agent import {agent_class}Agent


@pytest.fixture
def agent_config():
    """Configuração de teste para o agente"""
    return {{
        'name': '{agent_name}',
        'enabled': True,
        'log_level': 'DEBUG'
    }}


@pytest.fixture
def {agent_name}_agent(agent_config):
    """Instância do agente para testes"""
    return {agent_class}Agent(agent_config)


class Test{agent_class}Agent:
    """Testes para {agent_class}Agent"""
    
    def test_initialization(self, {agent_name}_agent):
        """Testa inicialização do agente"""
        assert {agent_name}_agent.name == '{agent_name}'
        assert {agent_name}_agent.description
        assert isinstance({agent_name}_agent.capabilities, list)
    
    @pytest.mark.asyncio
    async def test_analyze_message(self, {agent_name}_agent):
        """Testa processamento de mensagem de análise"""
        message = {{
            'type': 'analyze',
            'content': {{'data': 'test'}}
        }}
        
        result = await {agent_name}_agent.process_message(message)
        
        assert result['status'] == 'success'
        assert result['agent'] == '{agent_name}'
        assert result['action'] == 'analyze'
    
    @pytest.mark.asyncio
    async def test_execute_message(self, {agent_name}_agent):
        """Testa processamento de mensagem de execução"""
        message = {{
            'type': 'execute',
            'content': {{'command': 'test'}}
        }}
        
        result = await {agent_name}_agent.process_message(message)
        
        assert result['status'] == 'success'
        assert result['action'] == 'execute'
        assert result['result']['completed'] is True
    
    @pytest.mark.asyncio
    async def test_report_message(self, {agent_name}_agent):
        """Testa geração de relatório"""
        message = {{
            'type': 'report',
            'content': {{}}
        }}
        
        result = await {agent_name}_agent.process_message(message)
        
        assert result['status'] == 'success'
        assert result['action'] == 'report'
        assert 'timestamp' in result['result']
    
    @pytest.mark.asyncio
    async def test_unknown_message_type(self, {agent_name}_agent):
        """Testa mensagem de tipo desconhecido"""
        message = {{
            'type': 'unknown',
            'content': {{}}
        }}
        
        result = await {agent_name}_agent.process_message(message)
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    def test_get_status(self, {agent_name}_agent):
        """Testa obtenção de status"""
        status = {agent_name}_agent.get_status()
        
        assert status['name'] == '{agent_name}'
        assert status['type'] == '{agent_class}Agent'
        assert status['status'] == 'active'
    
    def test_get_capabilities(self, {agent_name}_agent):
        """Testa obtenção de capacidades"""
        capabilities = {agent_name}_agent.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert 'analyze' in capabilities
        assert 'execute' in capabilities
        assert 'report' in capabilities
'''
        return template
    
    def _update_agents_init(self, init_file: Path, agent_name: str, agent_class: str) -> bool:
        """Atualiza __init__.py dos agents"""
        try:
            content = self.read_file(init_file)
            
            # Adiciona import
            import_line = f"from .{agent_name}_agent import {agent_class}Agent"
            
            if import_line not in content:
                # Encontra última linha de import
                lines = content.split('\n')
                last_import_idx = 0
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('from .') and '_agent import' in line:
                        last_import_idx = i
                
                # Insere novo import
                lines.insert(last_import_idx + 1, import_line)
                
                # Atualiza __all__ se existir
                for i, line in enumerate(lines):
                    if line.strip().startswith('__all__'):
                        # Extrai lista atual
                        match = re.search(r'\[([^\]]*)\]', line)
                        if match:
                            items = match.group(1)
                            new_item = f'"{agent_class}Agent"'
                            if new_item not in items:
                                items = items.rstrip() + f', {new_item}'
                                lines[i] = f"__all__ = [{items}]"
                        break
                
                new_content = '\n'.join(lines)
                return self.write_file(init_file, new_content)
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar __init__.py: {e}")
            return False
    
    def _update_agents_config(self, config_file: Path, agent_name: str) -> bool:
        """Atualiza configuração dos agents"""
        try:
            content = self.read_file(config_file)
            config = yaml.safe_load(content)
            
            if 'agents' not in config:
                config['agents'] = {}
            
            if agent_name not in config['agents']:
                config['agents'][agent_name] = {
                    'enabled': True,
                    'class': f"{agent_name.title().replace('_', '')}Agent",
                    'module': f"agents.{agent_name}_agent",
                    'config': {
                        'max_retries': 3,
                        'timeout': 30,
                        'priority': 'normal'
                    }
                }
                
                new_content = yaml.dump(config, default_flow_style=False, allow_unicode=True)
                return self.write_file(config_file, new_content)
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar config: {e}")
            return False
    
    def _update_message_router(self, router_file: Path, agent_name: str) -> bool:
        """Atualiza roteador de mensagens"""
        try:
            content = self.read_file(router_file)
            
            # Adiciona rota para o novo agente
            route_pattern = f"'{agent_name}': ['{agent_name}_agent'],"
            
            if route_pattern not in content:
                # Encontra bloco de rotas
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'routes = {' in line or 'self.routes = {' in line:
                        # Encontra fim do dicionário
                        j = i + 1
                        while j < len(lines) and '}' not in lines[j]:
                            j += 1
                        
                        # Insere nova rota
                        lines.insert(j, f"            {route_pattern}")
                        break
                
                new_content = '\n'.join(lines)
                return self.write_file(router_file, new_content)
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar router: {e}")
            return False
    
    def _update_agents_docs(self, docs_file: Path, agent_name: str) -> bool:
        """Atualiza documentação dos agents"""
        try:
            content = self.read_file(docs_file)
            
            agent_doc = f"""
## {agent_name.title().replace('_', ' ')} Agent

**Arquivo**: `agents/{agent_name}_agent.py`

**Descrição**: Agente responsável por processamento especializado.

**Capacidades**:
- `analyze`: Análise de dados
- `execute`: Execução de comandos
- `report`: Geração de relatórios

**Configuração**:
```yaml
{agent_name}:
  enabled: true
  priority: normal
  timeout: 30
```

**Exemplo de uso**:
```python
message = {
    'type': 'analyze',
    'content': {'data': 'exemplo'}
}
result = await {agent_name}_agent.process_message(message)
```
"""
            
            if agent_name not in content:
                content += agent_doc
                return self.write_file(docs_file, content)
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar docs: {e}")
            return False
    
    def create_file(self, file_path: Path, content: str, backup: bool = True) -> bool:
        """Cria novo arquivo com validação e tratamento de erros aprimorado"""
        try:
            file_path = Path(file_path).resolve()
            self.logger.info(f"Creating file: {file_path}")
            
            # Validações
            if not content:
                self.logger.warning(f"Empty content provided for {file_path}")
                # Permite conteúdo vazio mas avisa
            
            # Verifica se o caminho é seguro (não sai do projeto)
            try:
                file_path.relative_to(self.project_root)
            except ValueError:
                # Permite criar fora do projeto mas avisa
                self.logger.warning(f"Creating file outside project root: {file_path}")
            
            # Verifica se já existe
            if file_path.exists():
                if backup:
                    self._backup_file(file_path)
                self.logger.info(f"File {file_path} already exists. Overwriting...")
                print(f"⚠️  Arquivo {file_path} já existe. Sobrescrevendo...")
            
            # Cria diretórios se necessário
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created parent directories for {file_path}")
            except PermissionError:
                self.logger.error(f"Permission denied creating directories for {file_path}")
                print(f"❌ Sem permissão para criar diretório: {file_path.parent}")
                return False
            except Exception as e:
                self.logger.error(f"Failed to create parent directories: {e}", exc_info=True)
                print(f"❌ Erro ao criar diretórios: {e}")
                return False
            
            # Escreve arquivo
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.debug(f"File written successfully: {file_path} ({len(content)} bytes)")
            except PermissionError:
                self.logger.error(f"Permission denied writing to {file_path}")
                print(f"❌ Sem permissão para escrever em: {file_path}")
                return False
            except UnicodeEncodeError as e:
                self.logger.error(f"Encoding error writing {file_path}: {e}")
                print(f"❌ Erro de codificação ao escrever {file_path}")
                return False
            
            # Verifica se foi criado com sucesso
            if not file_path.exists():
                self.logger.error(f"File not found after creation: {file_path}")
                print(f"❌ Arquivo não foi criado: {file_path}")
                return False
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='create',
                path=str(file_path),
                content=content
            ))
            
            self.logger.info(f"File created successfully: {file_path}")
            print(f"✅ Arquivo criado: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Unexpected error creating {file_path}: {e}", exc_info=True)
            print(f"❌ Erro ao criar arquivo {file_path}: {e}")
            return False
    
    def read_file(self, file_path: Path) -> str:
        """Lê conteúdo de arquivo com tratamento de erros"""
        try:
            file_path = Path(file_path).resolve()
            self.logger.debug(f"Reading file: {file_path}")
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            if not file_path.is_file():
                raise ValueError(f"Not a file: {file_path}")
            
            # Tenta diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        self.logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                        return content
                except UnicodeDecodeError:
                    continue
                    
            # Se falhou com todos encodings
            self.logger.error(f"Could not decode {file_path} with any encoding")
            raise UnicodeDecodeError("Unable to decode file with available encodings")
            
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}", exc_info=True)
            raise
    
    def write_file(self, file_path: Path, content: str, backup: bool = True) -> bool:
        """Escreve em arquivo existente com validação"""
        try:
            file_path = Path(file_path).resolve()
            self.logger.info(f"Writing to file: {file_path}")
            
            # Verifica se arquivo existe
            if not file_path.exists():
                self.logger.warning(f"File does not exist, creating new: {file_path}")
                return self.create_file(file_path, content, backup=False)
            
            # Backup se necessário
            if backup:
                if not self._backup_file(file_path):
                    self.logger.warning("Backup failed but continuing with write")
            
            # Lê conteúdo atual para comparar
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                    
                if old_content == content:
                    self.logger.info(f"No changes needed for {file_path}")
                    print(f"ℹ️ Arquivo {file_path} já está atualizado")
                    return True
            except Exception as e:
                self.logger.warning(f"Could not read existing file for comparison: {e}")
            
            # Escreve novo conteúdo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='modify',
                path=str(file_path),
                content=content
            ))
            
            self.logger.info(f"File updated successfully: {file_path}")
            print(f"✅ Arquivo atualizado: {file_path}")
            return True
            
        except PermissionError:
            self.logger.error(f"Permission denied writing to {file_path}")
            print(f"❌ Sem permissão para escrever em: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error writing to {file_path}: {e}", exc_info=True)
            print(f"❌ Erro ao escrever arquivo {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: Path, backup: bool = True) -> bool:
        """Deleta arquivo"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"⚠️  Arquivo {file_path} não existe")
                return False
            
            if backup:
                self._backup_file(file_path)
            
            file_path.unlink()
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='delete',
                path=str(file_path)
            ))
            
            print(f"✅ Arquivo deletado: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao deletar arquivo {file_path}: {e}")
            return False
    
    def move_file(self, src_path: Path, dst_path: Path, backup: bool = True) -> bool:
        """Move arquivo"""
        try:
            src_path = Path(src_path)
            dst_path = Path(dst_path)
            
            if not src_path.exists():
                print(f"⚠️  Arquivo origem {src_path} não existe")
                return False
            
            if backup and dst_path.exists():
                self._backup_file(dst_path)
            
            # Cria diretório destino se necessário
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='move',
                path=str(dst_path),
                old_path=str(src_path)
            ))
            
            print(f"✅ Arquivo movido: {src_path} → {dst_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao mover arquivo: {e}")
            return False
    
    def rename_file(self, file_path: Path, new_name: str) -> bool:
        """Renomeia arquivo"""
        file_path = Path(file_path)
        new_path = file_path.parent / new_name
        return self.move_file(file_path, new_path)
    
    def _backup_file(self, file_path: Path):
        """Cria backup de arquivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{file_path.name}.{timestamp}.bak"
            
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(file_path), str(backup_path))
            
            print(f"📦 Backup criado: {backup_path}")
            
        except Exception as e:
            print(f"⚠️  Erro ao criar backup: {e}")
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Método público para criar backup de arquivo."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{file_path_obj.name}.{timestamp}.bak"
            
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(file_path_obj), str(backup_path))
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def smart_file_operations(self, command: str) -> Dict[str, Any]:
        """Executa operações de arquivo baseadas em comando natural"""
        results = {
            'operation': 'unknown',
            'success': False,
            'details': {}
        }
        
        command_lower = command.lower()
        
        # Detecta tipo de operação
        if any(word in command_lower for word in ['cria', 'criar', 'novo']):
            results['operation'] = 'create'
            # TODO: Extrair nome e tipo do arquivo
            
        elif any(word in command_lower for word in ['deleta', 'deletar', 'remove', 'remover']):
            results['operation'] = 'delete'
            # TODO: Extrair arquivo a deletar
            
        elif any(word in command_lower for word in ['move', 'mover']):
            results['operation'] = 'move'
            # TODO: Extrair origem e destino
            
        elif any(word in command_lower for word in ['renomeia', 'renomear', 'muda nome']):
            results['operation'] = 'rename'
            # TODO: Extrair arquivo e novo nome
            
        elif any(word in command_lower for word in ['organiza', 'organizar']):
            results['operation'] = 'organize'
            results = self.organize_files()
        
        return results
    
    def organize_files(self) -> Dict[str, Any]:
        """Organiza arquivos do projeto"""
        results = {
            'operation': 'organize',
            'moved_files': [],
            'created_dirs': [],
            'suggestions': []
        }
        
        # Analisa estrutura atual
        # TODO: Implementar análise de estrutura do projeto
        # if not self.project_manager.structure:
        #     self.project_manager.scan_project()
        
        # Sugere organização
        # TODO: Implementar análise de arquivos
        # for file_path, file_info in self.project_manager.structure.files.items():
        #     path = Path(file_path)
        #     
        #     # Regras de organização
        #     if path.suffix == '.test.py' or 'test_' in path.name:
        #         suggested_path = self.project_root / 'tests' / path.name
        #         if path.parent != suggested_path.parent:
        #             results['suggestions'].append({
        #                 'file': file_path,
        #                 'current': str(path.parent),
        #                 'suggested': str(suggested_path.parent),
        #                 'reason': 'Arquivo de teste deve ficar em /tests'
        #             })
        #     
        #     elif path.suffix in ['.md', '.rst', '.txt'] and 'README' not in path.name:
        #         suggested_path = self.project_root / 'docs' / path.name
        #         if path.parent != suggested_path.parent:
        #             results['suggestions'].append({
        #                 'file': file_path,
        #                 'current': str(path.parent),
        #                 'suggested': str(suggested_path.parent),
        #                 'reason': 'Documentação deve ficar em /docs'
        #             })
        
        return results
    
    def get_file_history(self, file_path: str) -> List[FileOperation]:
        """Obtém histórico de operações de um arquivo"""
        return [op for op in self.operations_history if op.path == file_path]
    
    def undo_last_operation(self) -> bool:
        """Desfaz última operação"""
        if not self.operations_history:
            print("⚠️  Nenhuma operação para desfazer")
            return False
        
        last_op = self.operations_history[-1]
        
        # TODO: Implementar lógica de undo para cada tipo de operação
        
        return False
    
    def create_from_template(self, template_name: str, target_path: Path, **kwargs) -> bool:
        """Cria arquivo a partir de template"""
        template_file = self.templates_dir / f"{template_name}.template"
        
        if not template_file.exists():
            print(f"⚠️  Template {template_name} não encontrado")
            return False
        
        try:
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            # Substitui variáveis no template
            for key, value in kwargs.items():
                template_content = template_content.replace(f"{{{key}}}", str(value))
            
            return self.create_file(target_path, template_content)
            
        except Exception as e:
            print(f"❌ Erro ao criar de template: {e}")
            return False