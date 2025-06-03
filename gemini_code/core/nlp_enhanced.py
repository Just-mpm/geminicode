"""
Sistema NLP aprimorado para processamento 100% natural como Claude Code.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Tipos de intenção expandidos."""
    # Desenvolvimento
    CREATE_AGENT = "create_agent"
    CREATE_FEATURE = "create_feature"
    CREATE_FILE = "create_file"
    CREATE_FUNCTION = "create_function"
    CREATE_COMPONENT = "create_component"
    
    # Modificação
    MODIFY_CODE = "modify_code"
    UPDATE_FEATURE = "update_feature"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    FIX_ERROR = "fix_error"
    
    # Análise
    ANALYZE_PROJECT = "analyze_project"
    ANALYZE_ERROR = "analyze_error"
    ANALYZE_PERFORMANCE = "analyze_performance"
    CHECK_STATUS = "check_status"
    EXPLAIN_CODE = "explain_code"
    
    # Navegação
    NAVIGATE_FOLDER = "navigate_folder"
    LIST_FILES = "list_files"
    SEARCH_CODE = "search_code"
    SHOW_CONTENT = "show_content"
    
    # Git
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_STATUS = "git_status"
    ROLLBACK = "rollback"
    
    # Execução
    RUN_COMMAND = "run_command"
    RUN_TESTS = "run_tests"
    DEBUG = "debug"
    DEPLOY = "deploy"
    
    # Manutenção
    BACKUP = "backup"
    RESTORE = "restore"
    CLEAN = "clean"
    UPDATE_DEPS = "update_dependencies"
    DELETE = "delete"
    
    # Banco de Dados
    DATABASE_QUERY = "database_query"
    DATABASE_CREATE = "database_create"
    DATABASE_MODIFY = "database_modify"
    
    # Emergência
    EMERGENCY = "emergency"
    PANIC = "panic"
    
    # Comunicação
    QUESTION = "question"
    CONFIRMATION = "confirmation"
    CLARIFICATION = "clarification"
    
    # Outros
    UNKNOWN = "unknown"


@dataclass
class NLPIntent:
    """Intenção processada com contexto rico."""
    type: IntentType
    confidence: float
    entities: Dict[str, Any]
    original_text: str
    normalized_text: str
    sentiment: str  # positive, negative, neutral, urgent
    context_clues: List[str]
    suggested_action: Optional[str] = None


class NLPEnhanced:
    """Processador NLP aprimorado estilo Claude Code."""
    
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client
        self.patterns = self._build_patterns()
        self.context_keywords = self._build_context_keywords()
        self.entity_patterns = self._build_entity_patterns()
        self.conversation_history = []
    
    def _build_patterns(self) -> Dict[IntentType, List[Tuple[str, float]]]:
        """Constrói padrões de detecção com confiança."""
        return {
            # CRIAÇÃO - Padrões naturais
            IntentType.CREATE_AGENT: [
                (r'(cri[ae]|faz|construa?|adiciona?|novo|nova)\s+.*\s*agente\s+(\w+)', 0.95),
                (r'(preciso|quero|vamos)\s+.*\s*agente\s+.*\s+(\w+)', 0.90),
                (r'agente\s+(?:chamado|com nome|que se chama)\s+(\w+)', 0.92),
                (r'(agente|agent)\s+(\w+)\s+(?:que|para)', 0.85),
            ],
            
            IntentType.CREATE_FEATURE: [
                (r'(adiciona?|implementa?|cri[ae]|faz)\s+.*\s*(funcionalidade|feature|recurso|sistema)', 0.90),
                (r'(preciso|quero|vamos)\s+.*\s*(botão|tela|página|formulário|dashboard)', 0.88),
                (r'(adiciona|coloca|põe|bota)\s+.*\s*botão\s+(?:de|para)\s+\w+', 0.95),
                (r'(adiciona|cria)\s+.*\s*botão\s+.*\s*(exportar|importar|salvar|enviar)', 0.93),
                (r'botão\s+(?:de|para)\s+(exportar|importar)\s+(\w+)', 0.92),
                (r'(faz|cria)\s+um\s+(sistema|módulo)\s+(?:de|para|que)', 0.85),
                (r'(tipo|estilo|como)\s+(\w+)\s+mas\s+para', 0.82),  # "tipo Uber mas para..."
                (r'(implementa|adiciona)\s+.*\s*(login|autenticação|cadastro)', 0.90),
                (r'(sistema|módulo|tela)\s+(?:de|para)\s+\w+', 0.85),
            ],
            
            # PROBLEMAS - Linguagem coloquial
            IntentType.FIX_ERROR: [
                (r'(tá|está|ta)\s+(dando|com)\s+erro', 0.95),
                (r'(não|nao)\s+(funciona|roda|vai|está funcionando)', 0.93),
                (r'(quebrou|bugou|travou|crashou)', 0.95),
                (r'(conserta|corrige|arruma|resolve)\s+(?:isso|este|o)\s*(erro|problema|bug)?', 0.90),
                (r'por\s*que\s+.*\s*(erro|não funciona|problema)', 0.88),
            ],
            
            IntentType.ANALYZE_ERROR: [
                (r'(que|qual)\s+(?:é o|foi o)\s*(erro|problema)', 0.90),
                (r'(analisa|verifica|olha)\s+.*\s*(erro|problema|bug)', 0.88),
                (r'tem\s+(algum|algo)\s*(errado|problema|erro)', 0.85),
            ],
            
            # PERFORMANCE - Natural
            IntentType.OPTIMIZE: [
                (r'(tá|está|ta)\s+(lento|devagar|pesado|lerdo)', 0.95),
                (r'(sistema|site|aplicação|app)\s+(está|tá|ta)\s+(lento|devagar|pesado)', 0.95),
                (r'(melhora|otimiza|acelera)\s+.*\s*(performance|velocidade|desempenho)?', 0.90),
                (r'(demora|leva)\s+muito\s+tempo', 0.88),
                (r'(mais|muito)\s+(rápido|veloz|ágil)', 0.85),
                (r'muito\s+(lento|devagar)', 0.92),
                (r'performance\s+(ruim|péssima|horrível)', 0.90),
            ],
            
            # NAVEGAÇÃO - Pedidos diretos
            IntentType.NAVIGATE_FOLDER: [
                (r'(?:abre?|vai?|entra?|acessa?)\s+(?:a\s+)?(?:pasta|diretório|folder)\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)', 0.95),
                (r'(?:vamos\s+)?trabalhar\s+(?:na|em)\s+(?:pasta\s+)?([A-Z]:[\\\/][^\s]+|\/[^\s]+)', 0.93),
                (r'(?:muda|troca)\s+(?:para|pra)\s+(?:a\s+)?(?:pasta|diretório)\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)', 0.92),
                (r'cd\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)', 0.98),
                (r'navega\s+(?:para|até)\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)', 0.90),
                # Removido o padrão que captura apenas caminhos sozinhos
            ],
            
            IntentType.LIST_FILES: [
                (r'(lista|listar|mostra|mostrar|exibe|exibir)\s+(os\s+)?arquivos?', 0.95),
                (r'(quais|que)\s+arquivos?\s+(tem|existe|há)', 0.90),
                (r'^ls\s*$', 0.98),
                (r'^dir\s*$', 0.98),
                (r'(mostra|lista)\s+(tudo|todos)', 0.85),
                (r'(arquivos|files)\s+(da|na|no)\s+(pasta|diretório)', 0.88),
            ],
            
            IntentType.SHOW_CONTENT: [
                (r'(mostra|exibe|abre)\s+(?:o\s+)?(?:conteúdo|arquivo)\s+\w+', 0.90),
                (r'(cat|type|more)\s+\w+', 0.95),
                (r'(lê|ler|leia)\s+(?:o\s+)?arquivo\s+\w+', 0.88),
                (r'(vê|ver|visualiza)\s+\w+\.\w+', 0.85),
            ],
            
            # GIT - Linguagem simples
            IntentType.GIT_COMMIT: [
                (r'(salva|guarda)\s+(?:tudo|isso|mudanças)', 0.95),
                (r'(commit|comita)', 0.98),
                (r'(registra|grava)\s+.*\s*alterações', 0.88),
            ],
            
            IntentType.GIT_PUSH: [
                (r'(envia|manda)\s+.*\s*(github|git|repositório|pro git)', 0.95),
                (r'(enviar|mandar)\s+.*\s*(arquivo|arquivos|código|projeto)\s+.*\s*(github|git)', 0.93),
                (r'(push|sobe|upload)', 0.98),
                (r'(publica|compartilha)\s+.*\s*código', 0.85),
                (r'(atualiza|update)\s+.*\s*(github|repositório)', 0.90),
                (r'arquivos\s+.*\s*(atualizados?|novos?)\s+.*\s*(github|git)', 0.88),
            ],
            
            IntentType.ROLLBACK: [
                (r'(volta|desfaz|reverte)\s+.*\s*(tudo|mudanças|como estava)', 0.92),
                (r'(desfaz|cancela)\s+.*\s*(?:que|o que)\s+(?:fiz|fizemos)', 0.90),
                (r'(ontem|antes|versão anterior)', 0.80),
            ],
            
            # EXECUÇÃO - Comandos naturais
            IntentType.RUN_COMMAND: [
                (r'(roda|executa|inicia)\s+(?:o\s+)?(projeto|sistema|aplicação|app)', 0.90),
                (r'(instala)\s+.*\s*(dependências|pacotes|libs)', 0.92),
                (r'(para|mata|finaliza)\s+(?:o\s+)?(servidor|processo)', 0.88),
            ],
            
            IntentType.RUN_TESTS: [
                (r'(testa|roda.*teste|executa.*teste)', 0.95),
                (r'(verifica|checa)\s+se\s+.*\s*funciona', 0.85),
                (r'(simula)\s+.*\s*(usuário|uso|cenário)', 0.82),
            ],
            
            # DEPLOY - Pedidos diretos
            IntentType.DEPLOY: [
                (r'(coloca|põe|bota)\s+.*\s*(online|no ar|em produção)', 0.95),
                (r'(deploy|publica|lança)', 0.98),
                (r'(ativa|sobe)\s+.*\s*(site|aplicação|sistema)', 0.85),
            ],
            
            # BANCO DE DADOS - Natural
            IntentType.DATABASE_QUERY: [
                (r'(mostra|lista|exibe)\s+.*\s*(dados|registros|informações)', 0.88),
                (r'(mostra|exibe|lista)\s+.*\s*(últimos?|recentes?|novos?)\s+\w+', 0.95),
                (r'(mostra|me dá|quero ver)\s+os?\s+\w+', 0.90),
                (r'quantos?\s+.*\s*(tem|existe|há)', 0.85),
                (r'(busca|procura|encontra)\s+.*\s*(?:no banco|na tabela)', 0.90),
                (r'(pedidos?|clientes?|usuários?|vendas?|produtos?)\s+(?:de|da|do)\s+(hoje|ontem|semana|mês)', 0.92),
                (r'últimos?\s+(\d+)?\s*(pedidos?|vendas?|registros?)', 0.93),
                (r'(relatório|dados|informações)\s+(?:de|da|do)\s+\w+', 0.85),
            ],
            
            IntentType.DATABASE_CREATE: [
                (r'(cria|adiciona)\s+.*\s*(tabela|campo|coluna)\s+(?:para|de)', 0.92),
                (r'(guarda|armazena|salva)\s+.*\s*(dados|informações)\s+(?:de|sobre)', 0.85),
            ],
            
            # EMERGÊNCIA - Pânico
            IntentType.EMERGENCY: [
                (r'(socorro|emergência|crítico)', 0.95),
                (r'(urgente)\s+(socorro|ajuda|problema)', 0.93),
                (r'(cliente\s+furioso|chefe\s+bravo|problema\s+sério)', 0.92),
            ],
            
            IntentType.PANIC: [
                (r'(merda|porra|caralho|fudeu)', 0.98),  # Desculpe, mas é realista
                (r'(perdi|sumiu|deletou)\s+tudo', 0.95),
                (r'(site\s+caiu|hackearam|invadiu)', 0.95),
            ],
            
            # MANUTENÇÃO
            IntentType.BACKUP: [
                (r'(faz|cria|gera)\s+.*\s*(backup|cópia)', 0.95),
                (r'(salva|guarda)\s+.*\s*(segurança|backup)', 0.90),
            ],
            
            IntentType.UPDATE_DEPS: [
                (r'(atualiza)\s+.*\s*(dependências|pacotes|bibliotecas)', 0.95),
                (r'(upgrade|update)\s+.*\s*(npm|pip|packages)', 0.92),
            ],
            
            IntentType.CLEAN: [
                (r'(limpa|remove)\s+.*\s*(cache|lixo|desnecessário)', 0.90),
                (r'(organiza|arruma)\s+.*\s*(projeto|código|arquivos)', 0.85),
            ],
            
            IntentType.DELETE: [
                (r'(apague?|apagar|delete|remov[ae]|exclu[ai])\s+.*\s*(arquivo|pasta|diretório)\s+(?:chamad[oa]\s+)?(\w[\w\-\.]*)', 0.95),
                (r'(apague?|apagar|delete|remov[ae]|exclu[ai])\s+(?:o\s+|a\s+|um\s+|uma\s+)?(\w[\w\-\.]*)', 0.92),
                (r'(quero|preciso|pode)\s+(apagar|deletar|remover|excluir)\s+.*\s*(\w[\w\-\.]*)', 0.90),
                (r'(arquivo|pasta)\s+(\w[\w\-\.]*)\s+.*(apague?|delete|remov[ae])', 0.88),
            ],
            
            # AJUDA/INFORMAÇÃO
            IntentType.QUESTION: [
                (r'^(ajuda|help)$', 0.95),
                (r'(preciso\s+de\s+ajuda|me\s+ajuda)', 0.90),
                (r'(como\s+faço|como\s+fazer|como\s+que)', 0.88),
                (r'(o\s+que\s+é|qual\s+é|quais\s+são)', 0.85),
                (r'(pode\s+me\s+ajudar|consegue\s+ajudar)', 0.87),
                (r'\?$', 0.70),  # Qualquer pergunta com interrogação
            ],
        }
    
    def _build_context_keywords(self) -> Dict[str, List[str]]:
        """Keywords que indicam contexto."""
        return {
            'urgency': ['agora', 'já', 'urgente', 'rápido', 'correndo', 'asap'],
            'uncertainty': ['acho', 'talvez', 'será', 'parece', 'possível'],
            'frustration': ['droga', 'saco', 'merda', 'porra', 'irritante'],
            'satisfaction': ['ótimo', 'perfeito', 'legal', 'bacana', 'show'],
            'question': ['como', 'porque', 'quando', 'onde', 'qual', 'quem'],
            'negation': ['não', 'nao', 'nunca', 'jamais', 'nenhum'],
        }
    
    def _build_entity_patterns(self) -> Dict[str, str]:
        """Padrões para extrair entidades."""
        return {
            'agent_name': r'agente\s+(?:chamado\s+)?(\w+)',
            'feature_name': r'(?:funcionalidade|feature|recurso)\s+(?:de\s+)?(\w+)',
            'file_path': r'([A-Z]:\\\\[^\s]+|\/[^\s]+|\w+\.\w+)',
            'folder_path': r'pasta\s+([A-Z]:\\\\[^\s]+|\/[^\s]+)',
            'table_name': r'tabela\s+(?:de\s+)?(\w+)',
            'field_name': r'campo\s+(\w+)',
            'error_type': r'erro\s+(?:de\s+)?(\w+)',
            'time_reference': r'(ontem|hoje|agora|semana passada|mês passado)',
            'quantity': r'(\d+)\s*(?:vezes|registros|usuários|itens)',
        }
    
    def analyze(self, text: str) -> NLPIntent:
        """Analisa texto e retorna intenção rica."""
        # Normaliza texto
        normalized = self._normalize_text(text)
        
        # Detecta sentimento e urgência
        sentiment = self._detect_sentiment(normalized)
        
        # Identifica intenção principal
        intent_type, confidence = self._detect_intent(normalized)
        
        # Extrai entidades
        entities = self._extract_entities(normalized, intent_type)
        
        # Identifica pistas de contexto
        context_clues = self._extract_context_clues(normalized)
        
        # Sugere ação baseada no contexto
        suggested_action = self._suggest_action(intent_type, entities, context_clues)
        
        # Adiciona ao histórico
        intent = NLPIntent(
            type=intent_type,
            confidence=confidence,
            entities=entities,
            original_text=text,
            normalized_text=normalized,
            sentiment=sentiment,
            context_clues=context_clues,
            suggested_action=suggested_action
        )
        
        self.conversation_history.append(intent)
        
        return intent
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto mantendo naturalidade."""
        # Remove espaços extras mas mantém estrutura
        normalized = ' '.join(text.split())
        
        # Salva caminhos e nomes de arquivos antes de normalizar
        preserved_items = []
        path_pattern = r'([A-Z]:[\\\/][^\s]+|\/[^\s]+|\w+\.\w+)'
        for match in re.finditer(path_pattern, normalized, re.IGNORECASE):
            preserved_items.append((match.start(), match.end(), match.group()))
        
        # Converte para lowercase primeiro
        result = normalized.lower()
        
        # Padroniza algumas variações comuns
        replacements = {
            'tá': 'está',
            'pra': 'para',
            'pro': 'para o',
            'vc': 'você',
            'tb': 'também',
            'n': 'não',
            'q': 'que',
        }
        
        for old, new in replacements.items():
            result = re.sub(rf'\b{old}\b', new, result)
        
        # Restaura itens preservados com sua capitalização original
        for start, end, original in sorted(preserved_items, key=lambda x: x[0], reverse=True):
            result = result[:start] + original + result[end:]
        
        return result
    
    def _detect_intent(self, text: str) -> Tuple[IntentType, float]:
        """Detecta intenção com confiança."""
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        # Para NAVIGATE_FOLDER, primeiro verifica se realmente há um caminho
        has_valid_path = False
        if any(indicator in text.lower() for indicator in ['pasta', 'diretório', 'folder', 'trabalhar', 'cd']):
            # Verifica se há um caminho válido
            path_check = re.search(r'([A-Z]:[\\\/][^\s]+|\/[^\s]+|"[^"]+"|\'[^\']+\')', text, re.IGNORECASE)
            if path_check:
                path_candidate = path_check.group(1).strip('"\'')
                if ('\\' in path_candidate or '/' in path_candidate) and len(path_candidate) > 2:
                    has_valid_path = True
        
        for intent_type, patterns in self.patterns.items():
            # Skip NAVIGATE_FOLDER se não há caminho válido
            if intent_type == IntentType.NAVIGATE_FOLDER and not has_valid_path:
                continue
                
            for pattern, base_confidence in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Ajusta confiança baseado em contexto
                    confidence = self._adjust_confidence(base_confidence, text, intent_type)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type
        
        # Se confiança muito baixa, verifica contexto histórico
        if best_confidence < 0.5 and self.conversation_history:
            hist_intent, hist_confidence = self._infer_from_history(text)
            if hist_confidence > best_confidence:
                best_intent = hist_intent
                best_confidence = hist_confidence
        
        # Se ainda está muito baixo, verifica se é uma pergunta genérica
        if best_confidence < 0.3:
            if any(q in text.lower() for q in ['?', 'como', 'o que', 'qual', 'quando', 'onde']):
                best_intent = IntentType.QUESTION
                best_confidence = 0.6
        
        return best_intent, best_confidence
    
    def _adjust_confidence(self, base_confidence: float, text: str, intent_type: IntentType) -> float:
        """Ajusta confiança baseado em contexto."""
        confidence = base_confidence
        
        # Aumenta confiança se há palavras de urgência para ações
        if any(word in text for word in self.context_keywords['urgency']):
            if intent_type in [IntentType.FIX_ERROR, IntentType.DEPLOY, IntentType.EMERGENCY]:
                confidence *= 1.2
        
        # Diminui confiança se há incerteza
        if any(word in text for word in self.context_keywords['uncertainty']):
            confidence *= 0.8
        
        # Aumenta para comandos diretos (começam com verbo)
        first_word = text.split()[0] if text.split() else ''
        action_verbs = ['cria', 'faz', 'adiciona', 'remove', 'mostra', 'lista', 'executa', 'roda']
        if first_word in action_verbs:
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def _extract_entities(self, text: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extrai entidades relevantes do texto."""
        entities = {}
        
        # Extrai baseado no tipo de intenção
        if intent_type == IntentType.CREATE_AGENT:
            match = re.search(r'agente\s+(?:chamado\s+)?(\w+)', text, re.IGNORECASE)
            if match:
                entities['name'] = match.group(1)
        
        elif intent_type == IntentType.NAVIGATE_FOLDER:
            # Procura caminhos com padrões mais específicos
            path_patterns = [
                r'(?:pasta|diretório|folder)\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)',
                r'(?:trabalhar\s+(?:na|em)\s+)([A-Z]:[\\\/][^\s]+|\/[^\s]+)',
                r'cd\s+([A-Z]:[\\\/][^\s]+|\/[^\s]+)',
                r'"([^"]+)"',  # Caminhos entre aspas
                r"'([^']+)'",  # Caminhos entre aspas simples
            ]
            
            for pattern in path_patterns:
                path_match = re.search(pattern, text, re.IGNORECASE)
                if path_match:
                    path = path_match.group(1).strip()
                    # Valida se parece um caminho real
                    if ('\\' in path or '/' in path) and len(path) > 2:
                        entities['path'] = path
                        break
        
        elif intent_type == IntentType.DELETE:
            # Extrai nome do arquivo/pasta a deletar
            patterns = [
                r'(?:arquivo|pasta)\s+(?:chamad[oa]\s+)?(\w[\w\-\.]+)',
                r'(?:apague?|apagar|delete|remov[ae]|exclu[ai])\s+(?:o\s+|a\s+|um\s+|uma\s+)?(?:arquivo\s+|pasta\s+)?(\w[\w\-\.]+)',
                r'(\w+\.\w+)',  # arquivos com extensão
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['target'] = match.group(1)
                    break
                    
        elif intent_type in [IntentType.DATABASE_QUERY, IntentType.DATABASE_CREATE]:
            # Extrai nomes de tabela/campo
            table_match = re.search(r'tabela\s+(?:de\s+)?(\w+)', text, re.IGNORECASE)
            if table_match:
                entities['table'] = table_match.group(1)
            
            field_match = re.search(r'campo\s+(\w+)', text, re.IGNORECASE)
            if field_match:
                entities['field'] = field_match.group(1)
        
        # Extrai quantidades
        quantity_match = re.search(r'(\d+)\s*(?:vezes|registros|usuários|itens)', text)
        if quantity_match:
            entities['quantity'] = int(quantity_match.group(1))
        
        # Extrai referências temporais
        for time_ref in ['ontem', 'hoje', 'agora', 'semana passada', 'mês passado']:
            if time_ref in text:
                entities['time_reference'] = time_ref
        
        return entities
    
    def _extract_context_clues(self, text: str) -> List[str]:
        """Extrai pistas de contexto."""
        clues = []
        
        # Verifica cada categoria de contexto
        for category, keywords in self.context_keywords.items():
            if any(word in text for word in keywords):
                clues.append(category)
        
        # Adiciona pistas específicas
        if '?' in text:
            clues.append('question')
        if '!' in text:
            clues.append('emphasis')
        if len(text) < 20:
            clues.append('brief_command')
        if len(text) > 100:
            clues.append('detailed_request')
        
        return clues
    
    def _detect_sentiment(self, text: str) -> str:
        """Detecta sentimento do usuário."""
        if any(word in text for word in self.context_keywords['frustration']):
            return 'negative'
        elif any(word in text for word in self.context_keywords['urgency']):
            return 'urgent'
        elif any(word in text for word in self.context_keywords['satisfaction']):
            return 'positive'
        elif '?' in text:
            return 'curious'
        else:
            return 'neutral'
    
    def _suggest_action(self, intent_type: IntentType, entities: Dict[str, Any], 
                       context_clues: List[str]) -> Optional[str]:
        """Sugere ação baseada no contexto."""
        if intent_type == IntentType.UNKNOWN:
            if 'question' in context_clues:
                return "clarify_request"
            else:
                return "suggest_similar_commands"
        
        if 'urgency' in context_clues or 'frustration' in context_clues:
            return "execute_immediately"
        
        if 'uncertainty' in context_clues:
            return "confirm_before_execute"
        
        return None
    
    def _infer_from_history(self, text: str) -> Tuple[IntentType, float]:
        """Infere intenção baseado no histórico."""
        if not self.conversation_history:
            return IntentType.UNKNOWN, 0.0
        
        # Pega última intenção
        last_intent = self.conversation_history[-1]
        
        # Evita repetir navegação de pasta sem novo caminho
        if last_intent.type == IntentType.NAVIGATE_FOLDER:
            # Verifica se há um novo caminho no texto atual
            path_check = re.search(r'([A-Z]:[\\\/][^\s]+|\/[^\s]+)', text, re.IGNORECASE)
            if not path_check:
                # Não repete navegação sem novo caminho
                return IntentType.UNKNOWN, 0.0
        
        # Se é resposta curta, provavelmente é relacionada
        if len(text.split()) <= 3:
            # Respostas afirmativas
            if text.lower() in ['sim', 'isso', 'ok', 'pode', 'vai', 'beleza']:
                # Não infere navegação de pasta por respostas afirmativas
                if last_intent.type != IntentType.NAVIGATE_FOLDER:
                    return last_intent.type, 0.7
            # Respostas negativas
            elif text.lower() in ['não', 'nao', 'cancela', 'deixa']:
                return IntentType.CONFIRMATION, 0.8
        
        return IntentType.UNKNOWN, 0.0
    
    def get_clarification_questions(self, intent: NLPIntent) -> List[str]:
        """Gera perguntas de clarificação naturais."""
        questions = []
        
        if intent.type == IntentType.CREATE_AGENT and 'name' not in intent.entities:
            questions.append("Qual o nome do agente que você quer criar?")
        
        elif intent.type == IntentType.CREATE_FEATURE and not intent.entities:
            questions.append("Pode me dar mais detalhes sobre essa funcionalidade?")
            questions.append("Tem algum exemplo ou referência?")
        
        elif intent.type == IntentType.FIX_ERROR and not intent.entities:
            questions.append("Qual erro está acontecendo?")
            questions.append("Quando começou a dar esse erro?")
        
        elif intent.confidence < 0.5:
            questions.append("Não entendi bem. Pode explicar de outro jeito?")
            questions.append("O que exatamente você quer que eu faça?")
        
        return questions
    
    async def identify_intent(self, text: str) -> Dict[str, Any]:
        """Identifica intenção do texto (compatibilidade com main.py)."""
        intent = self.analyze(text)
        
        # Garante que a confiança mínima seja 1% se não for UNKNOWN
        confidence_percent = int(intent.confidence * 100)
        if intent.type != IntentType.UNKNOWN and confidence_percent == 0:
            confidence_percent = 1
        
        return {
            'intent': intent.type.value,
            'confidence': confidence_percent,
            'entities': intent.entities,
            'sentiment': intent.sentiment,
            'context_clues': intent.context_clues
        }