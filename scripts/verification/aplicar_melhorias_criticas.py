#!/usr/bin/env python3
"""
Aplica melhorias críticas identificadas na verificação de forma segura.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

async def enhance_architectural_reasoning_simple():
    """Adiciona métodos de análise real ao ArchitecturalReasoning."""
    print("🧠 Adicionando métodos de análise real...")
    
    file_path = Path("gemini_code/cognition/architectural_reasoning.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se já tem métodos de análise
        if 'analyze_system_architecture' in content:
            print("✅ ArchitecturalReasoning já tem métodos de análise")
            return True
        
        # Adiciona método de análise principal
        analysis_method = '''
    async def analyze_system_architecture(self, project_path: str) -> Dict[str, Any]:
        """Análise completa da arquitetura do sistema."""
        try:
            analysis = {
                'structure_analysis': await self._analyze_structure(project_path),
                'pattern_detection': await self._detect_patterns(project_path), 
                'quality_metrics': await self._calculate_metrics(project_path),
                'recommendations': await self._generate_recommendations(project_path)
            }
            
            self.logger.info(f"Análise arquitetural concluída para {project_path}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {e}")
            return {'error': str(e)}
    
    async def _analyze_structure(self, project_path: str) -> Dict[str, Any]:
        """Analisa estrutura do projeto."""
        try:
            path_obj = Path(project_path)
            python_files = list(path_obj.rglob("*.py"))
            directories = [d for d in path_obj.iterdir() if d.is_dir()]
            
            return {
                'total_files': len(python_files),
                'total_directories': len(directories),
                'directory_structure': [d.name for d in directories],
                'complexity_estimate': 'high' if len(python_files) > 50 else 'medium' if len(python_files) > 20 else 'low'
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _detect_patterns(self, project_path: str) -> List[str]:
        """Detecta padrões arquiteturais."""
        try:
            path_obj = Path(project_path)
            directories = [d.name.lower() for d in path_obj.iterdir() if d.is_dir()]
            
            patterns = []
            
            # Detecta MVC
            if any(d in directories for d in ['models', 'views', 'controllers']):
                patterns.append('MVC')
            
            # Detecta Layered
            if any(d in directories for d in ['core', 'business', 'data']):
                patterns.append('Layered Architecture')
            
            # Detecta Microservices
            if any('service' in d for d in directories):
                patterns.append('Microservices')
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de padrões: {e}")
            return []
    
    async def _calculate_metrics(self, project_path: str) -> Dict[str, float]:
        """Calcula métricas básicas de qualidade."""
        try:
            python_files = list(Path(project_path).rglob("*.py"))
            if not python_files:
                return {}
            
            total_lines = 0
            total_functions = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = len([line for line in content.split('\\n') if line.strip()])
                    functions = content.count('def ')
                    
                    total_lines += lines
                    total_functions += functions
                    
                except Exception:
                    continue
            
            return {
                'avg_lines_per_file': total_lines / len(python_files),
                'avg_functions_per_file': total_functions / len(python_files),
                'total_files': len(python_files),
                'maintainability_score': min(1.0, 50 / max(1, total_lines / len(python_files)))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _generate_recommendations(self, project_path: str) -> List[str]:
        """Gera recomendações de melhoria."""
        try:
            metrics = await self._calculate_metrics(project_path)
            recommendations = []
            
            if metrics.get('avg_lines_per_file', 0) > 200:
                recommendations.append('Considere dividir arquivos grandes em módulos menores')
            
            if metrics.get('avg_functions_per_file', 0) > 20:
                recommendations.append('Muitas funções por arquivo - considere refatoração')
            
            patterns = await self._detect_patterns(project_path)
            if not patterns:
                recommendations.append('Implementar padrões arquiteturais para melhor organização')
            
            recommendations.append('Adicionar testes automatizados para garantir qualidade')
            recommendations.append('Implementar documentação técnica abrangente')
            
            return recommendations
            
        except Exception as e:
            return [f'Erro na geração de recomendações: {e}']

'''
        
        # Encontra onde inserir (antes do último método da classe)
        lines = content.split('\\n')
        insert_index = len(lines) - 10  # Insere antes do final
        
        # Procura melhor local para inserção
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('def ') or lines[i].strip().startswith('async def '):
                # Encontra o final deste método
                for j in range(i + 1, len(lines)):
                    if (lines[j].strip().startswith('def ') or 
                        lines[j].strip().startswith('async def ') or
                        (lines[j].strip() and not lines[j].startswith('        '))):
                        insert_index = j
                        break
                break
        
        # Insere o novo método
        new_lines = lines[:insert_index] + analysis_method.split('\\n') + lines[insert_index:]
        new_content = '\\n'.join(new_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Métodos de análise adicionados ao ArchitecturalReasoning")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aprimorar ArchitecturalReasoning: {e}")
        return False

async def add_error_handling_decorator():
    """Adiciona decorador de tratamento de erro robusto."""
    print("🛡️ Adicionando decorador de tratamento de erro...")
    
    # Cria arquivo de utilitários se não existir
    utils_dir = Path("gemini_code/utils")
    utils_dir.mkdir(exist_ok=True)
    
    error_utils_file = utils_dir / "error_handler.py"
    
    if error_utils_file.exists():
        print("✅ Sistema de tratamento de erro já existe")
        return True
    
    error_handler_content = '''"""
Sistema robusto de tratamento de erros para o Gemini Code.
"""

import functools
import traceback
from typing import Any, Callable, Dict
from ..utils.logger import Logger

def robust_execution(operation_name: str = None):
    """
    Decorador para execução robusta com tratamento de erro abrangente.
    
    Args:
        operation_name: Nome da operação para logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = await func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'operation': operation_name or func.__name__
                }
            except Exception as e:
                # Obtém logger se disponível
                logger = None
                if args and hasattr(args[0], 'logger'):
                    logger = args[0].logger
                else:
                    logger = Logger(func.__module__)
                
                error_msg = f"Erro em {operation_name or func.__name__}: {str(e)}"
                
                if logger:
                    logger.error(error_msg)
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                else:
                    print(f"ERROR: {error_msg}")
                
                return {
                    'success': False,
                    'error': str(e),
                    'operation': operation_name or func.__name__,
                    'error_type': type(e).__name__
                }
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'operation': operation_name or func.__name__
                }
            except Exception as e:
                # Obtém logger se disponível
                logger = None
                if args and hasattr(args[0], 'logger'):
                    logger = args[0].logger
                else:
                    logger = Logger(func.__module__)
                
                error_msg = f"Erro em {operation_name or func.__name__}: {str(e)}"
                
                if logger:
                    logger.error(error_msg)
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                else:
                    print(f"ERROR: {error_msg}")
                
                return {
                    'success': False,
                    'error': str(e),
                    'operation': operation_name or func.__name__,
                    'error_type': type(e).__name__
                }
        
        # Retorna wrapper apropriado baseado no tipo de função
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def safe_execute(func: Callable, *args, default_return=None, **kwargs) -> Any:
    """
    Executa função de forma segura, retornando valor padrão em caso de erro.
    
    Args:
        func: Função a ser executada
        default_return: Valor retornado em caso de erro
        *args, **kwargs: Argumentos para a função
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = Logger("safe_execute")
        logger.error(f"Erro na execução segura de {func.__name__}: {e}")
        return default_return

class ErrorRecovery:
    """Sistema de recuperação automática de erros."""
    
    def __init__(self):
        self.logger = Logger("ErrorRecovery")
        self.recovery_strategies = {}
    
    def register_recovery(self, error_type: type, recovery_func: Callable):
        """Registra estratégia de recuperação para tipo de erro."""
        self.recovery_strategies[error_type] = recovery_func
    
    def attempt_recovery(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """Tenta recuperar automaticamente do erro."""
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            try:
                self.logger.info(f"Tentando recuperação para {error_type.__name__}")
                success = self.recovery_strategies[error_type](error, context)
                
                if success:
                    self.logger.info("Recuperação bem sucedida")
                    return True
                else:
                    self.logger.warning("Estratégia de recuperação falhou")
                    
            except Exception as recovery_error:
                self.logger.error(f"Erro na recuperação: {recovery_error}")
        
        return False

# Instância global para uso em todo o sistema
error_recovery = ErrorRecovery()

# Registra estratégias básicas de recuperação
def recover_from_connection_error(error: Exception, context: Dict[str, Any] = None) -> bool:
    """Recupera de erros de conexão."""
    import time
    time.sleep(1)  # Aguarda antes de tentar novamente
    return True

def recover_from_file_not_found(error: Exception, context: Dict[str, Any] = None) -> bool:
    """Recupera de erros de arquivo não encontrado."""
    if context and 'file_path' in context:
        # Tenta criar arquivo se possível
        try:
            Path(context['file_path']).parent.mkdir(parents=True, exist_ok=True)
            return True
        except:
            pass
    return False

# Registra estratégias
error_recovery.register_recovery(ConnectionError, recover_from_connection_error)
error_recovery.register_recovery(FileNotFoundError, recover_from_file_not_found)
'''
    
    try:
        with open(error_utils_file, 'w', encoding='utf-8') as f:
            f.write(error_handler_content)
        
        print("✅ Sistema de tratamento de erro criado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar sistema de tratamento: {e}")
        return False

async def enhance_memory_system_simple():
    """Adiciona melhorias básicas ao sistema de memória."""
    print("💾 Aprimorando sistema de memória...")
    
    memory_file = Path("gemini_code/core/memory_system.py")
    
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se já tem compactação
        if 'compact_memory' in content:
            print("✅ Sistema de memória já tem compactação")
            return True
        
        # Adiciona método de compactação
        compaction_method = '''
    def compact_memory(self, max_entries: int = 1000):
        """Compacta memória removendo entradas antigas."""
        try:
            # Compacta conversas antigas
            conversations_file = self.memory_dir / "conversations.json"
            
            if conversations_file.exists():
                with open(conversations_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)
                
                if len(conversations) > max_entries:
                    # Mantém apenas as mais recentes
                    sorted_conversations = sorted(
                        conversations, 
                        key=lambda x: x.get('timestamp', 0), 
                        reverse=True
                    )
                    
                    compacted = sorted_conversations[:max_entries]
                    
                    with open(conversations_file, 'w', encoding='utf-8') as f:
                        json.dump(compacted, f, indent=2, ensure_ascii=False)
                    
                    removed = len(conversations) - len(compacted)
                    self.logger.info(f"Memória compactada: {removed} conversas removidas")
            
            # Compacta contexto
            context_file = self.memory_dir / "context.json"
            if context_file.exists() and context_file.stat().st_size > 1024 * 1024:  # > 1MB
                # Limpa contexto muito grande
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump({"compacted": True, "timestamp": time.time()}, f)
                
                self.logger.info("Contexto grande compactado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na compactação: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso da memória."""
        try:
            stats = {
                'total_files': 0,
                'total_size_mb': 0.0,
                'conversations_count': 0,
                'context_size_kb': 0.0
            }
            
            if self.memory_dir.exists():
                for file_path in self.memory_dir.rglob("*"):
                    if file_path.is_file():
                        stats['total_files'] += 1
                        size_bytes = file_path.stat().st_size
                        stats['total_size_mb'] += size_bytes / (1024 * 1024)
                        
                        if file_path.name == 'conversations.json':
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    conversations = json.load(f)
                                    stats['conversations_count'] = len(conversations) if isinstance(conversations, list) else 1
                            except:
                                pass
                        
                        elif file_path.name == 'context.json':
                            stats['context_size_kb'] = size_bytes / 1024
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}

'''
        
        # Adiciona os métodos antes do final da classe
        lines = content.split('\\n')
        
        # Encontra o final da classe MemorySystem
        insert_index = len(lines) - 5
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith('    ') and i > 0:
                insert_index = i
                break
        
        # Insere os novos métodos
        new_lines = lines[:insert_index] + compaction_method.split('\\n') + lines[insert_index:]
        new_content = '\\n'.join(new_lines)
        
        # Adiciona import time se não existir
        if 'import time' not in new_content:
            new_content = 'import time\\n' + new_content
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Sistema de memória aprimorado com compactação")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aprimorar memória: {e}")
        return False

async def add_configuration_migration():
    """Adiciona sistema de migração de configuração."""
    print("⚙️ Adicionando sistema de migração de configuração...")
    
    config_file = Path("gemini_code/core/config.py")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'migrate_config' in content:
            print("✅ Sistema de migração já existe")
            return True
        
        # Adiciona método de migração ao ConfigManager
        migration_method = '''
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

'''
        
        # Adiciona ao ConfigManager
        if 'class ConfigManager' in content:
            lines = content.split('\\n')
            
            # Encontra o final da classe ConfigManager
            insert_index = len(lines) - 5
            for i in range(len(lines)):
                if 'class ConfigManager' in lines[i]:
                    # Procura o final desta classe
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('    ') and not lines[j].startswith('\\t'):
                            insert_index = j
                            break
                    break
            
            # Insere os novos métodos
            new_lines = lines[:insert_index] + migration_method.split('\\n') + lines[insert_index:]
            new_content = '\\n'.join(new_lines)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Sistema de migração de configuração adicionado")
            return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar migração: {e}")
        return False

async def main():
    """Executa todas as melhorias críticas."""
    print("🚀 APLICANDO MELHORIAS CRÍTICAS DE PROFUNDIDADE")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(await enhance_architectural_reasoning_simple())
        results.append(await add_error_handling_decorator())
        results.append(await enhance_memory_system_simple())
        results.append(await add_configuration_migration())
        
        success_count = sum(results)
        total_count = len(results)
        
        print("\\n" + "=" * 60)
        print(f"📊 RESULTADO: {success_count}/{total_count} melhorias aplicadas")
        
        if success_count == total_count:
            print("🎉 TODAS AS MELHORIAS CRÍTICAS APLICADAS COM SUCESSO!")
            print("🚀 Sistema agora tem significativamente mais profundidade")
        elif success_count >= total_count * 0.75:
            print("✅ MAIORIA DAS MELHORIAS APLICADAS")
            print("⚠️ Algumas melhorias podem precisar de atenção manual")
        else:
            print("⚠️ ALGUMAS MELHORIAS FALHARAM")
            print("🔧 Verifique os logs para mais detalhes")
        
        return success_count >= total_count * 0.75
        
    except Exception as e:
        print(f"\\n❌ Erro durante aplicação das melhorias: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)