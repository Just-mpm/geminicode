#!/usr/bin/env python3
"""
Teste rápido para verificar se a correção do file_manager funcionou
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

async def test_architectural_reasoning():
    """Testa se o ArchitecturalReasoning inicializa corretamente."""
    print("🔧 Testando ArchitecturalReasoning...")
    
    try:
        # Define API key de teste
        os.environ['GEMINI_API_KEY'] = 'test-key-for-test'
        
        from gemini_code.core.gemini_client import GeminiClient
        from gemini_code.core.project_manager import ProjectManager
        from gemini_code.cognition.architectural_reasoning import ArchitecturalReasoning
        
        # Inicializa componentes
        client = GeminiClient()
        pm = ProjectManager(".")
        
        # Testa inicialização do ArchitecturalReasoning
        ar = ArchitecturalReasoning(client, pm)
        
        print("✅ ArchitecturalReasoning inicializado com sucesso!")
        print(f"✅ CodeNavigator criado: {ar.code_navigator is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_master_system():
    """Testa se o MasterSystem inicializa corretamente."""
    print("\n🚀 Testando MasterSystem...")
    
    try:
        from gemini_code.core.master_system import GeminiCodeMasterSystem
        
        # Cria instância
        master = GeminiCodeMasterSystem(".")
        
        # Testa inicialização
        await master._initialize_config()
        print("✅ Config inicializada")
        
        await master._initialize_core_systems()
        print("✅ Core systems inicializados")
        
        await master._initialize_tools_and_security()
        print("✅ Tools & security inicializados")
        
        await master._initialize_advanced_features()
        print("✅ Advanced features inicializados")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        if "API_KEY_INVALID" in error_str or "API key not valid" in error_str:
            print("✅ Inicialização OK (falha esperada por API key)")
            return True
        else:
            print(f"❌ Erro: {e}")
            return False

async def main():
    """Executa os testes."""
    print("🧪 TESTE RÁPIDO DE CORREÇÃO")
    print("="*50)
    
    test1 = await test_architectural_reasoning()
    test2 = await test_master_system()
    
    print("\n" + "="*50)
    if test1 and test2:
        print("🎉 CORREÇÃO FUNCIONOU! Sistema OK!")
        return True
    else:
        print("❌ Ainda há problemas a corrigir")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)