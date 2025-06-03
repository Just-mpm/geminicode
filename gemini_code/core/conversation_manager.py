"""
Sistema de gerenciamento de conversas com memória contextual.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .memory_system import MemorySystem
from .gemini_client import GeminiClient
from .nlp_enhanced import NLPEnhanced


@dataclass
class ConversationContext:
    """Contexto de uma conversa."""
    conversation_id: str
    messages: List[Dict[str, Any]]
    intent_history: List[Dict[str, Any]]
    current_task: Optional[str] = None
    active_files: List[str] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.active_files is None:
            self.active_files = []
        if self.preferences is None:
            self.preferences = {}


class ConversationManager:
    """Gerencia conversas com memória contextual."""
    
    def __init__(self, project_path: str, gemini_client: GeminiClient):
        self.project_path = project_path
        self.gemini_client = gemini_client
        self.memory_system = MemorySystem(project_path)
        self.nlp = NLPEnhanced(gemini_client)
        
        # Contexto ativo
        self.current_context = ConversationContext(
            conversation_id=self._generate_conversation_id(),
            messages=[],
            intent_history=[]
        )
        
        # Cache de contexto
        self.context_cache = {}
        self.max_context_messages = 20
        
        # Carrega preferências e padrões do usuário
        self._load_user_context()
    
    def _generate_conversation_id(self) -> str:
        """Gera ID único para conversa."""
        return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _load_user_context(self):
        """Carrega contexto do usuário da memória."""
        # Carrega preferências
        preferences = self.memory_system.get_preferences()
        self.current_context.preferences.update(preferences)
        
        # Carrega padrões recentes do projeto
        patterns = self.memory_system.get_project_patterns()
        self.current_context.preferences['project_patterns'] = patterns[:10]
        
        # Carrega conversas recentes para contexto
        recent_conversations = self.memory_system.recall_similar_conversations("", limit=5)
        if recent_conversations:
            # Adiciona resumo das conversas recentes ao contexto
            self.current_context.preferences['recent_activity'] = [
                {
                    'user_input': conv['user_input'][:100],
                    'intent': conv['intent'],
                    'timestamp': conv['timestamp']
                }
                for conv in recent_conversations[:3]
            ]
    
    async def process_message(self, user_input: str) -> Dict[str, Any]:
        """Processa mensagem do usuário com contexto completo."""
        
        # 1. Analisa intenção
        intent_data = await self.nlp.identify_intent(user_input)
        
        # 2. Busca contexto relevante
        relevant_context = await self._get_relevant_context(user_input, intent_data)
        
        # 3. Prepara contexto completo para o Gemini
        full_context = self._prepare_context_for_gemini(user_input, intent_data, relevant_context)
        
        # 4. Gera resposta com contexto
        try:
            response = await self.gemini_client.generate_response(
                user_input,
                context=full_context,
                thinking_budget=self._calculate_thinking_budget(intent_data)
            )
            
            success = True
            error = None
            
        except Exception as e:
            response = f"❌ Erro ao processar mensagem: {str(e)}"
            success = False
            error = str(e)
        
        # 5. Salva na memória
        self._save_to_memory(user_input, response, intent_data, success, error)
        
        # 6. Atualiza contexto atual
        self._update_current_context(user_input, response, intent_data)
        
        # 7. Aprende padrões e preferências
        await self._learn_from_interaction(user_input, intent_data, success)
        
        return {
            'response': response,
            'intent': intent_data,
            'context_used': relevant_context,
            'success': success,
            'conversation_id': self.current_context.conversation_id
        }
    
    async def _get_relevant_context(self, user_input: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Busca contexto relevante para a mensagem."""
        context = {
            'similar_conversations': [],
            'error_solutions': [],
            'user_preferences': {},
            'project_patterns': []
        }
        
        # Busca conversas similares
        similar_convs = self.memory_system.recall_similar_conversations(user_input, limit=3)
        context['similar_conversations'] = similar_convs
        
        # Se é sobre erro, busca soluções anteriores
        if intent_data.get('intent') in ['fix_error', 'analyze_error']:
            error_solutions = self.memory_system.get_error_solutions(user_input)
            context['error_solutions'] = error_solutions
        
        # Busca preferências relevantes
        intent_category = intent_data.get('intent', 'general')
        user_prefs = self.memory_system.get_preferences(intent_category)
        context['user_preferences'] = user_prefs
        
        # Busca padrões do projeto relevantes
        if intent_data.get('intent') in ['create_feature', 'create_file', 'modify_code']:
            patterns = self.memory_system.get_project_patterns('code_style')
            context['project_patterns'] = patterns
        
        return context
    
    def _prepare_context_for_gemini(self, user_input: str, intent_data: Dict[str, Any], 
                                   relevant_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepara contexto formatado para o Gemini."""
        context_messages = []
        
        # Adiciona histórico recente da conversa atual
        recent_messages = self.current_context.messages[-10:]  # Últimas 10 mensagens
        for msg in recent_messages:
            context_messages.append({
                'role': 'user' if msg['role'] == 'user' else 'assistant',
                'content': msg['content'][:500]  # Limita tamanho
            })
        
        # Adiciona contexto de conversas similares se relevante
        if relevant_context['similar_conversations']:
            context_messages.append({
                'role': 'system',
                'content': f"📚 Conversas similares anteriores: {len(relevant_context['similar_conversations'])} encontradas. "
                          f"Última: '{relevant_context['similar_conversations'][0]['user_input'][:100]}...'"
            })
        
        # Adiciona soluções de erro se relevante
        if relevant_context['error_solutions']:
            solutions_text = "; ".join([sol['solution'][:100] for sol in relevant_context['error_solutions'][:2]])
            context_messages.append({
                'role': 'system',
                'content': f"🔧 Soluções anteriores para erros similares: {solutions_text}"
            })
        
        # Adiciona preferências do usuário
        if relevant_context['user_preferences']:
            prefs_text = str(relevant_context['user_preferences'])[:200]
            context_messages.append({
                'role': 'system', 
                'content': f"⚙️ Preferências do usuário: {prefs_text}"
            })
        
        # Adiciona padrões do projeto
        if relevant_context['project_patterns']:
            patterns_text = "; ".join([p['description'][:50] for p in relevant_context['project_patterns'][:3]])
            context_messages.append({
                'role': 'system',
                'content': f"🎯 Padrões do projeto: {patterns_text}"
            })
        
        return context_messages
    
    def _calculate_thinking_budget(self, intent_data: Dict[str, Any]) -> int:
        """Calcula budget de thinking baseado na complexidade."""
        base_budget = 8192
        
        # Ajusta baseado na intenção
        complex_intents = ['create_feature', 'refactor', 'analyze_project', 'fix_error']
        if intent_data.get('intent') in complex_intents:
            base_budget = 16384
        
        # Ajusta baseado na confiança
        confidence = intent_data.get('confidence', 50)
        if confidence < 30:  # Baixa confiança, precisa pensar mais
            base_budget = min(base_budget * 1.5, 24576)
        
        return int(base_budget)
    
    def _save_to_memory(self, user_input: str, response: str, intent_data: Dict[str, Any], 
                       success: bool, error: Optional[str]):
        """Salva interação na memória."""
        files_affected = []
        
        # Detecta arquivos mencionados
        import re
        file_patterns = [
            r'\.py\b', r'\.js\b', r'\.html\b', r'\.css\b', r'\.json\b', r'\.yaml\b', r'\.yml\b'
        ]
        for pattern in file_patterns:
            matches = re.findall(r'\S*' + pattern, user_input + ' ' + response)
            files_affected.extend(matches)
        
        self.memory_system.remember_conversation(
            user_input=user_input,
            response=response,
            intent=intent_data,
            files_affected=files_affected,
            success=success,
            error=error
        )
        
        # Se houve erro, lembra a solução (se houve)
        if error and success:  # Erro resolvido
            self.memory_system.remember_error_solution(error, response, True)
    
    def _update_current_context(self, user_input: str, response: str, intent_data: Dict[str, Any]):
        """Atualiza contexto da conversa atual."""
        # Adiciona mensagens
        self.current_context.messages.extend([
            {
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(),
                'intent': intent_data
            },
            {
                'role': 'assistant', 
                'content': response,
                'timestamp': datetime.now()
            }
        ])
        
        # Mantém apenas mensagens recentes
        if len(self.current_context.messages) > self.max_context_messages:
            self.current_context.messages = self.current_context.messages[-self.max_context_messages:]
        
        # Atualiza histórico de intenções
        self.current_context.intent_history.append(intent_data)
        if len(self.current_context.intent_history) > 10:
            self.current_context.intent_history = self.current_context.intent_history[-10:]
        
        # Atualiza tarefa atual se relevante
        if intent_data.get('intent') in ['create_feature', 'create_agent', 'refactor']:
            self.current_context.current_task = intent_data.get('intent')
    
    async def _learn_from_interaction(self, user_input: str, intent_data: Dict[str, Any], success: bool):
        """Aprende padrões e preferências da interação."""
        
        # Aprende preferências de comunicação
        if len(user_input.split()) < 5:
            self.memory_system.learn_preference(
                'communication', 'style', 'concise', 0.7
            )
        elif len(user_input.split()) > 20:
            self.memory_system.learn_preference(
                'communication', 'style', 'detailed', 0.7
            )
        
        # Aprende preferências de desenvolvimento
        if intent_data.get('intent') == 'create_feature':
            entities = intent_data.get('entities', {})
            if 'language' in entities:
                self.memory_system.learn_preference(
                    'development', 'preferred_language', entities['language'], 0.8
                )
        
        # Detecta padrões de uso
        intent_type = intent_data.get('intent', 'unknown')
        if intent_type != 'unknown':
            self.memory_system.detect_pattern(
                'user_behavior',
                intent_type,
                f"Usuário frequentemente usa comando: {intent_type}"
            )
    
    def get_conversation_summary(self) -> str:
        """Gera resumo da conversa atual."""
        if not self.current_context.messages:
            return "Nenhuma conversa ativa."
        
        total_messages = len(self.current_context.messages)
        user_messages = [msg for msg in self.current_context.messages if msg['role'] == 'user']
        
        # Últimas intenções
        recent_intents = [intent.get('intent', 'unknown') for intent in self.current_context.intent_history[-5:]]
        
        summary = f"""📋 **Resumo da Conversa Atual**

🔢 **Estatísticas:**
- Total de mensagens: {total_messages}
- Mensagens do usuário: {len(user_messages)}
- ID da conversa: {self.current_context.conversation_id}

🎯 **Atividade Recente:**
- Intenções: {', '.join(set(recent_intents))}
- Tarefa atual: {self.current_context.current_task or 'Nenhuma'}

📁 **Arquivos Ativos:**
{chr(10).join([f"- {file}" for file in self.current_context.active_files[:5]]) if self.current_context.active_files else "- Nenhum arquivo ativo"}

🕐 **Última atividade:** {self.current_context.messages[-1]['timestamp'].strftime('%H:%M:%S') if self.current_context.messages else 'N/A'}
"""
        return summary
    
    def reset_conversation(self):
        """Reseta conversa atual mantendo preferências."""
        preferences = self.current_context.preferences.copy()
        
        self.current_context = ConversationContext(
            conversation_id=self._generate_conversation_id(),
            messages=[],
            intent_history=[],
            preferences=preferences
        )
    
    def export_conversation(self, include_memory: bool = False) -> str:
        """Exporta conversa atual."""
        export_data = {
            'conversation_id': self.current_context.conversation_id,
            'messages': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'intent': msg.get('intent')
                }
                for msg in self.current_context.messages
            ],
            'intent_history': self.current_context.intent_history,
            'current_task': self.current_context.current_task,
            'active_files': self.current_context.active_files
        }
        
        if include_memory:
            export_data['memory_export'] = self.memory_system.export_memory()
        
        filename = f"conversation_{self.current_context.conversation_id}.json"
        
        import json
        from pathlib import Path
        
        export_path = Path(self.project_path) / '.gemini_code' / 'conversations' / filename
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(export_path)