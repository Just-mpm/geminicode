"""
Unit tests for MemorySystem module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_code.core.memory_system import MemorySystem


class TestMemorySystem:
    """Test suite for MemorySystem."""
    
    @pytest.fixture
    def temp_project_path(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_system(self, temp_project_path):
        """MemorySystem instance with temporary directory."""
        return MemorySystem(temp_project_path)
    
    def test_initialization(self, memory_system, temp_project_path):
        """Test MemorySystem initialization."""
        assert memory_system.project_path == Path(temp_project_path)
        assert memory_system.memory_dir.exists()
        assert memory_system.db_path.exists()
        assert memory_system.context_window == 50
        assert isinstance(memory_system.short_term_memory, list)
    
    def test_database_creation(self, memory_system):
        """Test database tables creation."""
        # Database should exist and have tables
        import sqlite3
        conn = sqlite3.connect(str(memory_system.db_path))
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['conversations', 'decisions', 'preferences', 'project_patterns']
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_remember_conversation(self, memory_system):
        """Test conversation memory storage."""
        user_input = "Create a new feature"
        response = "Feature created successfully"
        intent = {
            'intent': 'create_feature',
            'confidence': 0.9,
            'entities': {'feature_type': 'authentication'}
        }
        files_affected = ['auth.py', 'models.py']
        
        # Remember conversation
        memory_system.remember_conversation(
            user_input=user_input,
            response=response,
            intent=intent,
            files_affected=files_affected,
            success=True
        )
        
        # Check short-term memory
        assert len(memory_system.short_term_memory) == 1
        memory_item = memory_system.short_term_memory[0]
        assert memory_item['user_input'] == user_input
        assert memory_item['response'] == response
        assert memory_item['intent'] == intent
        assert memory_item['success'] is True
        
        # Check database storage
        import sqlite3
        conn = sqlite3.connect(str(memory_system.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversations")
        rows = cursor.fetchall()
        assert len(rows) == 1
        conn.close()
    
    def test_remember_decision(self, memory_system):
        """Test decision memory storage."""
        memory_system.remember_decision(
            decision_type='architecture',
            description='Choice of database',
            reason='Need fast queries',
            alternatives=['PostgreSQL', 'MongoDB', 'SQLite'],
            chosen='PostgreSQL',
            outcome='Implemented successfully'
        )
        
        # Check database
        import sqlite3
        conn = sqlite3.connect(str(memory_system.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decisions")
        rows = cursor.fetchall()
        assert len(rows) == 1
        
        row = rows[0]
        assert 'PostgreSQL' in row[5]  # chosen_option
        assert 'architecture' in row[2]  # decision_type
        conn.close()
    
    def test_learn_preference(self, memory_system):
        """Test preference learning."""
        memory_system.learn_preference(
            category='coding_style',
            preference='indentation',
            value='4_spaces',
            confidence=0.9
        )
        
        # Check retrieval
        preferences = memory_system.get_preferences('coding_style')
        assert 'coding_style' in preferences
        assert 'indentation' in preferences['coding_style']
        assert preferences['coding_style']['indentation']['value'] == '4_spaces'
        assert preferences['coding_style']['indentation']['confidence'] == 0.9
    
    def test_detect_pattern(self, memory_system):
        """Test pattern detection and storage."""
        # Add same pattern multiple times
        for i in range(3):
            memory_system.detect_pattern(
                pattern_type='code_style',
                pattern='snake_case_functions',
                description='Functions use snake_case naming'
            )
        
        # Check pattern frequency
        patterns = memory_system.get_project_patterns('code_style')
        assert len(patterns) == 1
        assert patterns[0]['frequency'] == 3
        assert patterns[0]['pattern'] == 'snake_case_functions'
    
    def test_recall_similar_conversations(self, memory_system):
        """Test similar conversation recall."""
        # Add multiple conversations
        conversations = [
            ("Create authentication system", "Auth system created"),
            ("Add login feature", "Login feature added"),
            ("Fix database error", "Database error fixed"),
            ("Create user management", "User management created")
        ]
        
        for user_input, response in conversations:
            memory_system.remember_conversation(
                user_input=user_input,
                response=response,
                success=True
            )
        
        # Search for similar conversations
        similar = memory_system.recall_similar_conversations("create user", limit=2)
        assert len(similar) <= 2
        
        # Should find conversations about creating/authentication
        found_keywords = []
        for conv in similar:
            found_keywords.extend(conv['user_input'].lower().split())
        
        assert any(keyword in found_keywords for keyword in ['create', 'user', 'authentication'])
    
    def test_error_solution_memory(self, memory_system):
        """Test error solution storage and retrieval."""
        error = "ImportError: No module named 'requests'"
        solution = "Install requests with: pip install requests"
        
        # Remember error solution
        memory_system.remember_error_solution(error, solution, True)
        
        # Retrieve similar error solutions
        solutions = memory_system.get_error_solutions("ImportError module requests")
        assert len(solutions) >= 1
        
        found_solution = solutions[0]
        assert 'requests' in found_solution['solution'].lower()
    
    def test_context_summary(self, memory_system):
        """Test context summary generation."""
        # Add some data
        memory_system.remember_conversation("Test input", "Test response", success=True)
        memory_system.learn_preference('ui', 'theme', 'dark', 0.8)
        memory_system.detect_pattern('code', 'clean_code', 'Well structured code')
        
        summary = memory_system.get_context_summary()
        
        assert "Contexto Atual" in summary
        assert "Conversas Recentes" in summary
        assert "Preferências Aprendidas" in summary
        assert "Padrões do Projeto" in summary
    
    def test_short_term_memory_limit(self, memory_system):
        """Test short-term memory context window limit."""
        # Add more conversations than the context window
        for i in range(memory_system.context_window + 10):
            memory_system.remember_conversation(
                user_input=f"Test {i}",
                response=f"Response {i}",
                success=True
            )
        
        # Should not exceed context window
        assert len(memory_system.short_term_memory) <= memory_system.context_window
        
        # Should contain most recent conversations
        last_item = memory_system.short_term_memory[-1]
        assert "Test" in last_item['user_input']
    
    def test_export_memory(self, memory_system):
        """Test memory export functionality."""
        # Add some data
        memory_system.remember_conversation("Export test", "Test response", success=True)
        memory_system.learn_preference('export', 'format', 'json', 0.9)
        
        # Export memory
        export_path = memory_system.export_memory()
        
        # Check export file exists
        assert Path(export_path).exists()
        
        # Check export content
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        assert 'conversations' in export_data
        assert 'preferences' in export_data
        assert len(export_data['conversations']) >= 1
        assert len(export_data['preferences']) >= 1
    
    def test_preference_confidence_filtering(self, memory_system):
        """Test preference filtering by confidence."""
        # Add preferences with different confidence levels
        memory_system.learn_preference('test', 'high_conf', 'value1', 0.9)
        memory_system.learn_preference('test', 'low_conf', 'value2', 0.3)
        
        # Get preferences (should filter low confidence)
        preferences = memory_system.get_preferences('test')
        
        assert 'test' in preferences
        assert 'high_conf' in preferences['test']
        assert 'low_conf' not in preferences['test']  # Filtered out due to low confidence
    
    def test_concurrent_access(self, memory_system):
        """Test concurrent database access."""
        import threading
        import time
        
        def add_conversations():
            for i in range(5):
                memory_system.remember_conversation(
                    user_input=f"Concurrent test {i}",
                    response=f"Response {i}",
                    success=True
                )
                time.sleep(0.01)  # Small delay
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_conversations)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all conversations were stored
        import sqlite3
        conn = sqlite3.connect(str(memory_system.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        count = cursor.fetchone()[0]
        assert count == 15  # 3 threads * 5 conversations each
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__])
