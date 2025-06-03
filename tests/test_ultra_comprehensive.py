#!/usr/bin/env python3
"""
Teste Ultra Abrangente - Verifica TODAS as capacidades do Gemini Code
Testa se o sistema consegue fazer TUDO que o Claude Code faz
"""

import asyncio
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.ultra_executor import UltraExecutor
from gemini_code.core.nlp_enhanced import NLPEnhanced
from gemini_code.core.self_healing import SelfHealingSystem


class UltraComprehensiveTester:
    """Testador que verifica TODAS as capacidades do sistema."""
    
    def __init__(self):
        self.test_workspace = Path("test_ultra_comprehensive_workspace")
        self.results = {
            'test_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now().isoformat(),
            'test_categories': {},
            'overall_results': {}
        }
        
        # Limpar workspace anterior
        if self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)
        self.test_workspace.mkdir(parents=True, exist_ok=True)
        
        # Inicializar executor ultra
        self.ultra_executor = UltraExecutor(str(self.test_workspace))
        
        # Comandos de teste ultra abrangentes
        self.test_commands = self._generate_comprehensive_test_commands()
    
    def _generate_comprehensive_test_commands(self) -> Dict[str, List[Dict[str, Any]]]:
        """Gera comandos de teste para TODAS as capacidades."""
        
        return {
            'agent_creation': [
                {
                    'name': 'Agente Simples',
                    'command': 'Crie um agente chamado DataProcessor que processa dados CSV',
                    'expected_files': ['agents/dataprocessor/', 'docs/', 'tests/'],
                    'complexity': 'medium'
                },
                {
                    'name': 'Agente Complexo AutoPrice',
                    'command': '''Quero criar um novo agente pro nosso sistema chamado AutoPrice. 
                    Vou te passar as informações iniciais sobre ele para você criar: LOUSA: Agente_AutoPrice_v2.1.txt
                    Tipo: agente
                    Data: 23/05/2025
                    
                    **Nome do Agente:** AutoPrice
                    **Versão:** v2.1
                    
                    **Função Principal:**
                    Subagente estratégico de precificação adaptativa do GPT Mestre.''',
                    'expected_files': ['agents/autoprice/', 'docs/', 'tests/'],
                    'complexity': 'ultra_high'
                }
            ],
            
            'code_creation': [
                {
                    'name': 'API REST Completa',
                    'command': '''Crie uma API REST completa em Python usando FastAPI para gerenciar produtos.
                    Preciso de endpoints para CRUD, autenticação JWT, validação de dados, tratamento de erros,
                    documentação automática, testes unitários e integração com banco de dados SQLite.''',
                    'expected_files': ['api/', 'models/', 'tests/', 'requirements.txt'],
                    'complexity': 'high'
                },
                {
                    'name': 'Sistema de Machine Learning',
                    'command': '''Implemente um sistema completo de ML para classificação de sentimentos.
                    Inclua pré-processamento, treinamento, avaliação, salvamento de modelo, API de predição,
                    pipeline de dados, métricas de performance e interface web simples.''',
                    'expected_files': ['ml_system/', 'models/', 'data/', 'api/', 'web/'],
                    'complexity': 'ultra_high'
                }
            ],
            
            'code_analysis': [
                {
                    'name': 'Análise Completa do Projeto',
                    'command': '''Analise completamente todo o código deste projeto. Verifique qualidade,
                    segurança, performance, padrões de código, documentação, cobertura de testes,
                    dependências, vulnerabilidades e gere um relatório detalhado com sugestões.''',
                    'expected_results': ['analysis_report', 'metrics', 'suggestions'],
                    'complexity': 'high'
                },
                {
                    'name': 'Detecção de Code Smells',
                    'command': '''Identifique todos os code smells, anti-patterns, duplicações de código,
                    complexidade ciclomática alta, acoplamento forte, baixa coesão e problemas de design.''',
                    'expected_results': ['code_smells', 'refactoring_suggestions'],
                    'complexity': 'medium'
                }
            ],
            
            'debugging': [
                {
                    'name': 'Debug Automático Completo',
                    'command': '''Encontre e corrija automaticamente todos os bugs no projeto.
                    Isso inclui erros de sintaxe, lógica, performance, memory leaks, race conditions,
                    problemas de concorrência e qualquer outro tipo de erro.''',
                    'expected_results': ['errors_found', 'fixes_applied', 'remaining_issues'],
                    'complexity': 'ultra_high'
                }
            ],
            
            'refactoring': [
                {
                    'name': 'Refatoração Massiva',
                    'command': '''Refatore completamente o código para melhorar qualidade, performance,
                    manutenibilidade e seguir as melhores práticas. Aplique SOLID, design patterns,
                    clean code e clean architecture.''',
                    'expected_results': ['refactored_files', 'improvements_applied'],
                    'complexity': 'ultra_high'
                }
            ],
            
            'testing': [
                {
                    'name': 'Suite Completa de Testes',
                    'command': '''Crie uma suite completa de testes para todo o projeto.
                    Inclua testes unitários, integração, end-to-end, performance, stress tests,
                    mocks, fixtures, coverage reports e CI/CD pipeline.''',
                    'expected_files': ['tests/', 'fixtures/', 'reports/'],
                    'complexity': 'high'
                }
            ],
            
            'documentation': [
                {
                    'name': 'Documentação Completa',
                    'command': '''Gere documentação completa para todo o projeto.
                    Inclua README detalhado, API docs, tutoriais, exemplos de uso,
                    arquitetura, deployment guide e changelog.''',
                    'expected_files': ['docs/', 'README.md', 'CHANGELOG.md'],
                    'complexity': 'medium'
                }
            ],
            
            'deployment': [
                {
                    'name': 'Setup de Deploy Completo',
                    'command': '''Configure deploy completo para produção.
                    Inclua Docker, docker-compose, Kubernetes, CI/CD, monitoring,
                    logging, backup automático e scaling horizontal.''',
                    'expected_files': ['Dockerfile', 'docker-compose.yml', '.github/workflows/'],
                    'complexity': 'high'
                }
            ],
            
            'complex_scenarios': [
                {
                    'name': 'Migração de Sistema Legacy',
                    'command': '''Analise um sistema legacy imaginário e crie um plano completo
                    de migração para arquitetura moderna. Inclua análise de dependências,
                    estratégia de migração gradual, testes de compatibilidade e rollback plan.''',
                    'expected_results': ['migration_plan', 'analysis_report'],
                    'complexity': 'ultra_high'
                },
                {
                    'name': 'Otimização de Performance Extrema',
                    'command': '''Otimize o sistema para performance extrema. Analise gargalos,
                    implemente caching avançado, otimize queries, configure load balancing,
                    adicione monitoring em tempo real e configure auto-scaling.''',
                    'expected_results': ['performance_improvements', 'monitoring_setup'],
                    'complexity': 'ultra_high'
                }
            ]
        }
    
    async def run_ultra_comprehensive_tests(self):
        """Executa TODOS os testes ultra abrangentes."""
        
        print("="*100)
        print(" "*30 + "TESTE ULTRA ABRANGENTE DO GEMINI CODE")
        print("="*100)
        print("\nVerificando se o sistema consegue fazer TUDO que o Claude Code faz...")
        print("Este é o teste mais completo e rigoroso possível!\n")
        
        total_score = 0
        total_tests = 0
        
        # Executar cada categoria de teste
        for category, commands in self.test_commands.items():
            print(f"\n{'='*60}")
            print(f"CATEGORIA: {category.upper()}")
            print(f"{'='*60}")
            
            category_results = await self._run_category_tests(category, commands)
            self.results['test_categories'][category] = category_results
            
            category_score = category_results['average_score']
            total_score += category_score
            total_tests += 1
            
            print(f"\n📊 RESULTADO {category.upper()}: {category_score:.1f}%")
        
        # Calcular resultado geral
        overall_score = total_score / total_tests if total_tests > 0 else 0
        
        self.results['overall_results'] = {
            'total_score': overall_score,
            'categories_tested': total_tests,
            'timestamp': datetime.now().isoformat()
        }
        
        # Gerar relatório final
        await self._generate_ultra_comprehensive_report(overall_score)
        
        return overall_score >= 90  # Exigir 90%+ para considerar sucesso
    
    async def _run_category_tests(self, category: str, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executa testes de uma categoria específica."""
        
        results = []
        
        for i, test_command in enumerate(commands, 1):
            print(f"\n[{i}/{len(commands)}] {test_command['name']}")
            print("-" * 50)
            
            start_time = time.time()
            
            try:
                # Executar comando
                result = await self.ultra_executor.execute_natural_command(test_command['command'])
                execution_time = time.time() - start_time
                
                # Avaliar resultado
                score = await self._evaluate_test_result(test_command, result)
                
                print(f"⏱️  Tempo: {execution_time:.2f}s")
                print(f"📊 Score: {score:.1f}%")
                
                if score >= 80:
                    print("✅ PASSOU")
                elif score >= 50:
                    print("⚠️  PARCIAL")
                else:
                    print("❌ FALHOU")
                
                results.append({
                    'name': test_command['name'],
                    'score': score,
                    'execution_time': execution_time,
                    'complexity': test_command['complexity'],
                    'result': result
                })
                
            except Exception as e:
                print(f"💥 ERRO: {e}")
                results.append({
                    'name': test_command['name'],
                    'score': 0,
                    'error': str(e),
                    'complexity': test_command['complexity']
                })
        
        # Calcular score médio da categoria
        scores = [r['score'] for r in results]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'tests_run': len(commands),
            'average_score': average_score,
            'individual_results': results
        }
    
    async def _evaluate_test_result(self, test_command: Dict[str, Any], result: Dict[str, Any]) -> float:
        """Avalia o resultado de um teste específico."""
        
        score = 0.0
        
        # Critério 1: Execução bem-sucedida (30 pontos)
        if result.get('success', False):
            score += 30
        elif result.get('status') == 'partial':
            score += 15
        
        # Critério 2: Arquivos criados conforme esperado (25 pontos)
        if 'expected_files' in test_command:
            expected_files = test_command['expected_files']
            created_files = result.get('files_created', [])
            
            if created_files:
                # Verificar se pelo menos alguns arquivos esperados foram criados
                matches = 0
                for expected in expected_files:
                    if any(expected in created for created in created_files):
                        matches += 1
                
                file_score = (matches / len(expected_files)) * 25
                score += file_score
        
        # Critério 3: Qualidade do resultado (25 pontos)
        if 'validation' in result and result['validation'].get('valid', False):
            score += 25
        elif result.get('files_created') or result.get('files_modified'):
            score += 15  # Pelo menos algo foi feito
        
        # Critério 4: Tempo de execução razoável (10 pontos)
        execution_time = result.get('execution_time', 0)
        if execution_time < 60:  # Menos de 1 minuto
            score += 10
        elif execution_time < 300:  # Menos de 5 minutos
            score += 5
        
        # Critério 5: Tratamento de complexidade (10 pontos)
        complexity = test_command.get('complexity', 'medium')
        if complexity == 'ultra_high' and result.get('success'):
            score += 10  # Bônus por lidar com ultra complexidade
        elif complexity == 'high' and result.get('success'):
            score += 7
        elif complexity == 'medium' and result.get('success'):
            score += 5
        
        return min(score, 100)  # Máximo 100 pontos
    
    async def _generate_ultra_comprehensive_report(self, overall_score: float):
        """Gera relatório ultra completo."""
        
        print(f"\n{'='*100}")
        print(" "*25 + "RELATÓRIO FINAL ULTRA ABRANGENTE")
        print(f"{'='*100}")
        
        # Score geral
        print(f"\n🎯 SCORE GERAL: {overall_score:.1f}%")
        
        if overall_score >= 95:
            classification = "🏆 EXCEPCIONAL - Sistema igual ao Claude Code!"
            status = "✅ APROVADO"
        elif overall_score >= 90:
            classification = "🥇 EXCELENTE - Sistema quase perfeito!"
            status = "✅ APROVADO"
        elif overall_score >= 80:
            classification = "🥈 MUITO BOM - Sistema funcional com pequenos ajustes"
            status = "⚠️  APROVADO COM RESSALVAS"
        elif overall_score >= 70:
            classification = "🥉 BOM - Sistema precisa de melhorias"
            status = "⚠️  PARCIAL"
        else:
            classification = "❌ INSUFICIENTE - Sistema precisa de muito trabalho"
            status = "❌ REPROVADO"
        
        print(f"\n{classification}")
        print(f"STATUS: {status}")
        
        # Detalhes por categoria
        print(f"\n📊 DETALHES POR CATEGORIA:")
        print("-" * 50)
        
        for category, results in self.results['test_categories'].items():
            score = results['average_score']
            tests_count = results['tests_run']
            status_icon = "✅" if score >= 80 else "⚠️ " if score >= 50 else "❌"
            
            print(f"{status_icon} {category.upper():25} {score:6.1f}% ({tests_count} testes)")
        
        # Testes que falharam
        failed_tests = []
        for category, results in self.results['test_categories'].items():
            for test in results['individual_results']:
                if test['score'] < 50:
                    failed_tests.append(f"{category}: {test['name']} ({test['score']:.1f}%)")
        
        if failed_tests:
            print(f"\n❌ TESTES QUE FALHARAM:")
            for failed in failed_tests:
                print(f"   - {failed}")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if overall_score >= 90:
            print("   - Sistema está pronto para uso em produção!")
            print("   - Pode ser usado como alternativa completa ao Claude Code")
        elif overall_score >= 80:
            print("   - Focar nas categorias com menor score")
            print("   - Implementar melhorias nos testes que falharam")
        else:
            print("   - Revisão completa do sistema necessária")
            print("   - Focar em estabilidade e funcionalidades básicas primeiro")
        
        # Salvar relatório JSON
        report_file = Path('ultra_comprehensive_test_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório completo salvo em: {report_file}")
    
    async def test_self_healing_capabilities(self):
        """Testa capacidades de auto-cura do sistema."""
        
        print(f"\n{'='*60}")
        print("TESTE DE AUTO-CURA")
        print(f"{'='*60}")
        
        try:
            # Criar sistema de auto-cura
            self_healing = SelfHealingSystem(str(self.test_workspace))
            
            # Executar diagnóstico
            health = await self_healing.diagnose_system()
            
            print(f"🏥 Saúde do sistema: {health.overall_health}%")
            print(f"🔧 Correções automáticas disponíveis: {health.auto_fixes_available}")
            
            # Tentar auto-correção
            if health.auto_fixes_available > 0:
                fixes = await self_healing.auto_fix(health)
                print(f"✅ {len(fixes)} correções aplicadas")
            
            return health.overall_health >= 70
            
        except Exception as e:
            print(f"❌ Erro no teste de auto-cura: {e}")
            return False
    
    def cleanup(self):
        """Limpa arquivos de teste."""
        if self.test_workspace.exists():
            print(f"\n🧹 Limpando workspace de teste...")
            shutil.rmtree(self.test_workspace)
            print("✅ Cleanup concluído!")


async def main():
    """Executa teste ultra abrangente."""
    
    tester = UltraComprehensiveTester()
    
    try:
        print("🚀 Iniciando teste ultra abrangente...")
        print("Este teste verifica se o Gemini Code consegue fazer TUDO que o Claude Code faz!\n")
        
        # Executar todos os testes
        success = await tester.run_ultra_comprehensive_tests()
        
        # Testar auto-cura
        self_healing_ok = await tester.test_self_healing_capabilities()
        
        print(f"\n{'='*100}")
        if success and self_healing_ok:
            print("🎉 SUCESSO TOTAL! Sistema está igual ao Claude Code!")
            return 0
        elif success:
            print("⚠️  Sistema muito bom, mas auto-cura precisa de ajustes")
            return 0
        else:
            print("❌ Sistema ainda precisa de melhorias significativas")
            return 1
            
    except Exception as e:
        print(f"\n💥 Erro crítico durante teste: {e}")
        traceback.print_exc()
        return 1
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)