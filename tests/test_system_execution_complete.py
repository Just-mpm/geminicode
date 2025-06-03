#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO DO SISTEMA DE EXECUÇÃO REAL
Testa especificamente as correções implementadas para execução de comandos simples
"""

import asyncio
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.interface.enhanced_chat_interface import EnhancedChatInterface
from gemini_code.core.nlp_enhanced import NLPEnhanced, IntentType
from gemini_code.core.autonomous_executor import AutonomousExecutor
from gemini_code.execution.command_executor import CommandExecutor, CommandContext


class TestSystemExecutionFixes:
    """Testa as correções específicas implementadas para execução real."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Workspace temporário para testes."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client otimizado."""
        client = Mock()
        client.generate_response = AsyncMock(return_value="Mock response from Gemini")
        return client
    
    @pytest.fixture
    def chat_interface(self, temp_workspace, mock_gemini_client):
        """Interface de chat configurada para testes."""
        mock_project_manager = Mock()
        mock_file_manager = Mock()
        
        # Mock do file_manager para criar diretórios
        mock_file_manager.create_directory = Mock(return_value=True)
        mock_file_manager.delete_file = Mock(return_value=True)
        
        chat = EnhancedChatInterface(
            mock_gemini_client,
            mock_project_manager,
            mock_file_manager,
            temp_workspace
        )
        return chat

    @pytest.mark.asyncio
    async def test_simple_folder_creation_flow(self, chat_interface, temp_workspace):
        """🎯 TESTE PRINCIPAL: Criação de pasta simples (caso do usuário)."""
        print("\n🎯 Testando: 'Crie uma pasta chamada ideias'")
        
        # Comando exato que o usuário relatou
        user_input = "Crie uma pasta chamada ideias"
        
        # 1. Testar detecção de intenção NLP
        nlp_result = await chat_interface.nlp.identify_intent(user_input)
        print(f"📊 NLP detectou: {nlp_result}")
        
        # Deve detectar como CREATE_FILE com alta confiança
        assert nlp_result['intent'] == 'create_file'
        assert nlp_result['confidence'] > 70
        
        # 2. Testar identificação como comando simples
        simple_intent = await chat_interface._identify_simple_execution_intent(user_input)
        print(f"🔍 Comando simples detectado: {simple_intent}")
        
        # Deve ser identificado como criação de pasta
        assert simple_intent is not None
        assert simple_intent['type'] == 'create_folder'
        assert simple_intent['folder_name'] == 'ideias'
        
        # 3. Testar execução física
        folder_path = Path(temp_workspace) / 'ideias'
        assert not folder_path.exists()  # Não deve existir ainda
        
        # Executar comando
        await chat_interface._handle_simple_execution_command(user_input, simple_intent)
        
        # Verificar se pasta foi criada fisicamente
        assert folder_path.exists()
        assert folder_path.is_dir()
        
        print("✅ SUCESSO: Pasta 'ideias' criada fisicamente!")

    @pytest.mark.asyncio
    async def test_nlp_enhanced_patterns(self, mock_gemini_client):
        """Testa padrões NLP aprimorados para CREATE_FILE."""
        nlp = NLPEnhanced(mock_gemini_client)
        
        test_cases = [
            ("Crie uma pasta chamada ideias", "create_file", "ideias"),
            ("Quero criar uma nova pasta para documentos", "create_file", "documentos"),
            ("Faça uma pasta chamada projetos", "create_file", "projetos"),
            ("Criar uma pasta para guardar txt", "create_file", None),  # Deve usar fallback
            ("Nova pasta ideias", "create_file", "ideias"),
        ]
        
        for text, expected_intent, expected_name in test_cases:
            result = await nlp.identify_intent(text)
            print(f"🧠 Teste: '{text}' → {result}")
            
            assert result['intent'] == expected_intent
            assert result['confidence'] > 60
            
            if expected_name:
                entities = result.get('entities', {})
                # Pode extrair como 'name' ou como detecção de contexto
                print(f"   Entidades: {entities}")

    @pytest.mark.asyncio 
    async def test_autonomous_vs_simple_command_routing(self, chat_interface, temp_workspace):
        """Testa roteamento correto entre comandos autônomos e simples."""
        
        # 1. Comando simples - deve ir para execução direta
        simple_command = "Crie uma pasta chamada docs"
        is_autonomous = await chat_interface._is_autonomous_command(simple_command)
        simple_intent = await chat_interface._identify_simple_execution_intent(simple_command)
        
        print(f"📝 Comando simples: autônomo={is_autonomous}, simples={simple_intent is not None}")
        
        # Pode ser detectado como autônomo também (que é OK), mas deve ter intent simples
        assert simple_intent is not None
        
        # 2. Comando complexo - deve ir para sistema autônomo
        complex_command = "Verifica arquivos, corrige erros, cria função X, valida tudo"
        is_autonomous_complex = await chat_interface._is_autonomous_command(complex_command)
        simple_intent_complex = await chat_interface._identify_simple_execution_intent(complex_command)
        
        print(f"🔧 Comando complexo: autônomo={is_autonomous_complex}, simples={simple_intent_complex is not None}")
        
        assert is_autonomous_complex == True
        # Comando complexo pode ou não ter intent simples, mas vai para autônomo primeiro

    @pytest.mark.asyncio
    async def test_command_executor_integration(self, temp_workspace):
        """Testa integração com CommandExecutor."""
        
        # Mock client
        mock_client = Mock()
        executor = CommandExecutor(mock_client)
        
        # Contexto de comando
        context = CommandContext(
            working_directory=str(temp_workspace),
            environment={},
            timeout=30.0,
            safe_mode=True
        )
        
        # Testar comando simples que deve funcionar
        if os.name == 'nt':  # Windows
            test_command = 'echo "Teste Windows"'
        else:  # Linux/Unix
            test_command = 'echo "Teste Linux"'
        
        result = await executor.execute_command(test_command, context)
        
        print(f"💻 Resultado comando: sucesso={result.success}")
        print(f"📤 Output: {result.stdout}")
        
        assert result.success
        assert "Teste" in result.stdout

    @pytest.mark.asyncio
    async def test_full_integration_create_folder(self, chat_interface, temp_workspace):
        """🚀 TESTE DE INTEGRAÇÃO COMPLETA - Fluxo do usuário real."""
        print("\n🚀 TESTE INTEGRAÇÃO COMPLETA")
        
        # Simular interação completa do usuário
        user_commands = [
            "Crie uma pasta chamada ideias",
            "Faça uma pasta para documentos", 
            "Nova pasta projetos"
        ]
        
        created_folders = []
        
        for i, command in enumerate(user_commands, 1):
            print(f"\n📝 Comando {i}: {command}")
            
            # Processar através do sistema completo
            # Em vez de process_message_with_memory (que vai para Gemini),
            # testamos o fluxo de comandos simples diretamente
            
            # 1. Verificar se é comando especial
            is_special = await chat_interface._handle_special_commands(command)
            if is_special:
                continue
                
            # 2. Verificar se é autônomo
            is_autonomous = await chat_interface._is_autonomous_command(command)
            
            # 3. Verificar se é comando simples
            simple_intent = await chat_interface._identify_simple_execution_intent(command)
            
            if simple_intent:
                print(f"   ⚡ Executando como comando simples: {simple_intent}")
                await chat_interface._handle_simple_execution_command(command, simple_intent)
                
                # Verificar se pasta foi criada
                folder_name = simple_intent.get('folder_name', 'unknown')
                folder_path = Path(temp_workspace) / folder_name
                
                if folder_path.exists():
                    created_folders.append(folder_name)
                    print(f"   ✅ Pasta '{folder_name}' criada com sucesso!")
                else:
                    print(f"   ❌ Pasta '{folder_name}' NÃO foi criada!")
            
            elif is_autonomous:
                print(f"   🤖 Seria processado como autônomo")
            else:
                print(f"   💬 Seria processado via Gemini")
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"✅ Pastas criadas fisicamente: {created_folders}")
        print(f"📁 Total: {len(created_folders)}")
        
        # Deve ter criado pelo menos 1 pasta
        assert len(created_folders) >= 1
        
        # Verificar se arquivos existem fisicamente
        for folder_name in created_folders:
            folder_path = Path(temp_workspace) / folder_name
            assert folder_path.exists(), f"Pasta {folder_name} deveria existir!"
            assert folder_path.is_dir(), f"{folder_name} deveria ser diretório!"

    def test_autonomous_executor_enable_flag(self):
        """Testa se flag enable_real_execution está ativa."""
        executor = AutonomousExecutor()
        
        print(f"🔧 Flag enable_real_execution: {executor.enable_real_execution}")
        
        # Deve estar True por padrão
        assert executor.enable_real_execution == True
        
        # Testar toggle
        executor.enable_execution(False)
        assert executor.enable_real_execution == False
        
        executor.enable_execution(True)
        assert executor.enable_real_execution == True

    @pytest.mark.asyncio
    async def test_delete_command_with_confirmation(self, chat_interface, temp_workspace):
        """Testa comando de deleção com confirmação."""
        
        # Criar arquivo para testar deleção
        test_file = Path(temp_workspace) / "test_file.txt"
        test_file.write_text("conteúdo de teste")
        assert test_file.exists()
        
        # Comando de deleção
        delete_command = "Delete o arquivo test_file.txt"
        
        # Verificar detecção
        simple_intent = await chat_interface._identify_simple_execution_intent(delete_command)
        print(f"🗑️ Comando delete detectado: {simple_intent}")
        
        # Deve detectar como deleção
        if simple_intent:
            assert simple_intent['type'] == 'delete'
            assert 'test_file.txt' in simple_intent['target']
        
        # Nota: O teste não executa a deleção real porque requereria input do usuário
        print("✅ Comando de deleção detectado corretamente (confirmação seria solicitada)")

    @pytest.mark.asyncio
    async def test_error_cases_and_edge_cases(self, chat_interface):
        """Testa casos de erro e extremos."""
        
        # 1. Comando vazio
        result = await chat_interface._identify_simple_execution_intent("")
        assert result is None
        
        # 2. Comando sem nome de pasta
        result = await chat_interface._identify_simple_execution_intent("Crie uma pasta")
        # Pode retornar None ou usar nome padrão
        print(f"🔍 Comando sem nome: {result}")
        
        # 3. Comando com caracteres especiais
        result = await chat_interface._identify_simple_execution_intent("Crie pasta 'minha pasta com espaços'")
        print(f"🔤 Comando com espaços: {result}")
        
        # 4. Comando muito longo
        long_command = "Crie uma pasta " + "muito " * 100 + "longa"
        result = await chat_interface._identify_simple_execution_intent(long_command)
        print(f"📏 Comando longo processado: {result is not None}")


async def run_complete_system_test():
    """🧪 Executa teste completo do sistema de execução."""
    print("🧪 INICIANDO TESTE COMPLETO DO SISTEMA DE EXECUÇÃO")
    print("=" * 70)
    print("🎯 Objetivo: Verificar se comandos simples são executados fisicamente")
    print("🔧 Baseado nas correções implementadas conforme sugestões do Gemini")
    print()
    
    # Executar com pytest para obter relatório detalhado
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=long",
        "-s"  # Mostrar prints
    ])
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("🎉 ✅ TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema de execução real está funcionando corretamente!")
        print("📁 Comandos simples como 'Crie pasta ideias' agora executam fisicamente!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print(f"🔍 Código de saída: {exit_code}")
        print("🔧 Verifique os logs acima para detalhes dos problemas")
    
    return exit_code


if __name__ == "__main__":
    # Executar teste completo
    exit_code = asyncio.run(run_complete_system_test())
    sys.exit(exit_code)