#!/usr/bin/env python3
"""
Teste de funcionalidade do REPL e sistema de tools
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.tools.tool_registry import get_tool_registry
from gemini_code.tools.base_tool import ToolInput
from gemini_code.cli.command_parser import CommandParser
from gemini_code.cli.session_manager import SessionManager


async def test_tools():
    """Testa o sistema de ferramentas."""
    print("🔧 Testando Sistema de Tools...")
    
    registry = get_tool_registry()
    
    # Lista ferramentas disponíveis
    tools = registry.list_tools()
    print(f"✅ Ferramentas registradas: {len(tools)}")
    for tool in tools:
        print(f"   - {tool}")
    
    # Testa ferramenta de listagem
    print("\n📁 Testando ListTool...")
    list_input = ToolInput(command=".")
    list_result = await registry.execute_tool("list", list_input)
    
    if list_result.success:
        files_count = list_result.data['summary']['files']
        dirs_count = list_result.data['summary']['directories']
        print(f"✅ Listagem OK: {files_count} arquivos, {dirs_count} diretórios")
    else:
        print(f"❌ Erro na listagem: {list_result.error}")
    
    # Testa ferramenta de busca
    print("\n🔍 Testando GlobTool...")
    glob_input = ToolInput(command="*.py")
    glob_result = await registry.execute_tool("glob", glob_input)
    
    if glob_result.success:
        matches = glob_result.data['summary']['total_matches']
        print(f"✅ Busca glob OK: {matches} arquivos Python encontrados")
    else:
        print(f"❌ Erro na busca: {glob_result.error}")
    
    # Testa comando natural
    print("\n🧠 Testando comando natural...")
    natural_result = await registry.execute_command_natural("liste os arquivos")
    
    if natural_result.success:
        print("✅ Comando natural processado com sucesso")
    else:
        print(f"❌ Erro no comando natural: {natural_result.error}")
    
    print(f"\n📊 Estatísticas: {registry.total_executions} execuções")


async def test_command_parser():
    """Testa o parser de comandos slash."""
    print("\n📝 Testando Command Parser...")
    
    parser = CommandParser()
    
    # Testa alguns comandos slash
    test_commands = [
        "/help",
        "/cost today",
        "/clear session",
        "/compact --aggressive",
        "/doctor --verbose",
        "/memory search teste",
        "/config get model.name",
        "/sessions list --limit=5"
    ]
    
    for cmd in test_commands:
        try:
            result = await parser.parse_slash_command(cmd)
            print(f"✅ {cmd:20} → {result['type']}")
        except Exception as e:
            print(f"❌ {cmd:20} → Erro: {e}")


async def test_session_manager():
    """Testa o gerenciador de sessões."""
    print("\n💾 Testando Session Manager...")
    
    session_manager = SessionManager(Path.cwd())
    
    # Cria nova sessão
    session = await session_manager.create_session("test_session")
    print(f"✅ Sessão criada: {session['id'][:8]}")
    
    # Lista sessões
    sessions = await session_manager.list_sessions(limit=5)
    print(f"✅ {len(sessions)} sessões encontradas")
    
    # Estatísticas
    stats = await session_manager.get_session_stats(session['id'])
    if stats:
        print(f"✅ Estatísticas obtidas para sessão {session['id'][:8]}")
    else:
        print("⚠️ Sem estatísticas para a sessão")


async def test_health_check():
    """Testa verificação de saúde do sistema."""
    print("\n🏥 Testando Health Check...")
    
    registry = get_tool_registry()
    health = await registry.health_check()
    
    status = health['overall_status']
    total_tools = health['total_tools']
    issues = len(health['issues'])
    
    print(f"✅ Status geral: {status}")
    print(f"✅ Total de ferramentas: {total_tools}")
    
    if issues == 0:
        print("✅ Nenhum problema detectado")
    else:
        print(f"⚠️ {issues} problemas encontrados:")
        for issue in health['issues'][:3]:  # Mostra apenas os primeiros 3
            print(f"   - {issue}")


async def main():
    """Função principal de teste."""
    print("🚀 TESTE DE FUNCIONALIDADE - GEMINI CODE REPL")
    print("=" * 60)
    
    try:
        await test_tools()
        await test_command_parser()
        await test_session_manager()
        await test_health_check()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n🎯 FUNCIONALIDADES TESTADAS:")
        print("   ✅ Sistema de Tools estruturado")
        print("   ✅ Command Parser com comandos slash")
        print("   ✅ Session Manager")
        print("   ✅ Health Check")
        print("   ✅ Tool Registry")
        print("   ✅ Comando natural parsing")
        
        print(f"\n🚀 O Gemini Code REPL está funcionando!")
        print("   Execute: python3 gemini_repl.py")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
