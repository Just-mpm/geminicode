#!/usr/bin/env python3
"""
Test System Functionality - Teste simplificado para verificar funcionalidade real
"""

import asyncio
import sys
from pathlib import Path
import subprocess
import json
import time

# Adiciona o diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

class SystemFunctionalityTester:
    def __init__(self):
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': [],
            'summary': {}
        }
    
    def run_command(self, command):
        """Executa comando via subprocess"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def test_import_modules(self):
        """Testa se os módulos podem ser importados"""
        print("\n[TEST 1] Testando imports dos módulos...")
        
        modules_to_test = [
            'gemini_code.core.gemini_client',
            'gemini_code.core.nlp_enhanced',
            'gemini_code.interface.enhanced_chat_interface',
            'gemini_code.core.autonomous_executor',
            'gemini_code.analysis.health_monitor',
            'gemini_code.core.config'
        ]
        
        success_count = 0
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"  [OK] {module}")
                success_count += 1
            except Exception as e:
                print(f"  [FAIL] {module}: {e}")
        
        result = {
            'test': 'import_modules',
            'success': success_count == len(modules_to_test),
            'details': f"{success_count}/{len(modules_to_test)} módulos importados com sucesso"
        }
        self.results['tests'].append(result)
        return result['success']
    
    def test_nlp_patterns(self):
        """Testa padrões NLP básicos"""
        print("\n[TEST 2] Testando padrões NLP...")
        
        try:
            from gemini_code.core.nlp_enhanced import NLPEnhanced
            nlp = NLPEnhanced()
            
            test_cases = [
                ("criar pasta teste", "create_file"),
                ("analisar código", "analyze_project"),
                ("git push", "git_push"),
                ("executar pytest", "run_command")
            ]
            
            success_count = 0
            for input_text, expected_intent in test_cases:
                result = asyncio.run(nlp.identify_intent(input_text))
                if result['intent'] == expected_intent:
                    print(f"  [OK] '{input_text}' -> {result['intent']}")
                    success_count += 1
                else:
                    print(f"  [FAIL] '{input_text}' -> {result['intent']} (expected {expected_intent})")
            
            result = {
                'test': 'nlp_patterns',
                'success': success_count == len(test_cases),
                'details': f"{success_count}/{len(test_cases)} padrões NLP funcionando"
            }
            self.results['tests'].append(result)
            return result['success']
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            result = {
                'test': 'nlp_patterns',
                'success': False,
                'details': f"Erro: {e}"
            }
            self.results['tests'].append(result)
            return False
    
    def test_config_system(self):
        """Testa sistema de configuração"""
        print("\n[TEST 3] Testando sistema de configuração...")
        
        try:
            from gemini_code.core.config_wrapper import Config
            
            config = Config()
            
            # Testa set/get
            config.set('test_key', 'test_value')
            value = config.get('test_key')
            
            success = value == 'test_value'
            
            if success:
                print("  [OK] Config set/get funcionando")
            else:
                print(f"  [FAIL] Config set/get: esperado 'test_value', obtido '{value}'")
            
            result = {
                'test': 'config_system',
                'success': success,
                'details': "Sistema de configuração funcionando" if success else "Falha no config"
            }
            self.results['tests'].append(result)
            return success
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            result = {
                'test': 'config_system',
                'success': False,
                'details': f"Erro: {e}"
            }
            self.results['tests'].append(result)
            return False
    
    def test_file_operations(self):
        """Testa operações básicas de arquivo"""
        print("\n[TEST 4] Testando operações de arquivo...")
        
        test_file = Path("test_temp_file.txt")
        test_content = "Test content for Gemini Code"
        
        try:
            # Criar arquivo
            test_file.write_text(test_content)
            
            # Verificar se existe
            exists = test_file.exists()
            
            # Ler conteúdo
            read_content = test_file.read_text() if exists else ""
            
            # Remover arquivo
            if exists:
                test_file.unlink()
            
            success = exists and read_content == test_content
            
            if success:
                print("  [OK] Operações de arquivo funcionando")
            else:
                print("  [FAIL] Problema nas operações de arquivo")
            
            result = {
                'test': 'file_operations',
                'success': success,
                'details': "Operações de arquivo OK" if success else "Falha em operações de arquivo"
            }
            self.results['tests'].append(result)
            return success
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            # Limpar se der erro
            if test_file.exists():
                test_file.unlink()
            
            result = {
                'test': 'file_operations',
                'success': False,
                'details': f"Erro: {e}"
            }
            self.results['tests'].append(result)
            return False
    
    def test_main_entry(self):
        """Testa se o main.py pode ser executado"""
        print("\n[TEST 5] Testando ponto de entrada principal...")
        
        # Testa apenas help para verificar se o script carrega
        result = self.run_command('python3 main.py --help')
        
        success = result['success'] and 'Gemini Code' in result['stdout']
        
        if success:
            print("  [OK] main.py carregou corretamente")
        else:
            print(f"  [FAIL] main.py não carregou: {result['stderr']}")
        
        test_result = {
            'test': 'main_entry',
            'success': success,
            'details': "main.py funcionando" if success else f"Erro: {result['stderr'][:100]}"
        }
        self.results['tests'].append(test_result)
        return success
    
    def generate_report(self):
        """Gera relatório final"""
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for t in self.results['tests'] if t['success'])
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        print("\n" + "="*60)
        print("RELATÓRIO FINAL - TESTE DE FUNCIONALIDADE")
        print("="*60)
        print(f"Total de testes: {total_tests}")
        print(f"Sucessos: {passed_tests}")
        print(f"Falhas: {total_tests - passed_tests}")
        print(f"Taxa de sucesso: {self.results['summary']['success_rate']:.1f}%")
        print("="*60)
        
        # Salvar relatório
        with open('functionality_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results['summary']['success_rate'] >= 80

def main():
    print("TESTE DE FUNCIONALIDADE DO SISTEMA GEMINI CODE")
    print("="*60)
    
    tester = SystemFunctionalityTester()
    
    # Executar testes
    tester.test_import_modules()
    tester.test_nlp_patterns()
    tester.test_config_system()
    tester.test_file_operations()
    tester.test_main_entry()
    
    # Gerar relatório
    success = tester.generate_report()
    
    if success:
        print("\n[SUCESSO] Sistema funcionando adequadamente!")
        return 0
    else:
        print("\n[FALHA] Sistema precisa de correções!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
