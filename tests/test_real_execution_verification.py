#!/usr/bin/env python3
"""
🔍 TESTE DE VERIFICAÇÃO DE EXECUÇÃO REAL - SEM SIMULAÇÃO
Garante que o Gemini Code REALMENTE executa comandos físicos no sistema
Testa linguagem natural extensa e complexa
"""

import asyncio
import tempfile
import shutil
import os
import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.interface.enhanced_chat_interface import EnhancedChatInterface
from gemini_code.core.autonomous_executor import AutonomousExecutor


class RealExecutionVerifier:
    """🔍 Verificador de execução real - SEM simulações."""
    
    def __init__(self):
        self.temp_workspace = None
        self.verification_results = []
        
    def setup_test_workspace(self):
        """Cria workspace para testes reais."""
        self.temp_workspace = tempfile.mkdtemp()
        print(f"📁 Workspace criado: {self.temp_workspace}")
        return self.temp_workspace
    
    def create_real_gemini_client(self):
        """Cria mock que simula respostas inteligentes mas NÃO executa comandos."""
        client = Mock()
        
        async def intelligent_response(prompt, **kwargs):
            """Respostas inteligentes baseadas no contexto."""
            prompt_lower = prompt.lower()
            
            if "create" in prompt_lower or "crie" in prompt_lower:
                return """
Entendi seu pedido! Vou criar o que você solicitou.

## Ação Realizada:
✅ Comando processado e executado
✅ Estruturas criadas conforme solicitado
✅ Validação concluída

Se você verificar o sistema de arquivos, encontrará os itens criados.
"""
            
            elif "complex" in prompt_lower or "completo" in prompt_lower:
                return """
Comando complexo processado com sucesso!

## Operações Realizadas:
✅ Análise completa do contexto
✅ Execução de múltiplas etapas
✅ Validação de cada componente
✅ Integração entre sistemas

Sistema está funcionando conforme esperado.
"""
            
            else:
                return "Comando processado. Sistema operacional atualizado conforme solicitado."
        
        client.generate_response = AsyncMock(side_effect=intelligent_response)
        return client

    async def test_physical_folder_creation(self):
        """🎯 TESTE 1: Criação física de pastas - VERIFICAÇÃO REAL."""
        print("\n" + "="*70)
        print("🎯 TESTE 1: CRIAÇÃO FÍSICA DE PASTAS")
        print("="*70)
        print("🔍 Verificando se pastas são REALMENTE criadas no sistema...")
        
        # Setup
        client = self.create_real_gemini_client()
        chat = EnhancedChatInterface(client, Mock(), Mock(), self.temp_workspace)
        
        test_cases = [
            {
                'command': 'Crie uma pasta chamada projeto_real',
                'expected_folder': 'projeto_real'
            },
            {
                'command': 'Quero que você faça uma pasta para guardar documentos importantes',
                'expected_folder': 'documentos'  # ou similar
            },
            {
                'command': 'Por favor, crie um diretório novo chamado backup_sistema',
                'expected_folder': 'backup_sistema'
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n📝 {i}. Comando: '{test['command']}'")
            
            # Verificar estado ANTES
            before_folders = set(p.name for p in Path(self.temp_workspace).iterdir() if p.is_dir())
            print(f"   📂 Pastas antes: {before_folders}")
            
            # Executar comando
            simple_intent = await chat._identify_simple_execution_intent(test['command'])
            
            if simple_intent and simple_intent['type'] == 'create_folder':
                await chat._handle_simple_execution_command(test['command'], simple_intent)
                
                # Verificar estado DEPOIS
                after_folders = set(p.name for p in Path(self.temp_workspace).iterdir() if p.is_dir())
                print(f"   📂 Pastas depois: {after_folders}")
                
                # Calcular diferença
                new_folders = after_folders - before_folders
                print(f"   🆕 Novas pastas: {new_folders}")
                
                # Verificar se pasta foi realmente criada
                folder_created = len(new_folders) > 0
                
                if folder_created:
                    created_folder = list(new_folders)[0]
                    folder_path = Path(self.temp_workspace) / created_folder
                    
                    # VERIFICAÇÃO FÍSICA REAL
                    exists = folder_path.exists()
                    is_dir = folder_path.is_dir()
                    can_write = os.access(folder_path, os.W_OK)
                    
                    print(f"   ✅ VERIFICAÇÃO FÍSICA:")
                    print(f"      - Existe no sistema: {exists}")
                    print(f"      - É diretório: {is_dir}")
                    print(f"      - Permissão de escrita: {can_write}")
                    
                    # Testar escrita REAL
                    try:
                        test_file = folder_path / "teste_real.txt"
                        test_file.write_text("Arquivo criado pelo teste real")
                        file_created = test_file.exists()
                        print(f"      - Pode criar arquivos: {file_created}")
                        
                        # Limpar
                        test_file.unlink()
                        
                    except Exception as e:
                        print(f"      - Erro ao criar arquivo: {e}")
                        file_created = False
                    
                    success = exists and is_dir and can_write and file_created
                    
                else:
                    success = False
                    print(f"   ❌ NENHUMA PASTA FOI CRIADA!")
                
            else:
                success = False
                print(f"   ❌ Comando não detectado como criação de pasta")
            
            results.append({
                'command': test['command'],
                'success': success,
                'folders_created': list(new_folders) if 'new_folders' in locals() else []
            })
        
        success_rate = sum(1 for r in results if r['success']) / len(results) * 100
        print(f"\n📊 RESULTADO TESTE 1:")
        print(f"   ✅ Taxa de criação REAL: {success_rate:.1f}%")
        
        return results, success_rate >= 80

    async def test_file_system_operations(self):
        """🎯 TESTE 2: Operações no sistema de arquivos - VERIFICAÇÃO FÍSICA."""
        print("\n" + "="*70)
        print("🎯 TESTE 2: OPERAÇÕES FÍSICAS NO SISTEMA")
        print("="*70)
        
        # Setup
        client = self.create_real_gemini_client()
        chat = EnhancedChatInterface(client, Mock(), Mock(), self.temp_workspace)
        
        operations = [
            "Crie uma pasta chamada dados_importantes",
            "Faça uma pasta para logs do sistema",
            "Crie um diretório backup_config"
        ]
        
        created_items = []
        
        print("🔄 Executando operações sequenciais...")
        
        for i, operation in enumerate(operations, 1):
            print(f"\n{i}. {operation}")
            
            simple_intent = await chat._identify_simple_execution_intent(operation)
            
            if simple_intent:
                await chat._handle_simple_execution_command(operation, simple_intent)
                
                # Verificar criação
                if simple_intent['type'] == 'create_folder':
                    folder_name = simple_intent.get('folder_name', 'unknown')
                    folder_path = Path(self.temp_workspace) / folder_name
                    
                    if folder_path.exists():
                        print(f"   ✅ Pasta '{folder_name}' criada fisicamente")
                        created_items.append(folder_name)
                    else:
                        print(f"   ❌ Pasta '{folder_name}' NÃO foi criada")
            else:
                print(f"   ❌ Operação não detectada")
        
        print(f"\n📋 VERIFICAÇÃO FINAL DO SISTEMA:")
        print(f"   📁 Workspace: {self.temp_workspace}")
        
        # Listar TUDO no workspace
        all_items = list(Path(self.temp_workspace).iterdir())
        print(f"   📂 Itens encontrados no sistema:")
        
        for item in all_items:
            size = item.stat().st_size if item.exists() else 0
            modified = datetime.fromtimestamp(item.stat().st_mtime).strftime('%H:%M:%S')
            print(f"      - {item.name} ({'dir' if item.is_dir() else 'file'}, {size}B, {modified})")
        
        # Verificação com comando do sistema
        print(f"\n🖥️  VERIFICAÇÃO COM COMANDO DO SISTEMA:")
        try:
            if os.name == 'nt':
                result = subprocess.run(['dir', self.temp_workspace], 
                                      capture_output=True, text=True, shell=True)
            else:
                result = subprocess.run(['ls', '-la', self.temp_workspace], 
                                      capture_output=True, text=True)
            
            print(f"   Comando executado: {'dir' if os.name == 'nt' else 'ls -la'}")
            print(f"   Saída do sistema:")
            for line in result.stdout.split('\n')[:10]:  # Primeiras 10 linhas
                if line.strip():
                    print(f"      {line}")
                    
        except Exception as e:
            print(f"   Erro no comando do sistema: {e}")
        
        success = len(created_items) >= 2  # Pelo menos 2 pastas criadas
        
        return created_items, success

    async def test_natural_language_comprehension(self):
        """🎯 TESTE 3: Compreensão de linguagem natural EXTENSA."""
        print("\n" + "="*70)
        print("🎯 TESTE 3: LINGUAGEM NATURAL EXTENSA")
        print("="*70)
        
        # Setup
        client = self.create_real_gemini_client()
        chat = EnhancedChatInterface(client, Mock(), Mock(), self.temp_workspace)
        
        complex_commands = [
            {
                'command': '''
                Olá Gemini, preciso que você me ajude com uma tarefa específica. 
                Gostaria que criasse uma pasta nova no meu sistema para organizar 
                alguns arquivos importantes que estou trabalhando. A pasta deve 
                se chamar "projeto_pessoal" e precisa estar no diretório atual. 
                É importante que seja realmente criada no sistema de arquivos, 
                não apenas uma simulação. Obrigado!
                ''',
                'expected_action': 'create_folder',
                'expected_name': 'projeto_pessoal'
            },
            
            {
                'command': '''
                Ei, você poderia fazer um favor para mim? Estou organizando meus 
                documentos e preciso de uma nova pasta para guardar as coisas 
                relacionadas ao trabalho. Que tal criarmos um diretório chamado 
                "arquivos_trabalho"? Seria muito útil ter isso organizado 
                adequadamente no meu computador.
                ''',
                'expected_action': 'create_folder',
                'expected_name': 'arquivos_trabalho'
            },
            
            {
                'command': '''
                Bom dia! Estou começando um novo projeto e preciso estruturar 
                melhor meus arquivos. Você consegue criar uma pasta chamada 
                "novo_projeto_2025" para mim? É para organizar documentos, 
                códigos e outros recursos que vou usar. Precisa ser uma pasta 
                real no sistema operacional, não virtual. Desde já agradeço 
                pela ajuda!
                ''',
                'expected_action': 'create_folder',
                'expected_name': 'novo_projeto_2025'
            }
        ]
        
        results = []
        
        for i, test in enumerate(complex_commands, 1):
            print(f"\n📝 TESTE {i}: Linguagem Natural Extensa")
            print(f"   📄 Comando ({len(test['command'])} caracteres):")
            print(f"   '{test['command'][:100]}...'")
            
            # Verificar compreensão do NLP
            nlp_result = await chat.nlp.identify_intent(test['command'])
            print(f"   🧠 NLP detectou: {nlp_result['intent']} ({nlp_result['confidence']}%)")
            
            # Verificar detecção de comando simples
            simple_intent = await chat._identify_simple_execution_intent(test['command'])
            print(f"   🔍 Comando simples: {simple_intent is not None}")
            
            if simple_intent:
                print(f"   📂 Tipo: {simple_intent['type']}")
                print(f"   📛 Nome extraído: {simple_intent.get('folder_name', 'N/A')}")
                
                # EXECUTAR REALMENTE
                before_count = len(list(Path(self.temp_workspace).iterdir()))
                
                await chat._handle_simple_execution_command(test['command'], simple_intent)
                
                after_count = len(list(Path(self.temp_workspace).iterdir()))
                
                # VERIFICAR RESULTADO FÍSICO
                new_items = after_count - before_count
                print(f"   📊 Itens criados: {new_items}")
                
                if new_items > 0:
                    # Encontrar nova pasta
                    all_folders = [p.name for p in Path(self.temp_workspace).iterdir() if p.is_dir()]
                    latest_folder = all_folders[-1] if all_folders else None
                    
                    if latest_folder:
                        folder_path = Path(self.temp_workspace) / latest_folder
                        
                        # VERIFICAÇÃO FÍSICA DETALHADA
                        stat_info = folder_path.stat()
                        print(f"   ✅ PASTA CRIADA: '{latest_folder}'")
                        print(f"      - Tamanho: {stat_info.st_size} bytes")
                        print(f"      - Criada em: {datetime.fromtimestamp(stat_info.st_ctime)}")
                        print(f"      - Permissões: {oct(stat_info.st_mode)}")
                        
                        success = True
                    else:
                        success = False
                else:
                    success = False
                    print(f"   ❌ NENHUM ITEM CRIADO")
            else:
                success = False
                print(f"   ❌ COMANDO NÃO COMPREENDIDO")
            
            results.append({
                'command_length': len(test['command']),
                'nlp_confidence': nlp_result['confidence'],
                'understood': simple_intent is not None,
                'executed': success
            })
        
        # Estatísticas
        avg_length = sum(r['command_length'] for r in results) / len(results)
        avg_confidence = sum(r['nlp_confidence'] for r in results) / len(results)
        understand_rate = sum(1 for r in results if r['understood']) / len(results) * 100
        execution_rate = sum(1 for r in results if r['executed']) / len(results) * 100
        
        print(f"\n📊 ESTATÍSTICAS LINGUAGEM NATURAL:")
        print(f"   📏 Tamanho médio dos comandos: {avg_length:.0f} caracteres")
        print(f"   🧠 Confiança média do NLP: {avg_confidence:.1f}%")
        print(f"   🎯 Taxa de compreensão: {understand_rate:.1f}%")
        print(f"   ⚡ Taxa de execução real: {execution_rate:.1f}%")
        
        return results, execution_rate >= 80

    async def test_autonomous_real_execution(self):
        """🎯 TESTE 4: Execução autônoma REAL (não simulada)."""
        print("\n" + "="*70)
        print("🎯 TESTE 4: EXECUÇÃO AUTÔNOMA REAL")
        print("="*70)
        
        # Criar executor autônomo REAL (não mock)
        executor = AutonomousExecutor(self.temp_workspace)
        
        # Verificar configuração
        print(f"🔧 Enable real execution: {executor.enable_real_execution}")
        print(f"📁 Working directory: {executor.project_path}")
        
        # Comando que deve criar estrutura real
        command = "Crie uma pasta chamada estrutura_autonoma e valide que foi criada"
        
        print(f"💬 Comando: {command}")
        print("🤖 Executando de forma autônoma...")
        
        # Verificar estado ANTES
        before_items = set(p.name for p in Path(self.temp_workspace).iterdir())
        print(f"📂 Antes: {before_items}")
        
        # EXECUTAR AUTONOMAMENTE
        start_time = time.time()
        result = await executor.execute_natural_command(command)
        execution_time = time.time() - start_time
        
        # Verificar estado DEPOIS
        after_items = set(p.name for p in Path(self.temp_workspace).iterdir())
        print(f"📂 Depois: {after_items}")
        
        new_items = after_items - before_items
        print(f"🆕 Itens criados: {new_items}")
        
        print(f"\n📊 RESULTADO EXECUÇÃO AUTÔNOMA:")
        print(f"   ⏱️  Tempo: {execution_time:.2f}s")
        print(f"   📊 Status: {result['status']}")
        print(f"   ✅ Taxa de sucesso: {result['success_rate']:.1f}%")
        print(f"   📋 Tarefas: {result['completed_tasks']}/{result['total_tasks']}")
        
        # VERIFICAÇÃO FÍSICA
        physical_creation = len(new_items) > 0
        print(f"   🔍 Criação física: {physical_creation}")
        
        if physical_creation:
            for item in new_items:
                item_path = Path(self.temp_workspace) / item
                print(f"      ✅ {item} - {item_path.stat().st_size} bytes")
        
        success = physical_creation and result['status'] in ['completed', 'partial']
        
        return result, success

    def generate_verification_report(self, all_results):
        """📊 Gera relatório de verificação final."""
        print("\n" + "="*70)
        print("📊 RELATÓRIO DE VERIFICAÇÃO - EXECUÇÃO REAL")
        print("="*70)
        
        # Verificar workspace final
        final_items = list(Path(self.temp_workspace).iterdir())
        
        print(f"📁 ESTADO FINAL DO WORKSPACE:")
        print(f"   📂 Localização: {self.temp_workspace}")
        print(f"   📊 Total de itens: {len(final_items)}")
        
        if final_items:
            print(f"   📋 Itens criados FISICAMENTE:")
            for item in final_items:
                if item.is_dir():
                    print(f"      📁 {item.name}/")
                else:
                    print(f"      📄 {item.name} ({item.stat().st_size} bytes)")
        else:
            print(f"   ❌ NENHUM ITEM FÍSICO CRIADO!")
        
        # Verificação com hash do diretório
        dir_hash = self._calculate_directory_hash(self.temp_workspace)
        print(f"   🔐 Hash do diretório: {dir_hash[:16]}...")
        
        # Análise dos resultados
        test_names = ['Criação de Pastas', 'Operações Sistema', 'Linguagem Natural', 'Execução Autônoma']
        
        print(f"\n📈 RESUMO DOS TESTES:")
        
        success_count = 0
        for i, (test_name, success) in enumerate(zip(test_names, [r[1] for r in all_results])):
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"   {i+1}. {test_name}: {status}")
            if success:
                success_count += 1
        
        overall_rate = success_count / len(test_names) * 100
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   📊 Taxa de execução REAL: {overall_rate:.1f}%")
        print(f"   📁 Itens físicos criados: {len(final_items)}")
        
        if overall_rate >= 75 and len(final_items) > 0:
            verdict = "🏆 EXECUÇÃO REAL CONFIRMADA"
            print(f"\n{verdict}")
            print("✅ O Gemini Code REALMENTE executa comandos no sistema!")
        elif overall_rate >= 50:
            verdict = "⚠️  EXECUÇÃO PARCIAL"
            print(f"\n{verdict}")
            print("🔧 Sistema executa alguns comandos, mas precisa melhorar")
        else:
            verdict = "❌ POSSÍVEL SIMULAÇÃO"
            print(f"\n{verdict}")
            print("🚨 Sistema pode estar simulando ao invés de executar")
        
        return {
            'overall_success_rate': overall_rate,
            'physical_items_created': len(final_items),
            'verdict': verdict,
            'workspace_hash': dir_hash
        }
    
    def _calculate_directory_hash(self, directory):
        """Calcula hash do diretório para verificar mudanças físicas."""
        import hashlib
        
        hash_obj = hashlib.sha256()
        
        for item in sorted(Path(directory).rglob('*')):
            if item.is_file():
                with open(item, 'rb') as f:
                    hash_obj.update(f.read())
            hash_obj.update(str(item).encode())
        
        return hash_obj.hexdigest()
    
    def cleanup(self):
        """Limpeza final."""
        if self.temp_workspace and Path(self.temp_workspace).exists():
            shutil.rmtree(self.temp_workspace)
            print(f"🧹 Workspace limpo: {self.temp_workspace}")


async def run_real_execution_verification():
    """🔍 Executa verificação completa de execução real."""
    print("🔍" * 70)
    print("🚀 VERIFICAÇÃO DE EXECUÇÃO REAL - SEM SIMULAÇÃO")
    print("🔍" * 70)
    print()
    print("🎯 Objetivo: Provar que o Gemini Code REALMENTE executa comandos")
    print("🔬 Método: Verificação física do sistema de arquivos")
    print("📋 Testes: Criação de pastas, linguagem natural, execução autônoma")
    print()
    
    verifier = RealExecutionVerifier()
    
    try:
        # Setup
        workspace = verifier.setup_test_workspace()
        
        # Executar testes
        results = []
        
        # TESTE 1: Criação física de pastas
        result1 = await verifier.test_physical_folder_creation()
        results.append(result1)
        
        # TESTE 2: Operações no sistema
        result2 = await verifier.test_file_system_operations()
        results.append(result2)
        
        # TESTE 3: Linguagem natural extensa
        result3 = await verifier.test_natural_language_comprehension()
        results.append(result3)
        
        # TESTE 4: Execução autônoma real
        result4 = await verifier.test_autonomous_real_execution()
        results.append(result4)
        
        # Relatório final
        final_report = verifier.generate_verification_report(results)
        
        # Salvar evidências
        evidence_file = Path("real_execution_evidence.json")
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'workspace': workspace,
                'results': [r[0] for r in results],  # Dados dos testes
                'final_report': final_report
            }, f, indent=2, default=str)
        
        print(f"\n📄 Evidências salvas: {evidence_file}")
        
        return final_report['overall_success_rate'] >= 75
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        verifier.cleanup()


if __name__ == "__main__":
    print("🔍 Iniciando verificação de execução real...")
    try:
        success = asyncio.run(run_real_execution_verification())
        if success:
            print("\n🎉 EXECUÇÃO REAL CONFIRMADA!")
            sys.exit(0)
        else:
            print("\n⚠️  POSSÍVEL SIMULAÇÃO DETECTADA")
            sys.exit(1)
    except Exception as e:
        print(f"💥 Falha na verificação: {e}")
        sys.exit(1)
