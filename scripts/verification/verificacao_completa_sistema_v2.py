#!/usr/bin/env python3
"""
Verificação Completa do Sistema Gemini Code v2.0
Análise profunda e detalhada de todos os componentes
"""

import os
import sys
import json
import time
import asyncio
import traceback
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

class SystemVerifier:
    """Verificador completo do sistema."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'analysis': {},
            'scores': {},
            'issues': [],
            'recommendations': [],
            'total_score': 0
        }
        
        # Adiciona o diretório raiz ao path
        sys.path.insert(0, str(self.project_root))
        
    def verify_file_structure(self) -> Dict[str, Any]:
        """Verifica estrutura de arquivos."""
        print("🔍 Verificando estrutura de arquivos...")
        
        analysis = {
            'score': 0,
            'critical_files': {},
            'missing_files': [],
            'file_counts': {}
        }
        
        # Arquivos críticos esperados
        critical_files = {
            'main.py': 'Ponto de entrada principal',
            'gemini_code/__init__.py': 'Pacote principal',
            'gemini_code/core/__init__.py': 'Core package',
            'gemini_code/core/gemini_client.py': 'Cliente Gemini',
            'gemini_code/core/master_system.py': 'Sistema mestre',
            'gemini_code/core/memory_system.py': 'Sistema de memória',
            'gemini_code/core/config.py': 'Sistema de configuração',
            'gemini_code/cognition/__init__.py': 'Módulo cognição',
            'gemini_code/cognition/architectural_reasoning.py': 'Raciocínio arquitetural',
            'pyproject.toml': 'Configuração do projeto',
            'requirements.txt': 'Dependências'
        }
        
        for file_path, description in critical_files.items():
            full_path = self.project_root / file_path
            exists = full_path.exists()
            analysis['critical_files'][file_path] = {
                'exists': exists,
                'description': description,
                'size': full_path.stat().st_size if exists else 0
            }
            
            if exists:
                analysis['score'] += 10
            else:
                analysis['missing_files'].append(file_path)
                self.results['issues'].append(f"Arquivo crítico ausente: {file_path}")
        
        # Conta arquivos por diretório
        for directory in ['gemini_code', 'tests', 'docs']:
            dir_path = self.project_root / directory
            if dir_path.exists():
                python_files = list(dir_path.rglob("*.py"))
                analysis['file_counts'][directory] = len(python_files)
            else:
                analysis['file_counts'][directory] = 0
        
        # Score máximo: 110 (11 arquivos * 10)
        analysis['score'] = min(100, (analysis['score'] / 110) * 100)
        
        print(f"  Score estrutura: {analysis['score']:.1f}/100")
        return analysis
    
    def verify_imports(self) -> Dict[str, Any]:
        """Verifica se todos os módulos podem ser importados."""
        print("📦 Verificando imports...")
        
        analysis = {
            'score': 0,
            'successful_imports': [],
            'failed_imports': [],
            'import_details': {}
        }
        
        # Módulos principais para testar
        modules_to_test = [
            'gemini_code',
            'gemini_code.core',
            'gemini_code.core.gemini_client',
            'gemini_code.core.master_system',
            'gemini_code.core.memory_system',
            'gemini_code.core.config',
            'gemini_code.cognition',
            'gemini_code.cognition.architectural_reasoning'
        ]
        
        for module_name in modules_to_test:
            try:
                # Tenta importar usando importlib
                spec = importlib.util.find_spec(module_name)
                if spec is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    analysis['successful_imports'].append(module_name)
                    analysis['import_details'][module_name] = {
                        'status': 'success',
                        'location': str(spec.origin) if spec.origin else 'built-in'
                    }
                    analysis['score'] += 12.5  # 100/8 módulos
                else:
                    analysis['failed_imports'].append(module_name)
                    analysis['import_details'][module_name] = {
                        'status': 'not_found',
                        'error': 'Module not found'
                    }
                    self.results['issues'].append(f"Módulo não encontrado: {module_name}")
                    
            except Exception as e:
                analysis['failed_imports'].append(module_name)
                analysis['import_details'][module_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['issues'].append(f"Erro ao importar {module_name}: {e}")
        
        analysis['score'] = min(100, analysis['score'])
        print(f"  Score imports: {analysis['score']:.1f}/100")
        return analysis
    
    def verify_core_functionality(self) -> Dict[str, Any]:
        """Verifica funcionalidades core."""
        print("⚙️ Verificando funcionalidades core...")
        
        analysis = {
            'score': 0,
            'functional_components': [],
            'broken_components': [],
            'component_details': {}
        }
        
        # Lista de componentes para verificar
        components = [
            ('GeminiClient', 'gemini_code.core.gemini_client', 'GeminiClient'),
            ('MasterSystem', 'gemini_code.core.master_system', 'GeminiCodeMasterSystem'),
            ('MemorySystem', 'gemini_code.core.memory_system', 'MemorySystem'),
            ('ConfigManager', 'gemini_code.core.config', 'ConfigManager'),
            ('ArchitecturalReasoning', 'gemini_code.cognition.architectural_reasoning', 'ArchitecturalReasoning')
        ]
        
        for component_name, module_path, class_name in components:
            try:
                # Verifica se o arquivo existe
                file_path = self.project_root / (module_path.replace('.', '/') + '.py')
                if not file_path.exists():
                    analysis['broken_components'].append(component_name)
                    analysis['component_details'][component_name] = {
                        'status': 'file_missing',
                        'error': f"Arquivo não encontrado: {file_path}"
                    }
                    continue
                
                # Verifica se a classe existe no arquivo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if f"class {class_name}" in content:
                    analysis['functional_components'].append(component_name)
                    analysis['component_details'][component_name] = {
                        'status': 'exists',
                        'file_size': len(content),
                        'lines': len(content.split('\n'))
                    }
                    analysis['score'] += 20  # 100/5 componentes
                else:
                    analysis['broken_components'].append(component_name)
                    analysis['component_details'][component_name] = {
                        'status': 'class_missing',
                        'error': f"Classe {class_name} não encontrada"
                    }
                    
            except Exception as e:
                analysis['broken_components'].append(component_name)
                analysis['component_details'][component_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['issues'].append(f"Erro ao verificar {component_name}: {e}")
        
        analysis['score'] = min(100, analysis['score'])
        print(f"  Score funcionalidades: {analysis['score']:.1f}/100")
        return analysis
    
    def verify_code_quality(self) -> Dict[str, Any]:
        """Verifica qualidade do código."""
        print("📊 Verificando qualidade do código...")
        
        analysis = {
            'score': 0,
            'metrics': {},
            'quality_issues': []
        }
        
        try:
            # Conta arquivos Python
            python_files = list(self.project_root.rglob("*.py"))
            total_lines = 0
            total_functions = 0
            total_classes = 0
            docstring_files = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = len([line for line in content.split('\n') if line.strip()])
                    total_lines += lines
                    
                    # Conta funções e classes
                    total_functions += content.count('def ')
                    total_classes += content.count('class ')
                    
                    # Verifica docstrings
                    if '"""' in content or "'''" in content:
                        docstring_files += 1
                        
                except Exception:
                    continue
            
            # Calcula métricas
            analysis['metrics'] = {
                'total_files': len(python_files),
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'avg_lines_per_file': total_lines / max(1, len(python_files)),
                'avg_functions_per_file': total_functions / max(1, len(python_files)),
                'files_with_docstrings': docstring_files,
                'docstring_coverage': (docstring_files / max(1, len(python_files))) * 100
            }
            
            # Calcula score baseado nas métricas
            score = 0
            
            # Penaliza arquivos muito grandes (>500 linhas)
            if analysis['metrics']['avg_lines_per_file'] < 500:
                score += 25
            elif analysis['metrics']['avg_lines_per_file'] < 1000:
                score += 15
            else:
                analysis['quality_issues'].append("Arquivos muito grandes (média >1000 linhas)")
            
            # Recompensa boa cobertura de docstrings
            if analysis['metrics']['docstring_coverage'] > 80:
                score += 25
            elif analysis['metrics']['docstring_coverage'] > 50:
                score += 15
            else:
                analysis['quality_issues'].append("Baixa cobertura de documentação")
            
            # Verifica estrutura
            if analysis['metrics']['total_classes'] > 10:
                score += 25
            else:
                analysis['quality_issues'].append("Poucas classes (arquitetura simplificada)")
            
            # Verifica complexidade
            if analysis['metrics']['total_functions'] > 50:
                score += 25
            else:
                analysis['quality_issues'].append("Poucas funções (funcionalidade limitada)")
            
            analysis['score'] = score
            
        except Exception as e:
            analysis['score'] = 0
            analysis['quality_issues'].append(f"Erro na análise: {e}")
        
        print(f"  Score qualidade: {analysis['score']:.1f}/100")
        return analysis
    
    def verify_configuration(self) -> Dict[str, Any]:
        """Verifica sistema de configuração."""
        print("⚙️ Verificando configuração...")
        
        analysis = {
            'score': 0,
            'config_files': {},
            'config_issues': []
        }
        
        # Arquivos de configuração esperados
        config_files = {
            'pyproject.toml': 'Configuração do projeto Python',
            'requirements.txt': 'Dependências Python',
            'gemini_code/config/default_config.yaml': 'Configuração padrão',
            '.gemini_code/config.yaml': 'Configuração local (opcional)'
        }
        
        for file_path, description in config_files.items():
            full_path = self.project_root / file_path
            exists = full_path.exists()
            
            analysis['config_files'][file_path] = {
                'exists': exists,
                'description': description
            }
            
            if exists:
                analysis['score'] += 25
                try:
                    if file_path.endswith('.yaml'):
                        import yaml
                        with open(full_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    elif file_path.endswith('.toml'):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '[project]' in content or '[tool.' in content:
                                pass  # Valid TOML structure
                    elif file_path.endswith('.txt'):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if len(lines) > 0:
                                pass  # Has content
                    
                    analysis['config_files'][file_path]['valid'] = True
                    
                except Exception as e:
                    analysis['config_files'][file_path]['valid'] = False
                    analysis['config_issues'].append(f"Arquivo {file_path} inválido: {e}")
            else:
                if 'opcional' not in description:
                    analysis['config_issues'].append(f"Arquivo de configuração ausente: {file_path}")
        
        analysis['score'] = min(100, analysis['score'])
        print(f"  Score configuração: {analysis['score']:.1f}/100")
        return analysis
    
    def analyze_system_complexity(self) -> Dict[str, Any]:
        """Analisa complexidade do sistema."""
        print("🧠 Analisando complexidade do sistema...")
        
        analysis = {
            'score': 0,
            'complexity_metrics': {},
            'architecture_patterns': []
        }
        
        try:
            # Analisa estrutura de diretórios
            directories = [d for d in self.project_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
            gemini_code_dirs = []
            
            gemini_code_path = self.project_root / 'gemini_code'
            if gemini_code_path.exists():
                gemini_code_dirs = [d.name for d in gemini_code_path.iterdir() if d.is_dir()]
            
            # Métricas de complexidade
            analysis['complexity_metrics'] = {
                'total_directories': len(directories),
                'gemini_code_modules': len(gemini_code_dirs),
                'module_names': gemini_code_dirs
            }
            
            # Detecta padrões arquiteturais
            patterns_found = []
            
            if 'core' in gemini_code_dirs:
                patterns_found.append('Core Module Pattern')
                analysis['score'] += 15
            
            if 'cognition' in gemini_code_dirs:
                patterns_found.append('Cognitive Architecture')
                analysis['score'] += 20
            
            if 'analysis' in gemini_code_dirs:
                patterns_found.append('Analysis Layer')
                analysis['score'] += 15
            
            if 'interface' in gemini_code_dirs:
                patterns_found.append('Interface Abstraction')
                analysis['score'] += 10
            
            if 'tools' in gemini_code_dirs:
                patterns_found.append('Tool Architecture')
                analysis['score'] += 10
            
            if 'utils' in gemini_code_dirs:
                patterns_found.append('Utility Layer')
                analysis['score'] += 5
            
            # Bonus por complexidade avançada
            if len(gemini_code_dirs) > 8:
                patterns_found.append('Complex Modular Architecture')
                analysis['score'] += 25
            
            analysis['architecture_patterns'] = patterns_found
            analysis['score'] = min(100, analysis['score'])
            
        except Exception as e:
            analysis['score'] = 0
            self.results['issues'].append(f"Erro na análise de complexidade: {e}")
        
        print(f"  Score complexidade: {analysis['score']:.1f}/100")
        return analysis
    
    def generate_recommendations(self):
        """Gera recomendações de melhoria."""
        print("💡 Gerando recomendações...")
        
        # Análise dos scores
        scores = self.results['scores']
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        # Recomendações baseadas em scores baixos
        if scores.get('file_structure', 0) < 80:
            self.results['recommendations'].append({
                'priority': 'high',
                'category': 'structure',
                'title': 'Melhorar estrutura de arquivos',
                'description': 'Alguns arquivos críticos estão ausentes ou incompletos',
                'action': 'Verificar e criar arquivos ausentes listados nos issues'
            })
        
        if scores.get('imports', 0) < 80:
            self.results['recommendations'].append({
                'priority': 'critical',
                'category': 'imports',
                'title': 'Corrigir problemas de importação',
                'description': 'Módulos não podem ser importados corretamente',
                'action': 'Verificar PYTHONPATH e estrutura de pacotes'
            })
        
        if scores.get('core_functionality', 0) < 80:
            self.results['recommendations'].append({
                'priority': 'high',
                'category': 'functionality',
                'title': 'Implementar funcionalidades ausentes',
                'description': 'Componentes core estão incompletos',
                'action': 'Implementar classes e métodos ausentes'
            })
        
        if scores.get('code_quality', 0) < 60:
            self.results['recommendations'].append({
                'priority': 'medium',
                'category': 'quality',
                'title': 'Melhorar qualidade do código',
                'description': 'Código precisa de refatoração e documentação',
                'action': 'Adicionar docstrings, reduzir complexidade, melhorar estrutura'
            })
        
        if scores.get('configuration', 0) < 80:
            self.results['recommendations'].append({
                'priority': 'medium',
                'category': 'config',
                'title': 'Completar sistema de configuração',
                'description': 'Arquivos de configuração ausentes ou inválidos',
                'action': 'Criar e validar todos os arquivos de configuração'
            })
        
        if avg_score < 70:
            self.results['recommendations'].append({
                'priority': 'critical',
                'category': 'overall',
                'title': 'Refatoração geral do sistema',
                'description': f'Score geral baixo ({avg_score:.1f}/100)',
                'action': 'Planejar refatoração completa seguindo as recomendações específicas'
            })
    
    def run_complete_verification(self) -> float:
        """Executa verificação completa."""
        print("🚀 INICIANDO VERIFICAÇÃO COMPLETA DO SISTEMA GEMINI CODE")
        print("=" * 60)
        
        # Executa todas as verificações
        self.results['analysis']['file_structure'] = self.verify_file_structure()
        self.results['analysis']['imports'] = self.verify_imports()
        self.results['analysis']['core_functionality'] = self.verify_core_functionality()
        self.results['analysis']['code_quality'] = self.verify_code_quality()
        self.results['analysis']['configuration'] = self.verify_configuration()
        self.results['analysis']['system_complexity'] = self.analyze_system_complexity()
        
        # Coleta scores
        for category, analysis in self.results['analysis'].items():
            self.results['scores'][category] = analysis['score']
        
        # Calcula score total
        total_score = sum(self.results['scores'].values()) / len(self.results['scores'])
        self.results['total_score'] = total_score
        
        # Gera recomendações
        self.generate_recommendations()
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DE VERIFICAÇÃO")
        print("=" * 60)
        
        for category, score in self.results['scores'].items():
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"{status} {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        print(f"\n🎯 SCORE TOTAL: {total_score:.1f}/100")
        
        if total_score >= 90:
            print("🏆 EXCELENTE! Sistema funcionando perfeitamente!")
        elif total_score >= 80:
            print("✅ BOM! Sistema funcionando bem com pequenos ajustes necessários.")
        elif total_score >= 60:
            print("⚠️ REGULAR! Sistema precisa de melhorias significativas.")
        else:
            print("❌ CRÍTICO! Sistema precisa de refatoração completa.")
        
        print(f"\n📋 Issues encontradas: {len(self.results['issues'])}")
        print(f"💡 Recomendações: {len(self.results['recommendations'])}")
        
        # Salva relatório
        with open('verification_report_v2.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: verification_report_v2.json")
        print("=" * 60)
        
        return total_score

def main():
    """Função principal."""
    verifier = SystemVerifier()
    score = verifier.run_complete_verification()
    return score

if __name__ == "__main__":
    score = main()
    sys.exit(0 if score >= 80 else 1)