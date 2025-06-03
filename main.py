#!/usr/bin/env python3
"""
Gemini Code - Interface Principal
Assistente de desenvolvimento completo com IA
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.gemini_client import GeminiClient
from gemini_code.core.nlp_enhanced import NLPEnhanced
from gemini_code.core.project_manager import ProjectManager
from gemini_code.core.file_manager import FileManagementSystem
from gemini_code.core.workspace_manager import WorkspaceManager
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
        """Inicializa todos os componentes do sistema."""
        print("🚀 Inicializando Gemini Code...")
        
        try:
            # Core components
            print("🔧 Inicializando GeminiClient...")
            self.gemini_client = GeminiClient(api_key=api_key)
            
            print("🔧 Inicializando NLPEnhanced...")
            self.nlp = NLPEnhanced(self.gemini_client)
            
            print("🔧 Inicializando DatabaseManager...")
            self.db_manager = DatabaseManager(self.gemini_client)
            
            # File and project management
            print("🔧 Inicializando FileManagementSystem...")
            self.file_manager = FileManagementSystem(self.gemini_client)
            
            print("🔧 Inicializando WorkspaceManager...")
            self.workspace_manager = WorkspaceManager(self.gemini_client)
            
            print("🔧 Inicializando ProjectManager...")
            self.project_manager = ProjectManager(self.gemini_client)
            
            # Monitoring and security
            print("🔧 Inicializando ContinuousMonitor...")
            self.monitor = ContinuousMonitor(self.gemini_client, str(Path.cwd()))
            
            print("🔧 Inicializando SecurityScanner...")
            self.security_scanner = SecurityScanner(self.gemini_client)
            
            # Analytics and metrics
            print("🔧 Inicializando BusinessMetrics...")
            self.business_metrics = BusinessMetrics(self.gemini_client, self.db_manager)
            
            print("🔧 Inicializando AnalyticsEngine...")
            self.analytics_engine = AnalyticsEngine(self.gemini_client, self.db_manager)
            
            # Componentes opcionais que dependem de matplotlib
            if DASHBOARD_AVAILABLE:
                print("🔧 Inicializando DashboardGenerator...")
                self.dashboard_generator = DashboardGenerator(
                    self.gemini_client, self.business_metrics, self.analytics_engine
                )
            else:
                self.dashboard_generator = None
                print("⚠️ DashboardGenerator desabilitado (matplotlib não disponível)")
            
            if KPI_TRACKER_AVAILABLE:
                print("🔧 Inicializando KPITracker...")
                self.kpi_tracker = KPITracker(self.gemini_client, self.db_manager)
            else:
                self.kpi_tracker = None
                print("⚠️ KPITracker desabilitado (matplotlib não disponível)")
            
            # Collaboration
            print("🔧 Inicializando TeamManager...")
            self.team_manager = TeamManager(self.gemini_client)
            
            print("🔧 Inicializando ProjectSharing...")
            self.project_sharing = ProjectSharing(self.gemini_client, self.team_manager)
            
            print("🔧 Inicializando RealTimeSync...")
            self.real_time_sync = RealTimeSync(self.gemini_client, self.team_manager)
            
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
            if intent == 'create_project':
                return await self._handle_create_project(command, entities)
            elif intent == 'analyze_code':
                return await self._handle_analyze_code(command, entities)
            elif intent == 'generate_dashboard':
                return await self._handle_generate_dashboard(command, entities)
            elif intent == 'security_scan':
                return await self._handle_security_scan(command, entities)
            elif intent == 'team_management':
                return await self._handle_team_management(command, entities)
            elif intent == 'metrics_query':
                return await self._handle_metrics_query(command, entities)
            elif intent == 'navigate_folder' or 'trabalhar' in command.lower() or 'pasta' in command.lower():
                return await self._handle_change_directory(command, entities)
            else:
                return await self._handle_general_query(command)
                
        except Exception as e:
            return f"❌ Erro ao processar comando: {e}"
    
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
    
    async def _handle_change_directory(self, command: str, entities: dict) -> str:
        """Trata mudança de diretório de trabalho."""
        try:
            import re
            import os
            
            # Extrai caminho do comando
            path_patterns = [
                r'[A-Z]:\\[^\\]*(?:\\[^\\]*)*',  # Windows paths
                r'/[^/\s]*(?:/[^/\s]*)*',         # Unix paths
                r'"([^"]*)"',                     # Quoted paths
                r"'([^']*)'",                     # Single quoted paths
            ]
            
            path = None
            for pattern in path_patterns:
                match = re.search(pattern, command)
                if match:
                    path = match.group(1) if match.groups() else match.group(0)
                    break
            
            if not path:
                return "❌ Não consegui identificar o caminho da pasta. Tente: 'Vamos trabalhar em C:\\MeuProjeto'"
            
            path = Path(path.strip('"').strip("'"))
            
            # Verifica se o caminho existe
            if not path.exists():
                return f"❌ Pasta não encontrada: {path}"
            
            if not path.is_dir():
                return f"❌ O caminho não é uma pasta: {path}"
            
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
            # Gera resposta com IA
            response = await self.gemini_client.generate_response(
                f"Como assistente de desenvolvimento, responda esta pergunta: {command}"
            )
            return f"🤖 {response}"
            
        except Exception as e:
            return f"❌ Erro na resposta: {e}"
    
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