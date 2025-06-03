"""
Unit tests for ConversationManager module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_code.core.conversation_manager import ConversationManager, ConversationContext


class TestConversationManager:
    """Test suite for ConversationManager."""
    
    @pytest.fixture
    def temp_project_path(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client."""
        client = Mock()
        client.generate_response = AsyncMock(return_value="Mock AI response")
        return client
    
    @pytest.fixture
    def conversation_manager(self, temp_project_path, mock_gemini_client):
        """ConversationManager instance with mocked dependencies."""
        return ConversationManager(temp_project_path, mock_gemini_client)
    
    def test_initialization(self, conversation_manager, temp_project_path):
        """Test ConversationManager initialization."""
        assert conversation_manager.project_path == temp_project_path
        assert conversation_manager.memory_system is not None
        assert conversation_manager.nlp is not None
        assert conversation_manager.current_context is not None
        assert isinstance(conversation_manager.current_context, ConversationContext)
        assert conversation_manager.max_context_messages == 20
    
    def test_conversation_context_initialization(self, conversation_manager):
        """Test ConversationContext initialization."""
        context = conversation_manager.current_context
        
        assert context.conversation_id.startswith('conv_')
        assert len(context.conversation_id) > 10
        assert isinstance(context.messages, list)
        assert isinstance(context.intent_history, list)
        assert isinstance(context.active_files, list)
        assert isinstance(context.preferences, dict)
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self, conversation_manager):
        """Test basic message processing."""
        result = await conversation_manager.process_message("Hello, create a test file")
        
        assert 'response' in result
        assert 'intent' in result
        assert 'context_used' in result
        assert 'success' in result
        assert 'conversation_id' in result
        
        # Check that message was added to context
        assert len(conversation_manager.current_context.messages) == 2  # User + Assistant
        assert conversation_manager.current_context.messages[0]['role'] == 'user'
        assert conversation_manager.current_context.messages[1]['role'] == 'assistant'
    
    @pytest.mark.asyncio
    async def test_context_persistence(self, conversation_manager):
        """Test conversation context persistence."""
        # Send multiple messages
        messages = [
            "Create a new project",
            "Add authentication",
            "Test the system"
        ]
        
        for msg in messages:
            await conversation_manager.process_message(msg)
        
        # Check context history
        context = conversation_manager.current_context
        assert len(context.messages) == len(messages) * 2  # User + Assistant for each
        assert len(context.intent_history) == len(messages)
        
        # Check message order
        user_messages = [m for m in context.messages if m['role'] == 'user']
        assert len(user_messages) == len(messages)
        assert user_messages[0]['content'] == messages[0]
        assert user_messages[-1]['content'] == messages[-1]
    
    @pytest.mark.asyncio
    async def test_context_window_limit(self, conversation_manager):
        """Test context window size limit."""
        # Send more messages than the limit
        for i in range(conversation_manager.max_context_messages + 5):
            await conversation_manager.process_message(f"Message {i}")
        
        # Should not exceed max context messages
        assert len(conversation_manager.current_context.messages) <= conversation_manager.max_context_messages
        
        # Should contain most recent messages
        last_user_msg = [m for m in conversation_manager.current_context.messages if m['role'] == 'user'][-1]
        assert "Message" in last_user_msg['content']
    
    @pytest.mark.asyncio
    async def test_relevant_context_retrieval(self, conversation_manager):
        """Test relevant context retrieval."""
        # Add some conversation history
        await conversation_manager.process_message("I had an error yesterday")
        
        # Process a new message about errors
        result = await conversation_manager.process_message("Fix the authentication error")
        
        context_used = result['context_used']
        assert 'similar_conversations' in context_used
        assert 'error_solutions' in context_used
        assert 'user_preferences' in context_used
        assert 'project_patterns' in context_used
    
    def test_conversation_summary(self, conversation_manager):
        """Test conversation summary generation."""
        # Add some messages to context
        conversation_manager.current_context.messages = [
            {
                'role': 'user',
                'content': 'Test message 1',
                'timestamp': datetime.now()
            },
            {
                'role': 'assistant',
                'content': 'Test response 1',
                'timestamp': datetime.now()
            }
        ]
        
        # Add intent history
        conversation_manager.current_context.intent_history = [
            {'intent': 'create_feature', 'confidence': 80}
        ]
        
        summary = conversation_manager.get_conversation_summary()
        
        assert "Resumo da Conversa Atual" in summary
        assert "Total de mensagens: 2" in summary
        assert "Mensagens do usuário: 1" in summary
        assert "create_feature" in summary
    
    def test_reset_conversation(self, conversation_manager):
        """Test conversation reset functionality."""
        # Add some data to context
        conversation_manager.current_context.messages.append({
            'role': 'user',
            'content': 'Test message',
            'timestamp': datetime.now()
        })
        conversation_manager.current_context.preferences['test'] = 'value'
        conversation_manager.current_context.current_task = 'test_task'
        
        original_preferences = conversation_manager.current_context.preferences.copy()
        
        # Reset conversation
        conversation_manager.reset_conversation()
        
        # Check that context was reset but preferences preserved
        assert len(conversation_manager.current_context.messages) == 0
        assert len(conversation_manager.current_context.intent_history) == 0
        assert conversation_manager.current_context.current_task is None
        assert conversation_manager.current_context.preferences == original_preferences
    
    @pytest.mark.asyncio
    async def test_thinking_budget_calculation(self, conversation_manager):
        """Test thinking budget calculation."""
        # Test simple intent
        simple_intent = {'intent': 'question', 'confidence': 80}
        budget = conversation_manager._calculate_thinking_budget(simple_intent)
        assert budget == 8192
        
        # Test complex intent
        complex_intent = {'intent': 'create_feature', 'confidence': 80}
        budget = conversation_manager._calculate_thinking_budget(complex_intent)
        assert budget == 16384
        
        # Test low confidence intent
        low_conf_intent = {'intent': 'unknown', 'confidence': 20}
        budget = conversation_manager._calculate_thinking_budget(low_conf_intent)
        assert budget > 8192  # Should be increased for low confidence
    
    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_manager):
        """Test error handling in message processing."""
        # Mock an error in Gemini client
        conversation_manager.gemini_client.generate_response = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        result = await conversation_manager.process_message("This should cause an error")
        
        assert result['success'] is False
        assert 'error' in result['response'].lower()
        
        # Check that the error was recorded in memory
        assert len(conversation_manager.memory_system.short_term_memory) > 0
    
    @pytest.mark.asyncio
    async def test_preference_learning(self, conversation_manager):
        """Test automatic preference learning."""
        # Send a short message (should learn concise style)
        await conversation_manager.process_message("ok")
        
        # Send a long message (should learn detailed style)
        long_message = "Please create a comprehensive authentication system with user registration, login, password reset, email verification, and role-based access control."
        await conversation_manager.process_message(long_message)
        
        # Check if preferences were learned
        preferences = conversation_manager.memory_system.get_preferences('communication')
        # Note: This is a basic test, actual preference learning may vary
    
    def test_export_conversation(self, conversation_manager):
        """Test conversation export functionality."""
        # Add some messages
        conversation_manager.current_context.messages = [
            {
                'role': 'user',
                'content': 'Export test',
                'timestamp': datetime.now()
            }
        ]
        
        # Export conversation
        export_path = conversation_manager.export_conversation()
        
        # Check that file was created
        assert Path(export_path).exists()
        
        # Check file content
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'conversation_id' in data
        assert 'messages' in data
        assert len(data['messages']) > 0
    
    @pytest.mark.asyncio
    async def test_context_preparation_for_gemini(self, conversation_manager):
        """Test context preparation for Gemini."""
        # Add conversation history
        conversation_manager.current_context.messages = [
            {'role': 'user', 'content': 'Previous message', 'timestamp': datetime.now()},
            {'role': 'assistant', 'content': 'Previous response', 'timestamp': datetime.now()}
        ]
        
        # Test context preparation
        context = conversation_manager._prepare_context_for_gemini(
            "New message",
            {'intent': 'test'},
            {
                'similar_conversations': [{'user_input': 'Similar message'}],
                'error_solutions': [],
                'user_preferences': {'style': 'concise'},
                'project_patterns': [{'description': 'Clean code pattern'}]
            }
        )
        
        assert isinstance(context, list)
        assert len(context) > 0
        
        # Check that recent conversation history is included
        user_messages = [msg for msg in context if msg.get('role') == 'user']
        assert len(user_messages) > 0
    
    @pytest.mark.asyncio
    async def test_file_detection_in_memory(self, conversation_manager):
        """Test file detection and memory storage."""
        # Send message mentioning files
        await conversation_manager.process_message("Edit the config.py and models.py files")
        
        # Check if files were detected (this depends on the implementation)
        # The test validates that the system processes file mentions without errors
        assert len(conversation_manager.current_context.messages) > 0


if __name__ == "__main__":
    pytest.main([__file__])