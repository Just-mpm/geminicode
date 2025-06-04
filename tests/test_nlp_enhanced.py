"""
Unit tests for NLPEnhanced module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_code.core.nlp_enhanced import NLPEnhanced, IntentType


class TestNLPEnhanced:
    """Test suite for NLPEnhanced."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client."""
        client = Mock()
        client.generate_response = AsyncMock(return_value="Mock response")
        return client
    
    @pytest.fixture
    def nlp(self, mock_gemini_client):
        """NLPEnhanced instance with mocked dependencies."""
        return NLPEnhanced(mock_gemini_client)
    
    def test_initialization(self, nlp):
        """Test NLPEnhanced initialization."""
        assert nlp is not None
        assert hasattr(nlp, 'patterns')
        assert hasattr(nlp, 'context_keywords')
        assert hasattr(nlp, 'entity_patterns')
        assert isinstance(nlp.conversation_history, list)
        assert nlp.context_window == 50
    
    @pytest.mark.asyncio
    async def test_empty_input_validation(self, nlp):
        """Test handling of empty input."""
        result = await nlp.identify_intent("")
        
        assert result['intent'] == IntentType.UNKNOWN.value
        assert result['confidence'] == 0
        assert result['entities'] == {}
        assert result['sentiment'] == 'neutral'
    
    @pytest.mark.asyncio
    async def test_whitespace_only_input(self, nlp):
        """Test handling of whitespace-only input."""
        result = await nlp.identify_intent("   \n\t   ")
        
        assert result['intent'] == IntentType.UNKNOWN.value
        assert result['confidence'] == 0
    
    @pytest.mark.asyncio
    async def test_oversized_input(self, nlp):
        """Test handling of oversized input."""
        long_text = "a" * 6000
        result = await nlp.identify_intent(long_text)
        
        # Should not crash and should return some result
        assert 'intent' in result
        assert 'confidence' in result
    
    @pytest.mark.asyncio
    async def test_create_agent_intent(self, nlp):
        """Test create agent intent detection."""
        test_cases = [
            "crie um agente chamado teste",
            "criar agente teste",
            "preciso de um agente para teste",
            "agente chamado bot_helper"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.CREATE_AGENT.value
            assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_create_feature_intent(self, nlp):
        """Test create feature intent detection."""
        test_cases = [
            "adicione uma funcionalidade de login",
            "crie um botão de exportar",
            "implementar sistema de autenticação",
            "faz um sistema de pagamento"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.CREATE_FEATURE.value
            assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_fix_error_intent(self, nlp):
        """Test fix error intent detection."""
        test_cases = [
            "está dando erro",
            "não funciona",
            "bugou",
            "conserta isso",
            "tem um problema aqui"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.FIX_ERROR.value
            assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_git_push_intent(self, nlp):
        """Test git push intent detection."""
        test_cases = [
            "envia para o github",
            "manda pro git",
            "push",
            "sobe o código",
            "atualiza o repositório"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.GIT_PUSH.value
            assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_navigate_folder_intent(self, nlp):
        """Test navigate folder intent detection."""
        test_cases = [
            "vai para a pasta /home/user",
            "abre a pasta C:\\Users\\Test",
            "cd /var/www",
            "trabalhar na pasta src",
            "muda para o diretório docs"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.NAVIGATE_FOLDER.value
            assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_question_intent(self, nlp):
        """Test question intent detection."""
        test_cases = [
            "como fazer isso?",
            "o que é isso?",
            "pode me ajudar?",
            "ajuda",
            "help"
        ]
        
        for text in test_cases:
            result = await nlp.identify_intent(text)
            assert result['intent'] == IntentType.QUESTION.value
            assert result['confidence'] > 0
    
    def test_normalize_text(self, nlp):
        """Test text normalization."""
        test_cases = [
            ("tá bom", "está bom"),
            ("pra fazer", "para fazer"),
            ("vc pode", "você pode"),
            ("n funciona", "não funciona")
        ]
        
        for input_text, expected in test_cases:
            normalized = nlp._normalize_text(input_text)
            assert expected in normalized.lower()
    
    def test_detect_sentiment(self, nlp):
        """Test sentiment detection."""
        test_cases = [
            ("urgente socorro", "urgent"),
            ("está ótimo", "positive"),
            ("que merda", "negative"),
            ("como fazer?", "curious"),
            ("normal texto", "neutral")
        ]
        
        for text, expected_sentiment in test_cases:
            sentiment = nlp._detect_sentiment(text.lower())
            assert sentiment == expected_sentiment
    
    def test_conversation_history(self, nlp):
        """Test conversation history management."""
        # Test adding to history
        intent = nlp.analyze("teste")
        assert len(nlp.conversation_history) == 1
        
        # Test context window limit
        for i in range(60):  # Exceed context window
            nlp.analyze(f"teste {i}")
        
        assert len(nlp.conversation_history) <= nlp.context_window
    
    def test_entity_extraction(self, nlp):
        """Test entity extraction."""
        # Test agent name extraction
        intent = nlp.analyze("crie um agente chamado test_bot")
        assert 'name' in intent.entities
        assert intent.entities['name'] == 'test_bot'
    
    def test_context_clues_extraction(self, nlp):
        """Test context clues extraction."""
        # Test urgency detection
        intent = nlp.analyze("urgente! preciso de ajuda agora")
        assert 'urgency' in intent.context_clues
        
        # Test question detection
        intent = nlp.analyze("como posso fazer isso?")
        assert 'question' in intent.context_clues
    
    def test_clarification_questions(self, nlp):
        """Test clarification question generation."""
        # Test for low confidence intent
        intent = nlp.analyze("fazer algo")
        intent.confidence = 0.3
        questions = nlp.get_clarification_questions(intent)
        assert len(questions) > 0
        assert any("não entendi" in q.lower() for q in questions)


@pytest.mark.asyncio
async def test_intent_integration():
    """Integration test for intent processing."""
    # Mock client
    mock_client = Mock()
    mock_client.generate_response = AsyncMock(return_value="Success")
    
    nlp = NLPEnhanced(mock_client)
    
    # Test complete flow
    result = await nlp.identify_intent("crie um agente de teste")
    
    assert result['intent'] == IntentType.CREATE_AGENT.value
    assert result['confidence'] > 80
    assert 'entities' in result
    assert 'sentiment' in result
    assert 'context_clues' in result


if __name__ == "__main__":
    pytest.main([__file__])
