"""
Sistema de Raciocínio Arquitetural - Análise e Design de Alto Nível
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import networkx as nx
from datetime import datetime

from ..core.gemini_client import GeminiClient
from ..core.project_manager import ProjectManager
from ..analysis.code_navigator import CodeNavigator
from ..utils.logger import Logger


class ArchitecturePattern(Enum):
    """Padrões arquiteturais reconhecidos."""
    MVC = "Model-View-Controller"
    MVP = "Model-View-Presenter"
    MVVM = "Model-View-ViewModel"
    LAYERED = "Layered Architecture"
    MICROSERVICES = "Microservices"
    MONOLITHIC = "Monolithic"
    EVENT_DRIVEN = "Event-Driven"
    HEXAGONAL = "Hexagonal (Ports and Adapters)"
    CLEAN = "Clean Architecture"
    DDD = "Domain-Driven Design"
    SERVERLESS = "Serverless"
    PIPE_FILTER = "Pipe and Filter"
    CLIENT_SERVER = "Client-Server"
    P2P = "Peer-to-Peer"
    HYBRID = "Hybrid Architecture"


@dataclass
class ArchitecturalComponent:
    """Componente arquitetural identificado."""
    name: str
    type: str
    path: str
    dependencies: List[str]
    interfaces: List[str]
    responsibility: str
    patterns: List[str]
    metrics: Dict[str, Any]


@dataclass
class ArchitecturalDecision:
    """Decisão arquitetural com justificativa."""
    decision: str
    rationale: str
    alternatives: List[str]
    trade_offs: Dict[str, List[str]]  # pros/cons
    impact: str
    confidence: float
    timestamp: datetime


@dataclass
class ArchitecturalIssue:
    """Problema arquitetural identificado."""
    type: str
    severity: str  # critical, high, medium, low
    description: str
    affected_components: List[str]
    suggested_solutions: List[str]
    estimated_effort: str


class ArchitecturalReasoning:
    """
    Sistema avançado de raciocínio arquitetural.
    Analisa, compreende e melhora arquitetura de software.
    """
    
    def __init__(self, gemini_client: GeminiClient, project_manager: ProjectManager, file_manager=None):
        self.gemini = gemini_client
        self.project = project_manager
        self.logger = Logger()
        # Se file_manager não foi fornecido, importa e cria uma instância
        if file_manager is None:
            from ..core.file_manager import FileManagementSystem
            from pathlib import Path
            file_manager = FileManagementSystem(gemini_client, Path(project_manager.project_root))
        self.code_navigator = CodeNavigator(gemini_client, file_manager)
        
        # Cache de análises
        self.architecture_cache = {}
        self.decision_history: List[ArchitecturalDecision] = []
        
        # Grafo de dependências
        self.dependency_graph = nx.DiGraph()
        
        # Padrões conhecidos
        self.known_patterns = self._load_architectural_patterns()
        
        # Métricas arquiteturais
        self.metrics = {
            'coupling': {},
            'cohesion': {},
            'complexity': {},
            'modularity': 0,
            'maintainability': 0
        }
    
    def _load_architectural_patterns(self) -> Dict[str, Any]:
        """Carrega padrões arquiteturais conhecidos."""
        return {
            'mvc': {
                'components': ['model', 'view', 'controller'],
                'relationships': [('controller', 'model'), ('controller', 'view'), ('view', 'model')],
                'indicators': ['controllers/', 'models/', 'views/', 'templates/']
            },
            'microservices': {
                'components': ['service', 'api_gateway', 'service_registry', 'config_server'],
                'indicators': ['docker-compose', 'kubernetes', 'service/', 'api/'],
                'characteristics': ['distributed', 'independent_deployment', 'service_boundaries']
            },
            'clean': {
                'layers': ['entities', 'use_cases', 'interface_adapters', 'frameworks_drivers'],
                'indicators': ['domain/', 'application/', 'infrastructure/', 'presentation/'],
                'principles': ['dependency_inversion', 'single_responsibility']
            },
            'hexagonal': {
                'components': ['domain', 'ports', 'adapters'],
                'indicators': ['domain/', 'ports/', 'adapters/', 'core/'],
                'characteristics': ['port_adapter_pattern', 'domain_centric']
            }
        }
    
    async def analyze_architecture(self, deep_analysis: bool = True) -> Dict[str, Any]:
        """
        Analisa arquitetura completa do projeto.
        
        Args:
            deep_analysis: Se deve fazer análise profunda com IA
            
        Returns:
            Análise arquitetural completa
        """
        self.logger.info("🏗️ Iniciando análise arquitetural...")
        
        # 1. Identificar estrutura básica
        structure = await self._identify_structure()
        
        # 2. Detectar padrões arquiteturais
        patterns = await self._detect_patterns(structure)
        
        # 3. Mapear componentes
        components = await self._map_components(structure)
        
        # 4. Analisar dependências
        dependencies = await self._analyze_dependencies(components)
        
        # 5. Calcular métricas
        metrics = await self._calculate_metrics(components, dependencies)
        
        # 6. Identificar problemas
        issues = await self._identify_issues(components, dependencies, metrics)
        
        # 7. Análise profunda com IA (se habilitado)
        ai_insights = {}
        if deep_analysis:
            ai_insights = await self._deep_ai_analysis(structure, patterns, issues)
        
        # 8. Gerar recomendações
        recommendations = await self._generate_recommendations(patterns, issues, ai_insights)
        
        # Compilar resultado
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'structure': structure,
            'detected_patterns': patterns,
            'components': [self._component_to_dict(c) for c in components],
            'dependencies': self._graph_to_dict(dependencies),
            'metrics': metrics,
            'issues': [self._issue_to_dict(i) for i in issues],
            'ai_insights': ai_insights,
            'recommendations': recommendations,
            'health_score': self._calculate_health_score(metrics, issues)
        }
        
        # Cachear resultado
        self.architecture_cache['latest'] = analysis
        
        return analysis
    
    async def _identify_structure(self) -> Dict[str, Any]:
        """Identifica estrutura básica do projeto."""
        if not self.project.structure:
            self.project.scan_project()
        
        structure = {
            'total_files': self.project.structure.total_files,
            'total_lines': self.project.structure.total_lines,
            'languages': dict(self.project.structure.languages),
            'directories': {},
            'entry_points': [],
            'configuration_files': [],
            'test_directories': []
        }
        
        # Analisa diretórios
        for directory in self.project.structure.directories:
            dir_path = Path(directory)
            dir_name = dir_path.name
            
            # Categoriza diretórios
            if any(test in dir_name for test in ['test', 'tests', 'spec', '__tests__']):
                structure['test_directories'].append(str(dir_path))
            
            # Conta arquivos por diretório
            files_in_dir = [f for f in self.project.structure.files if f.startswith(directory)]
            structure['directories'][directory] = {
                'file_count': len(files_in_dir),
                'purpose': self._infer_directory_purpose(dir_name, files_in_dir)
            }
        
        # Identifica entry points
        for file in self.project.structure.files:
            filename = Path(file).name
            if filename in ['main.py', 'app.py', 'index.js', 'server.js', 'index.ts']:
                structure['entry_points'].append(file)
            elif filename in ['config.py', 'settings.py', 'package.json', 'requirements.txt']:
                structure['configuration_files'].append(file)
        
        return structure
    
    def _infer_directory_purpose(self, dir_name: str, files: List[str]) -> str:
        """Infere o propósito de um diretório."""
        dir_lower = dir_name.lower()
        
        purpose_map = {
            'model': 'Data models and schemas',
            'view': 'UI components and templates',
            'controller': 'Business logic controllers',
            'service': 'Business services',
            'repository': 'Data access layer',
            'util': 'Utility functions',
            'helper': 'Helper functions',
            'config': 'Configuration files',
            'test': 'Test files',
            'doc': 'Documentation',
            'api': 'API endpoints',
            'core': 'Core business logic',
            'domain': 'Domain models',
            'infrastructure': 'Infrastructure code',
            'presentation': 'Presentation layer',
            'application': 'Application layer',
            'interface': 'Interface definitions',
            'adapter': 'Adapters and integrations',
            'migration': 'Database migrations',
            'static': 'Static assets',
            'template': 'Template files',
            'public': 'Public assets',
            'private': 'Private/internal code',
            'lib': 'Library code',
            'bin': 'Executable scripts',
            'script': 'Scripts',
            'tool': 'Development tools',
            'fixture': 'Test fixtures',
            'mock': 'Mock objects',
            'stub': 'Stub implementations'
        }
        
        # Verifica mapeamento direto
        for key, purpose in purpose_map.items():
            if key in dir_lower:
                return purpose
        
        # Analisa conteúdo dos arquivos
        if files:
            file_extensions = [Path(f).suffix for f in files]
            if '.py' in file_extensions:
                if any('test_' in f or '_test.py' in f for f in files):
                    return 'Test files'
                elif any('model' in f for f in files):
                    return 'Data models'
            elif '.js' in file_extensions or '.ts' in file_extensions:
                if any('component' in f for f in files):
                    return 'UI components'
                elif any('service' in f for f in files):
                    return 'Services'
        
        return 'General purpose'
    
    async def _detect_patterns(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta padrões arquiteturais no projeto."""
        detected_patterns = []
        
        # Verifica cada padrão conhecido
        for pattern_name, pattern_info in self.known_patterns.items():
            confidence = 0.0
            evidence = []
            
            # Verifica indicadores de diretório
            if 'indicators' in pattern_info:
                for indicator in pattern_info['indicators']:
                    for directory in structure['directories']:
                        if indicator in directory.lower():
                            confidence += 0.2
                            evidence.append(f"Found directory: {directory}")
            
            # Verifica componentes específicos
            if 'components' in pattern_info:
                found_components = []
                for component in pattern_info['components']:
                    for directory in structure['directories']:
                        if component in directory.lower():
                            found_components.append(component)
                
                if found_components:
                    confidence += 0.3 * (len(found_components) / len(pattern_info['components']))
                    evidence.append(f"Found components: {found_components}")
            
            # Análise adicional para padrões específicos
            if pattern_name == 'microservices':
                # Verifica arquivos de configuração
                docker_files = [f for f in structure.get('configuration_files', []) 
                               if 'docker' in f.lower() or 'kubernetes' in f.lower()]
                if docker_files:
                    confidence += 0.3
                    evidence.append(f"Found container configs: {docker_files}")
            
            # Se confiança é significativa, adiciona padrão detectado
            if confidence > 0.3:
                detected_patterns.append({
                    'pattern': pattern_name,
                    'confidence': min(confidence, 1.0),
                    'evidence': evidence,
                    'description': pattern_info.get('description', 
                                                  ArchitecturePattern[pattern_name.upper()].value 
                                                  if pattern_name.upper() in ArchitecturePattern.__members__ 
                                                  else pattern_name)
                })
        
        # Ordena por confiança
        detected_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        return detected_patterns
    
    async def _map_components(self, structure: Dict[str, Any]) -> List[ArchitecturalComponent]:
        """Mapeia componentes arquiteturais."""
        components = []
        
        # Analisa cada diretório principal
        for directory, info in structure['directories'].items():
            if info['file_count'] > 0:
                # Analisa arquivos no diretório
                files_in_dir = [f for f in self.project.structure.files if f.startswith(directory)]
                
                # Identifica interfaces e dependências
                interfaces = []
                dependencies = set()
                
                for file_path in files_in_dir[:10]:  # Limita análise para performance
                    try:
                        # Análise simplificada de imports
                        imports = await self.code_navigator.get_file_imports(file_path)
                        dependencies.update(imports)
                        
                        # Identifica interfaces (classes/funções públicas)
                        public_symbols = await self.code_navigator.get_public_symbols(file_path)
                        interfaces.extend(public_symbols)
                    except:
                        pass
                
                # Cria componente
                component = ArchitecturalComponent(
                    name=Path(directory).name,
                    type=self._classify_component_type(directory, info['purpose']),
                    path=directory,
                    dependencies=list(dependencies)[:20],  # Limita para não ficar muito grande
                    interfaces=interfaces[:20],
                    responsibility=info['purpose'],
                    patterns=[],  # Será preenchido depois
                    metrics={
                        'file_count': info['file_count'],
                        'size': 'medium' if info['file_count'] > 10 else 'small'
                    }
                )
                
                components.append(component)
        
        return components
    
    def _classify_component_type(self, directory: str, purpose: str) -> str:
        """Classifica o tipo de componente."""
        dir_lower = directory.lower()
        purpose_lower = purpose.lower()
        
        if any(x in dir_lower for x in ['model', 'entity', 'schema']):
            return 'Model'
        elif any(x in dir_lower for x in ['view', 'ui', 'component', 'template']):
            return 'View'
        elif any(x in dir_lower for x in ['controller', 'handler', 'endpoint']):
            return 'Controller'
        elif any(x in dir_lower for x in ['service', 'business', 'logic']):
            return 'Service'
        elif any(x in dir_lower for x in ['repository', 'dao', 'store']):
            return 'Repository'
        elif any(x in dir_lower for x in ['util', 'helper', 'common']):
            return 'Utility'
        elif any(x in dir_lower for x in ['test', 'spec']):
            return 'Test'
        elif any(x in dir_lower for x in ['config', 'setting']):
            return 'Configuration'
        elif any(x in dir_lower for x in ['api', 'rest', 'graphql']):
            return 'API'
        elif any(x in dir_lower for x in ['infrastructure', 'infra']):
            return 'Infrastructure'
        else:
            return 'Component'
    
    async def _analyze_dependencies(self, components: List[ArchitecturalComponent]) -> nx.DiGraph:
        """Analisa dependências entre componentes."""
        # Limpa grafo existente
        self.dependency_graph.clear()
        
        # Adiciona nós
        for component in components:
            self.dependency_graph.add_node(
                component.name,
                type=component.type,
                path=component.path,
                metrics=component.metrics
            )
        
        # Adiciona arestas (dependências)
        for component in components:
            for dep in component.dependencies:
                # Tenta encontrar componente correspondente
                for other in components:
                    if other.name != component.name and dep.startswith(other.path):
                        self.dependency_graph.add_edge(
                            component.name,
                            other.name,
                            type='depends_on'
                        )
        
        return self.dependency_graph
    
    async def _calculate_metrics(self, components: List[ArchitecturalComponent], 
                                dependencies: nx.DiGraph) -> Dict[str, Any]:
        """Calcula métricas arquiteturais."""
        metrics = {
            'coupling': {},
            'cohesion': {},
            'complexity': {},
            'modularity': 0,
            'maintainability': 0,
            'testability': 0,
            'scalability': 0
        }
        
        # Métricas de acoplamento
        for node in dependencies.nodes():
            in_degree = dependencies.in_degree(node)
            out_degree = dependencies.out_degree(node)
            
            metrics['coupling'][node] = {
                'afferent': in_degree,  # Componentes que dependem deste
                'efferent': out_degree,  # Componentes dos quais este depende
                'instability': out_degree / (in_degree + out_degree + 1)
            }
        
        # Modularidade (baseada em clustering do grafo)
        if len(dependencies.nodes()) > 0:
            try:
                import networkx.algorithms.community as nx_comm
                communities = list(nx_comm.greedy_modularity_communities(
                    dependencies.to_undirected()
                ))
                metrics['modularity'] = len(communities) / len(dependencies.nodes())
            except:
                metrics['modularity'] = 0.5
        
        # Calcula scores gerais
        avg_coupling = sum(m['instability'] for m in metrics['coupling'].values()) / max(len(metrics['coupling']), 1)
        
        # Maintainability Index simplificado
        metrics['maintainability'] = max(0, min(100, 
            100 - (avg_coupling * 50) - (len(components) / 100)
        ))
        
        # Testability (baseado em presença de testes)
        test_components = [c for c in components if c.type == 'Test']
        metrics['testability'] = min(100, (len(test_components) / max(len(components), 1)) * 200)
        
        # Escalabilidade (baseado em modularidade e acoplamento)
        metrics['scalability'] = max(0, min(100,
            (metrics['modularity'] * 50) + ((1 - avg_coupling) * 50)
        ))
        
        return metrics
    
    async def _identify_issues(self, components: List[ArchitecturalComponent],
                              dependencies: nx.DiGraph,
                              metrics: Dict[str, Any]) -> List[ArchitecturalIssue]:
        """Identifica problemas arquiteturais."""
        issues = []
        
        # 1. Verifica componentes com alto acoplamento
        for node, coupling in metrics['coupling'].items():
            if coupling['efferent'] > 10:
                issues.append(ArchitecturalIssue(
                    type='high_coupling',
                    severity='high',
                    description=f"Component '{node}' has high efferent coupling ({coupling['efferent']} dependencies)",
                    affected_components=[node],
                    suggested_solutions=[
                        "Apply Dependency Inversion Principle",
                        "Extract common interfaces",
                        "Use dependency injection"
                    ],
                    estimated_effort='medium'
                ))
        
        # 2. Detecta dependências circulares
        try:
            cycles = list(nx.simple_cycles(dependencies))
            for cycle in cycles:
                issues.append(ArchitecturalIssue(
                    type='circular_dependency',
                    severity='critical',
                    description=f"Circular dependency detected: {' -> '.join(cycle + [cycle[0]])}",
                    affected_components=cycle,
                    suggested_solutions=[
                        "Extract shared functionality to new component",
                        "Use interfaces to break the cycle",
                        "Apply Dependency Inversion Principle"
                    ],
                    estimated_effort='high'
                ))
        except:
            pass
        
        # 3. Componentes muito grandes
        for component in components:
            if component.metrics.get('file_count', 0) > 50:
                issues.append(ArchitecturalIssue(
                    type='large_component',
                    severity='medium',
                    description=f"Component '{component.name}' is too large ({component.metrics['file_count']} files)",
                    affected_components=[component.name],
                    suggested_solutions=[
                        "Split into smaller, focused components",
                        "Apply Single Responsibility Principle",
                        "Extract sub-modules"
                    ],
                    estimated_effort='high'
                ))
        
        # 4. Falta de testes
        if metrics['testability'] < 30:
            issues.append(ArchitecturalIssue(
                type='low_test_coverage',
                severity='high',
                description="Project has insufficient test coverage",
                affected_components=['all'],
                suggested_solutions=[
                    "Add unit tests for core components",
                    "Implement integration tests",
                    "Set up continuous testing"
                ],
                estimated_effort='high'
            ))
        
        # 5. Baixa modularidade
        if metrics['modularity'] < 0.3:
            issues.append(ArchitecturalIssue(
                type='low_modularity',
                severity='medium',
                description="Project has low modularity, making it hard to maintain and scale",
                affected_components=['architecture'],
                suggested_solutions=[
                    "Identify and extract bounded contexts",
                    "Apply Domain-Driven Design principles",
                    "Create clear module boundaries"
                ],
                estimated_effort='very_high'
            ))
        
        return issues
    
    async def _deep_ai_analysis(self, structure: Dict[str, Any],
                               patterns: List[Dict[str, Any]],
                               issues: List[ArchitecturalIssue]) -> Dict[str, Any]:
        """Análise profunda usando IA."""
        # Prepara contexto para análise
        context = {
            'file_count': structure['total_files'],
            'line_count': structure['total_lines'],
            'main_language': max(structure['languages'].items(), key=lambda x: x[1])[0] if structure['languages'] else 'unknown',
            'detected_patterns': [p['pattern'] for p in patterns],
            'issue_count': len(issues),
            'critical_issues': len([i for i in issues if i.severity == 'critical'])
        }
        
        prompt = f"""
Analyze this software architecture deeply:

Project Context:
- Files: {context['file_count']}
- Lines of code: {context['line_count']}
- Main language: {context['main_language']}
- Detected patterns: {', '.join(context['detected_patterns'])}
- Issues found: {context['issue_count']} ({context['critical_issues']} critical)

Main issues:
{self._format_issues_for_prompt(issues[:5])}

Provide deep architectural insights:
1. Overall architecture assessment
2. Scalability analysis
3. Security considerations
4. Performance implications
5. Recommended architectural improvements
6. Migration path if needed

Be specific and actionable.
"""
        
        try:
            response = await self.gemini.generate_response(
                prompt,
                thinking_budget=24576  # Alta complexidade
            )
            
            # Parse response into structured format
            insights = self._parse_ai_insights(response)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Erro na análise profunda: {e}")
            return {
                'error': str(e),
                'analysis_failed': True
            }
    
    def _format_issues_for_prompt(self, issues: List[ArchitecturalIssue]) -> str:
        """Formata issues para o prompt."""
        formatted = []
        for issue in issues:
            formatted.append(f"- {issue.type} ({issue.severity}): {issue.description}")
        return '\n'.join(formatted)
    
    def _parse_ai_insights(self, response: str) -> Dict[str, Any]:
        """Parse da resposta da IA em formato estruturado."""
        insights = {
            'overall_assessment': '',
            'scalability_analysis': '',
            'security_considerations': '',
            'performance_implications': '',
            'improvements': [],
            'migration_path': '',
            'raw_response': response
        }
        
        # Parse simples baseado em seções
        sections = response.split('\n\n')
        current_section = None
        
        for section in sections:
            section_lower = section.lower()
            
            if 'overall' in section_lower or 'assessment' in section_lower:
                insights['overall_assessment'] = section
            elif 'scalability' in section_lower:
                insights['scalability_analysis'] = section
            elif 'security' in section_lower:
                insights['security_considerations'] = section
            elif 'performance' in section_lower:
                insights['performance_implications'] = section
            elif 'improvement' in section_lower or 'recommend' in section_lower:
                # Extrai lista de melhorias
                lines = section.split('\n')
                for line in lines:
                    if line.strip().startswith(('-', '*', '•', '1.', '2.', '3.')):
                        insights['improvements'].append(line.strip())
            elif 'migration' in section_lower:
                insights['migration_path'] = section
        
        return insights
    
    async def _generate_recommendations(self, patterns: List[Dict[str, Any]],
                                      issues: List[ArchitecturalIssue],
                                      ai_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera recomendações arquiteturais."""
        recommendations = []
        
        # Recomendações baseadas em issues
        issue_priority = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        sorted_issues = sorted(issues, key=lambda x: issue_priority.get(x.severity, 5))
        
        for issue in sorted_issues[:5]:  # Top 5 issues
            for solution in issue.suggested_solutions[:2]:  # Top 2 soluções
                recommendations.append({
                    'type': 'fix_issue',
                    'priority': issue.severity,
                    'title': f"Fix {issue.type}",
                    'description': solution,
                    'effort': issue.estimated_effort,
                    'impact': 'high' if issue.severity in ['critical', 'high'] else 'medium',
                    'components': issue.affected_components
                })
        
        # Recomendações baseadas em padrões
        if not patterns or max(p['confidence'] for p in patterns) < 0.5:
            recommendations.append({
                'type': 'adopt_pattern',
                'priority': 'medium',
                'title': 'Adopt clear architectural pattern',
                'description': 'Consider adopting a well-defined architectural pattern like Clean Architecture or Hexagonal',
                'effort': 'high',
                'impact': 'high',
                'components': ['all']
            })
        
        # Recomendações da IA
        if ai_insights and 'improvements' in ai_insights:
            for improvement in ai_insights['improvements'][:3]:
                recommendations.append({
                    'type': 'ai_suggestion',
                    'priority': 'medium',
                    'title': 'AI-recommended improvement',
                    'description': improvement,
                    'effort': 'medium',
                    'impact': 'medium',
                    'components': ['architecture']
                })
        
        # Remove duplicatas e ordena por prioridade
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = (rec['type'], rec['title'])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _calculate_health_score(self, metrics: Dict[str, Any], 
                               issues: List[ArchitecturalIssue]) -> float:
        """Calcula score de saúde arquitetural (0-100)."""
        score = 100.0
        
        # Penaliza por issues
        issue_penalties = {
            'critical': 15,
            'high': 10,
            'medium': 5,
            'low': 2
        }
        
        for issue in issues:
            penalty = issue_penalties.get(issue.severity, 0)
            score -= penalty
        
        # Considera métricas
        score *= (metrics.get('maintainability', 50) / 100)
        score *= (metrics.get('modularity', 0.5) * 1.5)  # Boost modularidade
        
        # Garante range 0-100
        return max(0, min(100, score))
    
    def _component_to_dict(self, component: ArchitecturalComponent) -> Dict[str, Any]:
        """Converte componente para dict."""
        return {
            'name': component.name,
            'type': component.type,
            'path': component.path,
            'dependencies': component.dependencies,
            'interfaces': component.interfaces,
            'responsibility': component.responsibility,
            'patterns': component.patterns,
            'metrics': component.metrics
        }
    
    def _issue_to_dict(self, issue: ArchitecturalIssue) -> Dict[str, Any]:
        """Converte issue para dict."""
        return {
            'type': issue.type,
            'severity': issue.severity,
            'description': issue.description,
            'affected_components': issue.affected_components,
            'suggested_solutions': issue.suggested_solutions,
            'estimated_effort': issue.estimated_effort
        }
    
    def _graph_to_dict(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Converte grafo para dict."""
        return {
            'nodes': list(graph.nodes()),
            'edges': [(u, v) for u, v in graph.edges()],
            'node_count': graph.number_of_nodes(),
            'edge_count': graph.number_of_edges()
        }
    
    async def suggest_refactoring(self, component_name: str) -> Dict[str, Any]:
        """Sugere refatoração para um componente específico."""
        # Encontra componente
        analysis = self.architecture_cache.get('latest', {})
        components = analysis.get('components', [])
        
        target_component = None
        for comp in components:
            if comp['name'] == component_name:
                target_component = comp
                break
        
        if not target_component:
            return {'error': f'Component {component_name} not found'}
        
        # Analisa problemas específicos do componente
        prompt = f"""
Suggest refactoring for this component:

Component: {component_name}
Type: {target_component['type']}
Path: {target_component['path']}
Dependencies: {len(target_component['dependencies'])}
Responsibility: {target_component['responsibility']}

Provide specific refactoring suggestions:
1. How to reduce coupling
2. How to improve cohesion
3. Specific design patterns to apply
4. Step-by-step refactoring plan

Be practical and specific.
"""
        
        response = await self.gemini.generate_response(prompt, thinking_budget=16384)
        
        return {
            'component': component_name,
            'suggestions': response,
            'current_metrics': target_component.get('metrics', {})
        }
    
    async def visualize_architecture(self) -> Dict[str, Any]:
        """Gera visualização da arquitetura (dados para renderização)."""
        if not self.dependency_graph or self.dependency_graph.number_of_nodes() == 0:
            await self.analyze_architecture(deep_analysis=False)
        
        # Prepara dados para visualização
        visualization = {
            'nodes': [],
            'edges': [],
            'clusters': {},
            'layout': 'hierarchical'
        }
        
        # Adiciona nós com metadados
        for node, data in self.dependency_graph.nodes(data=True):
            visualization['nodes'].append({
                'id': node,
                'label': node,
                'type': data.get('type', 'Component'),
                'metrics': data.get('metrics', {}),
                'color': self._get_node_color(data.get('type', ''))
            })
        
        # Adiciona arestas
        for source, target in self.dependency_graph.edges():
            visualization['edges'].append({
                'source': source,
                'target': target,
                'type': 'depends_on'
            })
        
        # Identifica clusters (componentes relacionados)
        try:
            import networkx.algorithms.community as nx_comm
            communities = nx_comm.greedy_modularity_communities(
                self.dependency_graph.to_undirected()
            )
            
            for i, community in enumerate(communities):
                visualization['clusters'][f'cluster_{i}'] = list(community)
        except:
            pass
        
        return visualization
    
    def _get_node_color(self, node_type: str) -> str:
        """Retorna cor baseada no tipo de nó."""
        color_map = {
            'Model': '#4CAF50',      # Verde
            'View': '#2196F3',       # Azul
            'Controller': '#FF9800', # Laranja
            'Service': '#9C27B0',    # Roxo
            'Repository': '#795548', # Marrom
            'Test': '#607D8B',       # Cinza azulado
            'API': '#F44336',        # Vermelho
            'Utility': '#9E9E9E',    # Cinza
            'Configuration': '#FFEB3B', # Amarelo
            'Infrastructure': '#3F51B5' # Indigo
        }
        
        return color_map.get(node_type, '#757575')  # Cinza padrão
    
    async def generate_architecture_document(self) -> str:
        """Gera documentação arquitetural completa."""
        analysis = self.architecture_cache.get('latest')
        if not analysis:
            analysis = await self.analyze_architecture()
        
        doc = f"""# Architecture Documentation

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

- **Total Files**: {analysis['structure']['total_files']}
- **Total Lines**: {analysis['structure']['total_lines']}
- **Main Language**: {max(analysis['structure']['languages'].items(), key=lambda x: x[1])[0] if analysis['structure']['languages'] else 'N/A'}
- **Health Score**: {analysis['health_score']:.1f}/100

## Detected Patterns

"""
        
        for pattern in analysis['detected_patterns']:
            doc += f"### {pattern['pattern'].title()} (Confidence: {pattern['confidence']:.0%})\n"
            doc += f"{pattern['description']}\n\n"
            doc += "Evidence:\n"
            for evidence in pattern['evidence']:
                doc += f"- {evidence}\n"
            doc += "\n"
        
        doc += """## Components

| Component | Type | Responsibility | Dependencies |
|-----------|------|----------------|--------------|
"""
        
        for comp in analysis['components'][:20]:  # Top 20 componentes
            doc += f"| {comp['name']} | {comp['type']} | {comp['responsibility']} | {len(comp['dependencies'])} |\n"
        
        doc += f"\n## Architectural Issues\n\n"
        
        # Agrupa issues por severidade
        issues_by_severity = {}
        for issue in analysis['issues']:
            severity = issue['severity']
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in issues_by_severity:
                doc += f"### {severity.title()} Priority\n\n"
                for issue in issues_by_severity[severity]:
                    doc += f"**{issue['type']}**: {issue['description']}\n"
                    doc += f"- Affected: {', '.join(issue['affected_components'])}\n"
                    doc += f"- Solutions:\n"
                    for solution in issue['suggested_solutions']:
                        doc += f"  - {solution}\n"
                    doc += "\n"
        
        doc += "## Recommendations\n\n"
        
        for i, rec in enumerate(analysis['recommendations'][:10], 1):
            doc += f"{i}. **{rec['title']}** ({rec['priority']} priority)\n"
            doc += f"   - {rec['description']}\n"
            doc += f"   - Effort: {rec['effort']}, Impact: {rec['impact']}\n
    async def analyze_system_architecture(self, project_path: str) -> Dict[str, Any]:
        """Análise completa da arquitetura do sistema."""
        try:
            analysis = {
                'structure_analysis': await self._analyze_structure(project_path),
                'pattern_detection': await self._detect_patterns(project_path), 
                'quality_metrics': await self._calculate_metrics(project_path),
                'recommendations': await self._generate_recommendations(project_path)
            }
            
            self.logger.info(f"Análise arquitetural concluída para {project_path}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {e}")
            return {'error': str(e)}
    
    async def _analyze_structure(self, project_path: str) -> Dict[str, Any]:
        """Analisa estrutura do projeto."""
        try:
            path_obj = Path(project_path)
            python_files = list(path_obj.rglob("*.py"))
            directories = [d for d in path_obj.iterdir() if d.is_dir()]
            
            return {
                'total_files': len(python_files),
                'total_directories': len(directories),
                'directory_structure': [d.name for d in directories],
                'complexity_estimate': 'high' if len(python_files) > 50 else 'medium' if len(python_files) > 20 else 'low'
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _detect_patterns(self, project_path: str) -> List[str]:
        """Detecta padrões arquiteturais."""
        try:
            path_obj = Path(project_path)
            directories = [d.name.lower() for d in path_obj.iterdir() if d.is_dir()]
            
            patterns = []
            
            # Detecta MVC
            if any(d in directories for d in ['models', 'views', 'controllers']):
                patterns.append('MVC')
            
            # Detecta Layered
            if any(d in directories for d in ['core', 'business', 'data']):
                patterns.append('Layered Architecture')
            
            # Detecta Microservices
            if any('service' in d for d in directories):
                patterns.append('Microservices')
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de padrões: {e}")
            return []
    
    async def _calculate_metrics(self, project_path: str) -> Dict[str, float]:
        """Calcula métricas básicas de qualidade."""
        try:
            python_files = list(Path(project_path).rglob("*.py"))
            if not python_files:
                return {}
            
            total_lines = 0
            total_functions = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = len([line for line in content.split('\n') if line.strip()])
                    functions = content.count('def ')
                    
                    total_lines += lines
                    total_functions += functions
                    
                except Exception:
                    continue
            
            return {
                'avg_lines_per_file': total_lines / len(python_files),
                'avg_functions_per_file': total_functions / len(python_files),
                'total_files': len(python_files),
                'maintainability_score': min(1.0, 50 / max(1, total_lines / len(python_files)))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _generate_recommendations(self, project_path: str) -> List[str]:
        """Gera recomendações de melhoria."""
        try:
            metrics = await self._calculate_metrics(project_path)
            recommendations = []
            
            if metrics.get('avg_lines_per_file', 0) > 200:
                recommendations.append('Considere dividir arquivos grandes em módulos menores')
            
            if metrics.get('avg_functions_per_file', 0) > 20:
                recommendations.append('Muitas funções por arquivo - considere refatoração')
            
            patterns = await self._detect_patterns(project_path)
            if not patterns:
                recommendations.append('Implementar padrões arquiteturais para melhor organização')
            
            recommendations.append('Adicionar testes automatizados para garantir qualidade')
            recommendations.append('Implementar documentação técnica abrangente')
            
            return recommendations
            
        except Exception as e:
            return [f'Erro na geração de recomendações: {e}']

\n\n"
        
        if 'ai_insights' in analysis and analysis['ai_insights'].get('overall_assessment'):
            doc += "## AI Analysis\n\n"
            doc += analysis['ai_insights']['overall_assessment'] + "\n\n"
        
        doc += """## Metrics

| Metric | Value |
|--------|-------|
"""
        
        metrics = analysis['metrics']
        doc += f"| Maintainability | {metrics.get('maintainability', 0):.1f}/100 |\n"
        doc += f"| Modularity | {metrics.get('modularity', 0):.2f} |\n"
        doc += f"| Testability | {metrics.get('testability', 0):.1f}/100 |\n"
        doc += f"| Scalability | {metrics.get('scalability', 0):.1f}/100 |\n"
        
        return doc
    
    async def evaluate_new_component(self, component_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Avalia o impacto de adicionar um novo componente."""
        # Analisa arquitetura atual se necessário
        if not self.architecture_cache.get('latest'):
            await self.analyze_architecture(deep_analysis=False)
        
        current_analysis = self.architecture_cache['latest']
        
        # Simula adição do componente
        evaluation = {
            'component': component_spec,
            'impact_analysis': {},
            'recommendations': [],
            'warnings': [],
            'compatibility_score': 0
        }
        
        # Verifica compatibilidade com padrões existentes
        patterns = current_analysis.get('detected_patterns', [])
        if patterns:
            main_pattern = patterns[0]['pattern']
            
            # Verifica se componente se encaixa no padrão
            prompt = f"""
Evaluate if this new component fits the {main_pattern} architecture:

Component: {component_spec.get('name')}
Type: {component_spec.get('type')}
Purpose: {component_spec.get('purpose')}
Dependencies: {component_spec.get('dependencies', [])}

Current architecture uses {main_pattern} pattern.

Analyze:
1. Does it fit the pattern?
2. Where should it be placed?
3. Potential conflicts?
4. Integration recommendations?

Be specific.
"""
            
            response = await self.gemini.generate_response(prompt)
            evaluation['impact_analysis']['pattern_fit'] = response
        
        # Verifica impacto no acoplamento
        new_dependencies = component_spec.get('dependencies', [])
        if len(new_dependencies) > 5:
            evaluation['warnings'].append(
                f"High coupling warning: new component has {len(new_dependencies)} dependencies"
            )
            evaluation['recommendations'].append(
                "Consider reducing dependencies or using interfaces"
            )
        
        # Calcula score de compatibilidade
        score = 100
        score -= len(evaluation['warnings']) * 10
        score -= max(0, (len(new_dependencies) - 3) * 5)
        
        evaluation['compatibility_score'] = max(0, score)
        
        return evaluation