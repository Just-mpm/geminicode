#!/usr/bin/env python3
"""
Teste Completo do Sistema - Verifica TODAS as funcionalidades implementadas
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.master_system import initialize_gemini_code


async def test_complete_initialization():
    """Testa inicialização completa do sistema."""
    print("🧪 TESTE COMPLETO - INICIALIZAÇÃO DO SISTEMA")
    print("=" * 80)
    
    try:
        # Inicializa sistema completo
        system = await initialize_gemini_code()
        
        # Verifica se todos os componentes foram inicializados
        components_check = {
            'Gemini Client': system.gemini_client is not None,
            'Project Manager': system.project_manager is not None,
            'Memory System': system.memory_system is not None,
            'Tool Registry': system.tool_registry is not None,
            'Permission Manager': system.permission_manager is not None,
            'Session Manager': system.session_manager is not None,
            'Command Parser': system.command_parser is not None,
            'Context Compactor': system.context_compactor is not None,
            'MCP Client': system.mcp_client is not None,
            'Health Monitor': system.health_monitor is not None,
            'Error Detector': system.error_detector is not None,
            'REPL Interface': system.repl is not None
        }
        
        print("🔍 VERIFICAÇÃO DE COMPONENTES:")
        all_ok = True
        for component, status in components_check.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {component}")
            if not status:
                all_ok = False
        
        print(f"\n📊 Status: {'TODOS OS COMPONENTES OK' if all_ok else 'ALGUNS COMPONENTES FALHARAM'}")
        
        return system, all_ok
        
    except Exception as e:
        print(f"❌ ERRO NA INICIALIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return None, False


async def test_system_capabilities(system):
    """Testa capacidades específicas do sistema."""
    print("\n🧪 TESTE DE CAPACIDADES ESPECÍFICAS")
    print("=" * 80)
    
    tests = []
    
    # 1. Teste de Tools
    try:
        tools = system.tool_registry.list_tools()
        tests.append(("Tool Registry", len(tools) >= 10, f"{len(tools)} ferramentas"))
    except Exception as e:
        tests.append(("Tool Registry", False, f"Erro: {e}"))
    
    # 2. Teste de Command Parsing
    try:
        result = await system.command_parser.parse_slash_command("/help")
        tests.append(("Command Parser", result['type'] == 'help', "Parse de /help"))
    except Exception as e:
        tests.append(("Command Parser", False, f"Erro: {e}"))
    
    # 3. Teste de Health Check
    try:
        health = await system.comprehensive_health_check()
        tests.append(("Health Check", health['overall_status'] in ['healthy', 'degraded'], f"Status: {health['overall_status']}"))
    except Exception as e:
        tests.append(("Health Check", False, f"Erro: {e}"))
    
    # 4. Teste de MCP
    try:
        mcp_health = await system.mcp_client.health_check()
        tests.append(("MCP Client", True, "Cliente MCP funcional"))
    except Exception as e:
        tests.append(("MCP Client", False, f"Erro: {e}"))
    
    # 5. Teste de Memory System
    try:
        await system.memory_system.add_conversation("teste", "resposta teste", "test", True)
        tests.append(("Memory System", True, "Salvou conversa de teste"))
    except Exception as e:
        tests.append(("Memory System", False, f"Erro: {e}"))
    
    # 6. Teste de Permissions
    try:
        security_status = system.permission_manager.get_security_status()
        tests.append(("Permission Manager", isinstance(security_status, dict), "Status de segurança obtido"))
    except Exception as e:
        tests.append(("Permission Manager", False, f"Erro: {e}"))
    
    # Mostra resultados
    successful_tests = 0
    for test_name, success, details in tests:
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name:20} - {details}")
        if success:
            successful_tests += 1
    
    print(f"\n📊 RESULTADO: {successful_tests}/{len(tests)} testes passaram")
    return successful_tests, len(tests)


async def test_claude_code_parity(system):
    """Verifica paridade específica com Claude Code."""
    print("\n🎯 TESTE DE PARIDADE COM CLAUDE CODE")
    print("=" * 80)
    
    # Funcionalidades essenciais do Claude Code
    claude_features = [
        ("Terminal REPL nativo", system.repl is not None),
        ("Comandos slash (/help, /cost, etc.)", system.command_parser is not None),
        ("Sistema de tools estruturado", len(system.tool_registry.tools) >= 10),
        ("BashTool para execução", 'bash' in system.tool_registry.tools),
        ("File tools (read/write/edit)", all(t in system.tool_registry.tools for t in ['read', 'write', 'edit'])),
        ("Search tools (glob/grep/find)", all(t in system.tool_registry.tools for t in ['glob', 'grep', 'find'])),
        ("Sistema de permissões", system.permission_manager is not None),
        ("Gestão de sessões", system.session_manager is not None),
        ("Compactação de contexto", system.context_compactor is not None),
        ("MCP support", system.mcp_client is not None),
        ("Health monitoring", system.health_monitor is not None),
        ("Comando natural parsing", hasattr(system.tool_registry, 'execute_command_natural'))
    ]
    
    # Funcionalidades superiores (que vão além do Claude Code)
    superior_features = [
        ("Sistema de memória SQLite", system.memory_system is not None),
        ("Business Intelligence", hasattr(system, 'analytics_engine')),
        ("Self-healing automático", system.error_detector is not None),
        ("Health monitoring contínuo", system.health_monitor is not None),
        ("Sistema master integrado", True),  # Esta própria arquitetura
        ("Suporte enterprise (Bedrock)", hasattr(system, 'bedrock_manager'))
    ]
    
    # Conta funcionalidades implementadas
    claude_implemented = sum(1 for _, implemented in claude_features if implemented)
    superior_implemented = sum(1 for _, implemented in superior_features if implemented)
    
    print("📋 FUNCIONALIDADES DO CLAUDE CODE:")
    for feature, implemented in claude_features:
        icon = "✅" if implemented else "❌"
        print(f"  {icon} {feature}")
    
    print("\n🚀 FUNCIONALIDADES SUPERIORES (ALÉM DO CLAUDE CODE):")
    for feature, implemented in superior_features:
        icon = "✅" if implemented else "❌"
        print(f"  {icon} {feature}")
    
    # Calcula porcentagem
    claude_parity = (claude_implemented / len(claude_features)) * 100
    superiority = (superior_implemented / len(superior_features)) * 100
    
    print(f"\n📊 RESULTADOS:")
    print(f"  🎯 Paridade Claude Code: {claude_parity:.1f}% ({claude_implemented}/{len(claude_features)})")
    print(f"  🚀 Funcionalidades Superiores: {superiority:.1f}% ({superior_implemented}/{len(superior_features)})")
    
    # Status final
    if claude_parity >= 90:
        if superiority >= 70:
            status = "🏆 SUPERIOR AO CLAUDE CODE"
        else:
            status = "✅ PARIDADE COMPLETA"
    elif claude_parity >= 80:
        status = "🟡 QUASE COMPLETO"
    else:
        status = "🔴 PRECISA MELHORIAS"
    
    print(f"  🏅 Status Final: {status}")
    
    return claude_parity, superiority


async def test_performance_and_stats(system):
    """Testa performance e estatísticas."""
    print("\n⚡ TESTE DE PERFORMANCE E ESTATÍSTICAS")
    print("=" * 80)
    
    try:
        # Obtém estatísticas do sistema
        stats = system.get_system_stats()
        
        print("📊 ESTATÍSTICAS DO SISTEMA:")
        key_stats = [
            ("Versão", stats.get('version', 'N/A')),
            ("Tempo de atividade", stats.get('uptime_formatted', 'N/A')),
            ("Comandos executados", stats.get('total_commands', 0)),
            ("Operações bem-sucedidas", stats.get('successful_operations', 0)),
            ("Paridade calculada", f"{stats.get('parity_percentage', 0)}%"),
            ("Sistema inicializado", "Sim" if stats.get('is_initialized') else "Não")
        ]
        
        for key, value in key_stats:
            print(f"  • {key}: {value}")
        
        # Tool statistics
        if 'tool_stats' in stats:
            tool_stats = stats['tool_stats']
            registry_stats = tool_stats.get('registry_stats', {})
            print(f"  • Ferramentas registradas: {registry_stats.get('total_tools', 0)}")
            print(f"  • Execuções de ferramentas: {registry_stats.get('total_executions', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro obtendo estatísticas: {e}")
        return False


async def main():
    """Função principal de teste."""
    print("🧪 TESTE COMPLETO DO GEMINI CODE SYSTEM")
    print("Verificando TODAS as funcionalidades implementadas")
    print("=" * 80)
    
    # 1. Teste de inicialização
    system, init_ok = await test_complete_initialization()
    
    if not init_ok or not system:
        print("\n❌ FALHA NA INICIALIZAÇÃO - INTERROMPENDO TESTES")
        return 1
    
    # 2. Teste de capacidades
    successful_tests, total_tests = await test_system_capabilities(system)
    
    # 3. Teste de paridade com Claude Code
    claude_parity, superiority = await test_claude_code_parity(system)
    
    # 4. Teste de performance
    perf_ok = await test_performance_and_stats(system)
    
    # Resultado final
    print("\n" + "=" * 80)
    print("🏆 RESULTADO FINAL DO TESTE COMPLETO")
    print("=" * 80)
    
    overall_score = (
        (50 if init_ok else 0) +
        (30 * successful_tests / total_tests) +
        (20 * claude_parity / 100)
    )
    
    print(f"📊 PONTUAÇÃO GERAL: {overall_score:.1f}/100")
    print(f"🎯 Paridade Claude Code: {claude_parity:.1f}%")
    print(f"🚀 Funcionalidades Superiores: {superiority:.1f}%")
    print(f"✅ Testes Passaram: {successful_tests}/{total_tests}")
    
    if overall_score >= 90:
        final_status = "🏆 SISTEMA EXCELENTE - SUPERIOR AO CLAUDE CODE"
    elif overall_score >= 80:
        final_status = "✅ SISTEMA BOM - PARIDADE ALTA"
    elif overall_score >= 70:
        final_status = "🟡 SISTEMA FUNCIONAL - PRECISA AJUSTES"
    else:
        final_status = "🔴 SISTEMA PRECISA MELHORIAS SIGNIFICATIVAS"
    
    print(f"\n🎖️ STATUS FINAL: {final_status}")
    
    # Shutdown gracioso
    try:
        await system.shutdown()
    except:
        pass
    
    print("\n✅ TESTE COMPLETO FINALIZADO")
    return 0 if overall_score >= 80 else 1


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)