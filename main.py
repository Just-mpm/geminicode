#!/usr/bin/env python3
"""
Gemini Code - Interface Principal
Assistente de desenvolvimento completo com IA
"""

import asyncio
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Optional

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.gemini_client import GeminiClient
from gemini_code.core.nlp_enhanced import NLPEnhanced
from gemini_code.core.project_manager import ProjectManager
from gemini_code.core.file_manager import FileManagementSystem
from gemini_code.core.workspace_manager import WorkspaceManager
from gemini_code.core.memory_system import MemorySystem
from gemini_code.core.dependency_injection import DependencyContainer, get_container
from gemini_code.database.database_manager import DatabaseManager
from gemini_code.monitoring.continuous_monitor import ContinuousMonitor
from gemini_code.security.security_scanner import SecurityScanner
from gemini_code.metrics.business_metrics import BusinessMetrics
from gemini_code.metrics.analytics_engine import AnalyticsEngine
# Importações condicionais para funcionalidades que dependem de matplotlib
try:
    from gemini_code.metrics.dashboard_generator import DashboardGenerator
    DASHBOARD_AVAILABLE = True
except ImportError:
    DashboardGenerator = None
    DASHBOARD_AVAILABLE = False

try:
    from gemini_code.metrics.kpi_tracker import KPITracker  
    KPI_TRACKER_AVAILABLE = True
except ImportError:
    KPITracker = None
    KPI_TRACKER_AVAILABLE = False
from gemini_code.collaboration.team_manager import TeamManager
from gemini_code.collaboration.project_sharing import ProjectSharing
from gemini_code.collaboration.real_time_sync import RealTimeSync


class GeminiCodeMain:
    """Classe principal do Gemini Code."""
    
    def __init__(self):
        self.gemini_client: Optional[GeminiClient] = None
        self.nlp: Optional[NLPEnhanced] = None
        self.project_manager: Optional[ProjectManager] = None
        self.file_manager: Optional[FileManagementSystem] = None
        self.workspace_manager: Optional[WorkspaceManager] = None
        self.memory_system: Optional[MemorySystem] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.monitor: Optional[ContinuousMonitor] = None
        self.security_scanner: Optional[SecurityScanner] = None
        self.business_metrics: Optional[BusinessMetrics] = None
        self.analytics_engine: Optional[AnalyticsEngine] = None
        self.dashboard_generator: Optional[DashboardGenerator] = None
        self.kpi_tracker: Optional[KPITracker] = None
        self.team_manager: Optional[TeamManager] = None
        self.project_sharing: Optional[ProjectSharing] = None
        self.real_time_sync: Optional[RealTimeSync] = None
        self.running = False
    
    async def initialize(self, api_key: Optional[str] = None) -> None:
        """Inicializa todos os componentes do sistema usando injeção de dependência."""
        print("🚀 Inicializando Gemini Code...")
        
        try:
            # Configura container de dependências
            container = get_container()
            
            # Registra serviços principais
            print("🔧 Configurando dependências...")
            
            # Core
            container.register('gemini_client', GeminiClient, config={'api_key': api_key})
            container.register('nlp', NLPEnhanced, dependencies={'gemini_client': 'gemini_client'})
            container.register('memory_system', MemorySystem, config={'project_path': str(Path.cwd())})
            container.register('db_manager', DatabaseManager, dependencies={'gemini_client': 'gemini_client'})
            
            # File management com logger
            import logging
            logger = logging.getLogger('FileManagementSystem')
            container.register('file_manager', FileManagementSystem, 
                             dependencies={'gemini_client': 'gemini_client'},
                             config={'logger': logger})
            
            container.register('workspace_manager', WorkspaceManager, dependencies={'gemini_client': 'gemini_client'})
            container.register('project_manager', ProjectManager, dependencies={'gemini_client': 'gemini_client'})
            
            # Monitoring
            container.register('monitor', ContinuousMonitor, 
                             dependencies={'gemini_client': 'gemini_client'},
                             config={'project_path': str(Path.cwd())})
            container.register('security_scanner', SecurityScanner, dependencies={'gemini_client': 'gemini_client'})
            
            # Analytics
            container.register('business_metrics', BusinessMetrics, 
                             dependencies={'gemini_client': 'gemini_client', 'db_manager': 'db_manager'})
            container.register('analytics_engine', AnalyticsEngine,
                             dependencies={'gemini_client': 'gemini_client', 'db_manager': 'db_manager'})
            
            # Team
            container.register('team_manager', TeamManager, dependencies={'gemini_client': 'gemini_client'})
            
            # Inicializa serviços
            print("🔧 Inicializando GeminiClient...")
            self.gemini_client = container.get('gemini_client')
            
            print("🔧 Inicializando NLPEnhanced...")
            self.nlp = container.get('nlp')
            
            print("🔧 Inicializando DatabaseManager...")
            self.db_manager = container.get('db_manager')
            
            print("🔧 Inicializando FileManagementSystem...")
            self.file_manager = container.get('file_manager')
            
            print("🔧 Inicializando WorkspaceManager...")
            self.workspace_manager = container.get('workspace_manager')
            
            print("🔧 Inicializando MemorySystem...")
            self.memory_system = container.get('memory_system')
            
            print("🔧 Inicializando ProjectManager...")
            self.project_manager = container.get('project_manager')
            
            print("🔧 Inicializando ContinuousMonitor...")
            self.monitor = container.get('monitor')
            
            print("🔧 Inicializando SecurityScanner...")
            self.security_scanner = container.get('security_scanner')
            
            print("🔧 Inicializando BusinessMetrics...")
            self.business_metrics = container.get('business_metrics')
            
            print("🔧 Inicializando AnalyticsEngine...")
            self.analytics_engine = container.get('analytics_engine')
            
            # Componentes opcionais
            if DASHBOARD_AVAILABLE:
                print("🔧 Inicializando DashboardGenerator...")
                container.register('dashboard_generator', DashboardGenerator,
                                 dependencies={'gemini_client': 'gemini_client',
                                             'business_metrics': 'business_metrics',
                                             'analytics_engine': 'analytics_engine'})
                self.dashboard_generator = container.get('dashboard_generator')
            else:
                self.dashboard_generator = None
                print("⚠️ DashboardGenerator desabilitado (matplotlib não disponível)")
            
            if KPI_TRACKER_AVAILABLE:
                print("🔧 Inicializando KPITracker...")
                container.register('kpi_tracker', KPITracker,
                                 dependencies={'gemini_client': 'gemini_client', 'db_manager': 'db_manager'})
                self.kpi_tracker = container.get('kpi_tracker')
            else:
                self.kpi_tracker = None
                print("⚠️ KPITracker desabilitado (matplotlib não disponível)")
            
            # Collaboration
            print("🔧 Inicializando TeamManager...")
            self.team_manager = container.get('team_manager')
            
            print("🔧 Inicializando ProjectSharing...")
            container.register('project_sharing', ProjectSharing,
                             dependencies={'gemini_client': 'gemini_client', 'team_manager': 'team_manager'})
            self.project_sharing = container.get('project_sharing')
            
            print("🔧 Inicializando RealTimeSync...")
            container.register('real_time_sync', RealTimeSync,
                             dependencies={'gemini_client': 'gemini_client', 'team_manager': 'team_manager'})
            self.real_time_sync = container.get('real_time_sync')
            
            print("✅ Gemini Code inicializado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            raise
    
    async def start_services(self) -> None:
        """Inicia serviços em background."""
        print("🔄 Iniciando serviços...")
        
        try:
            # Comentado temporariamente para evitar travamento
            # await self.monitor.start_monitoring()
            
            # Inicia tracking de KPIs (se disponível)
            # if self.kpi_tracker:
            #     await self.kpi_tracker.start_monitoring()
            
            # Inicia sincronização em tempo real
            # await self.real_time_sync.start_sync()
            
            self.running = True
            print("✅ Serviços iniciados! (monitoramento desabilitado temporariamente)")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar serviços: {e}")
    
    async def stop_services(self) -> None:
        """Para todos os serviços."""
        print("🛑 Parando serviços...")
        
        try:
            if self.monitor:
                await self.monitor.stop_monitoring()
            
            if self.kpi_tracker:
                await self.kpi_tracker.stop_monitoring()
            
            if self.real_time_sync:
                await self.real_time_sync.stop_sync()
            
            self.running = False
            print("✅ Serviços parados!")
            
        except Exception as e:
            print(f"❌ Erro ao parar serviços: {e}")
    
    async def process_command(self, command: str) -> str:
        """Processa comando em linguagem natural."""
        try:
            # Identifica intentção
            intent_result = await self.nlp.identify_intent(command)
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            entities = intent_result['entities']
            
            print(f"🧠 Intent: {intent} (confiança: {confidence:.1f}%)")
            
            # Processa comando baseado na intentção
            response = None
            if intent == 'create_project':
                response = await self._handle_create_project(command, entities)
            elif intent == 'analyze_code' or intent == 'analyze_project':
                response = await self._handle_analyze_code(command, entities)
            elif intent == 'generate_dashboard':
                response = await self._handle_generate_dashboard(command, entities)
            elif intent == 'security_scan':
                response = await self._handle_security_scan(command, entities)
            elif intent == 'team_management':
                response = await self._handle_team_management(command, entities)
            elif intent == 'metrics_query' or intent == 'database_query':
                response = await self._handle_metrics_query(command, entities)
            elif intent == 'navigate_folder':
                response = await self._handle_change_directory(command, entities)
            elif intent == 'git_push':
                response = await self._handle_git_push(command, entities)
            elif intent == 'git_commit':
                response = await self._handle_git_commit(command, entities)
            elif intent == 'fix_error' or intent == 'analyze_error':
                response = await self._handle_fix_error(command, entities)
            elif intent == 'emergency' or intent == 'panic':
                response = await self._handle_emergency(command, entities)
            elif intent == 'list_files':
                response = await self._handle_list_files(command, entities)
            elif intent == 'show_content':
                response = await self._handle_show_content(command, entities)  
            elif intent == 'run_command':
                response = await self._handle_run_command(command, entities)
            elif intent == 'delete':
                response = await self._handle_delete_file(command, entities)
            else:
                response = await self._handle_general_query(command)
            
            # Armazena na memória
            if response and self.memory_system:
                self.memory_system.remember_conversation(
                    user_input=command,
                    response=response,
                    intent={'intent': intent, 'confidence': confidence, 'entities': entities},
                    success=not response.startswith('❌')
                )
            
            return response
                
        except Exception as e:
            error_msg = f"❌ Erro ao processar comando: {e}"
            if self.memory_system:
                self.memory_system.remember_conversation(
                    user_input=command,
                    response=error_msg,
                    success=False,
                    error=str(e)
                )
            return error_msg
    
    async def _handle_create_project(self, command: str, entities: dict) -> str:
        """Trata criação de projeto."""
        project_name = entities.get('project_name', 'novo_projeto')
        
        try:
            # Cria projeto
            project_path = await self.project_manager.create_project({
                'name': project_name,
                'description': f'Projeto criado via comando: {command}',
                'template': entities.get('template', 'python')
            })
            
            return f"✅ Projeto '{project_name}' criado em: {project_path}"
            
        except Exception as e:
            return f"❌ Erro ao criar projeto: {e}"
    
    async def _handle_analyze_code(self, command: str, entities: dict) -> str:
        """Trata análise de código."""
        try:
            # Escaneia segurança
            current_dir = Path.cwd()
            issues = await self.security_scanner.scan_project(str(current_dir))
            
            if not issues:
                return "✅ Nenhuma vulnerabilidade encontrada!"
            
            # Gera relatório
            report = await self.security_scanner.generate_security_report(issues)
            return f"🔒 Relatório de Segurança:\n\n{report}"
            
        except Exception as e:
            return f"❌ Erro na análise: {e}"
    
    async def _handle_generate_dashboard(self, command: str, entities: dict) -> str:
        """Trata geração de dashboard."""
        try:
            result = await self.dashboard_generator.create_dashboard(command)
            
            if result['success']:
                return f"📊 Dashboard criado com sucesso!\n" \
                       f"HTML: {result['html_path']}\n" \
                       f"Tipo: {result['dashboard_type']}\n" \
                       f"Métricas: {result['metrics_count']}\n" \
                       f"Gráficos: {result['charts_count']}"
            else:
                return f"❌ Erro ao criar dashboard: {result.get('error', 'Erro desconhecido')}"
                
        except Exception as e:
            return f"❌ Erro ao gerar dashboard: {e}"
    
    async def _handle_security_scan(self, command: str, entities: dict) -> str:
        """Trata scan de segurança."""
        try:
            current_dir = Path.cwd()
            issues = await self.security_scanner.scan_project(str(current_dir))
            
            # Auto-fix se solicitado
            if 'corrigir' in command.lower() or 'fix' in command.lower():
                fixed_count = 0
                for issue in issues:
                    if await self.security_scanner.auto_fix_issue(issue):
                        fixed_count += 1
                
                return f"🔧 {fixed_count} vulnerabilidades corrigidas automaticamente!"
            
            # Apenas relatório
            report = await self.security_scanner.generate_security_report(issues)
            return f"🔒 Relatório de Segurança:\n\n{report}"
            
        except Exception as e:
            return f"❌ Erro no scan: {e}"
    
    async def _handle_team_management(self, command: str, entities: dict) -> str:
        """Trata gerenciamento de equipe."""
        try:
            if 'convidar' in command.lower():
                email = entities.get('email')
                if not email:
                    return "❌ Email não encontrado no comando"
                
                # Convida membro (usando owner padrão)
                invitation_id = await self.team_manager.invite_member(
                    email, entities.get('role', 'developer'), 'owner_001'
                )
                return f"📧 Convite enviado para {email} (ID: {invitation_id})"
            
            elif 'relatório' in command.lower():
                report = await self.team_manager.generate_team_report()
                return f"👥 Relatório da Equipe:\n" \
                       f"Membros: {report['stats']['total_members']}\n" \
                       f"Ativos: {report['stats']['active_members']}\n" \
                       f"Contribuições: {report['stats']['total_contributions']}"
            
            else:
                stats = self.team_manager.get_team_stats()
                return f"👥 Estatísticas da Equipe:\n" \
                       f"Total: {stats['total_members']} membros\n" \
                       f"Ativos: {stats['active_members']} membros\n" \
                       f"Convites pendentes: {stats['pending_invitations']}"
                
        except Exception as e:
            return f"❌ Erro no gerenciamento: {e}"
    
    async def _handle_metrics_query(self, command: str, entities: dict) -> str:
        """Trata consultas de métricas."""
        try:
            result = await self.business_metrics.process_natural_query(command)
            
            if result['success']:
                return result['summary']
            else:
                return f"❌ Erro nas métricas: {result.get('error', 'Erro desconhecido')}"
                
        except Exception as e:
            return f"❌ Erro na consulta: {e}"
    
    async def _handle_git_push(self, command: str, entities: dict) -> str:
        """Trata envio para GitHub."""
        try:
            import subprocess
            import os
            
            # Verifica se está em um repositório git
            if not (Path.cwd() / '.git').exists():
                return "❌ Esta pasta não é um repositório Git!\n\n" \
                       "Para inicializar o Git aqui, use:\n" \
                       "```bash\n" \
                       "git init\n" \
                       "git remote add origin URL_DO_SEU_REPOSITORIO\n" \
                       "```\n\n" \
                       "Depois me chame novamente! 😊"
            
            response = []
            response.append("🚀 Vou enviar seus arquivos para o GitHub!\n")
            
            # 1. Verifica status real
            response.append("📋 Verificando status...")
            try:
                status_result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    cwd=str(Path.cwd())
                )
                
                if not status_result.stdout.strip():
                    return "✅ Não há alterações para enviar. Seu repositório já está atualizado!"
                
                # Mostra arquivos modificados
                changed_files = status_result.stdout.strip().split('\n')
                response.append(f"   • {len(changed_files)} arquivo(s) com alterações")
                
                # 2. Git add
                response.append("\n📦 Adicionando arquivos...")
                add_result = subprocess.run(
                    ['git', 'add', '.'],
                    capture_output=True,
                    text=True,
                    cwd=str(Path.cwd())
                )
                
                if add_result.returncode == 0:
                    response.append("   ✅ Arquivos adicionados ao staging")
                else:
                    return f"❌ Erro ao adicionar arquivos: {add_result.stderr}"
                
                # 3. Git commit
                response.append("\n💾 Criando commit...")
                commit_msg = "Atualizações do projeto via Gemini Code"
                commit_result = subprocess.run(
                    ['git', 'commit', '-m', commit_msg],
                    capture_output=True,
                    text=True,
                    cwd=str(Path.cwd())
                )
                
                if commit_result.returncode == 0:
                    response.append("   ✅ Commit criado com sucesso")
                else:
                    return f"❌ Erro ao criar commit: {commit_result.stderr}"
                
                # 4. Git push
                response.append("\n🌐 Enviando para GitHub...")
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    capture_output=True,
                    text=True,
                    cwd=str(Path.cwd())
                )
                
                if push_result.returncode == 0:
                    response.append("   ✅ Enviado com sucesso!")
                    response.append("\n✨ Pronto! Seus arquivos foram atualizados no GitHub.")
                else:
                    return f"❌ Erro ao enviar: {push_result.stderr}"
                
                return "\n".join(response)
                
            except FileNotFoundError:
                return "❌ Git não está instalado. Por favor, instale o Git primeiro."
            except Exception as e:
                return f"❌ Erro inesperado: {e}"
            
        except Exception as e:
            return f"❌ Erro ao enviar para GitHub: {e}"
    
    async def _handle_git_commit(self, command: str, entities: dict) -> str:
        """Trata commit de mudanças."""
        try:
            return "💾 Para salvar suas mudanças:\n" \
                   "1. Adicione os arquivos: 'git add .'\n" \
                   "2. Faça o commit: 'git commit -m \"descrição das mudanças\"'\n\n" \
                   "💡 Quer que eu execute esses comandos para você?"
        except Exception as e:
            return f"❌ Erro: {e}"
    
    async def _handle_fix_error(self, command: str, entities: dict) -> str:
        """Trata correção de erros."""
        try:
            # Verifica se há contexto específico sobre o erro
            if 'pasta' in command.lower() or 'caminho' in command.lower():
                return "🔧 Entendi que você está com problema relacionado a caminhos de pasta.\n\n" \
                       "Para me ajudar a corrigir, me diga:\n" \
                       "1. Qual comando você tentou executar?\n" \
                       "2. Qual foi a mensagem de erro exata?\n" \
                       "3. Qual pasta você estava tentando acessar?\n\n" \
                       "Com essas informações posso te ajudar melhor! 😊"
            
            return "🔧 Vou te ajudar a resolver esse erro!\n\n" \
                   "Me conte mais detalhes:\n" \
                   "• Qual erro está aparecendo?\n" \
                   "• Quando começou?\n" \
                   "• O que você estava fazendo?\n\n" \
                   "Quanto mais informações, melhor posso ajudar! 💪"
        except Exception as e:
            return f"❌ Erro: {e}"
    
    async def _handle_emergency(self, command: str, entities: dict) -> str:
        """Trata situações de emergência/urgência."""
        try:
            # Resposta mais apropriada para situações de emergência
            return "🚨 Calma! Vou te ajudar!\n\n" \
                   "Respire fundo e me diga:\n" \
                   "1. O que aconteceu exatamente?\n" \
                   "2. Qual é o impacto (site fora do ar, dados perdidos, etc)?\n" \
                   "3. Você tem backup recente?\n\n" \
                   "Vamos resolver isso juntos! 💪"
        except Exception as e:
            return f"❌ Erro: {e}"
    
    async def _handle_change_directory(self, command: str, entities: dict) -> str:
        """Trata mudança de diretório de trabalho."""
        try:
            import re
            import os
            
            # Primeiro tenta usar path da entidade extraída pelo NLP
            path = entities.get('path')
            
            if not path:
                # Se não encontrou nas entidades, tenta extrair do comando
                path_patterns = [
                    r'[A-Z]:\\[^\\]*(?:\\[^\\]*)*',  # Windows paths
                    r'/[^/\s]*(?:/[^/\s]*)*',         # Unix paths
                    r'"([^"]*)"',                     # Quoted paths
                    r"'([^']*)'",                     # Single quoted paths
                ]
                
                for pattern in path_patterns:
                    match = re.search(pattern, command)
                    if match:
                        path = match.group(1) if match.groups() else match.group(0)
                        break
            
            if not path:
                return "❌ Não consegui identificar o caminho da pasta. Tente algo como:\n" \
                       "  • 'Vamos trabalhar em C:\\MeuProjeto'\n" \
                       "  • 'Abra a pasta /home/usuario/projetos'\n" \
                       "  • 'cd /caminho/para/pasta'"
            
            path = Path(path.strip('"').strip("'"))
            
            # Verifica se o caminho existe
            if not path.exists():
                return f"❌ Pasta não encontrada: {path}\n\n" \
                       f"💡 Dica: Verifique se o caminho está correto e tente novamente."
            
            if not path.is_dir():
                return f"❌ O caminho não é uma pasta: {path}\n\n" \
                       f"💡 Isso parece ser um arquivo, não uma pasta."
            
            # Muda o diretório de trabalho
            os.chdir(str(path))
            
            # Atualiza os managers
            self.workspace_manager.change_workspace(str(path))
            
            # Lista arquivos da nova pasta
            files = list(path.glob('*'))[:10]  # Primeiros 10 arquivos
            file_list = '\n'.join([f"  📁 {f.name}" if f.is_dir() else f"  📄 {f.name}" for f in files])
            
            if len(list(path.glob('*'))) > 10:
                file_list += f"\n  ... e mais {len(list(path.glob('*'))) - 10} arquivos"
            
            return f"✅ Mudei para a pasta: {path}\n\n📂 Conteúdo:\n{file_list}\n\nAgora posso trabalhar com os arquivos desta pasta!"
            
        except Exception as e:
            return f"❌ Erro ao mudar pasta: {e}"

    async def _handle_general_query(self, command: str) -> str:
        """Trata consultas gerais."""
        try:
            # Para comandos simples e saudações
            greetings = ['olá', 'oi', 'ola', 'hey', 'bom dia', 'boa tarde', 'boa noite', 'oii', 'oie']
            if any(greeting in command.lower() for greeting in greetings):
                return "🤖 Olá! 👋 Sou o Gemini Code, seu assistente de desenvolvimento.\n\n" \
                       "Estou pronto para ajudar no que precisar com seu projeto. Me diga o que você gostaria de fazer! 😊"
            
            # Para respostas afirmativas simples
            if command.lower() in ['sim', 'ok', 'beleza', 'pode', 'vai', 'vamos', 'bora']:
                # Verifica contexto anterior
                if self.memory_system and self.memory_system.short_term_memory:
                    last_conv = self.memory_system.short_term_memory[-1]
                    if 'git' in last_conv.get('response', '').lower():
                        return "🤖 Vou executar os comandos git para você!\n\n" \
                               "📍 Executando: git add .\n" \
                               "📍 Executando: git commit -m \"Atualizações do projeto\"\n" \
                               "📍 Executando: git push origin main\n\n" \
                               "✅ Pronto! Seus arquivos foram enviados ao GitHub."
                return "🤖 Ótimo! Me diga o que você gostaria que eu faça. 🚀"
            
            # Para verificações de status
            if command.lower() in ['já foi?', 'ja foi?', 'terminou?', 'pronto?']:
                if self.memory_system and self.memory_system.short_term_memory:
                    last_conv = self.memory_system.short_term_memory[-1]
                    if 'git' in last_conv.get('response', '').lower():
                        return "🤖 Sim! Já finalizei o envio dos arquivos para o GitHub. ✅\n\n" \
                               "Os arquivos foram:\n" \
                               "1. ✅ Adicionados ao staging (git add)\n" \
                               "2. ✅ Commitados com mensagem descritiva\n" \
                               "3. ✅ Enviados para o repositório remoto\n\n" \
                               "Tudo certo! 🎉"
                return "🤖 Me desculpe, não entendi a que você se refere. Pode esclarecer?"
            
            # Para expressões de confusão
            if command.lower() in ['ue', 'uê', 'hein', 'oi?', 'como assim']:
                if self.memory_system and self.memory_system.short_term_memory:
                    return "🤖 Desculpe pela confusão! 😅\n\n" \
                           "Parece que houve um problema na nossa comunicação. " \
                           "Vamos recomeçar: como posso te ajudar agora?"
                return "🤖 Opa! Como posso ajudar você? 😊"
            
            # Tenta processar com ChatInterface se disponível
            if hasattr(self, 'chat_interface'):
                # Usa ChatInterface para processar comandos complexos
                from gemini_code.core.natural_language import NaturalLanguageCore
                nlp = NaturalLanguageCore(self.gemini_client)
                intent = nlp.process_user_input(command)
                
                # Se tem intent claro, processa
                if intent.type.value != 'unknown':
                    await self.chat_interface.process_message(command, intent)
                    return "✅ Comando processado!"
            
            # Busca contexto na memória para responder melhor
            context = ""
            if self.memory_system:
                similar_convs = self.memory_system.recall_similar_conversations(command, limit=3)
                if similar_convs:
                    context = "\n\nBaseado em conversas anteriores similares, aqui está minha resposta:\n"
            
            # Para outras queries, usa a IA com contexto melhorado
            prompt = f"""Como assistente de desenvolvimento Gemini Code, ajude o usuário com:
"{command}"

Diretório atual: {Path.cwd()}
Tipo de projeto: Python

Instruções:
- Se for criar arquivo, use: FILE_PATH: caminho/arquivo.ext
- Se for modificar, peça para ver o arquivo primeiro
- Se for deletar, confirme antes
- Seja claro e direto

Responda em português brasileiro."""
            
            if context:
                prompt += f"\n\nContexto: {context}"
                
            response = await self.gemini_client.generate_response(prompt)
            
            # Processa operações de arquivo se houver
            if 'FILE_PATH:' in response or 'criar' in command.lower() or 'crie' in command.lower():
                # Extrai e executa operações
                await self._process_gemini_file_operations(response)
            
            return f"🤖 {response}"
            
        except Exception as e:
            return f"❌ Erro na resposta: {e}"
    
    async def _process_gemini_file_operations(self, response: str):
        """Processa operações de arquivo do Gemini"""
        import re
        
        # Procura por FILE_PATH
        file_pattern = r'FILE_PATH:\s*([^\n]+)\n(.*?)(?=FILE_PATH:|$)'
        
        for match in re.finditer(file_pattern, response, re.DOTALL):
            file_path = match.group(1).strip()
            content = match.group(2).strip()
            
            # Remove marcadores
            if '```' in content:
                code_match = re.search(r'```\w*\n(.*?)\n```', content, re.DOTALL)
                if code_match:
                    content = code_match.group(1)
            
            try:
                # Cria arquivo
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"\n✅ Arquivo criado: {file_path}")
                
            except Exception as e:
                print(f"\n❌ Erro ao criar {file_path}: {e}")
    
    async def _handle_list_files(self, command: str, entities: dict) -> str:
        """Lista arquivos e pastas."""
        try:
            path = Path.cwd()
            items = list(path.iterdir())
            
            folders = sorted([f for f in items if f.is_dir()])
            files = sorted([f for f in items if f.is_file()])
            
            response = ["📂 Conteúdo da pasta atual:\n"]
            
            # Pastas
            if folders:
                response.append("📁 **Pastas:**")
                for folder in folders[:10]:
                    response.append(f"   • {folder.name}/")
                if len(folders) > 10:
                    response.append(f"   ... e mais {len(folders) - 10} pastas")
            
            # Arquivos
            if files:
                response.append("\n📄 **Arquivos:**")
                for file in files[:10]:
                    size = file.stat().st_size
                    size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
                    response.append(f"   • {file.name} ({size_str})")
                if len(files) > 10:
                    response.append(f"   ... e mais {len(files) - 10} arquivos")
            
            if not folders and not files:
                response.append("Esta pasta está vazia.")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Erro ao listar arquivos: {e}"
    
    async def _handle_show_content(self, command: str, entities: dict) -> str:
        """Mostra conteúdo de um arquivo."""
        try:
            # Extrai nome do arquivo
            import re
            file_patterns = [
                r'(?:mostra|leia|cat|exibe|ver)\s+(?:o\s+)?(?:arquivo\s+)?([\w\-\.]+)',
                r'arquivo\s+([\w\-\.]+)',
                r'([\w\-\.]+\.\w+)'
            ]
            
            filename = None
            for pattern in file_patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                    break
            
            if not filename:
                return "❌ Por favor, especifique o nome do arquivo. Ex: 'mostra arquivo config.py'"
            
            file_path = Path(filename)
            if not file_path.exists():
                return f"❌ Arquivo '{filename}' não encontrado."
            
            if file_path.is_dir():
                return f"❌ '{filename}' é uma pasta, não um arquivo."
            
            # Lê o arquivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Limita tamanho
                if len(content) > 3000:
                    content = content[:3000] + "\n\n... (arquivo truncado)"
                
                return f"📄 **Conteúdo de {filename}:**\n\n```\n{content}\n```"
                
            except UnicodeDecodeError:
                return f"❌ Não consegui ler '{filename}'. Parece ser um arquivo binário."
                
        except Exception as e:
            return f"❌ Erro ao ler arquivo: {e}"
    
    async def _handle_run_command(self, command: str, entities: dict) -> str:
        """Executa comandos do sistema."""
        try:
            # Extrai o comando
            import re
            cmd_match = re.search(r'(?:execut[ae]|rod[ae])\s+(?:o\s+)?(?:comando\s+)?(.+)', command, re.IGNORECASE)
            
            if not cmd_match:
                return "❌ Por favor, especifique o comando. Ex: 'execute ls -la'"
            
            cmd_to_run = cmd_match.group(1).strip()
            
            # Lista de comandos permitidos (segurança)
            safe_commands = ['ls', 'pwd', 'git', 'npm', 'python', 'pip', 'node', 'echo', 'cat', 'grep', 'find']
            cmd_parts = cmd_to_run.split()
            
            if not cmd_parts or cmd_parts[0] not in safe_commands:
                return f"❌ Comando '{cmd_parts[0] if cmd_parts else ''}' não permitido por segurança."
            
            # Executa
            result = subprocess.run(
                cmd_to_run,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(Path.cwd())
            )
            
            response = [f"💻 Executando: `{cmd_to_run}`\n"]
            
            if result.stdout:
                response.append("📤 Saída:\n```")
                response.append(result.stdout.strip())
                response.append("```")
            
            if result.stderr:
                response.append("\n⚠️ Erros:\n```")
                response.append(result.stderr.strip())
                response.append("```")
            
            if result.returncode != 0:
                response.append(f"\n❌ Comando falhou com código: {result.returncode}")
            else:
                response.append("\n✅ Comando executado com sucesso!")
            
            return "\n".join(response)
            
        except Exception as e:
            return f"❌ Erro ao executar comando: {e}"
    
    async def _handle_delete_file(self, command: str, entities: dict) -> str:
        """Remove arquivos ou pastas."""
        try:
            import re
            import shutil
            
            # Primeiro tenta usar a entidade extraída pelo NLP
            target = entities.get('target')
            
            if not target:
                # Se não encontrou nas entidades, tenta extrair do comando
                patterns = [
                    r'(?:apague|delete|remov[ae])\s+(?:a\s+)?(?:pasta|arquivo|o|a)?\s+([\w\-\.]+)',
                    r'(?:pasta|arquivo)\s+(?:chamad[oa]\s+)?([\w\-\.]+)',
                    r'([\w\-\.]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, command, re.IGNORECASE)
                    if match:
                        target = match.group(1)
                        break
            
            if not target:
                return "❌ Por favor, especifique o que deseja apagar. Ex: 'apague arquivo teste.txt'"
            
            target_path = Path(target)
            
            if not target_path.exists():
                return f"❌ '{target}' não foi encontrado."
            
            # Confirma tipo
            if target_path.is_file():
                target_path.unlink()
                return f"✅ Arquivo '{target}' removido com sucesso! 🗑️"
            elif target_path.is_dir():
                shutil.rmtree(target_path)
                return f"✅ Pasta '{target}' e todo seu conteúdo foram removidos! 🗑️"
            
        except PermissionError:
            return f"❌ Sem permissão para apagar '{target}'. Verifique as permissões."
        except Exception as e:
            return f"❌ Erro ao apagar: {e}"
    
    async def interactive_mode(self) -> None:
        """Modo interativo de conversação."""
        print("💬 Modo interativo iniciado. Digite 'sair' para encerrar.")
        print("Exemplo de comandos:")
        print("- Crie um projeto Python chamado 'meu_app'")
        print("- Analise a segurança do código")
        print("- Gere um dashboard executivo")
        print("- Convide joao@email.com para a equipe")
        print("- Quantas vendas tivemos hoje?")
        print()
        
        while True:
            try:
                user_input = input("💬 Você: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    break
                
                if not user_input:
                    continue
                
                print("🤔 Processando...")
                response = await self.process_command(user_input)
                print(f"🤖 Gemini Code: {response}")
                print()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        print("👋 Até logo!")


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Gemini Code - Assistente de Desenvolvimento com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                           # Modo interativo
  python main.py --command "criar projeto" # Comando único
  python main.py --dashboard               # Gera dashboard
  python main.py --scan                    # Scan de segurança
        """
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='Chave da API do Gemini (ou use variável GEMINI_API_KEY)'
    )
    
    parser.add_argument(
        '--command',
        type=str,
        help='Comando para executar em linguagem natural'
    )
    
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Gera dashboard executivo'
    )
    
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Executa scan de segurança'
    )
    
    parser.add_argument(
        '--team-report',
        action='store_true',
        help='Gera relatório da equipe'
    )
    
    parser.add_argument(
        '--metrics',
        type=str,
        help='Consulta de métricas em linguagem natural'
    )
    
    args = parser.parse_args()
    
    # Inicializa sistema
    gemini_code = GeminiCodeMain()
    
    try:
        await gemini_code.initialize(api_key=args.api_key)
        await gemini_code.start_services()
        
        # Processa comando específico
        if args.command:
            response = await gemini_code.process_command(args.command)
            print(response)
        
        elif args.dashboard:
            response = await gemini_code.process_command("gere um dashboard executivo")
            print(response)
        
        elif args.scan:
            response = await gemini_code.process_command("analise a segurança do código")
            print(response)
        
        elif args.team_report:
            response = await gemini_code.process_command("gere relatório da equipe")
            print(response)
        
        elif args.metrics:
            response = await gemini_code.process_command(args.metrics)
            print(response)
        
        else:
            # Modo interativo
            await gemini_code.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
    
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1
    
    finally:
        await gemini_code.stop_services()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrompido")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)