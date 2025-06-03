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
    
    def __init__(self, gemini_client: GeminiClient, project_root: Optional[Path] = None):
        self.gemini_client = gemini_client
        self.project_root = project_root or Path.cwd()
        self.operations_history: List[FileOperation] = []
        self.backup_dir = self.project_root / ".gemini_code" / "backups"
        self.templates_dir = Path(__file__).parent.parent / "templates"
        
        # Inicializa diretórios
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_templates_dir()
    
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
    """
    Agente {agent_class} responsável por tarefas específicas
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "{agent_name}"
        self.description = "Agente {agent_class} para processamento especializado"
        self.capabilities = []
        self._initialize()
    
    def _initialize(self):
        """Inicializa recursos do agente"""
        self.logger.info(f"Inicializando {agent_class}Agent")
        # TODO: Adicionar inicialização específica
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Processa mensagem recebida"""
        self.logger.info(f"{self.name} processando mensagem: {{message.get('type')}}")
        
        message_type = message.get('type')
        content = message.get('content', {{}})
        
        # Roteamento de mensagens
        handlers = {{
            'analyze': self._handle_analyze,
            'execute': self._handle_execute,
            'report': self._handle_report,
        }}
        
        handler = handlers.get(message_type, self._handle_default)
        return await handler(content)
    
    async def _handle_analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Processa análise"""
        self.logger.info(f"{self.name} analisando: {{content}}")
        
        # TODO: Implementar lógica de análise
        
        return {{
            'status': 'success',
            'agent': self.name,
            'action': 'analyze',
            'result': {{
                'summary': 'Análise concluída',
                'details': content
            }}
        }}
    
    async def _handle_execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ação"""
        self.logger.info(f"{self.name} executando: {{content}}")
        
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
        self.logger.info(f"{self.name} gerando relatório")
        
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
        self.logger.warning(f"{self.name} recebeu tipo de mensagem não reconhecido")
        
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
message = {{
    'type': 'analyze',
    'content': {{'data': 'exemplo'}}
}}
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
        """Cria novo arquivo"""
        try:
            file_path = Path(file_path)
            
            # Verifica se já existe
            if file_path.exists():
                if backup:
                    self._backup_file(file_path)
                print(f"⚠️  Arquivo {file_path} já existe. Sobrescrevendo...")
            
            # Cria diretórios se necessário
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escreve arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='create',
                path=str(file_path),
                content=content
            ))
            
            print(f"✅ Arquivo criado: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar arquivo {file_path}: {e}")
            return False
    
    def read_file(self, file_path: Path) -> str:
        """Lê conteúdo de arquivo"""
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, file_path: Path, content: str, backup: bool = True) -> bool:
        """Escreve em arquivo existente"""
        try:
            file_path = Path(file_path)
            
            if backup and file_path.exists():
                self._backup_file(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Registra operação
            self.operations_history.append(FileOperation(
                type='modify',
                path=str(file_path),
                content=content
            ))
            
            return True
            
        except Exception as e:
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
        if not self.project_manager.structure:
            self.project_manager.scan_project()
        
        # Sugere organização
        for file_path, file_info in self.project_manager.structure.files.items():
            path = Path(file_path)
            
            # Regras de organização
            if path.suffix == '.test.py' or 'test_' in path.name:
                suggested_path = self.project_root / 'tests' / path.name
                if path.parent != suggested_path.parent:
                    results['suggestions'].append({
                        'file': file_path,
                        'current': str(path.parent),
                        'suggested': str(suggested_path.parent),
                        'reason': 'Arquivo de teste deve ficar em /tests'
                    })
            
            elif path.suffix in ['.md', '.rst', '.txt'] and 'README' not in path.name:
                suggested_path = self.project_root / 'docs' / path.name
                if path.parent != suggested_path.parent:
                    results['suggestions'].append({
                        'file': file_path,
                        'current': str(path.parent),
                        'suggested': str(suggested_path.parent),
                        'reason': 'Documentação deve ficar em /docs'
                    })
        
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
                template_content = template_content.replace(f"{{{{{key}}}}}", str(value))
            
            return self.create_file(target_path, template_content)
            
        except Exception as e:
            print(f"❌ Erro ao criar de template: {e}")
            return False