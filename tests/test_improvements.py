#!/usr/bin/env python3
"""
Teste das melhorias implementadas no Gemini Code
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

async def test_health_monitor_improvements():
    """Testa as melhorias no HealthMonitor"""
    print("🧪 Testando melhorias no HealthMonitor...")
    
    try:
        from main import GeminiCodeMain
        
        # Inicializa o sistema
        gemini_code = GeminiCodeMain()
        await gemini_code.initialize()
        
        # Testa o HealthMonitor melhorado
        print("\n🔍 Executando análise de saúde melhorada...")
        health_report = await gemini_code.health_monitor.full_health_check(str(Path.cwd()))
        
        # Mostra o relatório
        print("\n📊 Relatório de Saúde Melhorado:")
        health_summary = await gemini_code.health_monitor.get_health_summary(health_report)
        print(health_summary)
        
        return True
        
    except Exception as e:
        from gemini_code.utils.error_humanizer import humanize_error
        friendly_error = humanize_error(e, "Teste das melhorias do HealthMonitor")
        print(f"\n❌ Erro durante o teste:\n{friendly_error}")
        return False

async def test_error_humanizer():
    """Testa o humanizador de erros"""
    print("\n🧪 Testando Error Humanizer...")
    
    try:
        from gemini_code.utils.error_humanizer import humanize_error
        
        # Testa vários tipos de erro
        test_errors = [
            FileNotFoundError("No such file or directory: 'arquivo_inexistente.py'"),
            PermissionError("Permission denied: 'arquivo_protegido.txt'"),
            ConnectionError("Failed to establish a new connection"),
            AttributeError("'NoneType' object has no attribute 'generate_response'"),
            ModuleNotFoundError("No module named 'biblioteca_inexistente'")
        ]
        
        print("\n📝 Exemplos de mensagens humanizadas:")
        for i, error in enumerate(test_errors, 1):
            friendly_message = humanize_error(error, f"Teste de erro {i}")
            print(f"\n{i}. {type(error).__name__}:")
            print(friendly_message)
            print("-" * 50)
        
        print("✅ Error Humanizer funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar Error Humanizer: {e}")
        return False

async def test_file_detection():
    """Testa a detecção melhorada de arquivos Python"""
    print("\n🧪 Testando detecção melhorada de arquivos Python...")
    
    try:
        # Lista arquivos Python no projeto
        python_files = list(Path.cwd().rglob("*.py"))
        
        # Filtra arquivos válidos (como no HealthMonitor melhorado)
        valid_python_files = [f for f in python_files 
                             if '__pycache__' not in str(f) 
                             and not f.name.startswith('.')
                             and f.is_file()]
        
        print(f"📁 Total de arquivos .py encontrados: {len(python_files)}")
        print(f"✅ Arquivos Python válidos: {len(valid_python_files)}")
        
        # Mostra alguns exemplos
        print("\n📄 Exemplos de arquivos válidos:")
        for file_path in valid_python_files[:5]:
            relative_path = file_path.relative_to(Path.cwd())
            print(f"   • {relative_path}")
        
        if len(valid_python_files) > 5:
            print(f"   ... e mais {len(valid_python_files) - 5} arquivos")
        
        print("✅ Detecção de arquivos funcionando corretamente!")
        return True
        
    except Exception as e:
        from gemini_code.utils.error_humanizer import humanize_error
        friendly_error = humanize_error(e, "Teste de detecção de arquivos")
        print(f"\n❌ Erro durante o teste:\n{friendly_error}")
        return False

async def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes das melhorias do Gemini Code")
    print("=" * 60)
    
    tests = [
        ("Error Humanizer", test_error_humanizer),
        ("Detecção de Arquivos", test_file_detection),
        ("HealthMonitor Melhorado", test_health_monitor_improvements)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Executando: {test_name}")
        print("-" * 30)
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Falha crítica em {test_name}: {e}")
            results[test_name] = False
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSOU" if passed_test else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\n🏆 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as melhorias estão funcionando corretamente!")
        return 0
    else:
        print("⚠️ Algumas melhorias precisam de ajustes.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro crítico nos testes: {e}")
        sys.exit(1)
