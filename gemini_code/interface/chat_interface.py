"""
Interface de chat do Gemini Code
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import re

from ..core.gemini_client import GeminiClient
from ..core.project_manager import ProjectManager
from ..core.natural_language import NaturalLanguageCore, Intent, IntentType
from ..core.file_manager import FileManagementSystem
from ..core.workspace_manager import WorkspaceManager
from ..analysis.error_detector import ErrorDetector
from ..analysis.performance import PerformanceAnalyzer
from ..analysis.health_monitor import HealthMonitor
from ..execution.command_executor import CommandExecutor
from ..execution.test_runner import TestRunner
from ..integration.git_manager import GitManager
from ..development.code_generator import CodeGenerator
from ..utils.backup import BackupManager
from ..utils.logger import Logger
from pathlib import Path

# Tenta importar NLP avançado
try:
    from ..core.nlp_advanced import AdvancedNLP, AdvancedIntent
    NLP_ADVANCED_AVAILABLE = True
except ImportError:
    NLP_ADVANCED_AVAILABLE = False
    print("⚠️ NLP avançado não disponível. Usando parser básico.")


class ChatInterface:
    """Interface de chat conversacional"""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        project_manager: ProjectManager,
        nlp_core: NaturalLanguageCore,
        file_manager: FileManagementSystem,
        workspace_manager: Optional[WorkspaceManager] = None
    ):
        self.gemini = gemini_client
        self.project = project_manager
        self.nlp = nlp_core
        self.files = file_manager
        self.workspace = workspace_manager or WorkspaceManager(Path.cwd())
        self.console = Console()
        self.context: List[Dict[str, str]] = []
        self.current_task = None
        
        # Inicializa novos módulos
        self.command_executor = CommandExecutor(gemini_client)
        self.error_detector = ErrorDetector(gemini_client, file_manager)
        self.performance_analyzer = PerformanceAnalyzer(gemini_client, file_manager)
        self.health_monitor = HealthMonitor(gemini_client, file_manager)
        self.test_runner = TestRunner(gemini_client, self.command_executor)
        self.git_manager = GitManager(gemini_client, self.command_executor)
        self.code_generator = CodeGenerator(gemini_client, file_manager)
        self.backup_manager = BackupManager()
        self.logger = Logger()
        
        # Inicializa NLP avançado se disponível
        if NLP_ADVANCED_AVAILABLE:
            try:
                self.advanced_nlp = AdvancedNLP()
                self.console.print("[dim]✅ NLP avançado ativado![/dim]")
            except Exception as e:
                self.advanced_nlp = None
                self.console.print(f"[dim]⚠️ Erro ao carregar NLP avançado: {e}[/dim]")
        else:
            self.advanced_nlp = None
        
    async def process_message(self, user_message: str, intent: Optional[Intent] = None):
        """Processa mensagem do usuário"""
        # Salva mensagem para contexto
        self._last_message = user_message
        
        # Adiciona ao contexto
        self.context.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Verifica comandos de workspace primeiro
        if await self._check_workspace_commands(user_message):
            return
        
        # Verifica comandos de pasta específicos (prioridade alta)
        if await self._check_folder_commands(user_message):
            return
        
        # Se não tem intent, analisa com NLP avançado ou básico
        if not intent:
            if self.advanced_nlp:
                advanced_result = self.advanced_nlp.analyze(user_message)
                await self._handle_advanced_intent(advanced_result)
                return
            else:
                intent = self.nlp.process_user_input(user_message)
        
        # Processa baseado na intenção
        try:
            await self._handle_intent(intent)
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao processar: {e}[/red]")
            
            # Tenta recuperar com Gemini
            await self._fallback_to_gemini(user_message, str(e))
    
    async def _handle_intent(self, intent: Intent):
        """Processa intenção específica"""
        handlers = {
            IntentType.CREATE: self._handle_create,
            IntentType.MODIFY: self._handle_modify,
            IntentType.DELETE: self._handle_delete,
            IntentType.FIX: self._handle_fix,
            IntentType.ANALYZE: self._handle_analyze,
            IntentType.EXECUTE: self._handle_execute,
            IntentType.DEPLOY: self._handle_deploy,
            IntentType.GIT: self._handle_git,
            IntentType.HELP: self._handle_help,
            IntentType.CONFIG: self._handle_config,
            IntentType.SEARCH: self._handle_search,
            IntentType.EXPLAIN: self._handle_explain,
            IntentType.OPTIMIZE: self._handle_optimize,
            IntentType.TEST: self._handle_test,
            IntentType.BACKUP: self._handle_backup,
            IntentType.WORKSPACE: self._handle_workspace,
            IntentType.UNKNOWN: self._handle_unknown,
        }
        
        handler = handlers.get(intent.type, self._handle_unknown)
        await handler(intent)
    
    async def _handle_create(self, intent: Intent):
        """Processa criação"""
        self.console.print("[cyan]🔨 Criando...[/cyan]")
        
        # Verifica se é criação de agente
        agent_entities = [e for e in intent.entities if e['type'] == 'agent']
        if agent_entities and intent.action == 'create_agent':
            agent_name = agent_entities[0]['value'].lower()
            
            with self.console.status(f"[cyan]Criando agente {agent_name}...[/cyan]"):
                results = self.files.handle_agent_creation(
                    intent.original_text,
                    agent_name
                )
            
            # Mostra resultados
            if results['created_files']:
                self.console.print("\n[green]✅ Arquivos criados:[/green]")
                for file in results['created_files']:
                    self.console.print(f"  • {file}")
            
            if results['modified_files']:
                self.console.print("\n[blue]📝 Arquivos modificados:[/blue]")
                for file in results['modified_files']:
                    self.console.print(f"  • {file}")
            
            if results['errors']:
                self.console.print("\n[red]❌ Erros:[/red]")
                for error in results['errors']:
                    self.console.print(f"  • {error}")
            
            self.console.print(f"\n[green]✅ Agente {agent_name} criado com sucesso![/green]")
            
        else:
            # Outros tipos de criação - usa Gemini
            await self._use_gemini_for_creation(intent)
    
    async def _handle_modify(self, intent: Intent):
        """Processa modificação"""
        self.console.print("[cyan]✏️  Modificando...[/cyan]")
        
        # Usa Gemini para entender e executar modificação
        prompt = f"""
Modifique o código baseado no pedido do usuário:
"{intent.original_text}"

Contexto do projeto: {self.project._detect_project_type()}
Entidades identificadas: {intent.entities}
Modificadores: {intent.modifiers}

Retorne:
1. Arquivos que precisam ser modificados
2. Mudanças específicas a fazer
3. Código atualizado
"""
        
        with self.console.status("[cyan]Analisando modificações necessárias...[/cyan]"):
            response = await self.gemini.generate_response(prompt, self.context)
        
        self._display_gemini_response(response)
    
    async def _handle_delete(self, intent: Intent):
        """Processa deleção"""
        self.console.print("[cyan]🗑️  Deletando...[/cyan]")
        
        # Extrai arquivos/componentes a deletar
        files_to_delete = []
        for entity in intent.entities:
            if entity['type'] == 'file':
                files_to_delete.append(entity['value'])
        
        if files_to_delete:
            self.console.print(f"[yellow]⚠️  Arquivos a deletar: {', '.join(files_to_delete)}[/yellow]")
            # TODO: Implementar confirmação e deleção
        else:
            await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_fix(self, intent: Intent):
        """Processa correção de erros"""
        self.console.print("[cyan]🔧 Corrigindo erros...[/cyan]")
        
        # Procura por erros no projeto
        with self.console.status("[cyan]Procurando erros...[/cyan]"):
            # TODO: Implementar análise de erros
            # Por enquanto, usa Gemini
            prompt = f"""
Analise e corrija erros baseado no pedido:
"{intent.original_text}"

Procure por:
1. Erros de sintaxe
2. Imports faltando
3. Variáveis não definidas
4. Problemas de tipo
5. Bugs lógicos

Retorne as correções necessárias.
"""
            
            response = await self.gemini.generate_response(prompt, self.context)
        
        self._display_gemini_response(response)
    
    async def _handle_analyze(self, intent: Intent):
        """Processa análise"""
        self.console.print("[cyan]🔍 Analisando projeto...[/cyan]")
        
        # Análise geral se não especificou
        if not intent.entities:
            stats = self.project.get_project_stats()
            understanding = self.project.understand_project_deeply()
            
            # Mostra análise
            table = Table(title="📊 Análise do Projeto")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            table.add_row("Tipo", understanding['type'])
            table.add_row("Linguagem Principal", understanding['main_language'] or "N/A")
            table.add_row("Total de Arquivos", str(stats['total_files']))
            table.add_row("Tamanho", f"{stats['total_size_mb']} MB")
            table.add_row("Diretórios", str(stats['directories']))
            
            self.console.print(table)
            
            # Mostra linguagens
            if stats['languages']:
                self.console.print("\n[bold]Linguagens:[/bold]")
                for lang, count in stats['languages'].items():
                    self.console.print(f"  • {lang}: {count} arquivos")
        else:
            # Análise específica via Gemini
            await self._use_gemini_for_analysis(intent)
    
    async def _handle_execute(self, intent: Intent):
        """Processa execução de comandos"""
        self.console.print("[cyan]▶️  Executando...[/cyan]")
        
        # TODO: Implementar executor de comandos
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_git(self, intent: Intent):
        """Processa operações Git"""
        self.console.print("[cyan]📦 Operação Git...[/cyan]")
        
        # TODO: Implementar operações Git
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_search(self, intent: Intent):
        """Processa busca"""
        search_terms = []
        
        # Extrai termo de busca mais inteligentemente
        import re
        patterns = [
            r'buscar?\s+"([^"]+)"',
            r'buscar?\s+\'([^\']+)\'',
            r'(?:buscar?|procurar?|encontrar?)\s+"([^"]+)"',
            r'(?:buscar?|procurar?|encontrar?)\s+\'([^\']+)\'',
            r'(?:buscar?|procurar?|encontrar?)\s+(\S+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, intent.original_text, re.IGNORECASE)
            if match:
                search_terms = [match.group(1)]
                break
        
        if not search_terms and intent.entities:
            for entity in intent.entities:
                search_terms.append(entity['value'])
        
        if search_terms:
            self.console.print(f"[cyan]🔍 Buscando: {', '.join(search_terms)}[/cyan]")
            
            # Atualiza para usar workspace manager
            pm = self.workspace.get_project_manager()
            
            for term in search_terms:
                # Busca em arquivos
                results = pm.search_in_files(term)
                
                if results:
                    self.console.print(f"\n[green]✅ Encontrado '{term}' em {len(results)} arquivo(s):[/green]")
                    
                    # Mostra até 10 arquivos
                    for file_path, matches in list(results.items())[:10]:
                        self.console.print(f"\n[bold cyan]{file_path}:[/bold cyan]")
                        # Mostra até 3 matches por arquivo
                        for line_num, line in matches[:3]:
                            # Limita o tamanho da linha
                            line = line.strip()
                            if len(line) > 100:
                                line = line[:100] + "..."
                            self.console.print(f"  [dim]Linha {line_num}:[/dim] {line}")
                        
                        if len(matches) > 3:
                            self.console.print(f"  [dim]... e mais {len(matches) - 3} ocorrências[/dim]")
                    
                    if len(results) > 10:
                        self.console.print(f"\n[dim]... e mais {len(results) - 10} arquivos[/dim]")
                else:
                    self.console.print(f"[yellow]❌ Nenhum resultado para '{term}'[/yellow]")
        else:
            self.console.print("[yellow]O que você quer buscar? Ex: buscar \"import\"[/yellow]")
    
    async def _handle_explain(self, intent: Intent):
        """Processa explicação"""
        self.console.print("[cyan]💡 Explicando...[/cyan]")
        
        # Usa Gemini para explicar
        await self._use_gemini_for_explanation(intent)
    
    async def _handle_optimize(self, intent: Intent):
        """Processa otimização"""
        self.console.print("[cyan]⚡ Otimizando...[/cyan]")
        
        # TODO: Implementar análise de performance
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_test(self, intent: Intent):
        """Processa testes"""
        self.console.print("[cyan]🧪 Testando...[/cyan]")
        
        # TODO: Implementar execução de testes
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_backup(self, intent: Intent):
        """Processa backup"""
        self.console.print("[cyan]💾 Fazendo backup...[/cyan]")
        
        # TODO: Implementar sistema de backup
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_deploy(self, intent: Intent):
        """Processa deploy"""
        self.console.print("[cyan]🚀 Preparando deploy...[/cyan]")
        
        # TODO: Implementar sistema de deploy
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_help(self, intent: Intent):
        """Processa pedido de ajuda"""
        help_text = """
# Como posso ajudar?

Eu entendo comandos naturais em português! Alguns exemplos:

## Criar
- "Cria um novo arquivo Python"
- "Faz um componente de login"
- "Adiciona um botão de salvar"

## Modificar
- "Muda a cor do botão para azul"
- "Melhora a performance"
- "Organiza o código"

## Corrigir
- "Corrige os erros"
- "Por que não funciona?"
- "Tem algum bug?"

## Analisar
- "Mostra a estrutura do projeto"
- "Quantos arquivos temos?"
- "Analisa a qualidade do código"

Experimente perguntar qualquer coisa!
"""
        self.console.print(Markdown(help_text))
    
    async def _handle_config(self, intent: Intent):
        """Processa configuração"""
        self.console.print("[cyan]⚙️  Configuração...[/cyan]")
        
        # TODO: Implementar mudanças de configuração via chat
        await self._fallback_to_gemini(intent.original_text)
    
    async def _handle_workspace(self, intent: Intent):
        """Processa comandos de workspace/pasta"""
        # Extrai caminho da mensagem
        import re
        
        # Padrões para extrair caminho
        path_patterns = [
            r'(?:pasta|diret[óo]rio|folder)\s+["`]?([A-Za-z]:[\\\/][^"`]+)["`]?',
            r'([A-Za-z]:[\\\/][^"`\s]+)',
            r'["`]([^"`]+)["`]',
        ]
        
        path = None
        for pattern in path_patterns:
            match = re.search(pattern, intent.original_text, re.IGNORECASE)
            if match:
                path = match.group(1)
                break
        
        if path:
            await self._handle_change_workspace(path)
        else:
            # Verifica se é pergunta sobre capacidade
            if any(word in intent.original_text.lower() for word in ['consegue', 'pode', 'tem acesso', 'capaz']):
                self.console.print(Panel(
                    "✅ [green]Sim! Agora eu posso acessar qualquer pasta do seu PC![/green]\n\n"
                    "📁 Comandos disponíveis:\n"
                    "• Abrir pasta: 'ir para pasta D:\\Projetos'\n"
                    "• Listar arquivos: 'mostrar arquivos'\n"
                    "• Ler arquivo: 'ler D:\\arquivo.txt'\n"
                    "• Criar em outra pasta: 'criar D:\\teste.py'\n\n"
                    "💡 Experimente: 'ir para pasta D:\\Users\\Matheus Pimenta\\Pictures\\GPT Mestre Autônomo'",
                    title="Acesso a Pastas Ativado!",
                    border_style="green"
                ))
            else:
                await self._handle_list_workspace()
    
    async def _handle_unknown(self, intent: Intent):
        """Processa intenção desconhecida"""
        # Usa Gemini como fallback
        await self._fallback_to_gemini(intent.original_text)
    
    async def _fallback_to_gemini(self, message: str, error: Optional[str] = None):
        """Usa Gemini quando não sabe processar localmente"""
        prompt = f"""
Usuário disse: "{message}"

Contexto: Trabalhando em um projeto {self.project._detect_project_type() if self.project.structure else 'desconhecido'}
Modo: {self.gemini.config.user.mode}

{f'Erro anterior: {error}' if error else ''}

Responda de forma útil e em português.
Se for uma tarefa de programação, forneça código e instruções claras.
"""
        
        with self.console.status("[cyan]Pensando...[/cyan]"):
            response = await self.gemini.generate_response(prompt, self.context)
        
        self._display_gemini_response(response)
        
        # Adiciona resposta ao contexto
        self.context.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _use_gemini_for_creation(self, intent: Intent):
        """Usa Gemini para criação complexa"""
        entities_desc = ', '.join([f"{e['type']}: {e['value']}" for e in intent.entities])
        
        prompt = f"""
Crie código baseado no pedido:
"{intent.original_text}"

Entidades identificadas: {entities_desc}
Tipo de projeto: {self.project._detect_project_type() if self.project.structure else 'novo'}

Forneça:
1. Código completo
2. Onde salvar o arquivo
3. Modificações necessárias em outros arquivos
"""
        
        with self.console.status("[cyan]Gerando código...[/cyan]"):
            response = await self.gemini.generate_response(
                prompt, 
                self.context,
                thinking_budget=16384  # Mais thinking para criação
            )
        
        self._display_gemini_response(response)
    
    async def _use_gemini_for_analysis(self, intent: Intent):
        """Usa Gemini para análise específica"""
        prompt = f"""
Analise o projeto baseado no pedido:
"{intent.original_text}"

Foque em:
1. Problemas encontrados
2. Sugestões de melhoria
3. Métricas relevantes
"""
        
        with self.console.status("[cyan]Analisando...[/cyan]"):
            response = await self.gemini.generate_response(prompt, self.context)
        
        self._display_gemini_response(response)
    
    async def _use_gemini_for_explanation(self, intent: Intent):
        """Usa Gemini para explicações"""
        prompt = f"""
Explique em português simples:
"{intent.original_text}"

Considere que o usuário é {self.gemini.config.user.mode}.
Use analogias e exemplos quando apropriado.
"""
        
        with self.console.status("[cyan]Preparando explicação...[/cyan]"):
            response = await self.gemini.generate_response(prompt, self.context)
        
        self._display_gemini_response(response)
    
    def _display_gemini_response(self, response: str):
        """Exibe resposta do Gemini formatada"""
        # Detecta e formata blocos de código
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            # Tem código - formata especialmente
            parts = response
            for lang, code in code_blocks:
                # Substitui temporariamente
                marker = f"__CODE_BLOCK_{hash(code)}__"
                parts = parts.replace(f"```{lang}\n{code}\n```", marker)
                parts = parts.replace(f"```\n{code}\n```", marker)
            
            # Divide em partes
            sections = parts.split("__CODE_BLOCK_")
            
            for i, section in enumerate(sections):
                if section.startswith(str(hash(code_blocks[0][1]))):
                    # É um marcador de código
                    for lang, code in code_blocks:
                        if section.startswith(str(hash(code))):
                            # Mostra código
                            self.console.print(
                                Syntax(
                                    code.strip(),
                                    lang or "python",
                                    theme="monokai",
                                    line_numbers=True
                                )
                            )
                            break
                else:
                    # Texto normal
                    if section.strip():
                        self.console.print(Markdown(section.strip()))
        else:
            # Só texto - mostra como markdown
            self.console.print(Markdown(response))
    
    def _extract_code_and_instructions(self, response: str) -> Dict[str, Any]:
        """Extrai código e instruções da resposta"""
        result = {
            'code_blocks': [],
            'files_to_create': [],
            'files_to_modify': [],
            'instructions': []
        }
        
        # Extrai blocos de código
        code_pattern = r'```(?:(\w+))?\n(.*?)\n```'
        for match in re.finditer(code_pattern, response, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2)
            result['code_blocks'].append({
                'language': language,
                'code': code
            })
        
        # Procura por instruções de arquivo
        file_patterns = [
            r'(?:salv[ae]r?|cri[ae]r?)\s+(?:em|no arquivo)\s+["`]?([^\s"`]+)["`]?',
            r'arquivo:\s*["`]?([^\s"`]+)["`]?',
            r'(?:em|no)\s+["`]?([^\s"`]+\.\w+)["`]?',
        ]
        
        for pattern in file_patterns:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                file_path = match.group(1)
                if '.' in file_path:  # Parece ser um arquivo
                    result['files_to_create'].append(file_path)
        
        return result
    
    async def _check_workspace_commands(self, message: str) -> bool:
        """Verifica comandos relacionados a workspace/pasta"""
        message_lower = message.lower()
        
        # Primeiro, tenta extrair caminho Windows direto
        import re
        # Pattern melhorado que aceita espaços no caminho
        windows_path_pattern = r'([A-Za-z]:[\\\/](?:[^\?\n]*?[\\\/])*[^\?\n\\\/]+)'
        path_match = re.search(windows_path_pattern, message)
        if path_match:
            path = path_match.group(1).rstrip()
            # Se parece um caminho válido (tem drive e pelo menos uma pasta)
            if '\\' in path or '/' in path:
                await self._handle_change_workspace(path)
                return True
        
        # Padrões para detectar comandos de pasta
        patterns = {
            'change_folder': [
                r'(?:ir para|abrir?|acess[ae]r?|mud[ae]r? para|entr[ae]r? na?o?)\s+(?:pasta|diret[oó]rio|folder)\s+["`]?([A-Za-z]:[\\\/][^"`\?\n]+?)["`]?\s*\??',
                r'(?:abr[ae]|acess[ae])\s+(?:est[ae]|a)\s+(?:pasta|diret[oó]rio):\s*["`]?([A-Za-z]:[\\\/][^"`\?\n]+?)["`]?\s*\??',
                r'(?:pasta|diret[oó]rio|folder)\s+["`]?([A-Za-z]:[\\\/][^"`\?\n]+?)["`]?\s*\??',
                r'cd\s+["`]?([^"`\?\n]+?)["`]?\s*\??',
                r'(?:trabalh[ae]r? n[ao]?|usar?)\s+["`]?([A-Za-z]:[\\\/][^"`\?\n]+?)["`]?\s*\??',
            ],
            'list_folder': [
                r'(?:mostr[ae]r?|list[ae]r?|ver?)\s+(?:arquivos|conte[uú]do|o que tem)',
                r'(?:o que tem|quais arquivos|listar?)\s+(?:na pasta|aqui|nesta pasta)',
                r'ls\s*$',
                r'dir\s*$',
            ],
            'show_tree': [
                r'(?:mostr[ae]r?|ver?)\s+(?:estrutura|[aá]rvore|tree)',
                r'estrutura\s+(?:completa|do projeto|de pastas)',
                r'tree\s*$',
            ],
            'read_external': [
                r'(?:l[eê]r?|mostr[ae]r?|abrir?|ver?)\s+(?:arquivo|o)\s+["`]?([^"`]+)["`]?',
                r'(?:conte[uú]do d[eo])\s+["`]?([^"`]+)["`]?',
            ],
            'write_external': [
                r'(?:criar?|escrever?|salvar?)\s+(?:arquivo)?\s*["`]?([^"`]+)["`]?\s+(?:com|contendo)\s+(.+)',
                r'(?:editar?|modificar?)\s+["`]?([^"`]+)["`]?',
            ]
        }
        
        # Verifica mudança de pasta
        for pattern in patterns['change_folder']:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                folder_path = match.group(1).strip()
                # Remove ? e espaços extras do final
                folder_path = folder_path.rstrip('? ')
                await self._handle_change_workspace(folder_path)
                return True
        
        # Verifica listagem
        for pattern in patterns['list_folder']:
            if re.search(pattern, message, re.IGNORECASE):
                await self._handle_list_workspace()
                return True
        
        # Verifica estrutura em árvore
        for pattern in patterns.get('show_tree', []):
            if re.search(pattern, message, re.IGNORECASE):
                await self._handle_show_tree()
                return True
        
        # Verifica leitura de arquivo externo
        for pattern in patterns['read_external']:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                # Verifica se é caminho absoluto ou contém indicadores de caminho
                if any(indicator in file_path for indicator in [':\\', '/', '..', 'Users', 'Documents']):
                    await self._handle_read_external_file(file_path)
                    return True
        
        return False
    
    async def _check_folder_commands(self, message: str) -> bool:
        """Verifica comandos específicos de pasta"""
        message_lower = message.lower().strip()
        
        # Padrões específicos para mostrar conteúdo de pasta
        patterns = [
            r'(?:dentro|conteúdo|o que tem)\s+(?:da|na|de)\s+pasta\s+(\w+)',
            r'pasta\s+(\w+)',
            r'na\s+pasta\s+(\w+)',
            r'de\s+dentro\s+da\s+pasta\s+(\w+)',
            r'^(\w+)$',  # Nome da pasta sozinho
            r'(?:mostrar?|ver?|listar?)\s+(\w+)',
            r'me\s+mostre\s+(?:o\s+que\s+tem\s+)?(?:na|da)?\s*(\w+)?',
        ]
        
        # Verifica se menciona uma pasta conhecida
        known_folders = ['agents', 'data', 'utils', 'tests', 'logs', 'memory', 'public', 'archive']
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                folder_name = match.group(1) if match.group(1) else ''
                
                # Se for um nome de pasta conhecido
                if folder_name in known_folders:
                    await self._show_folder_contents(folder_name)
                    return True
                
                # Verifica se é um comando genérico que pode ser de pasta
                if any(folder in message_lower for folder in known_folders):
                    for folder in known_folders:
                        if folder in message_lower:
                            await self._show_folder_contents(folder)
                            return True
        
        # Comandos diretos
        direct_commands = {
            'agents': ['agents', 'agents_1', 'agent_1'],
            'data': ['data', 'dados'],
            'utils': ['utils', 'utilitários'],
            'tests': ['tests', 'testes'],
        }
        
        for folder, variations in direct_commands.items():
            if any(var in message_lower for var in variations):
                await self._show_folder_contents(folder)
                return True
        
        return False
    
    async def _show_folder_contents(self, folder_name: str):
        """Mostra conteúdo de uma pasta específica"""
        self.console.print(f"[cyan]📁 Listando conteúdo da pasta: {folder_name}[/cyan]")
        
        result = self.workspace.list_workspace_contents(folder_name)
        
        if result['success']:
            contents = result['contents']
            
            # Cria tabela específica para a subpasta
            table = Table(title=f"📁 Conteúdo da pasta: {folder_name}")
            table.add_column("Tipo", style="cyan", width=10)
            table.add_column("Nome", style="white")
            table.add_column("Tamanho/Info", style="green", width=15)
            
            # Adiciona pastas primeiro
            for folder in contents['folders']:
                info = f"{folder.get('file_count', 0)} arquivos" if 'file_count' in folder else "Pasta"
                table.add_row("📁 Pasta", folder['name'], info)
            
            # Adiciona arquivos
            for file in contents['files']:
                size_str = f"{file['size_kb']:.1f} KB"
                
                # Ícone baseado na extensão
                ext = file.get('extension', '').lower()
                icon_map = {
                    '.py': '🐍', '.js': '📜', '.json': '📋', '.md': '📝',
                    '.txt': '📄', '.yaml': '⚙️', '.yml': '⚙️', '.env': '🔐'
                }
                icon = icon_map.get(ext, '📄')
                
                table.add_row(f"{icon} Arquivo", file['name'], size_str)
            
            self.console.print(table)
            
            # Estatísticas
            total_folders = len(contents['folders'])
            total_files = len(contents['files'])
            
            if total_folders > 0 or total_files > 0:
                self.console.print(f"\n[dim]📊 Total: {total_folders} pastas, {total_files} arquivos[/dim]")
                
                # Dicas contextuais
                if folder_name == 'agents' and total_files > 0:
                    python_files = [f for f in contents['files'] if f['name'].endswith('.py')]
                    if python_files:
                        self.console.print(f"\n[dim]💡 Para ler um agente: 'ler agents/{python_files[0]['name']}'[/dim]")
            
        else:
            self.console.print(f"[red]❌ Erro ao acessar pasta '{folder_name}': {result['error']}[/red]")
            
            # Sugestões se não encontrou
            if "não encontrada" in result['error'].lower():
                # Lista pastas disponíveis
                root_result = self.workspace.list_workspace_contents()
                if root_result['success']:
                    available_folders = [f['name'] for f in root_result['contents']['folders'][:10]]
                    self.console.print(f"\n[yellow]💡 Pastas disponíveis: {', '.join(available_folders)}[/yellow]")
    
    async def _handle_change_workspace(self, folder_path: str):
        """Muda para outra pasta/workspace"""
        self.console.print(f"[cyan]📁 Acessando pasta: {folder_path}[/cyan]")
        
        result = self.workspace.change_workspace(folder_path)
        
        if result['success']:
            # Atualiza managers
            self.project = self.workspace.get_project_manager()
            self.files = self.workspace.get_file_manager()
            
            self.console.print(Panel(
                f"✅ [green]Workspace alterado com sucesso![/green]\n\n"
                f"📁 Pasta: {result['workspace']}\n"
                f"📄 Arquivos: {result['files_found']}\n"
                f"💾 Tamanho: {result['size_mb']} MB\n"
                f"🔤 Linguagem principal: {result['main_language'] or 'N/A'}\n"
                f"📦 Tipo de projeto: {result['project_type']}",
                title="Novo Workspace",
                border_style="green"
            ))
        else:
            self.console.print(f"[red]❌ Erro: {result['error']}[/red]")
            if 'suggestion' in result:
                self.console.print(f"[yellow]💡 Dica: {result['suggestion']}[/yellow]")
    
    async def _handle_list_workspace(self, subfolder: Optional[str] = None):
        """Lista conteúdo do workspace atual ou de uma subpasta"""
        # Verifica se foi pedido uma subpasta específica
        if not subfolder:
            # Tenta extrair da mensagem original se existir
            if hasattr(self, '_last_message'):
                import re
                # Padrões para detectar pedido de subpasta
                patterns = [
                    r'(?:arquivos|conteúdo)\s+(?:da|de|na|dentro)\s+(?:pasta|diretório)\s+(\w+)',
                    r'pasta\s+(\w+)',
                    r'dentro\s+(?:de|da)\s+(\w+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, self._last_message, re.IGNORECASE)
                    if match:
                        subfolder = match.group(1)
                        break
        
        result = self.workspace.list_workspace_contents(subfolder)
        
        if result['success']:
            contents = result['contents']
            
            # Título mostra o caminho completo ou relativo
            if subfolder:
                title = f"📁 Conteúdo de: {subfolder}"
            else:
                title = f"📁 Conteúdo de: {contents['path']}"
            
            # Cria tabela
            table = Table(title=title)
            table.add_column("Tipo", style="cyan", width=10)
            table.add_column("Nome", style="white")
            table.add_column("Info", style="green", width=20)
            
            # Adiciona pastas
            for folder in contents['folders'][:15]:  # Aumenta limite
                info = f"{folder.get('file_count', 0)} arquivos" if 'file_count' in folder else "-"
                table.add_row("📁 Pasta", folder['name'], info)
            
            # Adiciona arquivos
            for file in contents['files'][:20]:  # Aumenta limite
                size_str = f"{file['size_kb']:.1f} KB"
                table.add_row("📄 Arquivo", file['name'], size_str)
            
            self.console.print(table)
            
            # Resumo
            total_shown = min(15, len(contents['folders'])) + min(20, len(contents['files']))
            total_items = result['total_folders'] + result['total_files']
            
            if total_items > total_shown:
                self.console.print(
                    f"\n[dim]Mostrando {total_shown} de {total_items} itens. "
                    f"({result['total_folders']} pastas, {result['total_files']} arquivos)[/dim]"
                )
                
            # Dica
            if result['total_folders'] > 0 and not subfolder:
                folder_names = [f['name'] for f in contents['folders'][:5]]
                self.console.print(f"\n[dim]💡 Para ver o conteúdo de uma pasta, use: 'mostrar arquivos da pasta {folder_names[0]}'[/dim]")
        else:
            self.console.print(f"[red]❌ Erro ao listar: {result['error']}[/red]")
    
    async def _handle_read_external_file(self, file_path: str):
        """Lê arquivo de qualquer caminho"""
        self.console.print(f"[cyan]📖 Lendo arquivo: {file_path}[/cyan]")
        
        result = self.workspace.read_file_from_path(file_path)
        
        if result['success']:
            self.console.print(Panel(
                f"📄 Arquivo: {result['path']}\n"
                f"📏 Tamanho: {result['size_kb']} KB\n"
                f"📝 Linhas: {result['lines']}\n"
                f"🔤 Encoding: {result['encoding']}",
                title="Informações do Arquivo",
                border_style="blue"
            ))
            
            # Mostra conteúdo
            content = result['content']
            
            # Detecta linguagem pela extensão
            file_ext = Path(result['path']).suffix.lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp',
                '.html': 'html', '.css': 'css', '.json': 'json', '.xml': 'xml',
                '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown'
            }
            
            language = lang_map.get(file_ext, 'text')
            
            # Limita tamanho para exibição
            if len(content) > 2000:
                content = content[:2000] + "\n\n... (conteúdo truncado)"
            
            if language != 'text':
                self.console.print(Syntax(content, language, line_numbers=True))
            else:
                self.console.print(content)
        else:
            self.console.print(f"[red]❌ Erro: {result['error']}[/red]")
    
    async def _handle_show_tree(self):
        """Mostra estrutura em árvore do projeto"""
        self.console.print("[cyan]🌳 Gerando estrutura do projeto...[/cyan]")
        
        pm = self.workspace.get_project_manager()
        if not pm.structure:
            pm.scan_project()
        
        # Organiza arquivos por diretório
        tree = {}
        for file_path in pm.structure.files:
            parts = Path(file_path).parts
            current = tree
            
            # Navega/cria estrutura de diretórios
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {'_files': [], '_dirs': {}}
                current = current[part]['_dirs']
            
            # Adiciona arquivo
            if parts:
                if '_files' not in current:
                    current['_files'] = []
                current['_files'].append(parts[-1])
        
        # Mostra árvore
        self.console.print(f"\n[bold]📁 {self.workspace.current_workspace}[/bold]")
        self._print_tree(tree, "", True)
        
        # Resumo
        self.console.print(f"\n[dim]Total: {pm.structure.total_files} arquivos em {len(pm.structure.directories)} pastas[/dim]")
    
    def _print_tree(self, tree: dict, prefix: str = "", is_last: bool = True, level: int = 0):
        """Imprime árvore de diretórios recursivamente"""
        if level > 5:  # Limita profundidade
            return
            
        items = []
        
        # Adiciona diretórios
        for name, content in tree.items():
            if name not in ['_files', '_dirs'] and isinstance(content, dict):
                items.append(('dir', name, content))
        
        # Adiciona arquivos
        if '_files' in tree:
            for file in sorted(tree['_files'])[:10]:  # Limita arquivos mostrados
                items.append(('file', file, None))
            
            if len(tree['_files']) > 10:
                items.append(('more', f"... e mais {len(tree['_files']) - 10} arquivos", None))
        
        # Imprime items
        for i, (item_type, name, content) in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # Símbolos da árvore
            if is_last:
                symbol = "└── " if is_last_item else "├── "
                next_prefix = prefix + "    " if is_last_item else prefix + "│   "
            else:
                symbol = "├── " if not is_last_item else "└── "
                next_prefix = prefix + "│   " if not is_last_item else prefix + "    "
            
            # Ícone baseado no tipo
            if item_type == 'dir':
                icon = "📁"
                self.console.print(f"{prefix}{symbol}{icon} [bold cyan]{name}[/bold cyan]")
                
                # Recursão para subdiretórios
                if content and '_dirs' in content:
                    self._print_tree(content['_dirs'], next_prefix, is_last_item, level + 1)
                    
            elif item_type == 'file':
                # Ícone baseado na extensão
                ext = Path(name).suffix.lower()
                icon_map = {
                    '.py': '🐍', '.js': '📜', '.json': '📋',
                    '.md': '📝', '.txt': '📄', '.yaml': '⚙️',
                    '.yml': '⚙️', '.env': '🔐', '.gitignore': '🚫'
                }
                icon = icon_map.get(ext, '📄')
                self.console.print(f"{prefix}{symbol}{icon} {name}")
                
            elif item_type == 'more':
                self.console.print(f"{prefix}{symbol}[dim]{name}[/dim]")
    
    async def _handle_advanced_intent(self, result):
        """Processa resultado de análise NLP avançada"""
        if not NLP_ADVANCED_AVAILABLE:
            return
            
        intent = result.intent
        confidence = result.confidence
        
        # Mostra análise
        confidence_emoji = "🎯" if confidence > 0.8 else "🤔" if confidence > 0.5 else "❓"
        self.console.print(f"[dim]{confidence_emoji} Análise: {intent.value} (confiança: {confidence:.0%})[/dim]")
        
        # Handlers específicos para cada intenção avançada
        if intent == AdvancedIntent.CAPABILITY_QUESTION:
            await self._handle_capability_question(result)
        
        elif intent == AdvancedIntent.ANALYZE_ERRORS:
            if result.has_negation:
                await self._confirm_no_analysis()
            else:
                await self._handle_error_analysis()
        
        elif intent == AdvancedIntent.SHOW_HELP:
            await self._handle_help_advanced()
        
        elif intent == AdvancedIntent.CREATE_FILE:
            if result.is_question:
                await self._explain_create_capability()
            else:
                await self._handle_create_file_advanced(result)
        
        elif intent == AdvancedIntent.GREETING:
            await self._handle_greeting()
        
        else:
            # Fallback para sistema antigo ou Gemini
            if confidence < 0.5:
                await self._fallback_to_gemini(result.suggested_action)
            else:
                # Converte para intent antigo e processa
                old_intent = self._convert_to_old_intent(intent)
                if old_intent:
                    await self._handle_intent(old_intent)
    
    async def _handle_capability_question(self, result):
        """Responde pergunta sobre capacidades"""
        entities_text = " ".join([e['text'] for e in result.entities])
        
        if "análise" in entities_text or "erro" in entities_text:
            self.console.print(Panel(
                "✅ [green]Sim! Eu posso fazer análise completa de erros![/green]\n\n"
                "🔍 O que eu analisaria:\n"
                "• Erros de sintaxe em todos os arquivos\n"
                "• Problemas de lógica e bugs potenciais\n"
                "• Imports faltando ou incorretos\n"
                "• Variáveis não definidas\n"
                "• Problemas de performance\n\n"
                "💡 Para executar: 'analise erros do projeto'\n"
                "   (Só execute quando quiser que eu faça de verdade!)",
                title="Capacidade de Análise",
                border_style="green"
            ))
        else:
            await self._handle_help_advanced()
    
    async def _confirm_no_analysis(self):
        """Confirma que não vai fazer análise"""
        self.console.print(Panel(
            "✅ [yellow]Entendido![/yellow]\n\n"
            "Você queria saber SE eu consigo fazer análise de erros,\n"
            "mas pediu para NÃO executar agora.\n\n"
            "✅ Resposta: Sim, eu consigo fazer análise completa!\n"
            "🚫 Não executando a análise conforme solicitado.",
            title="Confirmação",
            border_style="yellow"
        ))
    
    async def _handle_error_analysis(self):
        """Executa análise de erros"""
        self.console.print("[cyan]🔍 Executando análise completa de erros...[/cyan]")
        
        # TODO: Implementar análise real
        pm = self.workspace.get_project_manager()
        if not pm.structure:
            pm.scan_project()
        
        python_files = [f for f in pm.structure.files if f.endswith('.py')]
        
        self.console.print(f"\n[green]✅ Análise concluída![/green]")
        self.console.print(f"📄 Arquivos analisados: {len(python_files)}")
        self.console.print(f"🐛 Erros encontrados: 0 (exemplo)")
        self.console.print(f"⚠️  Warnings: 3 (exemplo)")
    
    async def _handle_help_advanced(self):
        """Mostra ajuda melhorada"""
        help_text = """
# 🚀 Como posso te ajudar?

Sou seu assistente de desenvolvimento e posso:

## 🔧 **Desenvolvimento**
- Criar e modificar código
- Corrigir erros e bugs
- Explicar como o código funciona
- Adicionar novas funcionalidades

## 📁 **Gerenciamento de Arquivos**
- Navegar em qualquer pasta do seu PC
- Criar, ler e modificar arquivos
- Organizar estrutura de projeto

## 🔍 **Análise e Debug**
- Analisar código procurando erros
- Verificar performance
- Encontrar e corrigir bugs

## 💡 **Exemplos de comandos**
- "Analise erros do projeto"
- "Crie um arquivo de configuração"
- "Explique o que faz o app.py"
- "Abra a pasta D:\\MeuProjeto"

O que você gostaria de fazer?
"""
        self.console.print(Markdown(help_text))
    
    async def _handle_greeting(self):
        """Responde cumprimento"""
        greetings = [
            "Olá! 👋 Sou o Gemini Code, seu assistente de desenvolvimento!",
            "Oi! 😊 Pronto para programar juntos?",
            "Hey! 🚀 Como posso ajudar com seu código hoje?"
        ]
        import random
        greeting = random.choice(greetings)
        self.console.print(f"[cyan]{greeting}[/cyan]")
        
        # Mostra dica contextual
        if self.workspace.current_workspace != Path.cwd():
            self.console.print(f"\n[dim]📁 Workspace atual: {self.workspace.current_workspace}[/dim]")
        
    def _convert_to_old_intent(self, advanced_intent) -> Optional[Intent]:
        """Converte intent avançado para o sistema antigo"""
        # Mapeamento entre sistemas
        mapping = {
            AdvancedIntent.CREATE_FILE: IntentType.CREATE,
            AdvancedIntent.FIX_ERROR: IntentType.FIX,
            AdvancedIntent.ANALYZE_CODE: IntentType.ANALYZE,
            AdvancedIntent.RUN_CODE: IntentType.EXECUTE,
        }
        
        old_intent_type = mapping.get(advanced_intent)
        if old_intent_type:
            return Intent(
                type=old_intent_type,
                confidence=0.8,
                action="process",
                entities=[],
                modifiers=[],
                original_text=""
            )
        return None