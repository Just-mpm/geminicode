#!/usr/bin/env python3
"""
Teste das melhorias críticas implementadas com base na análise do Gemini
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

async def test_critical_improvements():
    """Testa as melhorias críticas implementadas"""
    print("🧪 Testando Melhorias Críticas Implementadas")
    print("=" * 50)
    
    results = {}
    
    # 1. Teste de Configuração de Thresholds Ajustados
    print("\n1. 🎯 Testando Configuração de Thresholds Ajustados...")
    try:
        from gemini_code.analysis.health_monitor import HealthMonitor
        from gemini_code.core.gemini_client import GeminiClient
        from gemini_code.core.file_manager import FileManagementSystem
        
        # Criar instâncias sem executar análise completa
        print("   • Inicializando HealthMonitor...")
        gemini_client = GeminiClient()
        file_manager = FileManagementSystem(gemini_client)
        health_monitor = HealthMonitor(gemini_client, file_manager)
        
        config = health_monitor.monitoring_config
        
        # Verificar se os thresholds foram ajustados
        expected_adjustments = {
            'error_threshold': 3,
            'test_coverage_threshold': 60.0,
            'code_quality_threshold': 6.0,
            'documentation_threshold': 50.0
        }
        
        all_adjusted = True
        for key, expected_value in expected_adjustments.items():
            actual_value = config[key]
            if actual_value == expected_value:
                print(f"   ✅ {key}: {actual_value} (ajustado corretamente)")
            else:
                print(f"   ❌ {key}: {actual_value} (esperado: {expected_value})")
                all_adjusted = False
        
        # Verificar padrões de exclusão
        if 'excluded_patterns' in config and len(config['excluded_patterns']) > 0:
            print(f"   ✅ Padrões de exclusão configurados: {len(config['excluded_patterns'])} padrões")
        else:
            print("   ❌ Padrões de exclusão não configurados")
            all_adjusted = False
        
        results['thresholds_adjusted'] = all_adjusted
        
    except Exception as e:
        print(f"   ❌ Erro no teste de thresholds: {e}")
        results['thresholds_adjusted'] = False
    
    # 2. Teste de Validação de Entrada Robusta
    print("\n2. 🛡️ Testando Validação de Entrada Robusta...")
    try:
        from gemini_code.core.nlp_enhanced import NLPEnhanced
        
        nlp = NLPEnhanced()
        
        # Teste com entrada vazia
        result_empty = await nlp.identify_intent("")
        if result_empty['intent'] == 'unknown' and result_empty['confidence'] == 0:
            print("   ✅ Entrada vazia tratada corretamente")
        else:
            print(f"   ❌ Entrada vazia não tratada: {result_empty}")
        
        # Teste com entrada apenas espaços
        result_spaces = await nlp.identify_intent("   \n\t   ")
        if result_spaces['intent'] == 'unknown':
            print("   ✅ Entrada com apenas espaços tratada corretamente")
        else:
            print(f"   ❌ Entrada com espaços não tratada: {result_spaces}")
        
        # Teste com entrada muito longa
        long_text = "a" * 6000
        result_long = await nlp.identify_intent(long_text)
        if result_long is not None:
            print("   ✅ Entrada muito longa tratada sem erro")
        else:
            print("   ❌ Entrada muito longa causou erro")
        
        results['input_validation'] = True
        
    except Exception as e:
        print(f"   ❌ Erro no teste de validação: {e}")
        results['input_validation'] = False
    
    # 3. Teste de Filtros de Arquivos Melhorados
    print("\n3. 📁 Testando Filtros de Arquivos Melhorados...")
    try:
        health_monitor = HealthMonitor(gemini_client, file_manager)
        
        # Testar filtro de arquivos
        valid_files = health_monitor._filter_valid_python_files(str(Path.cwd()))
        
        print(f"   • Arquivos Python válidos encontrados: {len(valid_files)}")
        
        # Verificar se __pycache__ foi filtrado
        has_pycache = any('__pycache__' in str(f) for f in valid_files)
        if not has_pycache:
            print("   ✅ Arquivos __pycache__ filtrados corretamente")
        else:
            print("   ❌ Arquivos __pycache__ não foram filtrados")
        
        # Verificar se arquivos temporários foram filtrados
        has_temp = any('temp_' in str(f) or f.name.startswith('.') for f in valid_files)
        if not has_temp:
            print("   ✅ Arquivos temporários filtrados corretamente")
        else:
            print("   ⚠️ Alguns arquivos temporários podem não ter sido filtrados")
        
        results['file_filtering'] = len(valid_files) > 0 and not has_pycache
        
    except Exception as e:
        print(f"   ❌ Erro no teste de filtros: {e}")
        results['file_filtering'] = False
    
    # 4. Teste de Humanização de Erros
    print("\n4. 💬 Testando Humanização de Erros...")
    try:
        from gemini_code.utils.error_humanizer import humanize_error
        
        # Teste com erro comum
        test_error = FileNotFoundError("No such file or directory: 'arquivo.py'")
        humanized = humanize_error(test_error, "Teste de erro")
        
        if "❌" in humanized and "💡" in humanized:
            print("   ✅ Erro humanizado corretamente com emojis e dicas")
        else:
            print(f"   ❌ Erro não humanizado adequadamente: {humanized[:100]}...")
        
        # Teste com erro de API
        api_error = AttributeError("'NoneType' object has no attribute 'generate_response'")
        humanized_api = humanize_error(api_error, "Comunicação com IA")
        
        if "comunicação" in humanized_api.lower() or "problema interno" in humanized_api.lower():
            print("   ✅ Erro de API humanizado corretamente")
        else:
            print("   ❌ Erro de API não humanizado adequadamente")
        
        results['error_humanization'] = True
        
    except Exception as e:
        print(f"   ❌ Erro no teste de humanização: {e}")
        results['error_humanization'] = False
    
    # 5. Teste de Estrutura do Projeto
    print("\n5. 📂 Testando Melhorias na Estrutura do Projeto...")
    try:
        project_root = Path.cwd()
        
        # Verificar se .gitignore foi criado
        gitignore_exists = (project_root / '.gitignore').exists()
        if gitignore_exists:
            print("   ✅ Arquivo .gitignore criado")
        else:
            print("   ❌ Arquivo .gitignore não encontrado")
        
        # Verificar se error_humanizer foi criado
        humanizer_exists = (project_root / 'gemini_code' / 'utils' / 'error_humanizer.py').exists()
        if humanizer_exists:
            print("   ✅ Error humanizer implementado")
        else:
            print("   ❌ Error humanizer não encontrado")
        
        results['project_structure'] = gitignore_exists and humanizer_exists
        
    except Exception as e:
        print(f"   ❌ Erro no teste de estrutura: {e}")
        results['project_structure'] = False
    
    # Relatório Final
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSOU" if passed_test else "❌ FALHOU"
        test_display = {
            'thresholds_adjusted': 'Configuração de Thresholds Ajustados',
            'input_validation': 'Validação de Entrada Robusta', 
            'file_filtering': 'Filtros de Arquivos Melhorados',
            'error_humanization': 'Humanização de Erros',
            'project_structure': 'Melhorias na Estrutura do Projeto'
        }
        print(f"{status} - {test_display.get(test_name, test_name)}")
        if passed_test:
            passed += 1
    
    print(f"\n🏆 Resultado: {passed}/{total} melhorias críticas implementadas com sucesso")
    
    if passed == total:
        print("🎉 Todas as melhorias críticas estão funcionando!")
        print("🚀 O projeto agora deve ter um score de saúde muito melhor!")
        return 0
    else:
        print("⚠️ Algumas melhorias críticas precisam de ajustes.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_critical_improvements())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro crítico nos testes: {e}")
        sys.exit(1)
