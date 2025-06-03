"""
Interface de chat aprimorada com memória contextual e processamento inteligente.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import re

from ..core.gemini_client import GeminiClient
from ..core.conversation_manager import ConversationManager
from ..core.nlp_enhanced import NLPEnhanced
from ..core.file_manager import FileManagementSystem
from ..core.project_manager import ProjectManager
from ..core.autonomous_executor import AutonomousExecutor
from ..analysis.error_detector import ErrorDetector
from ..analysis.health_monitor import HealthMonitor
from ..execution.command_executor import CommandExecutor
from ..integration.git_manager import GitManager
from ..development.code_generator import CodeGenerator
from ..utils.error_humanizer import humanize_error
from ..utils.logger import Logger


class EnhancedChatInterface:
    """Interface de chat aprimorada com memória contextual."""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        project_manager: ProjectManager,
        file_manager: FileManagementSystem,
        project_path: str
    ):
        self.gemini = gemini_client
        self.project = project_manager
        self.files = file_manager
        self.project_path = project_path
        self.console = Console()
        self.logger = Logger()
        
        # Inicializa sistema de memória e conversação
        self.conversation_manager = ConversationManager(project_path, gemini_client)
        self.nlp = NLPEnhanced(gemini_client)
        
        # Módulos especializados
        self.error_detector = ErrorDetector(gemini_client, file_manager)
        self.health_monitor = HealthMonitor(gemini_client, file_manager)
        self.command_executor = CommandExecutor(gemini_client)
        self.git_manager = GitManager(gemini_client, self.command_executor)
        self.code_generator = CodeGenerator(gemini_client, file_manager)
        
        # 🚀 SISTEMA AUTÔNOMO - EXECUÇÃO REAL
        self.autonomous_executor = AutonomousExecutor(project_path)
        
        # Estado da interface
        self.interactive_mode = True
        self.debug_mode = False
        
        self.console.print("[green]✨ Gemini Code com Memória Ativada![/green]")
        self.console.print("[dim]Digite 'ajuda' para ver os comandos disponíveis.[/dim]\n")
    
    async def start_interactive_session(self):
        """Inicia sessão interativa."""
        self.console.print("[bold blue]🤖 Gemini Code - Assistente Inteligente[/bold blue]")
        self.console.print("[dim]Com memória contextual e aprendizado contínuo[/dim]")
        
        # Mostra resumo da memória se existir
        context_summary = self.conversation_manager.memory_system.get_context_summary()
        if context_summary.strip() != "📊 **Contexto Atual**\n\n":
            self.console.print(Panel(context_summary, title="💾 Memória Carregada", border_style="blue"))
        
        while self.interactive_mode:
            try:
                # Prompt interativo
                user_input = self.console.input("\n[bold cyan]Você:[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                
                # Comandos especiais
                if await self._handle_special_commands(user_input):
                    continue
                
                # 🚀 DETECÇÃO DE COMANDOS AUTÔNOMOS
                if await self._is_autonomous_command(user_input):
                    await self._handle_autonomous_command(user_input)
                    continue
                
                # 🔧 NOVA FUNCIONALIDADE: Comandos simples de execução direta
                simple_execution_intent = await self._identify_simple_execution_intent(user_input)
                if simple_execution_intent:
                    await self._handle_simple_execution_command(user_input, simple_execution_intent)
                    continue
                
                # Processa mensagem com memória
                await self.process_message_with_memory(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]👋 Até logo![/yellow]")
                break
            except Exception as e:
                error_msg = humanize_error(e, "Sessão interativa")
                self.console.print(f"[red]{error_msg}[/red]")
    
    async def process_message_with_memory(self, user_input: str) -> Dict[str, Any]:
        """Processa mensagem usando sistema de memória."""
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                
                task = progress.add_task("🧠 Processando com memória contextual...", total=None)
                
                # Processa com o gerenciador de conversas
                result = await self.conversation_manager.process_message(user_input)
                
                progress.update(task, description="✅ Processamento concluído")
            
            # Exibe resposta
            response = result['response']
            intent_data = result['intent']
            
            # Formata e exibe resposta
            self._display_response(response, intent_data)
            
            # Se houve erro, mostra informações de debug
            if not result['success']:
                self._display_debug_info(result, user_input)
            
            return result
            
        except Exception as e:
            error_msg = humanize_error(e, "Processamento de mensagem")
            self.console.print(f"[red]{error_msg}[/red]")
            
            # Tenta fallback direto com Gemini
            return await self._fallback_to_gemini(user_input, str(e))
    
    def _display_response(self, response: str, intent_data: Dict[str, Any]):
        """Exibe resposta formatada."""
        
        # Adiciona emoji baseado na intenção
        intent_emoji = {
            'create_feature': '🏗️',
            'create_agent': '🤖',
            'fix_error': '🔧',
            'analyze_project': '📊',
            'git_push': '🚀',
            'question': '❓',
            'navigate_folder': '📁'
        }.get(intent_data.get('intent'), '🤖')
        
        confidence = intent_data.get('confidence', 0)
        
        # Header com informações de contexto
        header = f"{intent_emoji} **Gemini Code** (Confiança: {confidence}%)"
        
        # Exibe resposta em painel
        self.console.print(Panel(
            Markdown(response),
            title=header,
            border_style="green" if confidence > 70 else "yellow" if confidence > 40 else "red",
            padding=(1, 2)
        ))
        
        # Mostra informações contextuais se debug ativado
        if self.debug_mode:
            self._show_debug_context(intent_data)
    
    def _show_debug_context(self, intent_data: Dict[str, Any]):
        """Mostra informações de debug."""
        debug_info = f"""
**🔍 Debug Info:**
- Intenção: {intent_data.get('intent', 'unknown')}
- Confiança: {intent_data.get('confidence', 0)}%
- Entidades: {intent_data.get('entities', {})}
- Sentimento: {intent_data.get('sentiment', 'neutral')}
- Pistas de contexto: {', '.join(intent_data.get('context_clues', []))}
"""
        self.console.print(Panel(debug_info, title="🔧 Debug", border_style="dim"))
    
    def _display_debug_info(self, result: Dict[str, Any], user_input: str):
        """Exibe informações de debug em caso de erro."""
        debug_panel = f"""
**❌ Erro no Processamento:**
- Input: {user_input[:100]}...
- Intent: {result.get('intent', {}).get('intent', 'unknown')}
- Contexto usado: {len(result.get('context_used', {}))} elementos
- ID da conversa: {result.get('conversation_id', 'N/A')}

**💡 Dica:** Tente reformular sua pergunta ou use comandos mais específicos.
"""
        self.console.print(Panel(debug_panel, title="🐛 Debug Info", border_style="red"))
    
    async def _handle_special_commands(self, user_input: str) -> bool:
        """Processa comandos especiais da interface."""
        command = user_input.lower().strip()
        
        # Comandos de memória
        if command in ['memoria', 'memory', 'context', 'contexto']:
            await self._show_memory_status()
            return True
        
        elif command.startswith('memoria limpar') or command.startswith('reset'):
            await self._reset_conversation()
            return True
        
        elif command in ['conversa', 'conversation', 'resumo']:
            await self._show_conversation_summary()
            return True
        
        # Comandos de configuração
        elif command in ['debug on', 'debug ativar']:
            self.debug_mode = True
            self.console.print("[green]🔧 Modo debug ativado[/green]")
            return True
        
        elif command in ['debug off', 'debug desativar']:
            self.debug_mode = False
            self.console.print("[green]🔧 Modo debug desativado[/green]")
            return True
        
        # Comandos de saúde
        elif command in ['saude', 'health', 'status']:
            await self._show_project_health()
            return True
        
        # Comandos de ajuda
        elif command in ['ajuda', 'help', '?']:
            await self._show_help()
            return True
        
        # Comandos de saída
        elif command in ['sair', 'exit', 'quit', 'bye']:
            await self._exit_session()
            return True
        
        return False
    
    # =================== SISTEMA AUTÔNOMO ===================
    
    async def _is_autonomous_command(self, user_input: str) -> bool:
        """Detecta se é um comando que deve ser executado de forma autônoma"""
        autonomous_indicators = [
            # Comandos de verificação + correção
            'verifica', 'check', 'analisa', 'depois', 'corrige', 'corrija',
            'crie', 'criar', 'adiciona', 'depois disso', 'em seguida',
            'valida', 'validar', 'testa', 'testar', 'garante', 'garantir',
            'até estar', '100%', 'perfeito', 'funcionando', 'funcional',
            # Padrões de sequência
            'primeiro', 'depois', 'em seguida', 'por último', 'finalmente',
            # Comandos complexos
            'pasta', 'arquivo', 'função', 'classe'
        ]
        
        # Comandos simples que sempre devem ser executados autonomamente
        simple_action_patterns = [
            r'crie?\s+(um|uma)?\s*(arquivo|pasta|diretório|diretorio)',
            r'criar?\s+(um|uma)?\s*(arquivo|pasta|diretório|diretorio)',
            r'faça?\s+(um|uma)?\s*(arquivo|pasta|diretório|diretorio)',
            r'gere?\s+(um|uma)?\s*(arquivo|pasta|diretório|diretorio)',
            r'para\s+(você|voce)\s+criar',
            r'é\s+para\s+(você|voce)\s+criar'
        ]
        
        user_lower = user_input.lower()
        
        # Verifica padrões de ação simples primeiro
        for pattern in simple_action_patterns:
            if re.search(pattern, user_lower, re.IGNORECASE):
                self.console.print(f"🤖 [bold yellow]Comando de ação detectado![/bold yellow] (ação simples)")
                return True
        
        # Conta indicadores
        indicator_count = sum(1 for indicator in autonomous_indicators if indicator in user_lower)
        
        # Detecta padrões de sequência
        sequence_patterns = [
            r'verifica.*corrige.*crie',
            r'analisa.*depois.*crie',
            r'check.*fix.*create',
            r'primeiro.*depois.*por',
            r'.*depois.*valida'
        ]
        
        has_sequence = any(re.search(pattern, user_lower, re.IGNORECASE) for pattern in sequence_patterns)
        
        # É autônomo se tem muitos indicadores OU padrão de sequência
        is_autonomous = indicator_count >= 3 or has_sequence
        
        if is_autonomous:
            self.console.print(f"🤖 [bold yellow]Comando autônomo detectado![/bold yellow] ({indicator_count} indicadores)")
        
        return is_autonomous
    
    async def _handle_autonomous_command(self, user_input: str):
        """Processa comando de forma totalmente autônoma"""
        self.console.print("\n🚀 [bold green]MODO EXECUÇÃO AUTÔNOMA ATIVADO[/bold green]")
        self.console.print("[dim]Processando comando de forma estruturada como Claude...[/dim]")
        
        try:
            # Exibe painel de início da execução autônoma
            self.console.print(Panel(
                f"[bold]🎯 COMANDO:[/bold] {user_input}\n\n"
                f"[yellow]⚡ EXECUTANDO DE FORMA AUTÔNOMA...[/yellow]\n"
                f"[dim]• Dividindo em tarefas estruturadas\n"
                f"• Executando comandos reais\n" 
                f"• Validando cada etapa\n"
                f"• Persistindo até 100% correto[/dim]",
                title="🤖 Execução Autônoma",
                border_style="green"
            ))
            
            # Executa comando de forma autônoma
            result = await self.autonomous_executor.execute_natural_command(user_input)
            
            # Exibe resultado final
            await self._display_autonomous_result(result)
            
            # Salva na memória
            self.conversation_manager.memory_system.remember_conversation(
                user_input=user_input,
                response=f"Comando executado autonomamente: {result['status']}",
                intent={'intent': 'autonomous_execution', 'confidence': 95},
                success=result['status'] == 'completed'
            )
            
        except Exception as e:
            error_msg = f"❌ Erro na execução autônoma: {e}"
            self.console.print(Panel(error_msg, title="💥 Erro", border_style="red"))
    
    async def _display_autonomous_result(self, result: Dict[str, Any]):
        """Exibe resultado da execução autônoma"""
        
        # Determina cor baseada no resultado
        if result['status'] == 'completed':
            border_color = "green"
            status_emoji = "🎉"
            status_text = "SUCESSO TOTAL"
        elif result['status'] == 'partial':
            border_color = "yellow"
            status_emoji = "⚠️"
            status_text = "PARCIALMENTE CONCLUÍDO"
        else:
            border_color = "red"
            status_emoji = "❌"
            status_text = "FALHOU"
        
        # Monta relatório
        report_text = f"[bold]{status_emoji} {status_text}[/bold]\n\n"
        report_text += f"🎯 **Comando Original:** {result['original_command']}\n\n"
        report_text += f"📊 **Estatísticas:**\n"
        report_text += f"• Total de tarefas: {result['total_tasks']}\n"
        report_text += f"• Concluídas: {result['completed_tasks']}\n"
        report_text += f"• Falharam: {result['failed_tasks']}\n"
        report_text += f"• Taxa de sucesso: {result['success_rate']:.1f}%\n"
        report_text += f"• Tempo de execução: {result['execution_time']:.1f}s\n\n"
        
        # Detalhes das tarefas
        report_text += f"📋 **Detalhes das Tarefas:**\n"
        for i, task in enumerate(result['tasks_detail'], 1):
            status_icon = "✅" if task['status'] == 'completed' else "❌" if task['status'] == 'failed' else "⏳"
            report_text += f"{i}. {status_icon} {task['description']}\n"
            if task['status'] == 'failed' and task['error']:
                report_text += f"   💭 Erro: {task['error'][:100]}...\n"
        
        # Exibe painel final
        self.console.print(Panel(
            Markdown(report_text),
            title=f"🤖 Resultado da Execução Autônoma",
            border_style=border_color,
            padding=(1, 2)
        ))
        
        # Mensagem final
        if result['status'] == 'completed':
            self.console.print(f"\n[bold green]🎉 Comando executado com sucesso! Projeto está funcionando 100%[/bold green]")
        elif result['status'] == 'partial':
            self.console.print(f"\n[bold yellow]⚠️ Comando parcialmente executado. Algumas tarefas falharam.[/bold yellow]")
        else:
            self.console.print(f"\n[bold red]❌ Comando falhou. Verifique os erros acima.[/bold red]")
    
    async def _show_memory_status(self):
        """Mostra status da memória."""
        summary = self.conversation_manager.memory_system.get_context_summary()
        preferences = self.conversation_manager.memory_system.get_preferences()
        patterns = self.conversation_manager.memory_system.get_project_patterns()
        
        memory_info = f"""
{summary}

**🧠 Estatísticas da Memória:**
- Preferências aprendidas: {sum(len(prefs) for prefs in preferences.values())}
- Padrões detectados: {len(patterns)}
- Conversa atual: {len(self.conversation_manager.current_context.messages)} mensagens
"""
        
        self.console.print(Panel(memory_info, title="💾 Status da Memória", border_style="blue"))
    
    async def _reset_conversation(self):
        """Reseta conversa atual."""
        self.conversation_manager.reset_conversation()
        self.console.print("[green]🔄 Conversa resetada. Memória de longo prazo mantida.[/green]")
    
    async def _show_conversation_summary(self):
        """Mostra resumo da conversa atual."""
        summary = self.conversation_manager.get_conversation_summary()
        self.console.print(Panel(summary, title="📋 Resumo da Conversa", border_style="cyan"))
    
    async def _show_project_health(self):
        """Mostra saúde do projeto."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("🔍 Analisando saúde do projeto..."),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Analisando...", total=None)
                
                health_report = await self.health_monitor.run_full_analysis(self.project_path)
                
                progress.update(task, description="✅ Análise concluída")
            
            # Formata relatório
            health_summary = f"""
**📊 Saúde do Projeto: {health_report.get('overall_score', 0):.1f}/100**

**🔍 Métricas:**
- Erros detectados: {health_report.get('errors_found', 0)}
- Qualidade do código: {health_report.get('code_quality_score', 0):.1f}/10
- Performance: {health_report.get('performance_score', 0):.1f}/10
- Documentação: {health_report.get('documentation_score', 0):.1f}/10

**📁 Arquivos analisados:** {health_report.get('files_analyzed', 0)}
**⏱️ Tempo de análise:** {health_report.get('analysis_time', 0):.2f}s
"""
            
            score = health_report.get('overall_score', 0)
            border_color = "green" if score > 80 else "yellow" if score > 50 else "red"
            
            self.console.print(Panel(health_summary, title="🏥 Saúde do Projeto", border_style=border_color))
            
        except Exception as e:
            error_msg = humanize_error(e, "Análise de saúde")
            self.console.print(f"[red]{error_msg}[/red]")
    
    async def _show_help(self):
        """Mostra ajuda."""
        help_text = """
**🤖 Gemini Code - Comandos Disponíveis**

**💬 Conversação Natural:**
- "Crie um arquivo chamado test.py"
- "Corrija os erros no projeto"
- "Analise a performance do código"
- "Faça commit das mudanças"

**🧠 Memória e Contexto:**
- `memoria` - Status da memória
- `conversa` - Resumo da conversa atual
- `reset` - Reseta conversa (mantém memória)

**🔧 Debug e Configuração:**
- `debug on/off` - Ativa/desativa modo debug
- `saude` - Saúde do projeto
- `status` - Status geral

**📂 Navegação:**
- "Vá para a pasta src"
- "Liste os arquivos"
- "Mostre o conteúdo de arquivo.py"

**🏃 Desenvolvimento:**
- "Crie um agente chamado [nome]"
- "Gere testes para [arquivo]"
- "Otimize a performance"
- "Execute os testes"

**🚀 Git:**
- "Faça commit"
- "Envie para o GitHub"
- "Mostre o status do git"

**ℹ️ Sistema:**
- `ajuda` - Esta ajuda
- `sair` - Sair do sistema
"""
        
        self.console.print(Panel(help_text, title="📚 Ajuda", border_style="blue"))
    
    async def _identify_simple_execution_intent(self, user_input: str) -> Optional[Dict]:
        """
        Identifica se o input do usuário é um comando simples que requer execução direta.
        Utiliza o NLPEnhanced para classificar a intenção.
        """
        try:
            nlp_result = await self.nlp.identify_intent(user_input)
            self.logger.info(f"NLP result for simple execution check: {nlp_result}")

            simple_execution_intents = [
                'create_file',
                'delete', 
                'run_command',
                'create_feature',  # Adicionar para capturar mais comandos
                'create_agent'     # Adicionar para capturar mais comandos
            ]

            # Adicionar uma verificação de confiança mínima
            if nlp_result['intent'] in simple_execution_intents and nlp_result['confidence'] > 70:
                
                if nlp_result['intent'] == 'delete':
                    target_entity = nlp_result['entities'].get('target')
                    if target_entity:
                        return {'type': 'delete', 'target': target_entity, 'raw_input': user_input}

                elif nlp_result['intent'] == 'run_command':
                    # Tenta extrair o comando real a ser executado
                    import re
                    
                    # Padrões para extrair comandos
                    command_patterns = [
                        r'(?:execute|roda|execute o comando)\s+(.+)',
                        r'^(ls|dir|pwd|cd|mkdir|rmdir)\s*(.*)$',
                        r'^(git\s+(?:status|log|diff|add|commit|push|pull))\s*(.*)$',
                        r'comando\s+(.+)'
                    ]
                    
                    for pattern in command_patterns:
                        match = re.search(pattern, user_input, re.IGNORECASE)
                        if match:
                            if len(match.groups()) == 1:
                                actual_command_to_run = match.group(1).strip()
                            else:
                                actual_command_to_run = (match.group(1) + ' ' + match.group(2)).strip()
                            
                            if actual_command_to_run:
                                return {'type': 'run_command', 'command_to_run': actual_command_to_run, 'raw_input': user_input}
                    
                    # Se não conseguir extrair, pode ser um comando simples conhecido
                    known_simple_commands = [
                        "git status", "git log", "git log -n 5", "dir", "ls", "ls -la", "pwd",
                        "git diff", "git add .", "npm install", "python --version"
                    ]
                    
                    user_lower = user_input.lower().strip()
                    for cmd in known_simple_commands:
                        if user_lower == cmd or user_lower.startswith(cmd + ' '):
                            return {'type': 'run_command', 'command_to_run': user_input.strip(), 'raw_input': user_input}
                        
                elif nlp_result['intent'] == 'create_file':
                    # Verifica se é criação de pasta
                    if any(word in user_input.lower() for word in ['pasta', 'diretório', 'diretorio', 'folder']):
                        # Extrai nome da pasta
                        import re
                        folder_patterns = [
                            r'pasta\s+(?:chamada?\s+)?(?:de\s+)?([\w\-_]+)',
                            r'diret[oó]rio\s+(?:chamado?\s+)?([\w\-_]+)',
                            r'criar?\s+(?:uma?\s+)?pasta\s+([\w\-_]+)',
                            r'crie?\s+(?:uma?\s+)?pasta\s+([\w\-_]+)'
                        ]
                        
                        for pattern in folder_patterns:
                            match = re.search(pattern, user_input, re.IGNORECASE)
                            if match:
                                folder_name = match.group(1)
                                return {'type': 'create_folder', 'folder_name': folder_name, 'raw_input': user_input}
                        
                        # Se não extraiu nome específico, usa nome padrão baseado no contexto
                        if 'ideias' in user_input.lower() or 'ideia' in user_input.lower():
                            return {'type': 'create_folder', 'folder_name': 'ideias', 'raw_input': user_input}
                        else:
                            return {'type': 'create_folder', 'folder_name': 'nova_pasta', 'raw_input': user_input}

            self.logger.info(f"Comando '{user_input}' não identificado como execução simples.")
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao identificar intenção simples: {e}")
            return None

    async def _handle_simple_execution_command(self, user_input: str, intent_details: Dict):
        """
        Lida com a execução de comandos simples identificados.
        Utiliza o self.command_executor para rodar os comandos.
        """
        self.console.print(f"[cyan]⚡ Executando comando simples: {intent_details['type']}[/cyan]")
        
        try:
            # Contexto para execução do comando
            from ..execution.command_executor import CommandContext
            cmd_context = CommandContext(
                working_directory=str(self.project_path),
                environment={},
                timeout=60.0,
                safe_mode=True
            )

            actual_command_to_execute = None
            operation_description = user_input

            if intent_details['type'] == 'delete':
                target = intent_details['target']
                # Confirmação do usuário antes de deletar
                confirm = self.console.input(f"[yellow]⚠️ Tem certeza que quer deletar '{target}'? (s/N): [/yellow]")
                if confirm.lower() == 's':
                    # Usar file_manager é mais seguro
                    from pathlib import Path
                    target_path = Path(self.project_path) / target
                    if target_path.exists():
                        if target_path.is_file():
                            target_path.unlink()
                            self.console.print(f"[green]✅ Arquivo '{target}' deletado com sucesso![/green]")
                        elif target_path.is_dir():
                            import shutil
                            shutil.rmtree(target_path)
                            self.console.print(f"[green]✅ Pasta '{target}' deletada com sucesso![/green]")
                    else:
                        self.console.print(f"[red]❌ '{target}' não encontrado.[/red]")
                else:
                    self.console.print("[yellow]🚫 Operação cancelada.[/yellow]")
                return

            elif intent_details['type'] == 'create_folder':
                from pathlib import Path
                folder_name = intent_details.get('folder_name', 'nova_pasta')
                folder_path = Path(self.project_path) / folder_name
                
                if folder_path.exists():
                    self.console.print(f"[yellow]⚠️ Pasta '{folder_name}' já existe.[/yellow]")
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    self.console.print(f"[green]✅ Pasta '{folder_name}' criada com sucesso![/green]")
                    self.console.print(f"[dim]📍 Localização: {folder_path}[/dim]")
                return

            elif intent_details['type'] == 'run_command':
                actual_command_to_execute = intent_details.get('command_to_run')
                if not actual_command_to_execute:
                     self.console.print("[red]❌ Não foi possível extrair o comando a ser executado.[/red]")
                     return

            if actual_command_to_execute:
                self.console.print(f"💻 Executando: `{actual_command_to_execute}`")
                result = await self.command_executor.execute_command(actual_command_to_execute, cmd_context)
                
                if result.success:
                    self.console.print(f"[green]✅ Comando executado com sucesso![/green]")
                    if result.stdout:
                        self.console.print(f"Saída:\n{result.stdout}")
                else:
                    self.console.print(f"[red]❌ Falha ao executar comando.[/red]")
                    if result.stderr:
                        self.console.print(f"Erro:\n{result.stderr}")
                    elif result.stdout:
                         self.console.print(f"Saída (pode conter erro):\n{result.stdout}")

                # Salvar na memória
                self.conversation_manager.memory_system.remember_conversation(
                    user_input=operation_description,
                    response=result.stdout if result.success else result.stderr,
                    intent={'intent': intent_details['type'], 'confidence': 90},
                    success=result.success,
                    error=result.stderr if not result.success else None
                )
            
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao executar comando simples: {e}[/red]")
            self.logger.error(f"Erro na execução de comando simples: {e}")

    async def _exit_session(self):
        """Encerra sessão."""
        # Exporta conversa se houve atividade
        if self.conversation_manager.current_context.messages:
            export_path = self.conversation_manager.export_conversation()
            self.console.print(f"[dim]💾 Conversa salva em: {export_path}[/dim]")
        
        self.console.print("[green]✨ Obrigado por usar o Gemini Code![/green]")
        self.console.print("[dim]Sua memória foi salva e estará disponível na próxima sessão.[/dim]")
        self.interactive_mode = False
    
    async def _fallback_to_gemini(self, user_input: str, error: str) -> Dict[str, Any]:
        """Fallback direto para Gemini em caso de erro."""
        try:
            self.console.print("[yellow]🔄 Tentando processamento direto...[/yellow]")
            
            # Contexto mínimo
            context = [{
                'role': 'system',
                'content': f"Erro anterior: {error}. Tente processar: {user_input}"
            }]
            
            response = await self.gemini.generate_response(user_input, context=context)
            
            # Salva na memória como fallback
            self.conversation_manager.memory_system.remember_conversation(
                user_input=user_input,
                response=response,
                intent={'intent': 'fallback', 'confidence': 30},
                success=True,
                error=error
            )
            
            self.console.print(Panel(
                Markdown(response),
                title="🤖 Gemini Code (Modo Direto)",
                border_style="yellow"
            ))
            
            return {
                'response': response,
                'intent': {'intent': 'fallback'},
                'success': True,
                'fallback': True
            }
            
        except Exception as e:
            error_msg = humanize_error(e, "Fallback para Gemini")
            self.console.print(f"[red]❌ {error_msg}[/red]")
            
            return {
                'response': f"Erro crítico: {error_msg}",
                'success': False,
                'error': str(e)
            }
    
    async def process_batch_commands(self, commands: List[str]) -> List[Dict[str, Any]]:
        """Processa múltiplos comandos em lote."""
        results = []
        
        self.console.print(f"[cyan]🔄 Processando {len(commands)} comandos...[/cyan]")
        
        with Progress(console=self.console) as progress:
            task = progress.add_task("Processando comandos...", total=len(commands))
            
            for i, command in enumerate(commands):
                progress.update(task, description=f"Comando {i+1}: {command[:30]}...")
                
                result = await self.process_message_with_memory(command)
                results.append(result)
                
                progress.advance(task)
        
        self.console.print(f"[green]✅ {len(commands)} comandos processados![/green]")
        return results
    
    def export_session(self, include_memory: bool = True) -> str:
        """Exporta sessão completa."""
        return self.conversation_manager.export_conversation(include_memory=include_memory)
    
    async def import_conversation(self, conversation_path: str):
        """Importa conversa de arquivo."""
        try:
            import json
            from datetime import datetime
            
            conversation_file = Path(conversation_path)
            if not conversation_file.exists():
                self.console.print(f"[red]❌ Arquivo não encontrado: {conversation_path}[/red]")
                return False
            
            with open(conversation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar estrutura do arquivo
            required_fields = ['conversation_id', 'messages']
            if not all(field in data for field in required_fields):
                self.console.print("[red]❌ Formato de arquivo inválido[/red]")
                return False
            
            # Importar mensagens para contexto atual
            imported_messages = []
            for msg_data in data['messages']:
                message = {
                    'role': msg_data.get('role', 'user'),
                    'content': msg_data.get('content', ''),
                    'timestamp': datetime.fromisoformat(msg_data.get('timestamp', datetime.now().isoformat())),
                    'intent': msg_data.get('intent')
                }
                imported_messages.append(message)
            
            # Atualizar contexto atual
            self.conversation_manager.current_context.messages.extend(imported_messages)
            
            # Limitar ao tamanho máximo do contexto
            max_messages = self.conversation_manager.max_context_messages
            if len(self.conversation_manager.current_context.messages) > max_messages:
                self.conversation_manager.current_context.messages = \
                    self.conversation_manager.current_context.messages[-max_messages:]
            
            # Importar histórico de intenções se disponível
            if 'intent_history' in data:
                self.conversation_manager.current_context.intent_history.extend(
                    data['intent_history'][-10:]  # Últimas 10 intenções
                )
            
            self.console.print(f"[green]✅ Conversa importada: {len(imported_messages)} mensagens[/green]")
            self.console.print(f"[dim]ID da conversa: {data['conversation_id']}[/dim]")
            
            return True
            
        except json.JSONDecodeError:
            self.console.print("[red]❌ Erro: Arquivo JSON inválido[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao importar conversa: {e}[/red]")
            return False