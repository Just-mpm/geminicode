"""
Learning Engine - Sistema de aprendizado e melhoria contínua
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
import statistics

from ..core.gemini_client import GeminiClient
from ..core.memory_system import MemorySystem
from ..utils.logger import Logger


class LearningType(Enum):
    """Tipos de aprendizado."""
    PATTERN_RECOGNITION = "Pattern Recognition"
    USER_PREFERENCE = "User Preference"
    ERROR_PREVENTION = "Error Prevention"
    PERFORMANCE_OPTIMIZATION = "Performance Optimization"
    CODE_STYLE = "Code Style"
    BEST_PRACTICES = "Best Practices"
    TOOL_USAGE = "Tool Usage"
    PROBLEM_SOLUTION = "Problem Solution"


@dataclass
class LearningEntry:
    """Entrada de aprendizado."""
    id: str
    type: LearningType
    context: str
    observation: str
    outcome: str
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    """Padrão aprendido."""
    id: str
    type: str
    description: str
    occurrences: int
    confidence: float
    first_seen: datetime
    last_seen: datetime
    examples: List[Dict[str, Any]]
    rules: List[str]


@dataclass
class UserPreference:
    """Preferência de usuário aprendida."""
    category: str
    preference: str
    evidence: List[str]
    confidence: float
    frequency: int


@dataclass
class PerformanceInsight:
    """Insight de performance aprendido."""
    operation: str
    average_time: float
    best_time: float
    worst_time: float
    optimization_suggestions: List[str]
    sample_size: int


class LearningEngine:
    """
    Sistema de aprendizado contínuo.
    Aprende com interações, erros e sucessos para melhorar ao longo do tempo.
    """
    
    def __init__(self, gemini_client: GeminiClient, memory_system: MemorySystem):
        self.gemini = gemini_client
        self.memory = memory_system
        self.logger = Logger()
        
        # Banco de dados de aprendizado
        self.db_path = Path('.gemini_code_learning.db')
        self._init_database()
        
        # Caches em memória
        self.patterns: Dict[str, Pattern] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        self.performance_insights: Dict[str, PerformanceInsight] = {}
        
        # Configurações de aprendizado
        self.min_confidence_threshold = 0.6
        self.pattern_detection_threshold = 3  # Mínimo de ocorrências
        
        # Carrega dados existentes
        self._load_learned_data()
    
    def _init_database(self):
        """Inicializa banco de dados de aprendizado."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de aprendizados
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_entries (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            context TEXT NOT NULL,
            observation TEXT NOT NULL,
            outcome TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT
        )
        ''')
        
        # Tabela de padrões
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            occurrences INTEGER NOT NULL,
            confidence REAL NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            examples TEXT,
            rules TEXT
        )
        ''')
        
        # Tabela de preferências
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            category TEXT NOT NULL,
            preference TEXT NOT NULL,
            evidence TEXT NOT NULL,
            confidence REAL NOT NULL,
            frequency INTEGER NOT NULL,
            PRIMARY KEY (category, preference)
        )
        ''')
        
        # Tabela de performance
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            operation TEXT PRIMARY KEY,
            total_time REAL NOT NULL,
            execution_count INTEGER NOT NULL,
            best_time REAL NOT NULL,
            worst_time REAL NOT NULL,
            last_updated TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_learned_data(self):
        """Carrega dados aprendidos do banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Carrega padrões
        cursor.execute('SELECT * FROM patterns')
        for row in cursor.fetchall():
            pattern = Pattern(
                id=row[0],
                type=row[1],
                description=row[2],
                occurrences=row[3],
                confidence=row[4],
                first_seen=datetime.fromisoformat(row[5]),
                last_seen=datetime.fromisoformat(row[6]),
                examples=json.loads(row[7]) if row[7] else [],
                rules=json.loads(row[8]) if row[8] else []
            )
            self.patterns[pattern.id] = pattern
        
        # Carrega preferências
        cursor.execute('SELECT * FROM user_preferences')
        for row in cursor.fetchall():
            pref = UserPreference(
                category=row[0],
                preference=row[1],
                evidence=json.loads(row[2]),
                confidence=row[3],
                frequency=row[4]
            )
            key = f"{pref.category}:{pref.preference}"
            self.user_preferences[key] = pref
        
        conn.close()
        
        self.logger.info(f"📚 Carregados {len(self.patterns)} padrões e {len(self.user_preferences)} preferências")
    
    async def learn_from_interaction(self, interaction: Dict[str, Any]) -> LearningEntry:
        """
        Aprende com uma interação.
        
        Args:
            interaction: Dados da interação
            
        Returns:
            Entrada de aprendizado criada
        """
        # Extrai informações relevantes
        command = interaction.get('command', '')
        result = interaction.get('result', {})
        success = result.get('success', False)
        execution_time = interaction.get('execution_time', 0)
        error = result.get('error', None)
        
        # Determina tipo de aprendizado
        learning_type = self._determine_learning_type(interaction)
        
        # Cria observação
        observation = self._create_observation(command, result, execution_time)
        
        # Determina outcome
        outcome = 'success' if success else f'failure: {error}'
        
        # Calcula confiança
        confidence = self._calculate_confidence(interaction, success)
        
        # Cria entrada de aprendizado
        entry = LearningEntry(
            id=self._generate_id(),
            type=learning_type,
            context=command,
            observation=observation,
            outcome=outcome,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata=interaction
        )
        
        # Salva no banco
        self._save_learning_entry(entry)
        
        # Processa aprendizados
        await self._process_learning(entry)
        
        return entry
    
    def _determine_learning_type(self, interaction: Dict[str, Any]) -> LearningType:
        """Determina tipo de aprendizado da interação."""
        command = interaction.get('command', '').lower()
        
        if 'error' in interaction.get('result', {}):
            return LearningType.ERROR_PREVENTION
        elif 'performance' in command or 'optimize' in command:
            return LearningType.PERFORMANCE_OPTIMIZATION
        elif 'style' in command or 'format' in command:
            return LearningType.CODE_STYLE
        elif any(tool in command for tool in ['create', 'modify', 'delete']):
            return LearningType.TOOL_USAGE
        else:
            return LearningType.PATTERN_RECOGNITION
    
    def _create_observation(self, command: str, result: Dict[str, Any], 
                          execution_time: float) -> str:
        """Cria observação da interação."""
        parts = [f"Command: {command}"]
        
        if result.get('success'):
            parts.append(f"Succeeded in {execution_time:.2f}s")
        else:
            parts.append(f"Failed: {result.get('error', 'Unknown error')}")
        
        if 'files_affected' in result:
            parts.append(f"Files affected: {len(result['files_affected'])}")
        
        return " | ".join(parts)
    
    def _calculate_confidence(self, interaction: Dict[str, Any], success: bool) -> float:
        """Calcula confiança no aprendizado."""
        base_confidence = 0.7 if success else 0.5
        
        # Ajusta baseado em fatores
        if interaction.get('verified', False):
            base_confidence += 0.2
        
        if interaction.get('user_feedback') == 'positive':
            base_confidence += 0.1
        elif interaction.get('user_feedback') == 'negative':
            base_confidence -= 0.2
        
        return max(0.1, min(1.0, base_confidence))
    
    def _generate_id(self) -> str:
        """Gera ID único."""
        import uuid
        return f"learn_{uuid.uuid4().hex[:8]}"
    
    def _save_learning_entry(self, entry: LearningEntry):
        """Salva entrada de aprendizado no banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO learning_entries 
        (id, type, context, observation, outcome, confidence, timestamp, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.type.value,
            entry.context,
            entry.observation,
            entry.outcome,
            entry.confidence,
            entry.timestamp.isoformat(),
            json.dumps(entry.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _process_learning(self, entry: LearningEntry):
        """Processa entrada de aprendizado."""
        # Detecta padrões
        await self._detect_patterns(entry)
        
        # Atualiza preferências
        await self._update_preferences(entry)
        
        # Atualiza métricas de performance
        if entry.type == LearningType.PERFORMANCE_OPTIMIZATION:
            await self._update_performance_metrics(entry)
        
        # Aprende com erros
        if entry.type == LearningType.ERROR_PREVENTION:
            await self._learn_from_error(entry)
    
    async def _detect_patterns(self, entry: LearningEntry):
        """Detecta padrões nos aprendizados."""
        # Busca entradas similares
        similar_entries = self._find_similar_entries(entry)
        
        if len(similar_entries) >= self.pattern_detection_threshold:
            # Cria ou atualiza padrão
            pattern = await self._create_pattern(entry, similar_entries)
            
            if pattern and pattern.confidence >= self.min_confidence_threshold:
                self.patterns[pattern.id] = pattern
                self._save_pattern(pattern)
                self.logger.info(f"🎯 Novo padrão detectado: {pattern.description}")
    
    def _find_similar_entries(self, entry: LearningEntry) -> List[LearningEntry]:
        """Encontra entradas similares."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Busca por contexto similar
        cursor.execute('''
        SELECT * FROM learning_entries
        WHERE type = ? AND context LIKE ?
        ORDER BY timestamp DESC
        LIMIT 20
        ''', (entry.type.value, f"%{entry.context.split()[0]}%"))
        
        similar = []
        for row in cursor.fetchall():
            similar_entry = LearningEntry(
                id=row[0],
                type=LearningType(row[1]),
                context=row[2],
                observation=row[3],
                outcome=row[4],
                confidence=row[5],
                timestamp=datetime.fromisoformat(row[6]),
                metadata=json.loads(row[7]) if row[7] else {}
            )
            similar.append(similar_entry)
        
        conn.close()
        return similar
    
    async def _create_pattern(self, entry: LearningEntry, 
                            similar_entries: List[LearningEntry]) -> Optional[Pattern]:
        """Cria padrão baseado em entradas similares."""
        if not similar_entries:
            return None
        
        # Analisa commonalities
        contexts = [e.context for e in similar_entries]
        outcomes = [e.outcome for e in similar_entries]
        
        # Se maioria tem mesmo outcome, é um padrão
        most_common_outcome = max(set(outcomes), key=outcomes.count)
        outcome_frequency = outcomes.count(most_common_outcome) / len(outcomes)
        
        if outcome_frequency < 0.7:  # Não há padrão claro
            return None
        
        # Cria padrão
        pattern = Pattern(
            id=self._generate_id(),
            type=entry.type.value,
            description=f"Pattern: {entry.context.split()[0]} usually {most_common_outcome}",
            occurrences=len(similar_entries),
            confidence=outcome_frequency,
            first_seen=min(e.timestamp for e in similar_entries),
            last_seen=max(e.timestamp for e in similar_entries),
            examples=[{'context': e.context, 'outcome': e.outcome} for e in similar_entries[:3]],
            rules=[f"When {entry.context.split()[0]}, expect {most_common_outcome}"]
        )
        
        return pattern
    
    def _save_pattern(self, pattern: Pattern):
        """Salva padrão no banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO patterns
        (id, type, description, occurrences, confidence, first_seen, last_seen, examples, rules)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.id,
            pattern.type,
            pattern.description,
            pattern.occurrences,
            pattern.confidence,
            pattern.first_seen.isoformat(),
            pattern.last_seen.isoformat(),
            json.dumps(pattern.examples),
            json.dumps(pattern.rules)
        ))
        
        conn.commit()
        conn.close()
    
    async def _update_preferences(self, entry: LearningEntry):
        """Atualiza preferências do usuário."""
        # Analisa comando para extrair preferências
        if entry.type == LearningType.USER_PREFERENCE or 'prefer' in entry.context.lower():
            preference = await self._extract_preference(entry)
            
            if preference:
                key = f"{preference.category}:{preference.preference}"
                
                if key in self.user_preferences:
                    # Atualiza existente
                    existing = self.user_preferences[key]
                    existing.frequency += 1
                    existing.evidence.append(entry.context)
                    existing.confidence = min(1.0, existing.confidence + 0.05)
                else:
                    # Nova preferência
                    self.user_preferences[key] = preference
                
                self._save_preference(preference)
    
    async def _extract_preference(self, entry: LearningEntry) -> Optional[UserPreference]:
        """Extrai preferência de uma entrada."""
        # Usa IA para extrair preferência
        prompt = f"""
Extract user preference from this interaction:

Context: {entry.context}
Outcome: {entry.outcome}

If there's a clear preference, return:
- Category (e.g., 'coding_style', 'tool_choice', 'output_format')
- Preference (what they prefer)

Return None if no clear preference.
"""
        
        try:
            response = await self.gemini.generate_response(prompt)
            
            # Parse response (simplificado)
            if 'None' in response or 'no clear preference' in response.lower():
                return None
            
            # Extrai categoria e preferência (implementação simplificada)
            lines = response.strip().split('\n')
            category = 'general'
            preference = entry.context
            
            for line in lines:
                if 'category' in line.lower():
                    category = line.split(':', 1)[1].strip()
                elif 'preference' in line.lower():
                    preference = line.split(':', 1)[1].strip()
            
            return UserPreference(
                category=category,
                preference=preference,
                evidence=[entry.context],
                confidence=0.7,
                frequency=1
            )
            
        except:
            return None
    
    def _save_preference(self, preference: UserPreference):
        """Salva preferência no banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO user_preferences
        (category, preference, evidence, confidence, frequency)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            preference.category,
            preference.preference,
            json.dumps(preference.evidence[-10:]),  # Últimas 10 evidências
            preference.confidence,
            preference.frequency
        ))
        
        conn.commit()
        conn.close()
    
    async def _update_performance_metrics(self, entry: LearningEntry):
        """Atualiza métricas de performance."""
        if 'execution_time' not in entry.metadata:
            return
        
        operation = entry.context.split()[0]  # Primeira palavra como operação
        execution_time = entry.metadata['execution_time']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Busca métricas existentes
        cursor.execute('SELECT * FROM performance_metrics WHERE operation = ?', (operation,))
        row = cursor.fetchone()
        
        if row:
            # Atualiza
            total_time = row[1] + execution_time
            count = row[2] + 1
            best_time = min(row[3], execution_time)
            worst_time = max(row[4], execution_time)
            
            cursor.execute('''
            UPDATE performance_metrics
            SET total_time = ?, execution_count = ?, best_time = ?, worst_time = ?, last_updated = ?
            WHERE operation = ?
            ''', (total_time, count, best_time, worst_time, datetime.now().isoformat(), operation))
        else:
            # Insere novo
            cursor.execute('''
            INSERT INTO performance_metrics
            (operation, total_time, execution_count, best_time, worst_time, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (operation, execution_time, 1, execution_time, execution_time, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Atualiza cache
        self._update_performance_cache(operation)
    
    def _update_performance_cache(self, operation: str):
        """Atualiza cache de performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM performance_metrics WHERE operation = ?', (operation,))
        row = cursor.fetchone()
        
        if row:
            avg_time = row[1] / row[2]
            
            self.performance_insights[operation] = PerformanceInsight(
                operation=operation,
                average_time=avg_time,
                best_time=row[3],
                worst_time=row[4],
                optimization_suggestions=self._generate_optimization_suggestions(avg_time, row[3]),
                sample_size=row[2]
            )
        
        conn.close()
    
    def _generate_optimization_suggestions(self, avg_time: float, best_time: float) -> List[str]:
        """Gera sugestões de otimização."""
        suggestions = []
        
        if avg_time > best_time * 2:
            suggestions.append("High variance in execution time - investigate environmental factors")
        
        if avg_time > 5.0:
            suggestions.append("Consider caching or parallel processing")
        
        if avg_time > 10.0:
            suggestions.append("Operation is slow - profile and optimize algorithm")
        
        return suggestions
    
    async def _learn_from_error(self, entry: LearningEntry):
        """Aprende com erros para preveni-los."""
        if 'error' not in entry.outcome:
            return
        
        # Analisa erro
        error_analysis = await self._analyze_error(entry)
        
        if error_analysis:
            # Cria regra de prevenção
            prevention_rule = {
                'error_type': error_analysis['type'],
                'context_pattern': error_analysis['context_pattern'],
                'prevention': error_analysis['prevention'],
                'confidence': error_analysis['confidence']
            }
            
            # Salva como padrão de erro
            error_pattern = Pattern(
                id=self._generate_id(),
                type='error_prevention',
                description=f"Prevent {error_analysis['type']}",
                occurrences=1,
                confidence=error_analysis['confidence'],
                first_seen=entry.timestamp,
                last_seen=entry.timestamp,
                examples=[{'error': entry.outcome, 'context': entry.context}],
                rules=[prevention_rule['prevention']]
            )
            
            self.patterns[error_pattern.id] = error_pattern
            self._save_pattern(error_pattern)
    
    async def _analyze_error(self, entry: LearningEntry) -> Optional[Dict[str, Any]]:
        """Analisa erro para aprender."""
        prompt = f"""
Analyze this error to learn how to prevent it:

Context: {entry.context}
Error: {entry.outcome}

Provide:
1. Error type
2. Context pattern that leads to this error
3. How to prevent it
4. Confidence in prevention strategy

Be specific and actionable.
"""
        
        try:
            response = await self.gemini.generate_response(prompt)
            
            # Parse response (simplificado)
            return {
                'type': 'generic_error',  # Seria extraído da resposta
                'context_pattern': entry.context.split()[0],
                'prevention': response[:200],  # Primeiros 200 chars
                'confidence': 0.7
            }
        except:
            return None
    
    def get_learned_patterns(self, pattern_type: Optional[str] = None) -> List[Pattern]:
        """
        Retorna padrões aprendidos.
        
        Args:
            pattern_type: Tipo específico ou None para todos
            
        Returns:
            Lista de padrões
        """
        if pattern_type:
            return [p for p in self.patterns.values() if p.type == pattern_type]
        
        return list(self.patterns.values())
    
    def get_user_preferences(self, category: Optional[str] = None) -> List[UserPreference]:
        """
        Retorna preferências do usuário.
        
        Args:
            category: Categoria específica ou None para todas
            
        Returns:
            Lista de preferências
        """
        if category:
            return [p for p in self.user_preferences.values() if p.category == category]
        
        return list(self.user_preferences.values())
    
    def get_performance_insights(self) -> Dict[str, PerformanceInsight]:
        """Retorna insights de performance."""
        # Atualiza cache se necessário
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT operation FROM performance_metrics')
        for row in cursor.fetchall():
            operation = row[0]
            if operation not in self.performance_insights:
                self._update_performance_cache(operation)
        
        conn.close()
        
        return self.performance_insights
    
    async def apply_learning(self, context: str) -> Dict[str, Any]:
        """
        Aplica aprendizados a um contexto.
        
        Args:
            context: Contexto atual (comando, situação, etc.)
            
        Returns:
            Sugestões e ajustes baseados em aprendizados
        """
        suggestions = {
            'patterns': [],
            'preferences': [],
            'optimizations': [],
            'error_preventions': []
        }
        
        # Busca padrões relevantes
        for pattern in self.patterns.values():
            if self._is_pattern_relevant(pattern, context):
                suggestions['patterns'].append({
                    'pattern': pattern.description,
                    'confidence': pattern.confidence,
                    'suggestion': pattern.rules[0] if pattern.rules else None
                })
        
        # Aplica preferências
        for pref in self.user_preferences.values():
            if pref.category in context.lower() or any(word in context.lower() for word in pref.preference.split()):
                suggestions['preferences'].append({
                    'category': pref.category,
                    'preference': pref.preference,
                    'confidence': pref.confidence
                })
        
        # Sugestões de otimização
        operation = context.split()[0] if context else ''
        if operation in self.performance_insights:
            insight = self.performance_insights[operation]
            suggestions['optimizations'].extend(insight.optimization_suggestions)
        
        # Prevenção de erros
        error_patterns = [p for p in self.patterns.values() if p.type == 'error_prevention']
        for pattern in error_patterns:
            if self._is_pattern_relevant(pattern, context):
                suggestions['error_preventions'].append({
                    'warning': pattern.description,
                    'prevention': pattern.rules[0] if pattern.rules else 'Be careful'
                })
        
        return suggestions
    
    def _is_pattern_relevant(self, pattern: Pattern, context: str) -> bool:
        """Verifica se padrão é relevante para contexto."""
        context_lower = context.lower()
        
        # Verifica se palavras-chave do padrão estão no contexto
        pattern_words = pattern.description.lower().split()
        
        return any(word in context_lower for word in pattern_words[:3])
    
    async def generate_learning_report(self) -> str:
        """Gera relatório de aprendizados."""
        report = f"""# Learning Engine Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total patterns learned: {len(self.patterns)}
- User preferences identified: {len(self.user_preferences)}
- Performance metrics tracked: {len(self.performance_insights)}

## Top Patterns
"""
        
        # Top 5 padrões por confiança
        top_patterns = sorted(self.patterns.values(), key=lambda p: p.confidence, reverse=True)[:5]
        
        for i, pattern in enumerate(top_patterns, 1):
            report += f"\n{i}. **{pattern.description}**\n"
            report += f"   - Confidence: {pattern.confidence:.1%}\n"
            report += f"   - Occurrences: {pattern.occurrences}\n"
            report += f"   - Last seen: {pattern.last_seen.strftime('%Y-%m-%d')}\n"
        
        report += "\n## User Preferences\n"
        
        # Agrupa preferências por categoria
        prefs_by_category = {}
        for pref in self.user_preferences.values():
            if pref.category not in prefs_by_category:
                prefs_by_category[pref.category] = []
            prefs_by_category[pref.category].append(pref)
        
        for category, prefs in prefs_by_category.items():
            report += f"\n### {category.title()}\n"
            for pref in sorted(prefs, key=lambda p: p.frequency, reverse=True)[:3]:
                report += f"- {pref.preference} (used {pref.frequency} times)\n"
        
        report += "\n## Performance Insights\n"
        
        # Top 5 operações mais lentas
        slow_ops = sorted(
            self.performance_insights.values(),
            key=lambda p: p.average_time,
            reverse=True
        )[:5]
        
        for op in slow_ops:
            report += f"\n**{op.operation}**\n"
            report += f"- Average time: {op.average_time:.2f}s\n"
            report += f"- Best time: {op.best_time:.2f}s\n"
            if op.optimization_suggestions:
                report += f"- Suggestions: {', '.join(op.optimization_suggestions)}\n"
        
        return report
    
    def export_learnings(self, filepath: str):
        """Exporta aprendizados para arquivo."""
        data = {
            'export_date': datetime.now().isoformat(),
            'patterns': [
                {
                    'id': p.id,
                    'type': p.type,
                    'description': p.description,
                    'confidence': p.confidence,
                    'occurrences': p.occurrences,
                    'rules': p.rules
                }
                for p in self.patterns.values()
            ],
            'preferences': [
                {
                    'category': p.category,
                    'preference': p.preference,
                    'confidence': p.confidence,
                    'frequency': p.frequency
                }
                for p in self.user_preferences.values()
            ],
            'performance': [
                {
                    'operation': p.operation,
                    'average_time': p.average_time,
                    'best_time': p.best_time,
                    'sample_size': p.sample_size
                }
                for p in self.performance_insights.values()
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"📤 Exportados aprendizados para {filepath}")
    
    def import_learnings(self, filepath: str):
        """Importa aprendizados de arquivo."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Importa padrões
        for pattern_data in data.get('patterns', []):
            pattern = Pattern(
                id=pattern_data['id'],
                type=pattern_data['type'],
                description=pattern_data['description'],
                occurrences=pattern_data['occurrences'],
                confidence=pattern_data['confidence'],
                first_seen=datetime.now(),  # Usa data atual
                last_seen=datetime.now(),
                examples=[],
                rules=pattern_data['rules']
            )
            
            self.patterns[pattern.id] = pattern
            self._save_pattern(pattern)
        
        self.logger.info(f"📥 Importados {len(data.get('patterns', []))} padrões")