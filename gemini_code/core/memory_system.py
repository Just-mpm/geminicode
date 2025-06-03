"""
Sistema de memória persistente que lembra de todas as conversas e decisões.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib


class MemorySystem:
    """Sistema de memória persistente do Gemini Code."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_dir = self.project_path / '.gemini_code' / 'memory'
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.memory_dir / 'memory.db'
        self._init_database()
        
        # Cache em memória
        self.short_term_memory: List[Dict[str, Any]] = []
        self.context_window = 50  # Últimas N interações
    
    def _init_database(self):
        """Inicializa banco de memória."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de conversas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT,
                assistant_response TEXT,
                intent TEXT,
                entities TEXT,
                files_affected TEXT,
                success BOOLEAN,
                error_message TEXT
            )
        """)
        
        # Tabela de decisões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                decision_type TEXT,
                description TEXT,
                reason TEXT,
                alternatives TEXT,
                chosen_option TEXT,
                outcome TEXT
            )
        """)
        
        # Tabela de preferências aprendidas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                preference TEXT,
                value TEXT,
                confidence REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, preference)
            )
        """)
        
        # Tabela de padrões do projeto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern TEXT,
                description TEXT,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def remember_conversation(self, user_input: str, response: str, 
                            intent: Dict[str, Any] = None, 
                            files_affected: List[str] = None,
                            success: bool = True,
                            error: str = None):
        """Lembra de uma conversa."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations 
            (user_input, assistant_response, intent, entities, files_affected, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_input,
            response,
            json.dumps(intent) if intent else None,
            json.dumps(intent.get('entities', [])) if intent else None,
            json.dumps(files_affected) if files_affected else None,
            success,
            error
        ))
        
        conn.commit()
        conn.close()
        
        # Atualiza memória de curto prazo
        self.short_term_memory.append({
            'timestamp': datetime.now(),
            'user_input': user_input,
            'response': response,
            'intent': intent,
            'success': success
        })
        
        # Mantém apenas contexto recente
        if len(self.short_term_memory) > self.context_window:
            self.short_term_memory.pop(0)
    
    def remember_decision(self, decision_type: str, description: str,
                         reason: str, alternatives: List[str],
                         chosen: str, outcome: str = None):
        """Lembra de uma decisão tomada."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decisions
            (decision_type, description, reason, alternatives, chosen_option, outcome)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            decision_type,
            description,
            reason,
            json.dumps(alternatives),
            chosen,
            outcome
        ))
        
        conn.commit()
        conn.close()
    
    def learn_preference(self, category: str, preference: str, 
                        value: str, confidence: float = 0.8):
        """Aprende uma preferência do usuário."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO preferences
            (category, preference, value, confidence, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (category, preference, value, confidence))
        
        conn.commit()
        conn.close()
    
    def detect_pattern(self, pattern_type: str, pattern: str, description: str):
        """Detecta e armazena um padrão do projeto."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Verifica se padrão já existe
        cursor.execute("""
            SELECT id, frequency FROM project_patterns
            WHERE pattern_type = ? AND pattern = ?
        """, (pattern_type, pattern))
        
        result = cursor.fetchone()
        
        if result:
            # Incrementa frequência
            cursor.execute("""
                UPDATE project_patterns
                SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (result[0],))
        else:
            # Novo padrão
            cursor.execute("""
                INSERT INTO project_patterns
                (pattern_type, pattern, description)
                VALUES (?, ?, ?)
            """, (pattern_type, pattern, description))
        
        conn.commit()
        conn.close()
    
    def recall_similar_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Lembra conversas similares."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Busca por palavras-chave
        keywords = query.lower().split()
        
        # Constrói query
        where_clauses = []
        params = []
        for keyword in keywords[:5]:  # Limita keywords
            where_clauses.append("(LOWER(user_input) LIKE ? OR LOWER(assistant_response) LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        where_sql = " OR ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM conversations
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
        """, params + [limit])
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        return results
    
    def get_preferences(self, category: str = None) -> Dict[str, Any]:
        """Obtém preferências aprendidas."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT * FROM preferences
                WHERE category = ? AND confidence > 0.5
                ORDER BY confidence DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT * FROM preferences
                WHERE confidence > 0.5
                ORDER BY category, confidence DESC
            """)
        
        preferences = {}
        for row in cursor.fetchall():
            cat = row['category']
            if cat not in preferences:
                preferences[cat] = {}
            preferences[cat][row['preference']] = {
                'value': row['value'],
                'confidence': row['confidence']
            }
        
        conn.close()
        return preferences
    
    def get_project_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """Obtém padrões detectados do projeto."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT * FROM project_patterns
                WHERE pattern_type = ?
                ORDER BY frequency DESC
            """, (pattern_type,))
        else:
            cursor.execute("""
                SELECT * FROM project_patterns
                ORDER BY pattern_type, frequency DESC
            """)
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append(dict(row))
        
        conn.close()
        return patterns
    
    def remember_error_solution(self, error: str, solution: str, success: bool):
        """Lembra soluções para erros."""
        # Cria hash do erro para referência rápida
        error_hash = hashlib.md5(error.encode()).hexdigest()[:8]
        
        self.remember_decision(
            decision_type='error_solution',
            description=f"Solução para erro {error_hash}",
            reason=error,
            alternatives=[],
            chosen=solution,
            outcome='success' if success else 'failed'
        )
    
    def get_error_solutions(self, error: str) -> List[Dict[str, Any]]:
        """Busca soluções anteriores para erros similares."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Busca por palavras-chave do erro
        keywords = error.lower().split()[:5]
        
        where_clauses = []
        params = []
        for keyword in keywords:
            where_clauses.append("LOWER(reason) LIKE ?")
            params.append(f"%{keyword}%")
        
        where_sql = " OR ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT * FROM decisions
            WHERE decision_type = 'error_solution' 
            AND ({where_sql})
            AND outcome = 'success'
            ORDER BY timestamp DESC
            LIMIT 5
        """, params)
        
        solutions = []
        for row in cursor.fetchall():
            solutions.append({
                'error': row['reason'],
                'solution': row['chosen_option'],
                'timestamp': row['timestamp']
            })
        
        conn.close()
        return solutions
    
    def get_context_summary(self) -> str:
        """Gera resumo do contexto atual."""
        recent_convs = self.short_term_memory[-5:]
        preferences = self.get_preferences()
        patterns = self.get_project_patterns()
        
        summary = "📊 **Contexto Atual**\n\n"
        
        if recent_convs:
            summary += "🕐 **Conversas Recentes:**\n"
            for conv in recent_convs[-3:]:
                summary += f"- {conv['user_input'][:50]}...\n"
        
        if preferences:
            summary += "\n⚙️ **Preferências Aprendidas:**\n"
            for cat, prefs in list(preferences.items())[:3]:
                summary += f"- {cat}: "
                pref_list = [f"{k}={v['value']}" for k, v in list(prefs.items())[:2]]
                summary += ", ".join(pref_list) + "\n"
        
        if patterns:
            summary += "\n🔍 **Padrões do Projeto:**\n"
            for pattern in patterns[:3]:
                summary += f"- {pattern['pattern_type']}: {pattern['description']}\n"
        
        return summary
    
    def export_memory(self, export_path: str = None) -> str:
        """Exporta memória completa."""
        if not export_path:
            export_path = self.memory_dir / f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        conn = sqlite3.connect(str(self.db_path))
        
        # Exporta todas as tabelas
        export_data = {}
        
        tables = ['conversations', 'decisions', 'preferences', 'project_patterns']
        
        for table in tables:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table}")
            
            export_data[table] = []
            for row in cursor.fetchall():
                export_data[table].append(dict(row))
        
        conn.close()
        
        # Salva JSON
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(export_path)