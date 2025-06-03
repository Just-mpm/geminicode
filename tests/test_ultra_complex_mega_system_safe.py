#!/usr/bin/env python3
"""
ULTRA COMPLEX MEGA SYSTEM TEST - SAFE VERSION
Sistema de teste extremo para o Gemini Code sem emojis problemáticos
"""

import os
import sys
import json
import time
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import random
import string
import traceback

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Imports do Gemini Code
from gemini_code.interface.enhanced_chat_interface import EnhancedChatInterface
from gemini_code.core.nlp_enhanced import NLPEnhanced
from gemini_code.core.autonomous_executor import AutonomousExecutor
from gemini_code.core.gemini_client import GeminiClient
from gemini_code.analysis.health_monitor import HealthMonitor
from gemini_code.analysis.error_detector import ErrorDetector
from gemini_code.core.config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UltraComplexMegaSystemTester:
    """Testador extremo para o sistema Gemini Code."""
    
    def __init__(self):
        self.temp_workspace = Path("temp_ultra_test_workspace")
        self.results_file = Path("ultra_complex_mega_test_report.json")
        self.test_results = {
            'test_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
        # Limpar workspace anterior se existir
        if self.temp_workspace.exists():
            shutil.rmtree(self.temp_workspace)
        self.temp_workspace.mkdir(parents=True, exist_ok=True)
        
        # Criar estrutura de projeto real
        self._create_realistic_project_structure()
        
    def _create_realistic_project_structure(self):
        """Cria uma estrutura de projeto realista para testes."""
        # Estrutura típica de um projeto Python
        dirs = [
            'src/api',
            'src/core',
            'src/utils',
            'src/models',
            'src/services',
            'tests/unit',
            'tests/integration',
            'docs',
            'config',
            'scripts',
            'data/raw',
            'data/processed',
            'logs',
            'output'
        ]
        
        files = {
            'README.md': '# Ultra Test Project\n\nThis is a test project for Gemini Code.',
            'requirements.txt': 'pytest==7.4.0\nrequests==2.31.0\npandas==2.0.3\n',
            'setup.py': 'from setuptools import setup\n\nsetup(name="ultra_test")',
            '.gitignore': '*.pyc\n__pycache__/\n.env\n*.log',
            'src/__init__.py': '',
            'src/core/__init__.py': '',
            'src/core/main.py': 'def main():\n    print("Hello from ultra test")\n',
            'tests/test_basic.py': 'def test_example():\n    assert True\n',
            'config/settings.json': '{"debug": true, "version": "1.0.0"}'
        }
        
        # Criar diretórios
        for dir_path in dirs:
            (self.temp_workspace / dir_path).mkdir(parents=True, exist_ok=True)
            
        # Criar arquivos
        for file_path, content in files.items():
            file_full_path = self.temp_workspace / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text(content, encoding='utf-8')
    
    def create_ultra_intelligent_client(self) -> GeminiClient:
        """Cria um cliente Gemini ultra inteligente para testes."""
        config = Config()
        config.set('enable_real_execution', True)
        config.set('enable_autonomous_mode', True)
        config.set('nlp_confidence_threshold', 0.7)
        config.set('max_retries', 3)
        return GeminiClient(config=config)
    
    async def test_ultra_complex_natural_language(self):
        """TESTE 1: Processamento de linguagem natural ultra complexa."""
        print("\n" + "="*80)
        print("TESTE 1: LINGUAGEM NATURAL ULTRA COMPLEXA")
        print("="*80)
        
        interface = EnhancedChatInterface()
        nlp = NLPEnhanced()
        
        # Comandos extremamente complexos em linguagem natural
        ultra_complex_commands = [
            {
                'name': 'Comando Mega Detalhado #1',
                'command': '''Por favor, crie uma estrutura completa de projeto para uma aplicação web moderna. 
                Preciso de pastas para frontend em React, backend em Python FastAPI, banco de dados PostgreSQL, 
                testes automatizados com pytest e cypress, CI/CD com GitHub Actions, Docker para containerização, 
                Kubernetes para orquestração, monitoramento com Prometheus e Grafana, logging centralizado com ELK, 
                documentação com Sphinx, e análise de código com SonarQube. Além disso, adicione templates para 
                README, CONTRIBUTING, CODE_OF_CONDUCT, e configurações para ESLint, Prettier, Black, e isort.''',
                'expected_actions': ['create_folders', 'create_files', 'setup_configs']
            },
            
            {
                'name': 'Comando Mega Detalhado #2',
                'command': '''Analise todo o código Python no projeto e faça um relatório detalhado sobre qualidade, 
                performance, segurança, e melhores práticas. Identifique code smells, duplicações, complexidade 
                ciclomática alta, falta de documentação, imports não utilizados, variáveis não usadas, funções 
                muito longas, classes com muitas responsabilidades, falta de testes, hardcoded values, e problemas 
                de segurança como SQL injection, XSS, CSRF. Depois crie um plano de refatoração priorizado.''',
                'expected_actions': ['analyze_code', 'generate_report', 'create_refactoring_plan']
            },
            
            {
                'name': 'Comando Mega Detalhado #3',
                'command': '''Desenvolva um sistema completo de autenticação e autorização com JWT, incluindo 
                registro de usuários com validação de email, login com 2FA opcional, recuperação de senha com 
                tokens temporários, refresh tokens, blacklist de tokens, rate limiting por IP e por usuário, 
                logs de auditoria de todas as ações, integração com OAuth2 (Google, GitHub, Microsoft), 
                gerenciamento de sessões, detecção de login suspeito, e notificações por email e SMS.''',
                'expected_actions': ['create_auth_system', 'implement_security', 'setup_notifications']
            }
        ]
        
        results = []
        
        for i, test in enumerate(ultra_complex_commands, 1):
            print(f"\n[*] COMANDO ULTRA COMPLEXO {i}: {test['name']}")
            print("="*50)
            
            start_time = time.time()
            
            try:
                # Processar com NLP
                nlp_result = await nlp.process_input(test['command'])
                print(f"[+] Tipo detectado: {nlp_result['intent_type']}")
                print(f"[+] Confianca NLP: {nlp_result['confidence']:.1f}%")
                
                # Verificar detecção
                simple_intent = await interface._identify_simple_execution_intent(test['command'])
                is_autonomous = nlp_result['intent_type'] in ['COMPLEX_TASK', 'CODE_GENERATION', 'ANALYSIS']
                
                print(f"[+] Detecao: {'SIM' if simple_intent or is_autonomous else 'NAO'}")
                print(f"[+] Tipo: {'SIMPLES' if simple_intent else 'AUTONOMO' if is_autonomous else 'TEXTO'}")
                print(f"[+] Comando de teste: {test['command'][:100]}...")
                
                # Simular execução
                execution_success = False
                changes_made = []
                
                if simple_intent:
                    # Execução simples
                    print("[*] Executando como comando simples...")
                    result = await interface._handle_simple_execution_command(simple_intent)
                    execution_success = result.get('success', False)
                    changes_made = result.get('changes', [])
                    
                elif is_autonomous:
                    # Execução autônoma
                    print("[*] Executando como comando autonomo...")
                    autonomous = AutonomousExecutor(self.temp_workspace)
                    result = await autonomous.execute_natural_command(test['command'])
                    execution_success = result.get('success', False)
                    changes_made = result.get('files_created', []) + result.get('files_modified', [])
                
                execution_time = time.time() - start_time
                
                # Calcular score
                success_score = 0
                if simple_intent or is_autonomous:
                    success_score += 30  # Detecção correta
                if execution_success:
                    success_score += 40  # Execução bem-sucedida
                if len(changes_made) > 0:
                    success_score += 30  # Mudanças realizadas
                
                print(f"\n[+] RESULTADO:")
                print(f"   - Tempo de execucao: {execution_time:.2f}s")
                print(f"   - Execucao bem-sucedida: {'SIM' if execution_success else 'NAO'}")
                print(f"   - Mudancas realizadas: {len(changes_made)}")
                print(f"   - Score: {success_score}/100")
                
                results.append({
                    'name': test['name'],
                    'command_length': len(test['command']),
                    'nlp_confidence': nlp_result['confidence'],
                    'detected': simple_intent is not None or is_autonomous,
                    'executed': execution_success,
                    'changes_made': changes_made,
                    'execution_time': execution_time,
                    'score': success_score
                })
                
            except Exception as e:
                print(f"[!] ERRO: {e}")
                results.append({
                    'name': test['name'],
                    'error': str(e),
                    'score': 0
                })
        
        # Calcular score geral
        avg_score = sum(r.get('score', 0) for r in results) / len(results)
        
        print(f"\n[+] RESULTADO LINGUAGEM NATURAL ULTRA COMPLEXA:")
        print(f"   - Score medio: {avg_score:.1f}/100")
        print(f"   - Tamanho medio dos comandos: {sum(r.get('command_length', 0) for r in results) / len(results):.0f} chars")
        print(f"   - Confianca media NLP: {sum(r.get('nlp_confidence', 0) for r in results) / len(results):.1f}%")
        print(f"   - Taxa de detecao: {sum(1 for r in results if r.get('detected', False)) / len(results) * 100:.1f}%")
        print(f"   - Taxa de execucao: {sum(1 for r in results if r.get('executed', False)) / len(results) * 100:.1f}%")
        
        self.test_results['natural_language_tests'] = results
        return avg_score >= 85
    
    async def test_massive_document_creation(self):
        """TESTE 2: Criação de documentos massivos e complexos."""
        print("\n" + "="*80)
        print("TESTE 2: CRIACAO DE DOCUMENTOS MASSIVOS")
        print("="*80)
        
        client = self.create_ultra_intelligent_client()
        autonomous_executor = AutonomousExecutor(self.temp_workspace)
        
        massive_document_requests = [
            {
                'name': 'Manual Tecnico Completo',
                'command': '''Crie um manual tecnico extenso e detalhado sobre desenvolvimento de software moderno. 
                O documento deve ter mais de 10.000 palavras, incluir multiplas secoes tecnicas, exemplos de codigo, 
                diagramas, melhores praticas, troubleshooting, e referencias. Organize em uma pasta chamada 
                'manuais_tecnicos' e chame o arquivo de 'manual_desenvolvimento_completo.md'.''',
                'expected_folder': 'manuais_tecnicos',
                'expected_file': 'manual_desenvolvimento_completo.md',
                'min_size': 50000  # 50KB minimo
            },
            
            {
                'name': 'Documentacao de API Enterprise',
                'command': '''Preciso de uma documentacao de API completa e profissional para um sistema enterprise. 
                Crie um documento massivo que inclua todos os endpoints, autenticacao, exemplos de request/response, 
                codigos de erro, rate limiting, SDKs, guias de implementacao, e casos de uso reais. Coloque em 
                'documentacao/api/' e nomeie como 'api_reference_complete.md'. Deve ser extremamente detalhado.''',
                'expected_folder': 'documentacao/api',
                'expected_file': 'api_reference_complete.md',
                'min_size': 75000  # 75KB minimo
            },
            
            {
                'name': 'Especificacao Arquitetural Massiva',
                'command': '''Gere uma especificacao arquitetural completa para um sistema distribuido moderno. 
                Inclua microservicos, containers, orquestracao, bancos de dados, cache, monitoramento, logging, 
                seguranca, escalabilidade, disaster recovery, e muito mais. Crie em 'arquitetura/especificacoes/' 
                com o nome 'arquitetura_sistema_completa.md'. Precisa ser um documento massivo e tecnico.''',
                'expected_folder': 'arquitetura/especificacoes',
                'expected_file': 'arquitetura_sistema_completa.md',
                'min_size': 100000  # 100KB minimo
            }
        ]
        
        results = []
        
        for i, doc_request in enumerate(massive_document_requests, 1):
            print(f"\n[*] DOCUMENTO MASSIVO {i}: {doc_request['name']}")
            print("="*50)
            
            start_time = time.time()
            
            try:
                # Executar criação do documento
                print("[*] Executando criacao de documento massivo...")
                result = await autonomous_executor.execute_natural_command(doc_request['command'])
                
                execution_time = time.time() - start_time
                
                print(f"[+] Tempo de criacao: {execution_time:.2f}s")
                print(f"[+] Status: {result['status']}")
                print(f"[+] Taxa de sucesso: {result['success_rate']:.1f}%")
                
                # Verificar se documento foi criado
                expected_path = Path(self.temp_workspace) / doc_request['expected_folder'] / doc_request['expected_file']
                document_created = expected_path.exists()
                
                if document_created:
                    file_size = expected_path.stat().st_size
                    print(f"[+] Documento criado: SIM")
                    print(f"[+] Tamanho: {file_size:,} bytes")
                    print(f"[+] Tamanho minimo atingido: {'SIM' if file_size >= doc_request['min_size'] else 'NAO'}")
                    
                    # Ler primeiras linhas
                    with open(expected_path, 'r', encoding='utf-8') as f:
                        preview = f.read(500)
                    print(f"[+] Preview do documento:\n{preview}...")
                    
                    success_score = 100 if file_size >= doc_request['min_size'] else 50
                else:
                    print(f"[!] Documento criado: NAO")
                    success_score = 0
                
                results.append({
                    'name': doc_request['name'],
                    'created': document_created,
                    'file_size': file_size if document_created else 0,
                    'min_size_met': file_size >= doc_request['min_size'] if document_created else False,
                    'execution_time': execution_time,
                    'score': success_score
                })
                
            except Exception as e:
                print(f"[!] ERRO: {e}")
                results.append({
                    'name': doc_request['name'],
                    'error': str(e),
                    'score': 0
                })
        
        # Calcular score geral
        avg_score = sum(r.get('score', 0) for r in results) / len(results)
        
        print(f"\n[+] RESULTADO CRIACAO DE DOCUMENTOS MASSIVOS:")
        print(f"   - Score medio: {avg_score:.1f}/100")
        print(f"   - Taxa de criacao: {sum(1 for r in results if r.get('created', False)) / len(results) * 100:.1f}%")
        print(f"   - Tamanho total criado: {sum(r.get('file_size', 0) for r in results):,} bytes")
        
        self.test_results['massive_document_tests'] = results
        return avg_score >= 80
    
    async def test_integration_with_existing_structure(self):
        """TESTE 3: Integração completa com estrutura existente."""
        print("\n" + "="*80)
        print("TESTE 3: INTEGRACAO COM ESTRUTURA EXISTENTE")
        print("="*80)
        
        autonomous_executor = AutonomousExecutor(self.temp_workspace)
        health_monitor = HealthMonitor(self.temp_workspace)
        error_detector = ErrorDetector()
        
        integration_tests = [
            {
                'name': 'Adicionar Nova Feature Completa',
                'command': '''Adicione uma nova feature completa de sistema de notificacoes ao projeto. 
                Crie os modulos necessarios em src/services/notifications/, implemente classes para email, 
                SMS e push notifications, adicione testes em tests/unit/test_notifications.py, atualize 
                o requirements.txt com as dependencias necessarias, e crie documentacao em docs/notifications.md.''',
                'validations': [
                    ('src/services/notifications/__init__.py', 'file_exists'),
                    ('tests/unit/test_notifications.py', 'file_exists'),
                    ('docs/notifications.md', 'file_exists'),
                    ('requirements.txt', 'contains', 'email')
                ]
            },
            
            {
                'name': 'Refatorar Codigo Existente',
                'command': '''Analise o arquivo src/core/main.py e refatore-o seguindo melhores praticas. 
                Adicione type hints, docstrings, separe responsabilidades, crie funcoes auxiliares, 
                melhore o tratamento de erros, e adicione logging apropriado. Mantenha a funcionalidade 
                original mas melhore a qualidade do codigo.''',
                'validations': [
                    ('src/core/main.py', 'file_modified'),
                    ('src/core/main.py', 'contains', 'def '),
                    ('src/core/main.py', 'contains', '"""')
                ]
            },
            
            {
                'name': 'Configurar Pipeline CI/CD',
                'command': '''Configure um pipeline completo de CI/CD para o projeto. Crie .github/workflows/ci.yml 
                com steps para linting, testes, coverage, build, e deploy. Adicione também um Dockerfile para 
                containerizacao, docker-compose.yml para desenvolvimento local, e scripts de deploy em scripts/deploy/.''',
                'validations': [
                    ('.github/workflows/ci.yml', 'file_exists'),
                    ('Dockerfile', 'file_exists'),
                    ('docker-compose.yml', 'file_exists'),
                    ('scripts/deploy/', 'dir_exists')
                ]
            }
        ]
        
        results = []
        
        for i, test in enumerate(integration_tests, 1):
            print(f"\n[*] TESTE DE INTEGRACAO {i}: {test['name']}")
            print("="*50)
            
            start_time = time.time()
            
            try:
                # Estado inicial
                print("[*] Analisando estado inicial do projeto...")
                initial_health = await health_monitor.get_project_health()
                print(f"[+] Health inicial: {initial_health['overall_score']:.1f}/100")
                
                # Executar comando
                print("[*] Executando comando de integracao...")
                result = await autonomous_executor.execute_natural_command(test['command'])
                
                execution_time = time.time() - start_time
                
                print(f"[+] Tempo de execucao: {execution_time:.2f}s")
                print(f"[+] Status: {result['status']}")
                
                # Validar mudanças
                validation_results = []
                for validation in test['validations']:
                    path = Path(self.temp_workspace) / validation[0]
                    check_type = validation[1]
                    
                    if check_type == 'file_exists':
                        valid = path.exists() and path.is_file()
                    elif check_type == 'dir_exists':
                        valid = path.exists() and path.is_dir()
                    elif check_type == 'file_modified':
                        valid = path.exists() and path.stat().st_mtime > start_time
                    elif check_type == 'contains' and len(validation) > 2:
                        valid = path.exists() and validation[2] in path.read_text(encoding='utf-8')
                    else:
                        valid = False
                    
                    validation_results.append(valid)
                    print(f"   [{'OK' if valid else 'FAIL'}] {validation[0]} - {check_type}")
                
                # Estado final
                print("\n[*] Analisando estado final do projeto...")
                final_health = await health_monitor.get_project_health()
                print(f"[+] Health final: {final_health['overall_score']:.1f}/100")
                print(f"[+] Melhoria: {final_health['overall_score'] - initial_health['overall_score']:.1f} pontos")
                
                # Detecção de erros
                errors = await error_detector.scan_directory(self.temp_workspace)
                print(f"[+] Erros detectados: {len(errors)}")
                
                # Calcular score
                validation_score = sum(validation_results) / len(validation_results) * 100
                health_improvement = max(0, final_health['overall_score'] - initial_health['overall_score'])
                error_penalty = min(20, len(errors) * 5)
                
                success_score = (validation_score * 0.6 + health_improvement * 0.3 + (20 - error_penalty) * 0.1)
                
                print(f"\n[+] SCORE DETALHADO:")
                print(f"   - Validacoes: {validation_score:.1f}%")
                print(f"   - Melhoria health: {health_improvement:.1f}")
                print(f"   - Penalidade erros: -{error_penalty}")
                print(f"   - Score final: {success_score:.1f}/100")
                
                results.append({
                    'name': test['name'],
                    'validations_passed': sum(validation_results),
                    'total_validations': len(validation_results),
                    'health_improvement': health_improvement,
                    'errors_found': len(errors),
                    'execution_time': execution_time,
                    'score': success_score
                })
                
            except Exception as e:
                print(f"[!] ERRO: {e}")
                traceback.print_exc()
                results.append({
                    'name': test['name'],
                    'error': str(e),
                    'score': 0
                })
        
        # Calcular score geral
        avg_score = sum(r.get('score', 0) for r in results) / len(results)
        
        print(f"\n[+] RESULTADO INTEGRACAO COM ESTRUTURA:")
        print(f"   - Score medio: {avg_score:.1f}/100")
        print(f"   - Taxa de sucesso validacoes: {sum(r.get('validations_passed', 0) for r in results) / sum(r.get('total_validations', 1) for r in results) * 100:.1f}%")
        print(f"   - Melhoria media health: {sum(r.get('health_improvement', 0) for r in results) / len(results):.1f}")
        
        self.test_results['integration_tests'] = results
        return avg_score >= 75
    
    async def test_error_detection_and_recovery(self):
        """TESTE 4: Detecção e recuperação de erros complexos."""
        print("\n" + "="*80)
        print("TESTE 4: DETECCAO E RECUPERACAO DE ERROS")
        print("="*80)
        
        autonomous_executor = AutonomousExecutor(self.temp_workspace)
        error_detector = ErrorDetector()
        
        # Introduzir erros propositais
        error_files = {
            'src/broken_syntax.py': '''
def broken_function(
    print("Missing closing parenthesis"
    
class BrokenClass
    def __init__(self):
        self.value = undefined_variable
            ''',
            
            'src/import_errors.py': '''
from non_existent_module import something
import another_missing_module
from ..invalid_relative import bad_import

def function_with_import_error():
    return something()
            ''',
            
            'src/runtime_errors.py': '''
def divide_by_zero():
    return 10 / 0

def index_error():
    lst = [1, 2, 3]
    return lst[10]

def type_error():
    return "string" + 123
            '''
        }
        
        # Criar arquivos com erros
        for file_path, content in error_files.items():
            full_path = self.temp_workspace / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        results = []
        
        # Teste 1: Detecção de erros
        print("\n[*] FASE 1: Detectando erros introduzidos...")
        detected_errors = await error_detector.scan_directory(self.temp_workspace)
        
        print(f"[+] Total de erros detectados: {len(detected_errors)}")
        for error in detected_errors[:5]:  # Mostrar apenas primeiros 5
            print(f"   - {error['file']}: {error['type']} - {error['message'][:50]}...")
        
        # Teste 2: Correção automática
        print("\n[*] FASE 2: Tentando correcao automatica...")
        
        fix_command = '''Analise todos os arquivos Python no projeto e corrija todos os erros encontrados. 
        Isso inclui erros de sintaxe, imports faltando, variaveis nao definidas, e problemas de runtime. 
        Mantenha a funcionalidade pretendida mas corrija todos os problemas.'''
        
        start_time = time.time()
        fix_result = await autonomous_executor.execute_natural_command(fix_command)
        fix_time = time.time() - start_time
        
        print(f"[+] Tempo de correcao: {fix_time:.2f}s")
        print(f"[+] Status: {fix_result['status']}")
        
        # Teste 3: Re-verificação
        print("\n[*] FASE 3: Re-verificando erros apos correcao...")
        remaining_errors = await error_detector.scan_directory(self.temp_workspace)
        
        errors_fixed = len(detected_errors) - len(remaining_errors)
        fix_rate = (errors_fixed / len(detected_errors) * 100) if detected_errors else 0
        
        print(f"[+] Erros corrigidos: {errors_fixed}/{len(detected_errors)} ({fix_rate:.1f}%)")
        print(f"[+] Erros restantes: {len(remaining_errors)}")
        
        # Calcular score
        detection_score = min(100, len(detected_errors) * 20)  # Máx 100 por detectar 5+ erros
        fix_score = fix_rate
        final_score = (detection_score * 0.3 + fix_score * 0.7)
        
        results.append({
            'errors_introduced': len(error_files),
            'errors_detected': len(detected_errors),
            'errors_fixed': errors_fixed,
            'errors_remaining': len(remaining_errors),
            'fix_rate': fix_rate,
            'fix_time': fix_time,
            'score': final_score
        })
        
        print(f"\n[+] RESULTADO DETECCAO E RECUPERACAO:")
        print(f"   - Taxa de deteccao: {len(detected_errors)}/{len(error_files) * 3} erros")
        print(f"   - Taxa de correcao: {fix_rate:.1f}%")
        print(f"   - Score final: {final_score:.1f}/100")
        
        self.test_results['error_recovery_tests'] = results
        return final_score >= 70
    
    async def generate_final_report(self):
        """Gera relatório final ultra detalhado."""
        print("\n" + "="*80)
        print("RELATORIO FINAL - ULTRA COMPLEX MEGA SYSTEM TEST")
        print("="*80)
        
        # Compilar resultados
        all_scores = []
        
        if 'natural_language_tests' in self.test_results:
            nl_scores = [r.get('score', 0) for r in self.test_results['natural_language_tests']]
            all_scores.extend(nl_scores)
            nl_avg = sum(nl_scores) / len(nl_scores) if nl_scores else 0
            print(f"\n[*] LINGUAGEM NATURAL ULTRA COMPLEXA:")
            print(f"   - Score medio: {nl_avg:.1f}/100")
            print(f"   - Testes executados: {len(nl_scores)}")
        
        if 'massive_document_tests' in self.test_results:
            doc_scores = [r.get('score', 0) for r in self.test_results['massive_document_tests']]
            all_scores.extend(doc_scores)
            doc_avg = sum(doc_scores) / len(doc_scores) if doc_scores else 0
            print(f"\n[*] DOCUMENTOS MASSIVOS:")
            print(f"   - Score medio: {doc_avg:.1f}/100")
            print(f"   - Documentos criados: {sum(1 for r in self.test_results['massive_document_tests'] if r.get('created', False))}")
        
        if 'integration_tests' in self.test_results:
            int_scores = [r.get('score', 0) for r in self.test_results['integration_tests']]
            all_scores.extend(int_scores)
            int_avg = sum(int_scores) / len(int_scores) if int_scores else 0
            print(f"\n[*] INTEGRACAO COM ESTRUTURA:")
            print(f"   - Score medio: {int_avg:.1f}/100")
            print(f"   - Integracoes bem-sucedidas: {sum(1 for r in self.test_results['integration_tests'] if r.get('score', 0) > 50)}")
        
        if 'error_recovery_tests' in self.test_results:
            err_scores = [r['score'] for r in self.test_results['error_recovery_tests']]
            all_scores.extend(err_scores)
            err_avg = sum(err_scores) / len(err_scores) if err_scores else 0
            print(f"\n[*] DETECCAO E RECUPERACAO DE ERROS:")
            print(f"   - Score medio: {err_avg:.1f}/100")
            if self.test_results['error_recovery_tests']:
                r = self.test_results['error_recovery_tests'][0]
                print(f"   - Taxa de correcao: {r.get('fix_rate', 0):.1f}%")
        
        # Score geral
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        print(f"\n{'='*80}")
        print(f"SCORE GERAL DO SISTEMA: {overall_score:.1f}/100")
        print(f"{'='*80}")
        
        # Classificação
        if overall_score >= 90:
            classification = "EXCEPCIONAL - Sistema funcionando perfeitamente!"
        elif overall_score >= 80:
            classification = "EXCELENTE - Sistema altamente funcional!"
        elif overall_score >= 70:
            classification = "BOM - Sistema funcional com pequenas melhorias necessarias"
        elif overall_score >= 60:
            classification = "REGULAR - Sistema precisa de melhorias significativas"
        else:
            classification = "CRITICO - Sistema requer atencao urgente"
        
        print(f"\nCLASSIFICACAO: {classification}")
        
        # Salvar resultados
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['overall_score'] = overall_score
        self.test_results['classification'] = classification
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[+] Relatorio completo salvo em: {self.results_file}")
        
        return overall_score >= 70
    
    def cleanup(self):
        """Limpa arquivos temporários do teste."""
        if self.temp_workspace.exists():
            print(f"\n[*] Limpando workspace temporario...")
            shutil.rmtree(self.temp_workspace)
            print("[+] Cleanup concluido!")

async def main():
    """Executa o teste ultra complexo mega system."""
    print("\n" + "*"*80)
    print("*" * 33 + " INICIANDO " + "*" * 36)
    print("*" * 20 + " ULTRA COMPLEX MEGA SYSTEM TEST " + "*" * 28)
    print("*" * 80 + "\n")
    
    print("[!] Este e o teste mais intensivo e complexo ja criado!")
    print("[*] Objetivo: Testar o sistema ate os limites absolutos")
    print("[*] Metodo: Linguagem natural extrema + documentos massivos + integracao\n")
    
    tester = UltraComplexMegaSystemTester()
    
    try:
        # Executar todos os testes
        print("[*] INICIANDO BATERIA DE TESTES ULTRA COMPLEXOS...\n")
        
        # Teste 1: Linguagem Natural Ultra Complexa
        nl_success = await tester.test_ultra_complex_natural_language()
        print(f"\n>>> Teste Linguagem Natural: {'PASSOU' if nl_success else 'FALHOU'}")
        
        # Teste 2: Documentos Massivos
        doc_success = await tester.test_massive_document_creation()
        print(f"\n>>> Teste Documentos Massivos: {'PASSOU' if doc_success else 'FALHOU'}")
        
        # Teste 3: Integração com Estrutura
        int_success = await tester.test_integration_with_existing_structure()
        print(f"\n>>> Teste Integracao: {'PASSOU' if int_success else 'FALHOU'}")
        
        # Teste 4: Detecção e Recuperação de Erros
        err_success = await tester.test_error_detection_and_recovery()
        print(f"\n>>> Teste Deteccao de Erros: {'PASSOU' if err_success else 'FALHOU'}")
        
        # Gerar relatório final
        overall_success = await tester.generate_final_report()
        
        if overall_success:
            print("\n" + "+"*80)
            print("+" * 25 + " TESTE CONCLUIDO COM SUCESSO! " + "+" * 25)
            print("+" * 80)
        else:
            print("\n" + "!"*80)
            print("!" * 25 + " TESTE FALHOU - MELHORIAS NECESSARIAS " + "!" * 16)
            print("!" * 80)
        
    except Exception as e:
        print(f"\n[!] ERRO CRITICO DURANTE TESTE: {e}")
        traceback.print_exc()
    
    finally:
        # Limpar workspace
        tester.cleanup()
        
    print("\n[*] Teste ultra complexo finalizado!")

if __name__ == "__main__":
    asyncio.run(main())