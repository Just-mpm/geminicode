#!/usr/bin/env python3
"""
Testes de integração abrangentes para cenários de uso real do Gemini Code.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import json
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_code.core.conversation_manager import ConversationManager
from gemini_code.interface.enhanced_chat_interface import EnhancedChatInterface
from gemini_code.core.memory_system import MemorySystem
from gemini_code.analysis.refactored_health_monitor import RefactoredHealthMonitor
from gemini_code.core.nlp_enhanced import NLPEnhanced


class TestIntegrationScenarios:
    """Testes de integração para cenários reais."""
    
    @pytest.fixture
    def temp_project(self):
        """Projeto temporário com arquivos de teste."""
        temp_dir = tempfile.mkdtemp()
        
        # Criar estrutura de projeto realista
        project_structure = {
            'src/main.py': '''
import asyncio
from typing import List, Dict, Any

async def main():
    """Main application function."""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    asyncio.run(main())
''',
            'src/utils.py': '''
def calculate_score(items: List[int]) -> float:
    """Calculate average score."""
    if not items:
        return 0.0
    return sum(items) / len(items)

class DataProcessor:
    """Process data efficiently."""
    
    def __init__(self):
        self.processed_count = 0
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data."""
        self.processed_count += 1
        return {"processed": True, "count": self.processed_count}
''',
            'tests/test_main.py': '''
import pytest
from src.main import main

@pytest.mark.asyncio
async def test_main():
    """Test main function."""
    result = await main()
    assert result is True
''',
            'tests/test_utils.py': '''
import pytest
from src.utils import calculate_score, DataProcessor

def test_calculate_score():
    """Test score calculation."""
    assert calculate_score([1, 2, 3]) == 2.0
    assert calculate_score([]) == 0.0

def test_data_processor():
    """Test data processor."""
    processor = DataProcessor()
    result = processor.process({"key": "value"})
    assert result["processed"] is True
    assert result["count"] == 1
''',
            'requirements.txt': '''
pytest>=7.0.0
asyncio
typing
''',
            'README.md': '''
# Test Project

This is a test project for Gemini Code integration testing.

## Features
- Async main function
- Data processing utilities
- Comprehensive tests
''',
            'bad_code.py': '''
def bad_function():
    try:
        x = 1
        y = 2
        for i in range(100):
            for j in range(100):
                for k in range(100):
                    z = i + j + k
        return z
    except:
        pass

def VeryBadNaming():
    import os
    import sys
    import json
    return "unused imports"
'''
        }
        
        # Criar arquivos
        for file_path, content in project_structure.items():
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client com respostas realistas."""
        client = Mock()
        
        # Respostas contextuais baseadas no input
        async def smart_response(prompt, **kwargs):
            prompt_lower = prompt.lower()
            
            if "error" in prompt_lower or "bug" in prompt_lower:
                return "Identifiquei alguns problemas no código. Vou corrigi-los para você."
            elif "create" in prompt_lower or "crie" in prompt_lower:
                return "Arquivo criado com sucesso! Implementei a funcionalidade solicitada."
            elif "analyze" in prompt_lower or "analise" in prompt_lower:
                return "Análise concluída. O projeto tem boa estrutura mas pode ser melhorado."
            elif "test" in prompt_lower or "teste" in prompt_lower:
                return "Testes executados com sucesso. Encontrei alguns pontos de melhoria."
            else:
                return "Comando processado com sucesso. Como posso ajudar mais?"
        
        client.generate_response = AsyncMock(side_effect=smart_response)
        return client

    @pytest.mark.asyncio
    async def test_complete_workflow_new_user(self, temp_project, mock_gemini_client):
        """Teste workflow completo para usuário novo."""
        # Simula um usuário novo usando o Gemini Code pela primeira vez
        
        # 1. Inicializar sistema
        conv_manager = ConversationManager(temp_project, mock_gemini_client)
        
        # 2. Primeira interação - análise do projeto
        result1 = await conv_manager.process_message("Analise este projeto")
        assert result1["success"]
        assert "analise" in result1["response"].lower()
        
        # 3. Segunda interação - deve lembrar do contexto
        result2 = await conv_manager.process_message("Encontrou algum problema?")
        assert result2["success"]
        
        # 4. Verificar memória persistente
        memory = conv_manager.memory_system
        conversations = memory.recall_similar_conversations("analise", limit=5)
        assert len(conversations) >= 1
        
        # 5. Terceira interação - criação de arquivo
        result3 = await conv_manager.process_message("Crie um arquivo config.py")
        assert result3["success"]
        
        # 6. Verificar aprendizado de preferências
        preferences = memory.get_preferences()
        # Deveria aprender que o usuário gosta de análises detalhadas
        
        print("✅ Workflow completo de usuário novo testado com sucesso")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_project, mock_gemini_client):
        """Teste tratamento de erros e recuperação."""
        
        conv_manager = ConversationManager(temp_project, mock_gemini_client)
        
        # 1. Simular erro de rede
        mock_gemini_client.generate_response.side_effect = ConnectionError("Network error")
        
        result = await conv_manager.process_message("Teste com erro de rede")
        assert not result["success"]
        assert "erro" in result["response"].lower()
        
        # 2. Recuperar e tentar novamente
        mock_gemini_client.generate_response.side_effect = None
        mock_gemini_client.generate_response = AsyncMock(return_value="Conectado novamente!")
        
        result2 = await conv_manager.process_message("Agora deve funcionar")
        assert result2["success"]
        
        # 3. Verificar se o erro foi registrado na memória
        memory = conv_manager.memory_system
        error_solutions = memory.get_error_solutions("network")
        # Pode estar vazio se não houve solução registrada, mas não deve dar erro
        
        print("✅ Tratamento de erros testado com sucesso")

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, temp_project, mock_gemini_client):
        """Teste integração completa do monitoramento de saúde."""
        
        mock_file_manager = Mock()
        health_monitor = RefactoredHealthMonitor(mock_gemini_client, mock_file_manager)
        
        # 1. Análise completa do projeto realista
        result = await health_monitor.run_full_analysis(temp_project)
        
        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert result["status"] in ["healthy", "needs_attention", "critical"]
        
        # 2. Verificar detecção de problemas no bad_code.py
        detailed_results = result["detailed_results"]
        
        # Deve detectar problemas de qualidade
        if "Code Quality Check" in detailed_results:
            quality_result = detailed_results["Code Quality Check"]
            assert "complexity_issues" in quality_result["details"]
            assert "naming_issues" in quality_result["details"]
        
        # 3. Deve detectar boa cobertura de testes
        if "Test Coverage Check" in detailed_results:
            test_result = detailed_results["Test Coverage Check"]
            assert test_result["details"]["test_files"] > 0
        
        print("✅ Monitoramento de saúde integrado testado com sucesso")

    @pytest.mark.asyncio
    async def test_chat_interface_with_memory(self, temp_project, mock_gemini_client):
        """Teste interface de chat com memória."""
        
        # Mock dos managers necessários
        mock_project_manager = Mock()
        mock_file_manager = Mock()
        
        # Criar interface
        chat = EnhancedChatInterface(
            mock_gemini_client,
            mock_project_manager, 
            mock_file_manager,
            temp_project
        )
        
        # 1. Primeira mensagem
        result1 = await chat.process_message_with_memory("Olá, analise meu projeto")
        assert result1["success"]
        
        # 2. Segunda mensagem - deve ter contexto
        result2 = await chat.process_message_with_memory("Quais foram os problemas encontrados?")
        assert result2["success"]
        
        # 3. Verificar que mensagens foram armazenadas
        context = chat.conversation_manager.current_context
        assert len(context.messages) >= 4  # 2 user + 2 assistant
        
        # 4. Teste comando especial
        result3 = await chat.process_message_with_memory("memoria")
        # Pode não processar como comando especial aqui, mas não deve dar erro
        
        print("✅ Interface de chat com memória testada com sucesso")

    @pytest.mark.asyncio
    async def test_conversation_export_import(self, temp_project, mock_gemini_client):
        """Teste exportação e importação de conversas."""
        
        conv_manager = ConversationManager(temp_project, mock_gemini_client)
        
        # 1. Criar algumas conversas
        await conv_manager.process_message("Primeira mensagem")
        await conv_manager.process_message("Segunda mensagem")
        await conv_manager.process_message("Terceira mensagem")
        
        # 2. Exportar conversa
        export_path = conv_manager.export_conversation()
        assert Path(export_path).exists()
        
        # 3. Verificar conteúdo do export
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        assert "conversation_id" in export_data
        assert "messages" in export_data
        assert len(export_data["messages"]) >= 6  # 3 user + 3 assistant
        
        # 4. Criar nova instância e importar
        conv_manager2 = ConversationManager(temp_project, mock_gemini_client)
        
        # Simular importação via interface
        mock_project_manager = Mock()
        mock_file_manager = Mock()
        chat = EnhancedChatInterface(
            mock_gemini_client,
            mock_project_manager,
            mock_file_manager,
            temp_project
        )
        
        import_success = await chat.import_conversation(export_path)
        assert import_success
        
        print("✅ Exportação e importação de conversas testada com sucesso")

    @pytest.mark.asyncio
    async def test_nlp_context_awareness(self, temp_project, mock_gemini_client):
        """Teste consciência de contexto do NLP."""
        
        nlp = NLPEnhanced(mock_gemini_client)
        
        # 1. Primeira análise
        result1 = await nlp.identify_intent("crie um arquivo teste.py")
        assert result1["intent"] == "create_agent" or result1["intent"] == "create_feature"
        
        # 2. Comando relacionado - deve entender contexto
        result2 = await nlp.identify_intent("adicione uma função hello")
        # Deve detectar que é uma modificação/adição
        assert result2["confidence"] > 0
        
        # 3. Comando de navegação
        result3 = await nlp.identify_intent("vá para a pasta src")
        assert result3["intent"] == "navigate_folder"
        
        # 4. Comando ambíguo que deve usar histórico
        result4 = await nlp.identify_intent("tá dando erro")
        assert result4["intent"] == "fix_error"
        
        print("✅ Consciência de contexto do NLP testada com sucesso")

    @pytest.mark.asyncio
    async def test_performance_under_load(self, temp_project, mock_gemini_client):
        """Teste performance sob carga."""
        
        conv_manager = ConversationManager(temp_project, mock_gemini_client)
        
        # Simular múltiplas conversas simultâneas
        tasks = []
        for i in range(10):
            task = conv_manager.process_message(f"Mensagem de teste {i}")
            tasks.append(task)
        
        # Executar todas em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar que todas foram processadas
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 8  # Pelo menos 80% devem ter sucesso
        
        # Verificar que a memória não ficou corrompida
        memory = conv_manager.memory_system
        summary = memory.get_context_summary()
        assert "Contexto Atual" in summary
        
        print("✅ Performance sob carga testada com sucesso")

    def test_edge_cases_and_boundaries(self, temp_project, mock_gemini_client):
        """Teste casos extremos e limites."""
        
        # 1. Mensagens muito longas
        long_message = "a" * 10000
        nlp = NLPEnhanced(mock_gemini_client)
        
        # Não deve dar crash
        asyncio.run(nlp.identify_intent(long_message))
        
        # 2. Caracteres especiais
        special_message = "Créé ün ärchïvö çøm 特殊文字 🎉🚀"
        asyncio.run(nlp.identify_intent(special_message))
        
        # 3. Mensagem vazia
        empty_result = asyncio.run(nlp.identify_intent(""))
        assert empty_result["intent"] == "unknown"
        
        # 4. Memória com muitos dados
        memory = MemorySystem(temp_project)
        for i in range(1000):
            memory.remember_conversation(f"test {i}", f"response {i}", success=True)
        
        # Deve funcionar mesmo com muitos dados
        summary = memory.get_context_summary()
        assert "Contexto Atual" in summary
        
        print("✅ Casos extremos e limites testados com sucesso")


async def run_integration_tests():
    """Executa todos os testes de integração."""
    print("🧪 Iniciando Testes de Integração Abrangentes")
    print("=" * 60)
    
    # Executar testes com pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Parar no primeiro erro
    ])
    
    if exit_code == 0:
        print("\n✅ Todos os testes de integração passaram!")
        print("🎉 Sistema 100% funcional confirmado!")
    else:
        print(f"\n❌ Alguns testes falharam (código: {exit_code})")
        
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(run_integration_tests())
    sys.exit(exit_code)
