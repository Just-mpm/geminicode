#!/usr/bin/env python3
"""
Teste assíncrono para debugar problema de inicialização
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.master_system import GeminiCodeMasterSystem


async def test_async_init():
    """Testa inicialização assíncrona passo a passo."""
    print("🔍 TESTANDO INICIALIZAÇÃO ASSÍNCRONA")
    print("=" * 50)
    
    try:
        system = GeminiCodeMasterSystem()
        print("✅ Sistema criado")
        
        # Testa cada passo da inicialização
        print("\n1. Inicializando configuração...")
        await system._initialize_config()
        print("✅ Configuração OK")
        
        print("\n2. Inicializando sistemas centrais...")
        await system._initialize_core_systems()
        print("✅ Sistemas centrais OK")
        
        print("\n3. Inicializando ferramentas e segurança...")
        await system._initialize_tools_and_security()
        print("✅ Ferramentas e segurança OK")
        
        print("\n4. Inicializando funcionalidades avançadas...")
        await system._initialize_advanced_features()
        print("✅ Funcionalidades avançadas OK")
        
        print("\n5. Inicializando funcionalidades empresariais...")
        await system._initialize_enterprise_features()
        print("✅ Funcionalidades empresariais OK")
        
        print("\n6. Inicializando monitoramento...")
        await system._initialize_monitoring()
        print("✅ Monitoramento OK")
        
        print("\n7. Inicializando interface...")
        await system._initialize_interface()
        print("✅ Interface OK")
        
        print("\n8. Verificando componentes...")
        components = {
            'gemini_client': system.gemini_client,
            'project_manager': system.project_manager,
            'memory_system': system.memory_system,
            'tool_registry': system.tool_registry,
            'permission_manager': system.permission_manager,
            'session_manager': system.session_manager,
            'command_parser': system.command_parser,
            'context_compactor': system.context_compactor,
            'mcp_client': system.mcp_client,
            'health_monitor': system.health_monitor,
            'error_detector': system.error_detector,
            'repl': system.repl
        }
        
        for name, component in components.items():
            status = "✅" if component is not None else "❌"
            print(f"  {status} {name}")
        
        print(f"\n🎯 Sistema inicializado: {system.is_initialized}")
        
        return system
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    system = await test_async_init()
    
    if system:
        print("\n✅ INICIALIZAÇÃO MANUAL SUCESSO!")
        
        # Agora testa a inicialização completa
        print("\n🔄 Testando inicialização completa...")
        try:
            result = await system.initialize()
            print(f"✅ Inicialização completa: {result}")
        except Exception as e:
            print(f"❌ Erro na inicialização completa: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ FALHA NA INICIALIZAÇÃO MANUAL")


if __name__ == "__main__":
    asyncio.run(main())
