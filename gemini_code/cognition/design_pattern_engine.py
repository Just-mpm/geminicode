"""
Engine de Design Patterns - Reconhecimento e aplicação de padrões de design
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import ast
import re

from ..core.gemini_client import GeminiClient
from ..core.project_manager import ProjectManager
from ..utils.logger import Logger


class DesignPattern(Enum):
    """Padrões de design reconhecidos."""
    # Creational
    SINGLETON = "Singleton"
    FACTORY = "Factory"
    ABSTRACT_FACTORY = "Abstract Factory"
    BUILDER = "Builder"
    PROTOTYPE = "Prototype"
    
    # Structural
    ADAPTER = "Adapter"
    BRIDGE = "Bridge"
    COMPOSITE = "Composite"
    DECORATOR = "Decorator"
    FACADE = "Facade"
    FLYWEIGHT = "Flyweight"
    PROXY = "Proxy"
    
    # Behavioral
    CHAIN_OF_RESPONSIBILITY = "Chain of Responsibility"
    COMMAND = "Command"
    INTERPRETER = "Interpreter"
    ITERATOR = "Iterator"
    MEDIATOR = "Mediator"
    MEMENTO = "Memento"
    OBSERVER = "Observer"
    STATE = "State"
    STRATEGY = "Strategy"
    TEMPLATE_METHOD = "Template Method"
    VISITOR = "Visitor"
    
    # Other common patterns
    MVC = "Model-View-Controller"
    MVP = "Model-View-Presenter"
    MVVM = "Model-View-ViewModel"
    REPOSITORY = "Repository"
    UNIT_OF_WORK = "Unit of Work"
    DEPENDENCY_INJECTION = "Dependency Injection"
    PUBLISH_SUBSCRIBE = "Publish-Subscribe"


@dataclass
class PatternInstance:
    """Instância de um padrão identificado no código."""
    pattern: DesignPattern
    confidence: float
    location: str
    components: Dict[str, List[str]]
    evidence: List[str]
    quality_score: float


@dataclass
class PatternSuggestion:
    """Sugestão de aplicação de padrão."""
    pattern: DesignPattern
    problem: str
    solution: str
    implementation_steps: List[str]
    code_example: str
    benefits: List[str]
    drawbacks: List[str]
    effort: str  # low, medium, high


class DesignPatternEngine:
    """
    Engine para reconhecimento e aplicação de design patterns.
    Identifica padrões existentes e sugere novos.
    """
    
    def __init__(self, gemini_client: GeminiClient, project_manager: ProjectManager):
        self.gemini = gemini_client
        self.project = project_manager
        self.logger = Logger()
        
        # Definições de padrões
        self.pattern_definitions = self._load_pattern_definitions()
        
        # Cache de análises
        self.pattern_cache = {}
        
        # Indicadores de padrões
        self.pattern_indicators = self._load_pattern_indicators()
    
    def _load_pattern_definitions(self) -> Dict[DesignPattern, Dict[str, Any]]:
        """Carrega definições de padrões."""
        return {
            DesignPattern.SINGLETON: {
                'description': 'Ensures a class has only one instance',
                'components': ['instance', 'getInstance'],
                'indicators': ['_instance', 'getInstance', '__new__', 'singleton'],
                'use_cases': ['Database connections', 'Configuration managers', 'Logging']
            },
            DesignPattern.FACTORY: {
                'description': 'Creates objects without specifying exact classes',
                'components': ['Factory', 'create', 'Product'],
                'indicators': ['Factory', 'create', 'make', 'build'],
                'use_cases': ['Object creation with complex logic', 'Multiple product types']
            },
            DesignPattern.OBSERVER: {
                'description': 'Defines one-to-many dependency between objects',
                'components': ['Subject', 'Observer', 'notify', 'update'],
                'indicators': ['subscribe', 'unsubscribe', 'notify', 'observer', 'listener'],
                'use_cases': ['Event handling', 'Model-View architectures', 'Notifications']
            },
            DesignPattern.STRATEGY: {
                'description': 'Defines family of algorithms, encapsulates each',
                'components': ['Strategy', 'Context', 'execute'],
                'indicators': ['Strategy', 'Algorithm', 'Policy', 'execute'],
                'use_cases': ['Multiple algorithms', 'Runtime algorithm selection']
            },
            DesignPattern.DECORATOR: {
                'description': 'Adds new functionality to objects dynamically',
                'components': ['Component', 'Decorator', 'ConcreteDecorator'],
                'indicators': ['Decorator', 'Wrapper', 'wrap', '@'],
                'use_cases': ['Adding features dynamically', 'Extending functionality']
            },
            DesignPattern.ADAPTER: {
                'description': 'Allows incompatible interfaces to work together',
                'components': ['Target', 'Adapter', 'Adaptee'],
                'indicators': ['Adapter', 'Wrapper', 'adapt'],
                'use_cases': ['Third-party integration', 'Legacy code integration']
            },
            DesignPattern.REPOSITORY: {
                'description': 'Encapsulates data access logic',
                'components': ['Repository', 'Entity', 'find', 'save'],
                'indicators': ['Repository', 'find', 'save', 'delete', 'getBy'],
                'use_cases': ['Data access abstraction', 'Testing with mocks']
            },
            DesignPattern.MVC: {
                'description': 'Separates presentation, logic, and data',
                'components': ['Model', 'View', 'Controller'],
                'indicators': ['Controller', 'Model', 'View', 'render', 'update'],
                'use_cases': ['Web applications', 'GUI applications']
            }
        }
    
    def _load_pattern_indicators(self) -> Dict[str, List[DesignPattern]]:
        """Mapeia indicadores para padrões."""
        indicators = {}
        
        for pattern, definition in self.pattern_definitions.items():
            for indicator in definition.get('indicators', []):
                if indicator not in indicators:
                    indicators[indicator] = []
                indicators[indicator].append(pattern)
        
        return indicators
    
    async def analyze_patterns(self, deep_analysis: bool = True) -> Dict[str, Any]:
        """
        Analisa padrões de design no projeto.
        
        Args:
            deep_analysis: Se deve usar IA para análise profunda
            
        Returns:
            Análise completa de padrões
        """
        self.logger.info("🎨 Analisando design patterns...")
        
        if not self.project.structure:
            self.project.scan_project()
        
        # 1. Detecta padrões existentes
        detected_patterns = await self._detect_patterns()
        
        # 2. Avalia qualidade dos padrões
        pattern_quality = await self._evaluate_pattern_quality(detected_patterns)
        
        # 3. Identifica oportunidades de padrões
        opportunities = await self._identify_pattern_opportunities()
        
        # 4. Análise com IA (se habilitado)
        ai_analysis = {}
        if deep_analysis and (detected_patterns or opportunities):
            ai_analysis = await self._ai_pattern_analysis(detected_patterns, opportunities)
        
        # 5. Gera sugestões
        suggestions = await self._generate_pattern_suggestions(
            detected_patterns, opportunities, ai_analysis
        )
        
        # Compila resultado
        analysis = {
            'detected_patterns': [self._pattern_to_dict(p) for p in detected_patterns],
            'pattern_quality': pattern_quality,
            'opportunities': opportunities,
            'suggestions': [self._suggestion_to_dict(s) for s in suggestions],
            'ai_analysis': ai_analysis,
            'summary': self._generate_pattern_summary(detected_patterns, suggestions)
        }
        
        # Cacheia
        self.pattern_cache['latest'] = analysis
        
        return analysis
    
    async def _detect_patterns(self) -> List[PatternInstance]:
        """Detecta padrões existentes no código."""
        detected_patterns = []
        
        # Analisa arquivos Python
        for file_path in self.project.structure.files:
            if not file_path.endswith('.py'):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Análise AST para Python
                tree = ast.parse(content)
                
                # Detecta padrões baseado em estrutura
                file_patterns = self._analyze_ast_for_patterns(tree, file_path)
                
                # Análise textual para indicadores
                text_patterns = self._analyze_text_for_patterns(content, file_path)
                
                # Combina resultados
                detected_patterns.extend(file_patterns)
                detected_patterns.extend(text_patterns)
                
            except Exception as e:
                self.logger.error(f"Erro ao analisar {file_path}: {e}")
        
        # Remove duplicatas e ajusta confiança
        detected_patterns = self._consolidate_patterns(detected_patterns)
        
        return detected_patterns
    
    def _analyze_ast_for_patterns(self, tree: ast.AST, file_path: str) -> List[PatternInstance]:
        """Analisa AST em busca de padrões."""
        patterns = []
        
        # Visitor para diferentes padrões
        class PatternVisitor(ast.NodeVisitor):
            def __init__(self, file_path):
                self.file_path = file_path
                self.patterns = []
                self.classes = {}
                self.methods = {}
            
            def visit_ClassDef(self, node):
                # Coleta informações da classe
                class_info = {
                    'name': node.name,
                    'methods': [],
                    'attributes': [],
                    'base_classes': [self._get_name(base) for base in node.bases]
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append(item.name)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info['attributes'].append(target.id)
                
                self.classes[node.name] = class_info
                
                # Detecta Singleton
                if self._is_singleton_pattern(node, class_info):
                    self.patterns.append(PatternInstance(
                        pattern=DesignPattern.SINGLETON,
                        confidence=0.8,
                        location=f"{self.file_path}:{node.lineno}",
                        components={'class': [node.name]},
                        evidence=['Private instance variable', 'getInstance method'],
                        quality_score=0.7
                    ))
                
                # Detecta Factory
                if self._is_factory_pattern(node, class_info):
                    self.patterns.append(PatternInstance(
                        pattern=DesignPattern.FACTORY,
                        confidence=0.7,
                        location=f"{self.file_path}:{node.lineno}",
                        components={'factory': [node.name]},
                        evidence=['create methods', 'Product creation logic'],
                        quality_score=0.7
                    ))
                
                self.generic_visit(node)
            
            def _get_name(self, node):
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return node.attr
                return 'Unknown'
            
            def _is_singleton_pattern(self, node, class_info):
                # Verifica indicadores de Singleton
                has_instance = any('_instance' in attr for attr in class_info['attributes'])
                has_getInstance = 'getInstance' in class_info['methods'] or 'get_instance' in class_info['methods']
                has_new = '__new__' in class_info['methods']
                
                return (has_instance and has_getInstance) or has_new
            
            def _is_factory_pattern(self, node, class_info):
                # Verifica indicadores de Factory
                factory_methods = ['create', 'make', 'build', 'produce']
                has_factory_method = any(
                    any(fm in method for fm in factory_methods) 
                    for method in class_info['methods']
                )
                
                return has_factory_method and 'Factory' in node.name
        
        visitor = PatternVisitor(file_path)
        visitor.visit(tree)
        
        return visitor.patterns
    
    def _analyze_text_for_patterns(self, content: str, file_path: str) -> List[PatternInstance]:
        """Analisa texto em busca de indicadores de padrões."""
        patterns = []
        
        # Conta ocorrências de indicadores
        indicator_counts = {}
        for indicator, associated_patterns in self.pattern_indicators.items():
            count = len(re.findall(rf'\b{indicator}\b', content, re.IGNORECASE))
            if count > 0:
                for pattern in associated_patterns:
                    if pattern not in indicator_counts:
                        indicator_counts[pattern] = 0
                    indicator_counts[pattern] += count
        
        # Cria instâncias de padrão baseado em contagens
        for pattern, count in indicator_counts.items():
            if count >= 2:  # Threshold mínimo
                confidence = min(0.9, count * 0.1)
                
                patterns.append(PatternInstance(
                    pattern=pattern,
                    confidence=confidence,
                    location=file_path,
                    components={'file': [file_path]},
                    evidence=[f'Found {count} indicators for {pattern.value}'],
                    quality_score=0.5  # Score inicial
                ))
        
        return patterns
    
    def _consolidate_patterns(self, patterns: List[PatternInstance]) -> List[PatternInstance]:
        """Consolida e remove duplicatas de padrões."""
        consolidated = {}
        
        for pattern in patterns:
            key = (pattern.pattern, pattern.location.split(':')[0])  # Pattern + file
            
            if key not in consolidated:
                consolidated[key] = pattern
            else:
                # Merge informações
                existing = consolidated[key]
                existing.confidence = max(existing.confidence, pattern.confidence)
                existing.evidence.extend(pattern.evidence)
                
                # Merge components
                for comp_type, comp_list in pattern.components.items():
                    if comp_type not in existing.components:
                        existing.components[comp_type] = []
                    existing.components[comp_type].extend(comp_list)
        
        return list(consolidated.values())
    
    async def _evaluate_pattern_quality(self, patterns: List[PatternInstance]) -> Dict[str, Any]:
        """Avalia qualidade da implementação dos padrões."""
        quality_metrics = {
            'overall_score': 0,
            'pattern_scores': {},
            'issues': [],
            'best_implementations': [],
            'worst_implementations': []
        }
        
        if not patterns:
            return quality_metrics
        
        total_score = 0
        
        for pattern in patterns:
            # Avalia cada padrão
            score = await self._evaluate_single_pattern(pattern)
            pattern.quality_score = score
            
            quality_metrics['pattern_scores'][str(pattern.pattern.value)] = score
            total_score += score
            
            # Identifica issues
            if score < 0.5:
                quality_metrics['issues'].append({
                    'pattern': pattern.pattern.value,
                    'location': pattern.location,
                    'score': score,
                    'reason': 'Poor implementation quality'
                })
        
        # Calcula score geral
        quality_metrics['overall_score'] = total_score / len(patterns) if patterns else 0
        
        # Identifica melhores e piores
        sorted_patterns = sorted(patterns, key=lambda p: p.quality_score, reverse=True)
        
        quality_metrics['best_implementations'] = [
            {'pattern': p.pattern.value, 'location': p.location, 'score': p.quality_score}
            for p in sorted_patterns[:3]
        ]
        
        quality_metrics['worst_implementations'] = [
            {'pattern': p.pattern.value, 'location': p.location, 'score': p.quality_score}
            for p in sorted_patterns[-3:] if p.quality_score < 0.7
        ]
        
        return quality_metrics
    
    async def _evaluate_single_pattern(self, pattern: PatternInstance) -> float:
        """Avalia qualidade de um padrão específico."""
        score = pattern.confidence * 0.5  # Base score
        
        # Ajusta baseado em completude
        if pattern.pattern == DesignPattern.SINGLETON:
            # Verifica se tem todos os componentes
            if 'class' in pattern.components:
                score += 0.2
            if any('getInstance' in e for e in pattern.evidence):
                score += 0.3
        
        elif pattern.pattern == DesignPattern.FACTORY:
            if 'factory' in pattern.components and 'product' in pattern.components:
                score += 0.4
            else:
                score += 0.2
        
        # Normaliza score
        return min(1.0, score)
    
    async def _identify_pattern_opportunities(self) -> List[Dict[str, Any]]:
        """Identifica oportunidades para aplicar padrões."""
        opportunities = []
        
        # Analisa problemas comuns que podem ser resolvidos com padrões
        
        # 1. Múltiplas instâncias de configuração -> Singleton
        config_files = [f for f in self.project.structure.files 
                       if 'config' in f.lower() or 'settings' in f.lower()]
        
        if len(config_files) > 2:
            opportunities.append({
                'problem': 'Multiple configuration files/classes',
                'pattern': DesignPattern.SINGLETON.value,
                'locations': config_files,
                'benefit': 'Centralized configuration management',
                'confidence': 0.7
            })
        
        # 2. Múltiplas condicionais para criar objetos -> Factory
        for file_path in self.project.structure.files[:50]:  # Limita para performance
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Conta if/elif para criação de objetos
                    creation_patterns = re.findall(
                        r'if.*:\s*\n\s*\w+\s*=\s*\w+\(',
                        content
                    )
                    
                    if len(creation_patterns) > 3:
                        opportunities.append({
                            'problem': 'Complex object creation logic',
                            'pattern': DesignPattern.FACTORY.value,
                            'locations': [file_path],
                            'benefit': 'Simplified object creation',
                            'confidence': 0.6
                        })
                except:
                    pass
        
        # 3. Acoplamento direto a implementações -> Strategy/Adapter
        # Esta é uma análise mais complexa que seria melhor com IA
        
        return opportunities
    
    async def _ai_pattern_analysis(self, detected: List[PatternInstance], 
                                  opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise profunda de padrões usando IA."""
        # Prepara contexto
        detected_summary = {}
        for pattern in detected:
            pattern_name = pattern.pattern.value
            if pattern_name not in detected_summary:
                detected_summary[pattern_name] = 0
            detected_summary[pattern_name] += 1
        
        prompt = f"""
Analyze design patterns in this codebase:

Detected patterns:
{self._format_pattern_summary(detected_summary)}

Identified opportunities:
{self._format_opportunities(opportunities[:5])}

Provide:
1. Assessment of current pattern usage
2. Missing patterns that would benefit the architecture
3. Refactoring recommendations
4. Pattern anti-patterns to avoid
5. Specific implementation improvements

Focus on actionable insights.
"""
        
        try:
            response = await self.gemini.generate_response(
                prompt,
                thinking_budget=16384
            )
            
            return {
                'analysis': response,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _format_pattern_summary(self, summary: Dict[str, int]) -> str:
        """Formata resumo de padrões para prompt."""
        lines = []
        for pattern, count in summary.items():
            lines.append(f"- {pattern}: {count} instance(s)")
        return '\n'.join(lines) if lines else "No patterns detected"
    
    def _format_opportunities(self, opportunities: List[Dict[str, Any]]) -> str:
        """Formata oportunidades para prompt."""
        lines = []
        for opp in opportunities:
            lines.append(f"- {opp['problem']} -> {opp['pattern']}")
        return '\n'.join(lines) if lines else "No clear opportunities identified"
    
    async def _generate_pattern_suggestions(self, detected: List[PatternInstance],
                                          opportunities: List[Dict[str, Any]],
                                          ai_analysis: Dict[str, Any]) -> List[PatternSuggestion]:
        """Gera sugestões de aplicação de padrões."""
        suggestions = []
        
        # Sugestões baseadas em oportunidades
        for opp in opportunities[:5]:
            pattern_enum = self._get_pattern_enum(opp['pattern'])
            if pattern_enum:
                suggestion = await self._create_pattern_suggestion(
                    pattern_enum,
                    opp['problem'],
                    opp['locations']
                )
                suggestions.append(suggestion)
        
        # Sugestões para melhorar padrões existentes
        for pattern in detected:
            if pattern.quality_score < 0.7:
                improvement = await self._create_improvement_suggestion(pattern)
                if improvement:
                    suggestions.append(improvement)
        
        return suggestions
    
    def _get_pattern_enum(self, pattern_name: str) -> Optional[DesignPattern]:
        """Converte nome de padrão para enum."""
        for pattern in DesignPattern:
            if pattern.value == pattern_name:
                return pattern
        return None
    
    async def _create_pattern_suggestion(self, pattern: DesignPattern,
                                       problem: str,
                                       locations: List[str]) -> PatternSuggestion:
        """Cria sugestão de aplicação de padrão."""
        definition = self.pattern_definitions.get(pattern, {})
        
        # Gera exemplo de código
        code_example = await self._generate_code_example(pattern)
        
        return PatternSuggestion(
            pattern=pattern,
            problem=problem,
            solution=definition.get('description', ''),
            implementation_steps=self._generate_implementation_steps(pattern),
            code_example=code_example,
            benefits=self._get_pattern_benefits(pattern),
            drawbacks=self._get_pattern_drawbacks(pattern),
            effort=self._estimate_implementation_effort(pattern, len(locations))
        )
    
    async def _generate_code_example(self, pattern: DesignPattern) -> str:
        """Gera exemplo de código para um padrão."""
        examples = {
            DesignPattern.SINGLETON: '''
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.config = {}
        self._load_config()
    
    def get(self, key):
        return self.config.get(key)
''',
            DesignPattern.FACTORY: '''
class ShapeFactory:
    @staticmethod
    def create_shape(shape_type: str):
        if shape_type == "circle":
            return Circle()
        elif shape_type == "square":
            return Square()
        elif shape_type == "triangle":
            return Triangle()
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
''',
            DesignPattern.OBSERVER: '''
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def detach(self, observer):
        self._observers.remove(observer)
    
    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(self, *args, **kwargs)
''',
            DesignPattern.STRATEGY: '''
class PaymentProcessor:
    def __init__(self, strategy):
        self._strategy = strategy
    
    def process_payment(self, amount):
        return self._strategy.process(amount)

class CreditCardStrategy:
    def process(self, amount):
        # Credit card processing logic
        return f"Processed ${amount} via credit card"
'''
        }
        
        return examples.get(pattern, "# Pattern implementation example")
    
    def _generate_implementation_steps(self, pattern: DesignPattern) -> List[str]:
        """Gera passos de implementação para um padrão."""
        steps_map = {
            DesignPattern.SINGLETON: [
                "Create private class variable for instance",
                "Implement __new__ method to control instantiation",
                "Add initialization logic in private method",
                "Create public access method if needed",
                "Add thread safety if required"
            ],
            DesignPattern.FACTORY: [
                "Define abstract product interface/base class",
                "Create concrete product implementations",
                "Implement factory class with creation method",
                "Add logic to determine which product to create",
                "Replace direct instantiation with factory calls"
            ],
            DesignPattern.OBSERVER: [
                "Define observer interface with update method",
                "Create subject class with attach/detach/notify",
                "Implement concrete observers",
                "Register observers with subject",
                "Call notify when state changes"
            ],
            DesignPattern.STRATEGY: [
                "Define strategy interface",
                "Create concrete strategy implementations",
                "Add strategy field to context class",
                "Implement method to change strategy at runtime",
                "Delegate algorithm execution to strategy"
            ]
        }
        
        return steps_map.get(pattern, ["Analyze specific requirements", "Design pattern structure", "Implement incrementally", "Test thoroughly"])
    
    def _get_pattern_benefits(self, pattern: DesignPattern) -> List[str]:
        """Retorna benefícios de um padrão."""
        benefits_map = {
            DesignPattern.SINGLETON: [
                "Global access point",
                "Controlled instantiation",
                "Memory efficiency",
                "Consistent state"
            ],
            DesignPattern.FACTORY: [
                "Decouples creation logic",
                "Easy to extend with new types",
                "Centralizes object creation",
                "Promotes loose coupling"
            ],
            DesignPattern.OBSERVER: [
                "Loose coupling between objects",
                "Dynamic subscription",
                "Broadcast communication",
                "Separation of concerns"
            ],
            DesignPattern.STRATEGY: [
                "Algorithm independence",
                "Runtime algorithm switching",
                "Easy to add new algorithms",
                "Eliminates conditional statements"
            ]
        }
        
        return benefits_map.get(pattern, ["Improved code organization", "Better maintainability"])
    
    def _get_pattern_drawbacks(self, pattern: DesignPattern) -> List[str]:
        """Retorna desvantagens de um padrão."""
        drawbacks_map = {
            DesignPattern.SINGLETON: [
                "Global state issues",
                "Testing difficulties",
                "Violates single responsibility",
                "Thread safety complexity"
            ],
            DesignPattern.FACTORY: [
                "Added complexity",
                "Extra classes needed",
                "Can be overengineered"
            ],
            DesignPattern.OBSERVER: [
                "Memory leaks if not careful",
                "Unexpected updates",
                "Debugging complexity"
            ],
            DesignPattern.STRATEGY: [
                "Increased number of classes",
                "Client must know strategies",
                "Strategy selection complexity"
            ]
        }
        
        return drawbacks_map.get(pattern, ["Added complexity", "Learning curve"])
    
    def _estimate_implementation_effort(self, pattern: DesignPattern, 
                                      affected_files: int) -> str:
        """Estima esforço de implementação."""
        # Complexidade base do padrão
        complexity = {
            DesignPattern.SINGLETON: 1,
            DesignPattern.FACTORY: 2,
            DesignPattern.OBSERVER: 3,
            DesignPattern.STRATEGY: 2,
            DesignPattern.DECORATOR: 3,
            DesignPattern.ADAPTER: 2
        }
        
        base_complexity = complexity.get(pattern, 2)
        total_complexity = base_complexity * (1 + affected_files * 0.2)
        
        if total_complexity < 2:
            return "low"
        elif total_complexity < 4:
            return "medium"
        else:
            return "high"
    
    async def _create_improvement_suggestion(self, pattern: PatternInstance) -> Optional[PatternSuggestion]:
        """Cria sugestão para melhorar padrão existente."""
        if pattern.quality_score >= 0.7:
            return None
        
        # Identifica problemas específicos
        problems = []
        if pattern.confidence < 0.5:
            problems.append("Incomplete implementation")
        if len(pattern.evidence) < 2:
            problems.append("Missing key components")
        
        problem_description = f"Poor {pattern.pattern.value} implementation: " + ", ".join(problems)
        
        return PatternSuggestion(
            pattern=pattern.pattern,
            problem=problem_description,
            solution=f"Improve existing {pattern.pattern.value} implementation",
            implementation_steps=[
                f"Review {pattern.pattern.value} best practices",
                "Identify missing components",
                "Refactor to match pattern structure",
                "Add proper documentation",
                "Write tests for pattern behavior"
            ],
            code_example=await self._generate_code_example(pattern.pattern),
            benefits=["Better pattern conformance", "Improved maintainability"],
            drawbacks=["Refactoring effort required"],
            effort="medium"
        )
    
    def _generate_pattern_summary(self, detected: List[PatternInstance],
                                suggestions: List[PatternSuggestion]) -> Dict[str, Any]:
        """Gera resumo da análise de padrões."""
        pattern_counts = {}
        for pattern in detected:
            pattern_name = pattern.pattern.value
            if pattern_name not in pattern_counts:
                pattern_counts[pattern_name] = 0
            pattern_counts[pattern_name] += 1
        
        return {
            'total_patterns_detected': len(detected),
            'unique_patterns': len(pattern_counts),
            'most_used_pattern': max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None,
            'improvement_opportunities': len(suggestions),
            'average_quality_score': sum(p.quality_score for p in detected) / len(detected) if detected else 0,
            'recommendation': self._get_overall_recommendation(detected, suggestions)
        }
    
    def _get_overall_recommendation(self, detected: List[PatternInstance],
                                   suggestions: List[PatternSuggestion]) -> str:
        """Gera recomendação geral."""
        if not detected and len(suggestions) > 3:
            return "Consider adopting design patterns to improve architecture"
        elif detected and sum(p.quality_score for p in detected) / len(detected) < 0.6:
            return "Focus on improving existing pattern implementations"
        elif len(suggestions) > 0:
            return "Good pattern usage with room for targeted improvements"
        else:
            return "Excellent design pattern implementation"
    
    def _pattern_to_dict(self, pattern: PatternInstance) -> Dict[str, Any]:
        """Converte PatternInstance para dict."""
        return {
            'pattern': pattern.pattern.value,
            'confidence': pattern.confidence,
            'location': pattern.location,
            'components': pattern.components,
            'evidence': pattern.evidence,
            'quality_score': pattern.quality_score
        }
    
    def _suggestion_to_dict(self, suggestion: PatternSuggestion) -> Dict[str, Any]:
        """Converte PatternSuggestion para dict."""
        return {
            'pattern': suggestion.pattern.value,
            'problem': suggestion.problem,
            'solution': suggestion.solution,
            'implementation_steps': suggestion.implementation_steps,
            'code_example': suggestion.code_example,
            'benefits': suggestion.benefits,
            'drawbacks': suggestion.drawbacks,
            'effort': suggestion.effort
        }
    
    async def apply_pattern(self, pattern: DesignPattern, 
                           target_location: str,
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica um padrão de design específico.
        
        Args:
            pattern: Padrão a aplicar
            target_location: Onde aplicar (arquivo/classe)
            context: Contexto adicional
            
        Returns:
            Resultado da aplicação
        """
        self.logger.info(f"🎨 Aplicando padrão {pattern.value} em {target_location}")
        
        # Gera código para o padrão
        generated_code = await self._generate_pattern_code(pattern, context)
        
        # Cria plano de refatoração
        refactoring_plan = await self._create_refactoring_plan(
            pattern, target_location, context
        )
        
        return {
            'pattern': pattern.value,
            'generated_code': generated_code,
            'refactoring_plan': refactoring_plan,
            'estimated_changes': len(refactoring_plan['steps']),
            'risk_level': refactoring_plan['risk_level']
        }
    
    async def _generate_pattern_code(self, pattern: DesignPattern,
                                   context: Dict[str, Any]) -> str:
        """Gera código específico para um padrão no contexto."""
        prompt = f"""
Generate {pattern.value} pattern implementation for:

Context:
- Language: Python
- Purpose: {context.get('purpose', 'General purpose')}
- Components: {context.get('components', [])}

Requirements:
1. Follow {pattern.value} pattern structure precisely
2. Use clear, descriptive names
3. Include docstrings
4. Make it production-ready

Generate the complete implementation.
"""
        
        response = await self.gemini.generate_response(prompt)
        
        # Extrai código da resposta
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return response
    
    async def _create_refactoring_plan(self, pattern: DesignPattern,
                                     target_location: str,
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Cria plano de refatoração para aplicar padrão."""
        steps = []
        
        # Passos genéricos
        steps.append({
            'order': 1,
            'action': 'Backup current code',
            'target': target_location,
            'risk': 'low'
        })
        
        steps.append({
            'order': 2,
            'action': f'Create {pattern.value} structure',
            'target': 'New files/classes',
            'risk': 'low'
        })
        
        steps.append({
            'order': 3,
            'action': 'Migrate existing functionality',
            'target': target_location,
            'risk': 'medium'
        })
        
        steps.append({
            'order': 4,
            'action': 'Update references',
            'target': 'All dependent code',
            'risk': 'high'
        })
        
        steps.append({
            'order': 5,
            'action': 'Add tests',
            'target': 'Test files',
            'risk': 'low'
        })
        
        # Calcula risco geral
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        avg_risk = sum(risk_scores[s['risk']] for s in steps) / len(steps)
        
        risk_level = 'low' if avg_risk < 1.5 else 'medium' if avg_risk < 2.5 else 'high'
        
        return {
            'steps': steps,
            'risk_level': risk_level,
            'estimated_time': f"{len(steps) * 30} minutes",
            'rollback_strategy': 'Restore from backup if issues arise'
        }