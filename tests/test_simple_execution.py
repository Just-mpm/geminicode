#!/usr/bin/env python3
"""
🧪 TESTE SIMPLES - Sistema de Execução Real (sem pytest)
Testa as correções implementadas para execução de comandos simples
"""

import asyncio
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.interface.enhanced_chat_interface import EnhancedChatInterface
from gemini_code.core.nlp_enhanced import NLPEnhanced
from gemini_code.core.autonomous_executor import AutonomousExecutor


async def test_folder_creation():
    """🎯 Teste principal: Criação de pasta como o usuário relatou."""
    print("🎯 TESTANDO: Criação de pasta 'ideias'")
    print("-" * 50)
    
    # Criar workspace temporário
    temp_workspace = tempfile.mkdtemp()
    print(f"📁 Workspace: {temp_workspace}")
    
    try:
        # Mock Gemini client
        mock_client = Mock()
        mock_client.generate_response = AsyncMock(return_value="Mock response")
        
        # Mock managers
        mock_project_manager = Mock()
        mock_file_manager = Mock()
        
        # Criar interface
        chat = EnhancedChatInterface(
            mock_client,
            mock_project_manager,
            mock_file_manager,
            temp_workspace
        )
        
        # Comando do usuário
        user_input = "Crie uma pasta chamada ideias"
        print(f"💬 Comando: '{user_input}'")
        
        # 1. Testar NLP
        print("\n1️⃣ Testando NLP...")
        nlp_result = await chat.nlp.identify_intent(user_input)
        print(f"   Intent: {nlp_result['intent']}")
        print(f"   Confidence: {nlp_result['confidence']}%")
        print(f"   Entities: {nlp_result.get('entities', {})}")
        
        # 2. Testar detecção de comando simples
        print("\n2️⃣ Testando detecção de comando simples...")
        simple_intent = await chat._identify_simple_execution_intent(user_input)
        print(f"   Simple intent: {simple_intent}")
        
        if simple_intent:
            print(f"   ✅ Detectado como: {simple_intent['type']}")
            print(f"   📁 Nome da pasta: {simple_intent.get('folder_name', 'N/A')}")
            
            # 3. Testar execução física
            print("\n3️⃣ Testando execução física...")
            folder_path = Path(temp_workspace) / simple_intent['folder_name']
            print(f"   Caminho: {folder_path}")
            print(f"   Existe antes: {folder_path.exists()}")
            
            # Executar comando
            await chat._handle_simple_execution_command(user_input, simple_intent)
            
            # Verificar resultado
            exists_after = folder_path.exists()
            is_dir = folder_path.is_dir() if exists_after else False
            
            print(f"   Existe depois: {exists_after}")
            print(f"   É diretório: {is_dir}")
            
            if exists_after and is_dir:
                print("\n🎉 ✅ SUCESSO! Pasta criada fisicamente!")
                return True
            else:
                print("\n❌ FALHA! Pasta não foi criada.")
                return False
        else:
            print("\n❌ FALHA! Comando não foi detectado como simples.")
            return False
            
    except Exception as e:
        print(f"\n💥 ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar workspace
        shutil.rmtree(temp_workspace)
        print(f"\n🧹 Workspace limpo: {temp_workspace}")


async def test_nlp_patterns():
    """Testa padrões NLP para diferentes comandos."""
    print("\n🧠 TESTANDO: Padrões NLP")
    print("-" * 50)
    
    mock_client = Mock()
    nlp = NLPEnhanced(mock_client)
    
    test_cases = [
        "Crie uma pasta chamada ideias",
        "Quero criar uma nova pasta para documentos", 
        "Faça uma pasta projetos",
        "Nova pasta para txt",
        "Criar diretório backup"
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. '{test_case}'")
        try:
            result = await nlp.identify_intent(test_case)
            print(f"   → Intent: {result['intent']}")
            print(f"   → Confidence: {result['confidence']}%")
            print(f"   → Entities: {result.get('entities', {})}")
            
            # Considera sucesso se detectou CREATE_FILE com confidence > 50
            success = result['intent'] == 'create_file' and result['confidence'] > 50
            results.append(success)
            print(f"   → Status: {'✅' if success else '❌'}")
            
        except Exception as e:
            print(f"   → ❌ ERRO: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Taxa de sucesso: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return success_rate >= 70  # Pelo menos 70% de sucesso


def test_autonomous_executor_flag():
    """Testa flag de execução real."""
    print("\n🔧 TESTANDO: Flag enable_real_execution")
    print("-" * 50)
    
    try:
        executor = AutonomousExecutor()
        
        print(f"   Flag atual: {executor.enable_real_execution}")
        
        # Deve estar True por padrão
        if executor.enable_real_execution:
            print("   ✅ Flag está ativa (True)")
            
            # Testar toggle
            executor.enable_execution(False)
            print(f"   Após desativar: {executor.enable_real_execution}")
            
            executor.enable_execution(True) 
            print(f"   Após reativar: {executor.enable_real_execution}")
            
            return True
        else:
            print("   ❌ Flag deveria estar ativa por padrão")
            return False
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        return False


async def test_routing_logic():
    """Testa roteamento entre comandos autônomos e simples."""
    print("\n🚏 TESTANDO: Roteamento de comandos")
    print("-" * 50)
    
    try:
        # Criar interface mock
        mock_client = Mock()
        mock_client.generate_response = AsyncMock(return_value="Mock")
        
        temp_workspace = tempfile.mkdtemp()
        
        chat = EnhancedChatInterface(
            mock_client,
            Mock(),
            Mock(),
            temp_workspace
        )
        
        # Testar comando simples
        simple_cmd = "Crie uma pasta docs"
        is_autonomous = await chat._is_autonomous_command(simple_cmd)
        simple_intent = await chat._identify_simple_execution_intent(simple_cmd)
        
        print(f"1. Comando simples: '{simple_cmd}'")
        print(f"   Autônomo: {is_autonomous}")
        print(f"   Intent simples: {simple_intent is not None}")
        
        # Testar comando complexo
        complex_cmd = "Verifica arquivos, corrige erros, cria função X, valida tudo"
        is_autonomous_complex = await chat._is_autonomous_command(complex_cmd)
        simple_intent_complex = await chat._identify_simple_execution_intent(complex_cmd)
        
        print(f"\n2. Comando complexo: '{complex_cmd}'")
        print(f"   Autônomo: {is_autonomous_complex}")
        print(f"   Intent simples: {simple_intent_complex is not None}")
        
        # Limpar
        shutil.rmtree(temp_workspace)
        
        # Sucesso se comando simples tem intent E comando complexo é autônomo
        success = simple_intent is not None and is_autonomous_complex
        print(f"\n   Status: {'✅' if success else '❌'}")
        
        return success
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        return False


async def run_all_tests():
    """🧪 Executa todos os testes."""
    print("🧪 INICIANDO TESTES DO SISTEMA DE EXECUÇÃO REAL")
    print("=" * 70)
    print("🎯 Objetivo: Verificar correções implementadas conforme Gemini")
    print()
    
    tests = [
        ("🎯 Criação de Pasta Principal", test_folder_creation()),
        ("🧠 Padrões NLP", test_nlp_patterns()),
        ("🔧 Flag Execução Real", test_autonomous_executor_flag()),
        ("🚏 Roteamento de Comandos", test_routing_logic()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        print(f"\n{'='*70}")
        print(f"🔍 EXECUTANDO: {test_name}")
        print(f"{'='*70}")
        
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
                
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"\n🏁 RESULTADO: {status}")
            
        except Exception as e:
            print(f"\n💥 ERRO CRÍTICO: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Relatório final
    print(f"\n{'='*70}")
    print("📊 RELATÓRIO FINAL")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📈 RESULTADO GERAL: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 🚀 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de execução real está funcionando!")
        print("📁 Comando 'Crie pasta ideias' agora executa fisicamente!")
        return True
    else:
        print(f"\n⚠️ {total-passed} teste(s) falharam")
        print("🔍 Verifique os logs acima para detalhes")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Testes interrompidos pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")
        sys.exit(1)
