"""
Teste completo de integração do sistema Gemini Code
Verifica todas as funcionalidades principais
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.master_system import GeminiCodeMasterSystem
from gemini_code.utils.logger import Logger


class SystemIntegrationTest:
    """Testa integração completa do sistema."""
    
    def __init__(self):
        self.logger = Logger()
        self.master_system = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    async def run_all_tests(self):
        """Executa todos os testes de integração."""
        print("\n" + "="*80)
        print("🧪 TESTE COMPLETO DE INTEGRAÇÃO DO GEMINI CODE")
        print("="*80 + "\n")
        
        # 1. Teste de inicialização
        await self.test_system_initialization()
        
        # 2. Teste de comandos slash
        await self.test_slash_commands()
        
        # 3. Teste de processamento de linguagem natural
        await self.test_natural_language_processing()
        
        # 4. Teste de ferramentas (tools)
        await self.test_tools_execution()
        
        # 5. Teste de sistema de permissões
        await self.test_permission_system()
        
        # 6. Teste de módulos de cognição
        await self.test_cognition_modules()
        
        # 7. Teste de memória e contexto
        await self.test_memory_system()
        
        # 8. Teste de health check
        await self.test_health_check()
        
        # 9. Teste de compactação de contexto
        await self.test_context_compaction()
        
        # 10. Teste de aprendizado
        await self.test_learning_engine()
        
        # Relatório final
        self.print_test_report()
    
    async def test_system_initialization(self):
        """Testa inicialização do sistema."""
        print("🔧 Testando inicialização do sistema...")
        
        try:
            self.master_system = GeminiCodeMasterSystem(project_path=".")
            success = await self.master_system.initialize()
            
            if success and self.master_system.is_initialized:
                print("✅ Sistema inicializado com sucesso")
                self.test_results['passed'] += 1
                
                # Verifica componentes principais
                components = [
                    ('Gemini Client', self.master_system.gemini_client),
                    ('Project Manager', self.master_system.project_manager),
                    ('Memory System', self.master_system.memory_system),
                    ('Tool Registry', self.master_system.tool_registry),
                    ('Permission Manager', self.master_system.permission_manager),
                    ('Chat Interface', hasattr(self.master_system, 'chat_interface')),
                    ('Command Executor', hasattr(self.master_system, 'command_executor')),
                    ('Architectural Reasoning', hasattr(self.master_system, 'architectural_reasoning')),
                    ('Learning Engine', hasattr(self.master_system, 'learning_engine'))
                ]
                
                for name, component in components:
                    if component:
                        print(f"  ✓ {name}: OK")
                    else:
                        print(f"  ✗ {name}: FALHOU")
                        self.test_results['errors'].append(f"{name} não inicializado")
            else:
                print("❌ Falha na inicialização do sistema")
                self.test_results['failed'] += 1
                self.test_results['errors'].append("Sistema não inicializou corretamente")
                
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Erro de inicialização: {str(e)}")
    
    async def test_slash_commands(self):
        """Testa comandos slash."""
        print("\n📝 Testando comandos slash...")
        
        if not self.master_system:
            print("⚠️ Sistema não inicializado, pulando teste")
            return
        
        commands = [
            ('/help', 'help'),
            ('/cost', 'cost'),
            ('/memory', 'memory'),
            ('/doctor', 'doctor')
        ]
        
        for command, expected_type in commands:
            try:
                result = await self.master_system.execute_command(command)
                
                if result.get('success') and result.get('type') == expected_type:
                    print(f"  ✓ {command}: OK")
                    self.test_results['passed'] += 1
                else:
                    print(f"  ✗ {command}: Resposta inesperada")
                    self.test_results['failed'] += 1
                    
            except Exception as e:
                print(f"  ✗ {command}: Erro - {e}")
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"Erro em {command}: {str(e)}")
    
    async def test_natural_language_processing(self):
        """Testa processamento de linguagem natural."""
        print("\n🗣️ Testando processamento de linguagem natural...")
        
        if not self.master_system:
            print("⚠️ Sistema não inicializado, pulando teste")
            return
        
        test_commands = [
            "mostre os arquivos do projeto",
            "analise a estrutura do código",
            "crie um arquivo teste.py com print('Hello')"
        ]
        
        for command in test_commands:
            try:
                result = await self.master_system.execute_command(command)
                
                if result.get('success') or 'processed_by' in result:
                    print(f"  ✓ '{command[:30]}...': Processado")
                    self.test_results['passed'] += 1
                else:
                    print(f"  ✗ '{command[:30]}...': Falhou")
                    self.test_results['failed'] += 1
                    
            except Exception as e:
                print(f"  ✗ '{command[:30]}...': Erro - {e}")
                self.test_results['failed'] += 1
    
    async def test_tools_execution(self):
        """Testa execução de ferramentas."""
        print("\n🔨 Testando sistema de ferramentas...")
        
        if not self.master_system or not self.master_system.tool_registry:
            print("⚠️ Tool registry não disponível, pulando teste")
            return
        
        # Lista ferramentas disponíveis
        tools = self.master_system.tool_registry.list_tools()
        print(f"  📦 {len(tools)} ferramentas registradas")
        
        # Testa health check do registry
        try:
            health = await self.master_system.tool_registry.health_check()
            
            if health.get('overall_status') == 'healthy':
                print("  ✓ Tool registry saudável")
                self.test_results['passed'] += 1
            else:
                print("  ✗ Tool registry com problemas")
                self.test_results['failed'] += 1
                
        except Exception as e:
            print(f"  ✗ Erro no health check: {e}")
            self.test_results['failed'] += 1
    
    async def test_permission_system(self):
        """Testa sistema de permissões."""
        print("\n🔒 Testando sistema de permissões...")
        
        if not self.master_system or not self.master_system.permission_manager:
            print("⚠️ Permission manager não disponível, pulando teste")
            return
        
        # Testa verificação de permissão
        try:
            permission_check = await self.master_system.permission_manager.check_permission(
                'execute_command',
                {'command': 'ls', 'context': {}}
            )
            
            if isinstance(permission_check, dict) and 'allowed' in permission_check:
                print("  ✓ Sistema de permissões funcionando")
                self.test_results['passed'] += 1
            else:
                print("  ✗ Resposta inválida do sistema de permissões")
                self.test_results['failed'] += 1
                
        except Exception as e:
            print(f"  ✗ Erro no sistema de permissões: {e}")
            self.test_results['failed'] += 1
    
    async def test_cognition_modules(self):
        """Testa módulos de cognição."""
        print("\n🧠 Testando módulos de cognição...")
        
        if not self.master_system:
            print("⚠️ Sistema não inicializado, pulando teste")
            return
        
        # Testa cada módulo de cognição
        cognition_tests = [
            ('Architectural Reasoning', self.master_system.architectural_reasoning, 
             lambda m: m.analyze_architecture(deep_analysis=False)),
            ('Complexity Analyzer', self.master_system.complexity_analyzer,
             lambda m: m.analyze_project_complexity()),
            ('Design Pattern Engine', self.master_system.design_pattern_engine,
             lambda m: m.analyze_patterns(deep_analysis=False)),
            ('Problem Solver', self.master_system.problem_solver,
             lambda m: m.analyze_project_problems()),
            ('Learning Engine', self.master_system.learning_engine,
             lambda m: m.get_learned_patterns())
        ]
        
        for name, module, test_func in cognition_tests:
            if module:
                try:
                    result = await test_func(module)
                    print(f"  ✓ {name}: OK")
                    self.test_results['passed'] += 1
                except Exception as e:
                    print(f"  ✗ {name}: Erro - {str(e)[:50]}...")
                    self.test_results['failed'] += 1
            else:
                print(f"  ⚠️ {name}: Não inicializado")
    
    async def test_memory_system(self):
        """Testa sistema de memória."""
        print("\n💾 Testando sistema de memória...")
        
        if not self.master_system or not self.master_system.memory_system:
            print("⚠️ Memory system não disponível, pulando teste")
            return
        
        try:
            # Adiciona uma conversa de teste
            await self.master_system.memory_system.add_conversation(
                user_input="teste de memória",
                assistant_response="memória funcionando",
                intent="test",
                success=True
            )
            
            # Recupera contexto recente
            context = await self.master_system.memory_system.get_recent_context(1)
            
            if context and len(context) > 0:
                print("  ✓ Sistema de memória funcionando")
                self.test_results['passed'] += 1
            else:
                print("  ✗ Falha ao recuperar contexto")
                self.test_results['failed'] += 1
                
        except Exception as e:
            print(f"  ✗ Erro no sistema de memória: {e}")
            self.test_results['failed'] += 1
    
    async def test_health_check(self):
        """Testa health check completo."""
        print("\n🏥 Testando health check...")
        
        if not self.master_system:
            print("⚠️ Sistema não inicializado, pulando teste")
            return
        
        try:
            health = await self.master_system.comprehensive_health_check()
            
            print(f"  📊 Status geral: {health['overall_status']}")
            print(f"  🔧 Sistemas verificados: {len(health['systems'])}")
            
            # Verifica cada sistema
            for system_name, system_health in health['systems'].items():
                status = system_health.get('status', 'unknown')
                if status == 'healthy':
                    print(f"    ✓ {system_name}: {status}")
                else:
                    print(f"    ✗ {system_name}: {status}")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Erro no health check: {e}")
            self.test_results['failed'] += 1
    
    async def test_context_compaction(self):
        """Testa compactação de contexto."""
        print("\n📦 Testando compactação de contexto...")
        
        if not self.master_system or not self.master_system.context_compactor:
            print("⚠️ Context compactor não disponível, pulando teste")
            return
        
        try:
            # Simula contexto grande
            test_context = [
                {'role': 'user', 'content': f'Mensagem {i}'} 
                for i in range(10)
            ]
            
            result = await self.master_system.context_compactor.compact_context(
                test_context,
                custom_instructions="Manter apenas informações essenciais"
            )
            
            if result and 'compacted_count' in result:
                print(f"  ✓ Contexto compactado: {result['original_count']} → {result['compacted_count']}")
                self.test_results['passed'] += 1
            else:
                print("  ✗ Falha na compactação")
                self.test_results['failed'] += 1
                
        except Exception as e:
            print(f"  ✗ Erro na compactação: {e}")
            self.test_results['failed'] += 1
    
    async def test_learning_engine(self):
        """Testa engine de aprendizado."""
        print("\n🎓 Testando engine de aprendizado...")
        
        if not self.master_system or not self.master_system.learning_engine:
            print("⚠️ Learning engine não disponível, pulando teste")
            return
        
        try:
            # Simula interação para aprendizado
            test_interaction = {
                'command': 'create file test.py',
                'result': {'success': True},
                'execution_time': 0.5
            }
            
            entry = await self.master_system.learning_engine.learn_from_interaction(
                test_interaction
            )
            
            if entry and entry.id:
                print("  ✓ Aprendizado registrado")
                
                # Testa aplicação de aprendizado
                suggestions = await self.master_system.learning_engine.apply_learning(
                    "create file"
                )
                
                print(f"  ✓ Sugestões geradas: {len(suggestions.get('patterns', []))} padrões")
                self.test_results['passed'] += 1
            else:
                print("  ✗ Falha no aprendizado")
                self.test_results['failed'] += 1
                
        except Exception as e:
            print(f"  ✗ Erro no learning engine: {e}")
            self.test_results['failed'] += 1
    
    def print_test_report(self):
        """Imprime relatório final dos testes."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("="*80)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n✅ Testes aprovados: {self.test_results['passed']}")
        print(f"❌ Testes falhados: {self.test_results['failed']}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n⚠️ Erros encontrados ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors'][:10]:  # Mostra até 10 erros
                print(f"  • {error}")
        
        # Avaliação final
        print(f"\n🏆 AVALIAÇÃO FINAL: ", end="")
        if success_rate >= 90:
            print("EXCELENTE - Sistema está funcionando perfeitamente! ✨")
        elif success_rate >= 70:
            print("BOM - Sistema funcional com pequenos ajustes necessários 👍")
        elif success_rate >= 50:
            print("REGULAR - Sistema precisa de melhorias significativas 🔧")
        else:
            print("CRÍTICO - Sistema com muitos problemas, requer atenção urgente ⚠️")
        
        print("\n" + "="*80)


async def main():
    """Função principal."""
    tester = SystemIntegrationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("\n🚀 Iniciando teste completo do Gemini Code...")
    print("⏳ Este teste pode levar alguns minutos...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro crítico durante os testes: {e}")
        import traceback
        traceback.print_exc()