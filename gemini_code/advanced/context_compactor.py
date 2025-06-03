"""
Context Compactor - Compactação inteligente de contexto estilo Claude Code
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from ..core.gemini_client import GeminiClient
from ..core.memory_system import MemorySystem


@dataclass
class ContextItem:
    """Item de contexto para compactação."""
    content: str
    type: str  # 'user', 'assistant', 'system', 'file', 'command'
    timestamp: datetime
    importance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_estimate: int = 0
    should_preserve: bool = False


@dataclass
class CompactionResult:
    """Resultado da compactação de contexto."""
    original_items: int
    compacted_items: int
    original_tokens: int
    compacted_tokens: int
    compression_ratio: float
    preserved_items: List[ContextItem]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompactor:
    """
    Sistema de compactação inteligente de contexto.
    Replica e melhora o comportamento do Claude Code.
    """
    
    def __init__(self, gemini_client: GeminiClient, memory_system: MemorySystem):
        self.gemini = gemini_client
        self.memory = memory_system
        
        # Configurações de compactação
        self.target_compression_ratio = 0.3  # Reduzir para 30% do tamanho original
        self.min_importance_threshold = 0.3
        self.preserve_recent_count = 5
        self.max_context_tokens = 1000000  # 1M tokens
        self.compaction_trigger_threshold = 0.95  # 95% da capacidade
        
        # Pesos para scoring de importância
        self.importance_weights = {
            'recency': 0.3,
            'user_interaction': 0.4,
            'code_relevance': 0.2,
            'error_information': 0.1
        }
        
        # Padrões para identificar conteúdo importante
        self.important_patterns = [
            r'(?i)erro|error|exception|falha|failed',
            r'(?i)importante|critical|urgent|atenção',
            r'(?i)def\s+\w+|class\s+\w+|function\s+\w+',
            r'(?i)todo|fixme|hack|bug',
            r'(?i)api[_\s]key|secret|password|token'
        ]
        
        # Histórico de compactações
        self.compaction_history: List[CompactionResult] = []
    
    async def should_compact(self, context_items: List[ContextItem]) -> bool:
        """Determina se o contexto deve ser compactado."""
        total_tokens = sum(item.tokens_estimate for item in context_items)
        
        # Verifica se excedeu limite
        if total_tokens > self.max_context_tokens * self.compaction_trigger_threshold:
            return True
        
        # Verifica se há muitos itens antigos de baixa importância
        low_importance_count = sum(
            1 for item in context_items 
            if item.importance_score < self.min_importance_threshold
        )
        
        if low_importance_count > len(context_items) * 0.6:  # 60% são de baixa importância
            return True
        
        return False
    
    async def compact_context(self, context_items: List[ContextItem], 
                            instructions: Optional[str] = None) -> CompactionResult:
        """
        Compacta contexto mantendo informações importantes.
        """
        if not context_items:
            return CompactionResult(0, 0, 0, 0, 1.0, [], "Contexto vazio")
        
        # 1. Calcula importância de cada item
        scored_items = await self._score_importance(context_items)
        
        # 2. Identifica itens a preservar
        items_to_preserve = self._select_items_to_preserve(scored_items, instructions)
        
        # 3. Agrupa itens para compactação
        items_to_compact = [item for item in scored_items if item not in items_to_preserve]
        
        # 4. Gera resumo dos itens compactados
        summary = await self._generate_summary(items_to_compact, instructions)
        
        # 5. Calcula métricas
        original_tokens = sum(item.tokens_estimate for item in context_items)
        preserved_tokens = sum(item.tokens_estimate for item in items_to_preserve)
        summary_tokens = self._estimate_tokens(summary)
        
        compacted_tokens = preserved_tokens + summary_tokens
        compression_ratio = compacted_tokens / original_tokens if original_tokens > 0 else 1.0
        
        result = CompactionResult(
            original_items=len(context_items),
            compacted_items=len(items_to_preserve) + 1,  # +1 para o summary
            original_tokens=original_tokens,
            compacted_tokens=compacted_tokens,
            compression_ratio=compression_ratio,
            preserved_items=items_to_preserve,
            summary=summary,
            metadata={
                'instructions': instructions,
                'compacted_at': datetime.now().isoformat(),
                'preservation_criteria': self._get_preservation_criteria(),
                'items_compacted': len(items_to_compact)
            }
        )
        
        # Registra no histórico
        self.compaction_history.append(result)
        
        return result
    
    async def _score_importance(self, context_items: List[ContextItem]) -> List[ContextItem]:
        """Calcula score de importância para cada item."""
        now = datetime.now()
        
        for item in context_items:
            scores = {}
            
            # Score de recência
            age_hours = (now - item.timestamp).total_seconds() / 3600
            scores['recency'] = max(0, 1 - (age_hours / 24))  # Decai ao longo de 24h
            
            # Score de interação do usuário
            if item.type == 'user':
                scores['user_interaction'] = 1.0
            elif item.type == 'assistant' and item.metadata.get('response_to_user'):
                scores['user_interaction'] = 0.8
            else:
                scores['user_interaction'] = 0.2
            
            # Score de relevância de código
            code_indicators = [
                'def ', 'class ', 'import ', 'from ', 'function',
                '.py', '.js', '.ts', '.java', '.cpp', '.c'
            ]
            
            code_score = 0
            for indicator in code_indicators:
                if indicator in item.content.lower():
                    code_score += 0.2
            
            scores['code_relevance'] = min(code_score, 1.0)
            
            # Score de informação de erro
            error_score = 0
            for pattern in self.important_patterns:
                if re.search(pattern, item.content):
                    error_score += 0.3
            
            scores['error_information'] = min(error_score, 1.0)
            
            # Score final ponderado
            final_score = sum(
                scores[category] * weight 
                for category, weight in self.importance_weights.items()
            )
            
            # Ajustes especiais
            if item.should_preserve:
                final_score = 1.0
            
            if any(keyword in item.content.lower() for keyword in ['delete', 'remove', 'drop']):
                final_score *= 1.2  # Aumenta importância de operações destrutivas
            
            item.importance_score = min(final_score, 1.0)
        
        return context_items
    
    def _select_items_to_preserve(self, scored_items: List[ContextItem], 
                                instructions: Optional[str] = None) -> List[ContextItem]:
        """Seleciona itens que devem ser preservados."""
        preserve = []
        
        # 1. Preserva itens marcados explicitamente
        preserve.extend([item for item in scored_items if item.should_preserve])
        
        # 2. Preserva os mais recentes
        recent_items = sorted(scored_items, key=lambda x: x.timestamp, reverse=True)
        preserve.extend(recent_items[:self.preserve_recent_count])
        
        # 3. Preserva itens de alta importância
        high_importance = [
            item for item in scored_items 
            if item.importance_score >= 0.8
        ]
        preserve.extend(high_importance)
        
        # 4. Preserva baseado em instruções customizadas
        if instructions:
            custom_preserves = self._apply_custom_preservation_rules(scored_items, instructions)
            preserve.extend(custom_preserves)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique_preserve = []
        for item in preserve:
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                unique_preserve.append(item)
        
        return unique_preserve
    
    def _apply_custom_preservation_rules(self, items: List[ContextItem], 
                                       instructions: str) -> List[ContextItem]:
        """Aplica regras customizadas de preservação."""
        preserve = []
        instructions_lower = instructions.lower()
        
        # Preserva baseado em palavras-chave nas instruções
        if 'code' in instructions_lower or 'código' in instructions_lower:
            preserve.extend([
                item for item in items 
                if item.type in ['file', 'command'] or 'def ' in item.content
            ])
        
        if 'error' in instructions_lower or 'erro' in instructions_lower:
            preserve.extend([
                item for item in items
                if any(re.search(pattern, item.content) for pattern in self.important_patterns)
            ])
        
        if 'recent' in instructions_lower or 'recente' in instructions_lower:
            # Preserva mais itens recentes
            recent_items = sorted(items, key=lambda x: x.timestamp, reverse=True)
            preserve.extend(recent_items[:10])
        
        return preserve
    
    async def _generate_summary(self, items_to_compact: List[ContextItem], 
                              instructions: Optional[str] = None) -> str:
        """Gera resumo inteligente dos itens compactados."""
        if not items_to_compact:
            return "Nenhum item foi compactado."
        
        # Agrupa itens por tipo e período
        grouped_items = self._group_items_for_summary(items_to_compact)
        
        # Cria prompt para o Gemini
        summary_prompt = self._build_summary_prompt(grouped_items, instructions)
        
        try:
            # Gera resumo usando Gemini
            response = await self.gemini.generate_content(
                summary_prompt,
                max_output_tokens=2048,
                temperature=0.1
            )
            
            summary = response.text if response else "Resumo não disponível"
            
            # Adiciona metadados do resumo
            metadata_summary = self._create_metadata_summary(grouped_items)
            
            full_summary = f"""## Resumo da Sessão Compactada

{summary}

### Estatísticas
- Itens compactados: {len(items_to_compact)}
- Período: {self._get_time_range(items_to_compact)}
- Tipos de conteúdo: {metadata_summary}

*Este resumo foi gerado automaticamente pela compactação de contexto.*
"""
            
            return full_summary
            
        except Exception as e:
            # Fallback para resumo simples
            return self._create_fallback_summary(grouped_items)
    
    def _group_items_for_summary(self, items: List[ContextItem]) -> Dict[str, List[ContextItem]]:
        """Agrupa itens por categoria para resumo."""
        groups = {
            'user_commands': [],
            'assistant_responses': [],
            'file_operations': [],
            'code_snippets': [],
            'errors': [],
            'other': []
        }
        
        for item in items:
            if item.type == 'user':
                groups['user_commands'].append(item)
            elif item.type == 'assistant':
                groups['assistant_responses'].append(item)
            elif item.type == 'file':
                groups['file_operations'].append(item)
            elif any(keyword in item.content for keyword in ['def ', 'class ', 'function']):
                groups['code_snippets'].append(item)
            elif any(re.search(pattern, item.content) for pattern in self.important_patterns):
                groups['errors'].append(item)
            else:
                groups['other'].append(item)
        
        return {k: v for k, v in groups.items() if v}  # Remove grupos vazios
    
    def _build_summary_prompt(self, grouped_items: Dict[str, List[ContextItem]], 
                            instructions: Optional[str] = None) -> str:
        """Constrói prompt para geração de resumo."""
        
        prompt_parts = [
            "Crie um resumo conciso e informativo da seguinte sessão de desenvolvimento:",
            ""
        ]
        
        for group_name, items in grouped_items.items():
            if not items:
                continue
                
            group_title = {
                'user_commands': 'Comandos do Usuário',
                'assistant_responses': 'Respostas do Assistente', 
                'file_operations': 'Operações de Arquivo',
                'code_snippets': 'Trechos de Código',
                'errors': 'Erros e Problemas',
                'other': 'Outras Atividades'
            }.get(group_name, group_name)
            
            prompt_parts.append(f"### {group_title}:")
            
            for item in items[:3]:  # Limita para evitar prompt muito longo
                content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
                prompt_parts.append(f"- {content_preview}")
            
            if len(items) > 3:
                prompt_parts.append(f"... e mais {len(items) - 3} itens")
            
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Instruções para o resumo:",
            "- Foque nos pontos principais e resultados importantes",
            "- Mencione erros encontrados e suas soluções",
            "- Destaque arquivos criados ou modificados",
            "- Use linguagem clara e concisa",
            "- Máximo de 3 parágrafos"
        ])
        
        if instructions:
            prompt_parts.append(f"- Instruções especiais: {instructions}")
        
        return "\\n".join(prompt_parts)
    
    def _create_fallback_summary(self, grouped_items: Dict[str, List[ContextItem]]) -> str:
        """Cria resumo simples como fallback."""
        summary_parts = ["## Resumo da Sessão"]
        
        total_items = sum(len(items) for items in grouped_items.values())
        summary_parts.append(f"Total de {total_items} atividades processadas:")
        
        for group_name, items in grouped_items.items():
            count = len(items)
            group_title = group_name.replace('_', ' ').title()
            summary_parts.append(f"- {group_title}: {count} itens")
        
        return "\\n".join(summary_parts)
    
    def _create_metadata_summary(self, grouped_items: Dict[str, List[ContextItem]]) -> str:
        """Cria resumo dos metadados."""
        summary_parts = []
        
        for group_name, items in grouped_items.items():
            if items:
                group_title = group_name.replace('_', ' ')
                summary_parts.append(f"{group_title} ({len(items)})")
        
        return ", ".join(summary_parts)
    
    def _get_time_range(self, items: List[ContextItem]) -> str:
        """Obtém período temporal dos itens."""
        if not items:
            return "N/A"
        
        timestamps = [item.timestamp for item in items if item.timestamp]
        if not timestamps:
            return "N/A"
        
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        if start_time.date() == end_time.date():
            return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} ({start_time.strftime('%d/%m/%Y')})"
        else:
            return f"{start_time.strftime('%d/%m %H:%M')} - {end_time.strftime('%d/%m %H:%M')}"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens de um texto."""
        # Estimativa simples: ~4 caracteres por token
        return len(text) // 4
    
    def _get_preservation_criteria(self) -> Dict[str, Any]:
        """Retorna critérios de preservação utilizados."""
        return {
            'preserve_recent_count': self.preserve_recent_count,
            'min_importance_threshold': self.min_importance_threshold,
            'importance_weights': self.importance_weights,
            'target_compression_ratio': self.target_compression_ratio
        }
    
    def get_compaction_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de compactação."""
        if not self.compaction_history:
            return {
                'total_compactions': 0,
                'average_compression_ratio': 0,
                'total_tokens_saved': 0
            }
        
        total_compactions = len(self.compaction_history)
        compression_ratios = [result.compression_ratio for result in self.compaction_history]
        average_compression = sum(compression_ratios) / len(compression_ratios)
        
        total_tokens_saved = sum(
            result.original_tokens - result.compacted_tokens 
            for result in self.compaction_history
        )
        
        return {
            'total_compactions': total_compactions,
            'average_compression_ratio': average_compression,
            'total_tokens_saved': total_tokens_saved,
            'last_compaction': self.compaction_history[-1].metadata.get('compacted_at'),
            'best_compression': min(compression_ratios),
            'worst_compression': max(compression_ratios)
        }
    
    def configure_compaction(self, **kwargs):
        """Configura parâmetros de compactação."""
        if 'target_compression_ratio' in kwargs:
            self.target_compression_ratio = kwargs['target_compression_ratio']
        
        if 'preserve_recent_count' in kwargs:
            self.preserve_recent_count = kwargs['preserve_recent_count']
        
        if 'min_importance_threshold' in kwargs:
            self.min_importance_threshold = kwargs['min_importance_threshold']
        
        if 'importance_weights' in kwargs:
            self.importance_weights.update(kwargs['importance_weights'])
    
    async def auto_compact_if_needed(self, context_items: List[ContextItem]) -> Optional[CompactionResult]:
        """Compacta automaticamente se necessário."""
        if await self.should_compact(context_items):
            return await self.compact_context(context_items)
        return None