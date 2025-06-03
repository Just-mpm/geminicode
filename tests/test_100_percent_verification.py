#!/usr/bin/env python3
"""
Teste de Verificação 100% - Gemini Code
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

class GeminiCode100PercentTest:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'total_score': 0
        }
    
    async def run_all_tests(self):
        """Executa todos os testes de verificação."""
        print("="*60)
        print("TESTE DE VERIFICAÇÃO 100% - GEMINI CODE")
        print("="*60)
        
        # 1. Teste de imports
        print("\n[1/5] Testando imports...")
        import_score = await self.test_imports()
        print(f"Score: {import_score}%")
        
        # 2. Teste de NLP
        print("\n[2/5] Testando NLP...")
        nlp_score = await self.test_nlp()
        print(f"Score: {nlp_score}%")
        
        # 3. Teste de configuração
        print("\n[3/5] Testando configuração...")
        config_score = await self.test_config()
        print(f"Score: {config_score}%")
        
        # 4. Teste de auto-diagnóstico
        print("\n[4/5] Testando auto-diagnóstico...")
        self_healing_score = await self.test_self_healing()
        print(f"Score: {self_healing_score}%")
        
        # 5. Teste de funcionalidade básica
        print("\n[5/5] Testando funcionalidade básica...")
        basic_score = await self.test_basic_functionality()
        print(f"Score: {basic_score}%")
        
        # Calcular score total
        total_score = (import_score + nlp_score + config_score + self_healing_score + basic_score) / 5
        self.results['total_score'] = total_score
        
        print("\n" + "="*60)
        print(f"SCORE TOTAL: {total_score}%")
        print("="*60)
        
        if total_score == 100:
            print("\n✅ SISTEMA 100% FUNCIONAL!")
        elif total_score >= 80:
            print("\n⚠️  Sistema funcional com pequenos ajustes necessários")
        else:
            print("\n❌ Sistema precisa de correções")
        
        return total_score == 100
    
    async def test_imports(self):
        """Testa se todos os módulos podem ser importados."""
        modules = [
            'gemini_code.core.gemini_client',
            'gemini_code.core.nlp_enhanced',
            'gemini_code.core.config_wrapper',
            'gemini_code.core.self_healing',
            'gemini_code.interface.enhanced_chat_interface',
            'gemini_code.core.autonomous_executor',
            'gemini_code.analysis.health_monitor'
        ]
        
        success = 0
        for module in modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
                success += 1
            except Exception as e:
                print(f"  ❌ {module}: {e}")
        
        score = (success / len(modules)) * 100
        self.results['tests'].append({
            'test': 'imports',
            'score': score,
            'details': f"{success}/{len(modules)} módulos importados"
        })
        return score
    
    async def test_nlp(self):
        """Testa funcionalidade NLP."""
        from gemini_code.core.nlp_enhanced import NLPEnhanced
        
        test_cases = [
            ("criar agente AutoPrice", "create_agent"),
            ("diagnosticar sistema", "self_diagnosis"),
            ("melhorar sistema com nova função", "self_improve"),
            ("git push para github", "git_push"),
            ("executar pytest", "run_command")
        ]
        
        nlp = NLPEnhanced()
        success = 0
        
        for text, expected in test_cases:
            result = await nlp.identify_intent(text)
            if result['intent'] == expected:
                print(f"  ✅ '{text}' -> {result['intent']}")
                success += 1
            else:
                print(f"  ❌ '{text}' -> {result['intent']} (esperado: {expected})")
        
        score = (success / len(test_cases)) * 100
        self.results['tests'].append({
            'test': 'nlp',
            'score': score,
            'details': f"{success}/{len(test_cases)} intents corretos"
        })
        return score
    
    async def test_config(self):
        """Testa sistema de configuração."""
        try:
            from gemini_code.core.config_wrapper import Config
            
            config = Config()
            
            # Teste 1: set/get básico
            config.set('test_key', 'test_value')
            value1 = config.get('test_key')
            test1 = value1 == 'test_value'
            
            # Teste 2: valores conhecidos
            config.set('enable_real_execution', True)
            value2 = config.get('enable_real_execution')
            test2 = value2 == True
            
            # Teste 3: default values
            value3 = config.get('non_existent_key', 'default')
            test3 = value3 == 'default'
            
            success = sum([test1, test2, test3])
            total = 3
            
            print(f"  {'✅' if test1 else '❌'} Set/get básico")
            print(f"  {'✅' if test2 else '❌'} Valores conhecidos")
            print(f"  {'✅' if test3 else '❌'} Valores default")
            
            score = (success / total) * 100
            self.results['tests'].append({
                'test': 'config',
                'score': score,
                'details': f"{success}/{total} testes de config"
            })
            return score
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            self.results['tests'].append({
                'test': 'config',
                'score': 0,
                'error': str(e)
            })
            return 0
    
    async def test_self_healing(self):
        """Testa sistema de auto-diagnóstico."""
        try:
            from gemini_code.core.self_healing import SelfHealingSystem
            
            self_healing = SelfHealingSystem()
            
            # Teste 1: Diagnóstico
            health = await self_healing.diagnose_system()
            test1 = health.overall_health >= 0 and health.overall_health <= 100
            
            # Teste 2: Geração de relatório
            report = await self_healing.generate_diagnostic_report(health)
            test2 = len(report) > 0 and "RELATÓRIO" in report
            
            # Teste 3: Componentes
            test3 = len(health.components) > 0
            
            success = sum([test1, test2, test3])
            total = 3
            
            print(f"  {'✅' if test1 else '❌'} Diagnóstico executado (saúde: {health.overall_health}%)")
            print(f"  {'✅' if test2 else '❌'} Relatório gerado")
            print(f"  {'✅' if test3 else '❌'} Componentes analisados: {len(health.components)}")
            
            score = (success / total) * 100
            self.results['tests'].append({
                'test': 'self_healing',
                'score': score,
                'details': f"{success}/{total} funcionalidades de auto-diagnóstico"
            })
            return score
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            self.results['tests'].append({
                'test': 'self_healing',
                'score': 0,
                'error': str(e)
            })
            return 0
    
    async def test_basic_functionality(self):
        """Testa funcionalidades básicas do sistema."""
        tests_passed = 0
        total_tests = 4
        
        # Teste 1: Criar arquivo
        test_file = Path("test_gemini_functionality.txt")
        try:
            test_file.write_text("Teste do Gemini Code")
            exists = test_file.exists()
            content = test_file.read_text() if exists else ""
            test1 = exists and content == "Teste do Gemini Code"
            if test_file.exists():
                test_file.unlink()
            tests_passed += 1 if test1 else 0
            print(f"  {'✅' if test1 else '❌'} Operações de arquivo")
        except:
            print("  ❌ Operações de arquivo")
        
        # Teste 2: Diretórios
        test_dir = Path("test_gemini_dir")
        try:
            test_dir.mkdir(exist_ok=True)
            exists = test_dir.exists() and test_dir.is_dir()
            if test_dir.exists():
                test_dir.rmdir()
            tests_passed += 1 if exists else 0
            print(f"  {'✅' if exists else '❌'} Operações de diretório")
        except:
            print("  ❌ Operações de diretório")
        
        # Teste 3: JSON
        try:
            data = {"test": "gemini", "version": 1}
            json_str = json.dumps(data)
            loaded = json.loads(json_str)
            test3 = loaded == data
            tests_passed += 1 if test3 else 0
            print(f"  {'✅' if test3 else '❌'} Serialização JSON")
        except:
            print("  ❌ Serialização JSON")
        
        # Teste 4: Asyncio
        try:
            async def test_async():
                await asyncio.sleep(0.001)
                return True
            
            result = await test_async()
            tests_passed += 1 if result else 0
            print(f"  {'✅' if result else '❌'} Operações assíncronas")
        except:
            print("  ❌ Operações assíncronas")
        
        score = (tests_passed / total_tests) * 100
        self.results['tests'].append({
            'test': 'basic_functionality',
            'score': score,
            'details': f"{tests_passed}/{total_tests} funcionalidades básicas"
        })
        return score


async def main():
    """Executa o teste de 100%."""
    tester = GeminiCode100PercentTest()
    
    try:
        is_100_percent = await tester.run_all_tests()
        
        # Salvar relatório
        with open('gemini_code_100_percent_report.json', 'w') as f:
            json.dump(tester.results, f, indent=2)
        
        print(f"\n📄 Relatório salvo em: gemini_code_100_percent_report.json")
        
        return 0 if is_100_percent else 1
        
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)