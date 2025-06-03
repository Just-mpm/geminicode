#!/usr/bin/env python3
"""
Verificação Completa do Sistema Gemini Code
Analisa todas as áreas do sistema para identificar pontos de melhoria,
áreas rasas que precisam de profundidade e possíveis pontos de falha.
"""

import asyncio
import sys
import os
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
import ast
import json

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

class SystemAuditor:
    """Auditor completo do sistema Gemini Code."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.recommendations = []
        self.shallow_areas = []
        self.error_prone_areas = []
        
    def add_issue(self, category: str, severity: str, description: str, location: str = ""):
        """Adiciona um problema identificado."""
        self.issues.append({
            'category': category,
            'severity': severity,
            'description': description,
            'location': location
        })
    
    def add_warning(self, description: str, location: str = ""):
        """Adiciona um aviso."""
        self.warnings.append({
            'description': description,
            'location': location
        })
    
    def add_recommendation(self, description: str, priority: str = "medium"):
        """Adiciona uma recomendação."""
        self.recommendations.append({
            'description': description,
            'priority': priority
        })
    
    def add_shallow_area(self, area: str, reason: str, suggested_improvements: List[str]):
        """Adiciona área que precisa de mais profundidade."""
        self.shallow_areas.append({
            'area': area,
            'reason': reason,
            'improvements': suggested_improvements
        })

async def audit_core_modules():
    """Auditoria dos módulos principais."""
    print("🔍 AUDITANDO MÓDULOS PRINCIPAIS...")
    auditor = SystemAuditor()
    
    core_modules = [
        'gemini_code.core.master_system',
        'gemini_code.core.gemini_client', 
        'gemini_code.core.project_manager',
        'gemini_code.core.file_manager',
        'gemini_code.core.memory_system',
        'gemini_code.core.config'
    ]
    
    for module_name in core_modules:
        try:
            module = importlib.import_module(module_name)
            
            # Verifica se o módulo tem classes principais
            classes = [name for name, obj in inspect.getmembers(module, inspect.isclass)]
            if not classes:
                auditor.add_issue("Structure", "medium", f"Módulo sem classes principais", module_name)
            
            # Verifica documentação
            if not module.__doc__ or len(module.__doc__.strip()) < 50:
                auditor.add_warning(f"Documentação insuficiente", module_name)
            
            # Verifica métodos async sem tratamento de erro
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, '__init__'):
                    methods = [m for m in inspect.getmembers(obj, inspect.ismethod) 
                              if asyncio.iscoroutinefunction(m[1])]
                    for method_name, method in methods:
                        source = inspect.getsource(method) if hasattr(method, '__code__') else ""
                        if "try:" not in source and "except:" not in source:
                            auditor.add_warning(f"Método async sem tratamento de erro: {method_name}", f"{module_name}.{name}")
            
            print(f"✅ {module_name} - {len(classes)} classes encontradas")
            
        except Exception as e:
            auditor.add_issue("Import", "high", f"Erro ao importar: {e}", module_name)
            print(f"❌ {module_name} - Erro: {e}")
    
    return auditor

async def audit_cognition_modules():
    """Auditoria dos módulos de cognição avançada."""
    print("\n🧠 AUDITANDO MÓDULOS DE COGNIÇÃO...")
    auditor = SystemAuditor()
    
    cognition_modules = [
        'gemini_code.cognition.architectural_reasoning',
        'gemini_code.cognition.complexity_analyzer',
        'gemini_code.cognition.design_pattern_engine',
        'gemini_code.cognition.problem_solver',
        'gemini_code.cognition.learning_engine'
    ]
    
    for module_name in cognition_modules:
        try:
            module = importlib.import_module(module_name)
            
            # Verifica se implementa padrões de IA
            classes = [obj for name, obj in inspect.getmembers(module, inspect.isclass)]
            has_ai_patterns = False
            
            for cls in classes:
                methods = [m[0] for m in inspect.getmembers(cls, inspect.ismethod)]
                ai_methods = ['analyze', 'process', 'predict', 'learn', 'reason']
                if any(ai_method in ''.join(methods).lower() for ai_method in ai_methods):
                    has_ai_patterns = True
                    break
            
            if not has_ai_patterns:
                auditor.add_shallow_area(
                    module_name,
                    "Não implementa padrões de IA suficientes",
                    ["Adicionar métodos de análise", "Implementar aprendizado", "Adicionar raciocínio"]
                )
            
            print(f"✅ {module_name} - IA patterns: {has_ai_patterns}")
            
        except Exception as e:
            auditor.add_issue("Cognition", "high", f"Módulo de cognição com erro: {e}", module_name)
            print(f"❌ {module_name} - Erro: {e}")
    
    return auditor

async def audit_tools_system():
    """Auditoria do sistema de ferramentas."""
    print("\n🔧 AUDITANDO SISTEMA DE FERRAMENTAS...")
    auditor = SystemAuditor()
    
    try:
        from gemini_code.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry(".")
        tools = registry.list_tools()
        
        if len(tools) < 10:
            auditor.add_warning("Poucas ferramentas registradas", "tool_registry")
        
        # Verifica se cada ferramenta tem tratamento de erro
        for tool_name in tools:
            try:
                tool = registry.get_tool(tool_name)
                if hasattr(tool, 'execute'):
                    source = inspect.getsource(tool.execute)
                    if "try:" not in source:
                        auditor.add_warning(f"Ferramenta sem tratamento de erro: {tool_name}")
            except:
                pass
        
        print(f"✅ Sistema de Tools - {len(tools)} ferramentas registradas")
        
        # Verifica se tem ferramentas essenciais
        essential_tools = ['bash', 'read', 'write', 'list', 'grep', 'glob']
        missing_tools = [tool for tool in essential_tools if tool not in tools]
        if missing_tools:
            auditor.add_issue("Tools", "medium", f"Ferramentas essenciais ausentes: {missing_tools}")
        
    except Exception as e:
        auditor.add_issue("Tools", "high", f"Sistema de tools com problema: {e}")
        print(f"❌ Sistema de Tools - Erro: {e}")
    
    return auditor

async def audit_error_handling():
    """Auditoria do tratamento de erros em todo o sistema."""
    print("\n🛡️ AUDITANDO TRATAMENTO DE ERROS...")
    auditor = SystemAuditor()
    
    # Analisa arquivos Python para verificar tratamento de erros
    python_files = list(Path("gemini_code").rglob("*.py"))
    
    files_without_error_handling = []
    files_with_poor_error_handling = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica se tem try/except
            has_try_except = "try:" in content and "except" in content
            
            if not has_try_except:
                files_without_error_handling.append(str(file_path))
            else:
                # Verifica qualidade do tratamento de erro
                bare_except_count = content.count("except:")
                generic_except_count = content.count("except Exception:")
                specific_except_count = content.count("except ") - bare_except_count - generic_except_count
                
                if bare_except_count > specific_except_count:
                    files_with_poor_error_handling.append(str(file_path))
        
        except Exception as e:
            auditor.add_warning(f"Erro ao analisar arquivo: {e}", str(file_path))
    
    if files_without_error_handling:
        auditor.add_shallow_area(
            "Error Handling",
            f"{len(files_without_error_handling)} arquivos sem tratamento de erro",
            ["Adicionar try/except blocks", "Implementar logging de erros", "Adicionar recovery automático"]
        )
    
    if files_with_poor_error_handling:
        auditor.add_warning(f"{len(files_with_poor_error_handling)} arquivos com tratamento de erro genérico")
    
    print(f"✅ Análise de erros - {len(python_files)} arquivos analisados")
    print(f"⚠️ {len(files_without_error_handling)} sem tratamento, {len(files_with_poor_error_handling)} com tratamento pobre")
    
    return auditor

async def audit_configuration_system():
    """Auditoria do sistema de configuração."""
    print("\n⚙️ AUDITANDO SISTEMA DE CONFIGURAÇÃO...")
    auditor = SystemAuditor()
    
    try:
        from gemini_code.core.config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Verifica se configurações essenciais existem
        essential_configs = ['model', 'user', 'security', 'advanced']
        for config_key in essential_configs:
            if not hasattr(config, config_key):
                auditor.add_issue("Config", "medium", f"Configuração essencial ausente: {config_key}")
        
        # Verifica se há validação de configuração
        config_file = Path("gemini_code/config/default_config.yaml")
        if config_file.exists():
            print("✅ Arquivo de configuração padrão existe")
        else:
            auditor.add_issue("Config", "high", "Arquivo de configuração padrão ausente")
        
        # Verifica se há sistema de migração de configuração
        has_migration = hasattr(config_manager, 'migrate') or hasattr(config_manager, 'upgrade')
        if not has_migration:
            auditor.add_shallow_area(
                "Configuration Migration",
                "Sistema não tem migração de configurações",
                ["Implementar sistema de versionamento", "Adicionar migração automática", "Validação de configuração"]
            )
        
        print("✅ Sistema de configuração analisado")
        
    except Exception as e:
        auditor.add_issue("Config", "high", f"Sistema de configuração com erro: {e}")
        print(f"❌ Sistema de configuração - Erro: {e}")
    
    return auditor

async def audit_memory_system():
    """Auditoria do sistema de memória."""
    print("\n💾 AUDITANDO SISTEMA DE MEMÓRIA...")
    auditor = SystemAuditor()
    
    try:
        from gemini_code.core.memory_system import MemorySystem
        
        memory = MemorySystem(".")
        
        # Verifica se tem diferentes tipos de memória
        has_short_term = hasattr(memory, 'short_term') or 'short_term' in str(memory.__dict__)
        has_long_term = hasattr(memory, 'long_term') or 'long_term' in str(memory.__dict__)
        has_working = hasattr(memory, 'working') or 'working' in str(memory.__dict__)
        
        if not all([has_short_term, has_long_term, has_working]):
            auditor.add_shallow_area(
                "Memory Types",
                "Sistema de memória não implementa todos os tipos",
                ["Implementar memória de curto prazo", "Implementar memória de longo prazo", "Implementar memória de trabalho"]
            )
        
        # Verifica se tem compactação de memória
        has_compaction = hasattr(memory, 'compact') or hasattr(memory, 'compress')
        if not has_compaction:
            auditor.add_shallow_area(
                "Memory Compaction",
                "Sistema não tem compactação de memória",
                ["Implementar algoritmo de compactação", "Adicionar limpeza automática", "Otimizar uso de memória"]
            )
        
        # Verifica persistência
        memory_file = Path(".gemini_code/memory")
        if not memory_file.exists():
            auditor.add_warning("Diretório de memória não existe")
        
        print("✅ Sistema de memória analisado")
        
    except Exception as e:
        auditor.add_issue("Memory", "high", f"Sistema de memória com erro: {e}")
        print(f"❌ Sistema de memória - Erro: {e}")
    
    return auditor

async def audit_security_system():
    """Auditoria do sistema de segurança."""
    print("\n🔒 AUDITANDO SISTEMA DE SEGURANÇA...")
    auditor = SystemAuditor()
    
    try:
        # Verifica se existe sistema de permissões
        security_files = list(Path("gemini_code/security").glob("*.py"))
        
        if not security_files:
            auditor.add_issue("Security", "high", "Sistema de segurança não encontrado")
        else:
            # Verifica componentes de segurança
            security_components = []
            for file_path in security_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'permission' in content.lower():
                        security_components.append('permissions')
                    if 'security' in content.lower():
                        security_components.append('security_scanner')
                    if 'vulnerability' in content.lower():
                        security_components.append('vulnerability_detection')
            
            missing_components = []
            if 'permissions' not in security_components:
                missing_components.append('Sistema de permissões')
            if 'security_scanner' not in security_components:
                missing_components.append('Scanner de segurança')
            if 'vulnerability_detection' not in security_components:
                missing_components.append('Detecção de vulnerabilidades')
            
            if missing_components:
                auditor.add_shallow_area(
                    "Security Components",
                    f"Componentes de segurança ausentes: {missing_components}",
                    ["Implementar sistema de permissões completo", "Adicionar scanner de vulnerabilidades", "Implementar sandboxing"]
                )
        
        # Verifica se API keys são tratadas com segurança
        python_files = list(Path("gemini_code").rglob("*.py"))
        insecure_key_handling = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'api_key' in content.lower() and 'print' in content:
                        insecure_key_handling.append(str(file_path))
            except:
                pass
        
        if insecure_key_handling:
            auditor.add_issue("Security", "medium", f"Possível exposição de API keys em: {insecure_key_handling}")
        
        print("✅ Sistema de segurança analisado")
        
    except Exception as e:
        auditor.add_issue("Security", "high", f"Erro na auditoria de segurança: {e}")
        print(f"❌ Sistema de segurança - Erro: {e}")
    
    return auditor

async def audit_testing_coverage():
    """Auditoria da cobertura de testes."""
    print("\n🧪 AUDITANDO COBERTURA DE TESTES...")
    auditor = SystemAuditor()
    
    # Verifica arquivos de teste
    test_files = list(Path(".").glob("test_*.py")) + list(Path("tests").glob("*.py"))
    source_files = list(Path("gemini_code").rglob("*.py"))
    
    if len(test_files) < len(source_files) * 0.3:  # Menos de 30% de cobertura
        auditor.add_shallow_area(
            "Test Coverage",
            f"Cobertura de testes insuficiente: {len(test_files)} testes para {len(source_files)} arquivos",
            ["Criar testes unitários para cada módulo", "Implementar testes de integração", "Adicionar testes de stress"]
        )
    
    # Verifica se tem diferentes tipos de teste
    test_types = {
        'unit': False,
        'integration': False, 
        'system': False,
        'performance': False
    }
    
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if 'unittest' in content or 'test_' in content:
                    test_types['unit'] = True
                if 'integration' in content:
                    test_types['integration'] = True
                if 'system' in content or 'complete' in content:
                    test_types['system'] = True
                if 'performance' in content or 'stress' in content:
                    test_types['performance'] = True
        except:
            pass
    
    missing_test_types = [t for t, exists in test_types.items() if not exists]
    if missing_test_types:
        auditor.add_shallow_area(
            "Test Types",
            f"Tipos de teste ausentes: {missing_test_types}",
            [f"Implementar testes {t}" for t in missing_test_types]
        )
    
    print(f"✅ Testes analisados - {len(test_files)} arquivos de teste")
    
    return auditor

async def audit_performance_optimization():
    """Auditoria de otimizações de performance."""
    print("\n⚡ AUDITANDO OTIMIZAÇÕES DE PERFORMANCE...")
    auditor = SystemAuditor()
    
    # Verifica se há sistema de cache
    cache_implementations = []
    python_files = list(Path("gemini_code").rglob("*.py"))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'cache' in content.lower():
                    cache_implementations.append(str(file_path))
        except:
            pass
    
    if not cache_implementations:
        auditor.add_shallow_area(
            "Caching System",
            "Sistema não implementa cache",
            ["Implementar cache de resultados", "Adicionar cache de memória", "Implementar cache persistente"]
        )
    
    # Verifica se há otimizações async
    async_usage = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'async def' in content:
                    async_usage.append(str(file_path))
        except:
            pass
    
    if len(async_usage) < len(python_files) * 0.2:  # Menos de 20% usa async
        auditor.add_shallow_area(
            "Async Optimization",
            "Pouco uso de programação assíncrona",
            ["Converter operações I/O para async", "Implementar processamento paralelo", "Otimizar operações de rede"]
        )
    
    # Verifica se há monitoramento de performance
    has_performance_monitoring = False
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'performance' in content.lower() and ('time' in content or 'profile' in content):
                    has_performance_monitoring = True
                    break
        except:
            pass
    
    if not has_performance_monitoring:
        auditor.add_shallow_area(
            "Performance Monitoring",
            "Sistema não tem monitoramento de performance",
            ["Implementar profiling automático", "Adicionar métricas de tempo", "Monitorar uso de recursos"]
        )
    
    print("✅ Performance analisada")
    
    return auditor

def generate_comprehensive_report(auditors: List[SystemAuditor]) -> Dict[str, Any]:
    """Gera relatório abrangente de todas as auditorias."""
    
    all_issues = []
    all_warnings = []
    all_recommendations = []
    all_shallow_areas = []
    
    for auditor in auditors:
        all_issues.extend(auditor.issues)
        all_warnings.extend(auditor.warnings)
        all_recommendations.extend(auditor.recommendations)
        all_shallow_areas.extend(auditor.shallow_areas)
    
    # Categoriza por severidade
    critical_issues = [i for i in all_issues if i['severity'] == 'high']
    medium_issues = [i for i in all_issues if i['severity'] == 'medium']
    low_issues = [i for i in all_issues if i['severity'] == 'low']
    
    # Agrupa áreas rasas por categoria
    shallow_by_category = {}
    for area in all_shallow_areas:
        category = area['area'].split('.')[0] if '.' in area['area'] else area['area']
        if category not in shallow_by_category:
            shallow_by_category[category] = []
        shallow_by_category[category].append(area)
    
    return {
        'summary': {
            'total_issues': len(all_issues),
            'critical_issues': len(critical_issues),
            'medium_issues': len(medium_issues),
            'low_issues': len(low_issues),
            'warnings': len(all_warnings),
            'shallow_areas': len(all_shallow_areas),
            'recommendations': len(all_recommendations)
        },
        'critical_issues': critical_issues,
        'medium_issues': medium_issues,
        'low_issues': low_issues,
        'warnings': all_warnings,
        'shallow_areas_by_category': shallow_by_category,
        'recommendations': all_recommendations
    }

async def main():
    """Executa verificação completa do sistema."""
    print("🔍 VERIFICAÇÃO COMPLETA DO SISTEMA GEMINI CODE")
    print("=" * 80)
    
    # Executa todas as auditorias
    auditors = []
    
    auditors.append(await audit_core_modules())
    auditors.append(await audit_cognition_modules())
    auditors.append(await audit_tools_system())
    auditors.append(await audit_error_handling())
    auditors.append(await audit_configuration_system())
    auditors.append(await audit_memory_system())
    auditors.append(await audit_security_system())
    auditors.append(await audit_testing_coverage())
    auditors.append(await audit_performance_optimization())
    
    # Gera relatório final
    report = generate_comprehensive_report(auditors)
    
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL DE VERIFICAÇÃO")
    print("=" * 80)
    
    # Summary
    summary = report['summary']
    print(f"\n📈 RESUMO:")
    print(f"   🔴 Problemas Críticos: {summary['critical_issues']}")
    print(f"   🟡 Problemas Médios: {summary['medium_issues']}")
    print(f"   🟢 Problemas Menores: {summary['low_issues']}")
    print(f"   ⚠️  Avisos: {summary['warnings']}")
    print(f"   📊 Áreas Rasas: {summary['shallow_areas']}")
    print(f"   💡 Recomendações: {summary['recommendations']}")
    
    # Problemas críticos
    if report['critical_issues']:
        print(f"\n🔴 PROBLEMAS CRÍTICOS ENCONTRADOS:")
        for issue in report['critical_issues']:
            print(f"   ❌ {issue['category']}: {issue['description']}")
            if issue['location']:
                print(f"      📍 Local: {issue['location']}")
    
    # Áreas que precisam de profundidade
    if report['shallow_areas_by_category']:
        print(f"\n📊 ÁREAS QUE PRECISAM DE MAIOR PROFUNDIDADE:")
        for category, areas in report['shallow_areas_by_category'].items():
            print(f"\n   🔍 {category.upper()}:")
            for area in areas:
                print(f"      📌 {area['reason']}")
                for improvement in area['improvements'][:3]:  # Máximo 3 melhorias
                    print(f"         💡 {improvement}")
    
    # Recomendações prioritárias
    high_priority_recommendations = [r for r in report['recommendations'] if r.get('priority') == 'high']
    if high_priority_recommendations:
        print(f"\n💡 RECOMENDAÇÕES PRIORITÁRIAS:")
        for rec in high_priority_recommendations[:5]:  # Top 5
            print(f"   🎯 {rec['description']}")
    
    # Score geral do sistema
    total_possible_points = 100
    deductions = 0
    deductions += len(report['critical_issues']) * 15
    deductions += len(report['medium_issues']) * 8
    deductions += len(report['low_issues']) * 3
    deductions += len(report['shallow_areas_by_category']) * 5
    
    system_score = max(0, total_possible_points - deductions)
    
    print(f"\n🏆 SCORE GERAL DO SISTEMA: {system_score}/100")
    
    if system_score >= 90:
        print("🎉 EXCELENTE - Sistema robusto e bem implementado!")
    elif system_score >= 75:
        print("✅ BOM - Sistema sólido com algumas áreas para melhoria")
    elif system_score >= 60:
        print("⚠️ SATISFATÓRIO - Sistema funcional mas precisa de melhorias")
    else:
        print("🚨 PRECISA DE ATENÇÃO - Várias áreas críticas requerem correção")
    
    # Salva relatório detalhado
    with open('relatorio_verificacao_completa.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório detalhado salvo em: relatorio_verificacao_completa.json")
    
    return system_score >= 75

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Verificação interrompida")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante verificação: {e}")
        sys.exit(1)