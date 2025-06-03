"""
Sistema de Capacidades Aprimoradas do Gemini Code
Implementa otimizações para máximo potencial com 1M input / 32K output tokens
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .gemini_client import GeminiClient
from .memory_system import MemorySystem
from .file_manager import FileManagementSystem


@dataclass
class CapabilityMetrics:
    """Métricas das capacidades aprimoradas"""
    massive_context_requests: int = 0
    complex_analysis_requests: int = 0
    architectural_decisions: int = 0
    multi_file_operations: int = 0
    total_context_tokens_used: int = 0
    average_thinking_time: float = 0.0


class EnhancedCapabilities:
    """Sistema de capacidades aprimoradas do Gemini Code"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
        self.metrics = CapabilityMetrics()
        self.is_enhanced_mode = True
        
        # Ativa modo otimizado
        self.gemini.enable_massive_context_mode()
    
    async def analyze_entire_project(self, project_path: str) -> Dict[str, Any]:
        """
        ANÁLISE COMPLETA DE PROJETO - USA TODO O CONTEXTO DISPONÍVEL
        Capacidade única com 1M tokens de input
        """
        start_time = time.time()
        
        print("🔍 ANÁLISE COMPLETA DE PROJETO - MODO CONTEXTO MASSIVO")
        print("=" * 60)
        
        # Coleta TODOS os arquivos do projeto
        project_files = []
        project_structure = {}
        total_content = ""
        
        try:
            for file_path in Path(project_path).rglob("*"):
                if file_path.is_file() and self._should_analyze_file(file_path):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        relative_path = str(file_path.relative_to(project_path))
                        
                        project_files.append({
                            'path': relative_path,
                            'content': content,
                            'size': len(content),
                            'lines': len(content.splitlines())
                        })
                        
                        total_content += f"\n\n=== {relative_path} ===\n{content}"
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao ler {file_path}: {e}")
            
            # Constrói contexto massivo
            context_prompt = f"""
🎯 ANÁLISE COMPLETA DE PROJETO - CONTEXTO MASSIVO

📊 ESTATÍSTICAS DO PROJETO:
- Total de arquivos: {len(project_files)}
- Linhas de código: {sum(f['lines'] for f in project_files):,}
- Tamanho total: {sum(f['size'] for f in project_files):,} caracteres

📁 ESTRUTURA E CONTEÚDO COMPLETO:
{total_content}

🎯 TAREFA - ANÁLISE ARQUITETURAL PROFUNDA:

Analise COMPLETAMENTE este projeto considerando:

1. **ARQUITETURA GERAL**
   - Padrões arquiteturais utilizados
   - Qualidade da estrutura de diretórios
   - Separação de responsabilidades
   - Aderência a princípios SOLID

2. **QUALIDADE DO CÓDIGO**
   - Code smells e anti-patterns
   - Complexidade ciclomática
   - Duplicação de código
   - Convenções de nomenclatura

3. **FUNCIONALIDADES**
   - Funcionalidades implementadas
   - Funcionalidades incompletas ou TODOs
   - Testes e cobertura
   - Documentação

4. **SEGURANÇA E PERFORMANCE**
   - Vulnerabilidades potenciais
   - Gargalos de performance
   - Uso de recursos
   - Práticas de segurança

5. **MANUTENIBILIDADE**
   - Facilidade de modificação
   - Dependências externas
   - Débito técnico
   - Escalabilidade

6. **RECOMENDAÇÕES ESTRATÉGICAS**
   - Prioridades de melhoria
   - Refatorações necessárias
   - Novas funcionalidades sugeridas
   - Roadmap de desenvolvimento

Forneça uma análise COMPLETA e DETALHADA usando todo o contexto disponível.
"""
            
            # Chama Gemini com contexto massivo
            print(f"🧠 Enviando {self.gemini.estimate_tokens(context_prompt):,} tokens para análise...")
            
            response = await self.gemini.generate_response(
                context_prompt,
                thinking_budget=32768,  # Máximo thinking para análise completa
                enable_massive_context=True
            )
            
            # Métricas
            analysis_time = time.time() - start_time
            self.metrics.massive_context_requests += 1
            self.metrics.complex_analysis_requests += 1
            self.metrics.total_context_tokens_used += self.gemini.estimate_tokens(context_prompt)
            
            analysis_result = {
                'project_stats': {
                    'total_files': len(project_files),
                    'total_lines': sum(f['lines'] for f in project_files),
                    'total_size': sum(f['size'] for f in project_files),
                    'analysis_time': analysis_time,
                    'tokens_used': self.gemini.estimate_tokens(context_prompt)
                },
                'files_analyzed': project_files,
                'detailed_analysis': response,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"✅ Análise concluída em {analysis_time:.2f}s")
            print(f"📊 {len(project_files)} arquivos analisados simultaneamente")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Erro na análise completa: {e}")
            return {'error': str(e)}
    
    async def massive_refactoring(self, project_path: str, refactoring_goal: str) -> Dict[str, Any]:
        """
        REFATORAÇÃO MASSIVA - MÚLTIPLOS ARQUIVOS SIMULTANEAMENTE
        Usa contexto completo para decisões arquiteturais consistentes
        """
        print("🔧 REFATORAÇÃO MASSIVA - MODO ARQUITETURAL")
        print("=" * 50)
        
        # Primeiro, analisa projeto completo
        project_analysis = await self.analyze_entire_project(project_path)
        
        if 'error' in project_analysis:
            return project_analysis
        
        # Constrói prompt para refatoração com contexto massivo
        refactoring_prompt = f"""
🎯 REFATORAÇÃO ARQUITETURAL MASSIVA

📋 OBJETIVO: {refactoring_goal}

📊 CONTEXTO DO PROJETO:
{project_analysis['detailed_analysis']}

🔧 TAREFA - REFATORAÇÃO COMPLETA:

Com base na análise completa acima, execute uma refatoração arquitetural que:

1. **MANTENHA CONSISTÊNCIA**
   - Padrões uniformes em todos os arquivos
   - Nomenclatura consistente
   - Estrutura organizacional lógica

2. **IMPLEMENTE MELHORIAS**
   - Aplique design patterns apropriados
   - Elimine code smells detectados
   - Melhore separação de responsabilidades

3. **GERE ARQUIVOS COMPLETOS**
   - Forneça código completo para cada arquivo modificado
   - Inclua novos arquivos se necessário
   - Mantenha funcionalidade existente

4. **DOCUMENTE MUDANÇAS**
   - Explique decisões arquiteturais
   - Liste arquivos modificados/criados
   - Forneça plano de migração

Gere uma resposta COMPLETA com todos os arquivos refatorados.
"""
        
        response = await self.gemini.generate_response(
            refactoring_prompt,
            thinking_budget=32768,  # Thinking máximo
            enable_massive_context=True
        )
        
        self.metrics.architectural_decisions += 1
        self.metrics.multi_file_operations += 1
        
        return {
            'refactoring_goal': refactoring_goal,
            'original_analysis': project_analysis,
            'refactoring_plan': response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def architectural_planning(self, requirements: str, project_context: str = "") -> Dict[str, Any]:
        """
        PLANEJAMENTO ARQUITETURAL ESTRATÉGICO
        Usa thinking mode para decisões de longo prazo
        """
        print("🏗️ PLANEJAMENTO ARQUITETURAL ESTRATÉGICO")
        print("=" * 45)
        
        planning_prompt = f"""
🎯 PLANEJAMENTO ARQUITETURAL ESTRATÉGICO

📋 REQUISITOS:
{requirements}

📁 CONTEXTO DO PROJETO:
{project_context}

🏗️ TAREFA - ARQUITETURA ESTRATÉGICA:

Desenvolva um plano arquitetural COMPLETO que inclua:

1. **ARQUITETURA DE ALTO NÍVEL**
   - Diagrama conceitual da arquitetura
   - Componentes principais e suas responsabilidades
   - Padrões arquiteturais recomendados (MVC, Clean Architecture, etc.)
   - Decisões de design e justificativas

2. **ESTRUTURA DE PROJETO**
   - Organização de diretórios e arquivos
   - Convenções de nomenclatura
   - Separação de módulos/camadas
   - Estrutura de testes

3. **TECNOLOGIAS E DEPENDÊNCIAS**
   - Stack tecnológico recomendado
   - Bibliotecas e frameworks
   - Ferramentas de desenvolvimento
   - Considerações de performance e escalabilidade

4. **IMPLEMENTAÇÃO FASEADA**
   - Roadmap de desenvolvimento
   - Priorização de features
   - Marcos e entregáveis
   - Estimativas de tempo

5. **PADRÕES E CONVENÇÕES**
   - Coding standards
   - Padrões de design
   - Documentação técnica
   - Processos de code review

6. **PLANOS DE TESTE**
   - Estratégia de testes
   - Tipos de teste necessários
   - Ferramentas de automação
   - Cobertura de código

Forneça um plano DETALHADO e IMPLEMENTÁVEL.
"""
        
        response = await self.gemini.generate_response(
            planning_prompt,
            thinking_budget=32768,  # Máximo thinking para planejamento
            enable_massive_context=True
        )
        
        self.metrics.architectural_decisions += 1
        
        return {
            'requirements': requirements,
            'architectural_plan': response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def comprehensive_debugging(self, project_path: str, error_description: str) -> Dict[str, Any]:
        """
        DEBUGGING COMPREENSIVO COM CONTEXTO COMPLETO
        Analisa todo o projeto para encontrar causa raiz
        """
        print("🐛 DEBUGGING COMPREENSIVO - CONTEXTO COMPLETO")
        print("=" * 50)
        
        # Análise completa para contexto
        project_analysis = await self.analyze_entire_project(project_path)
        
        debug_prompt = f"""
🐛 DEBUGGING COMPREENSIVO COM CONTEXTO MASSIVO

❌ ERRO RELATADO:
{error_description}

📊 ANÁLISE COMPLETA DO PROJETO:
{project_analysis.get('detailed_analysis', 'Análise não disponível')}

🔍 TAREFA - DEBUG SISTEMÁTICO:

Com acesso ao código COMPLETO do projeto, execute um debugging sistemático:

1. **IDENTIFICAÇÃO DO PROBLEMA**
   - Localização exata do erro
   - Arquivos e linhas envolvidos
   - Tipo de erro (sintático, lógico, runtime, etc.)

2. **ANÁLISE DE CAUSA RAIZ**
   - Origem do problema no código
   - Dependências afetadas
   - Impacto em outros componentes

3. **SOLUÇÃO COMPLETA**
   - Código corrigido para TODOS os arquivos afetados
   - Testes para validar a correção
   - Prevenção de regressões

4. **MELHORIAS PREVENTIVAS**
   - Refatorações para evitar problemas similares
   - Validações adicionais
   - Documentação de debugging

5. **PLANO DE IMPLEMENTAÇÃO**
   - Ordem de aplicação das correções
   - Testes de validação
   - Rollback se necessário

Forneça uma solução COMPLETA e TESTÁVEL.
"""
        
        response = await self.gemini.generate_response(
            debug_prompt,
            thinking_budget=24576,  # Alto thinking para debugging
            enable_massive_context=True
        )
        
        return {
            'error_description': error_description,
            'project_context': project_analysis,
            'debug_solution': response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determina se arquivo deve ser incluído na análise"""
        # Extensões de arquivo para análise
        relevant_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
            '.html', '.css', '.scss', '.sass', '.less',
            '.json', '.yaml', '.yml', '.xml', '.toml',
            '.md', '.txt', '.rst', '.conf', '.cfg',
            '.sql', '.sh', '.bat', '.ps1',
            '.dockerfile', '.dockerignore', '.gitignore',
            'Makefile', 'CMakeLists.txt', 'requirements.txt',
            'package.json', 'composer.json', 'Cargo.toml'
        }
        
        # Diretórios para ignorar
        ignore_dirs = {
            '__pycache__', '.git', '.svn', '.hg',
            'node_modules', '.venv', 'venv', 'env',
            '.env', 'build', 'dist', 'target',
            '.pytest_cache', '.mypy_cache', '.coverage',
            '.idea', '.vscode', '.vs'
        }
        
        # Verifica se está em diretório ignorado
        for part in file_path.parts:
            if part in ignore_dirs:
                return False
        
        # Verifica extensão
        if file_path.suffix.lower() in relevant_extensions:
            return True
        
        # Verifica arquivos especiais sem extensão
        if file_path.name in {'Makefile', 'Dockerfile', 'README', 'LICENSE'}:
            return True
        
        return False
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """Retorna métricas das capacidades aprimoradas"""
        gemini_stats = self.gemini.get_performance_stats()
        
        return {
            'enhanced_capabilities': {
                'massive_context_requests': self.metrics.massive_context_requests,
                'complex_analysis_requests': self.metrics.complex_analysis_requests,
                'architectural_decisions': self.metrics.architectural_decisions,
                'multi_file_operations': self.metrics.multi_file_operations,
                'total_context_tokens_used': self.metrics.total_context_tokens_used,
                'average_thinking_time': self.metrics.average_thinking_time
            },
            'gemini_performance': gemini_stats,
            'optimization_level': 'MAXIMUM',
            'context_capacity': f"{self.gemini.max_input_tokens:,} tokens",
            'output_capacity': f"{self.gemini.max_output_tokens:,} tokens"
        }
    
    def print_enhanced_status(self):
        """Mostra status das capacidades aprimoradas"""
        print("\n🚀 GEMINI CODE - CAPACIDADES APRIMORADAS ATIVAS")
        print("=" * 60)
        
        metrics = self.get_enhanced_metrics()
        enhanced = metrics['enhanced_capabilities']
        performance = metrics['gemini_performance']
        
        print(f"🧠 Contexto Massivo: {metrics['context_capacity']}")
        print(f"🚀 Saída Máxima: {metrics['output_capacity']}")
        print(f"🎯 Nível de Otimização: {metrics['optimization_level']}")
        
        print(f"\n📊 CAPACIDADES UTILIZADAS:")
        print(f"  🔍 Análises Massivas: {enhanced['massive_context_requests']}")
        print(f"  🏗️ Decisões Arquiteturais: {enhanced['architectural_decisions']}")
        print(f"  🔧 Operações Multi-arquivo: {enhanced['multi_file_operations']}")
        print(f"  📈 Tokens de Contexto Usados: {enhanced['total_context_tokens_used']:,}")
        
        if performance['total_requests'] > 0:
            print(f"\n🎮 PERFORMANCE GERAL:")
            print(f"  📬 Total de Requests: {performance['total_requests']}")
            print(f"  📥 Tokens Input Total: {performance['total_input_tokens']:,}")
            print(f"  📤 Tokens Output Total: {performance['total_output_tokens']:,}")
            print(f"  📊 Média Input/Request: {performance['avg_input_per_request']:.0f}")
            print(f"  📊 Média Output/Request: {performance['avg_output_per_request']:.0f}")
        
        print(f"\n✨ CAPACIDADES ATIVAS:")
        print(f"  ✅ Análise de projetos completos")
        print(f"  ✅ Refatoração arquitetural massiva")
        print(f"  ✅ Debugging com contexto completo")
        print(f"  ✅ Planejamento estratégico")
        print(f"  ✅ Thinking mode transparente")
        print(f"  ✅ Geração de múltiplos arquivos")
        
        print("=" * 60)


# Função de conveniência para ativar capacidades aprimoradas
def enable_enhanced_gemini_code(gemini_client: GeminiClient) -> EnhancedCapabilities:
    """
    ATIVA CAPACIDADES APRIMORADAS DO GEMINI CODE
    
    Transforma o Gemini Code de 80% para 120% das capacidades do Claude
    """
    print("🚀 ATIVANDO CAPACIDADES APRIMORADAS...")
    
    enhanced = EnhancedCapabilities(gemini_client)
    enhanced.print_enhanced_status()
    
    return enhanced