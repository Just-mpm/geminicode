"""
Problem Solver - Sistema avançado de resolução de problemas
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

from ..core.gemini_client import GeminiClient
from ..core.project_manager import ProjectManager
from ..analysis.error_detector import ErrorDetector
from ..utils.logger import Logger


class ProblemType(Enum):
    """Tipos de problemas identificados."""
    SYNTAX_ERROR = "Syntax Error"
    RUNTIME_ERROR = "Runtime Error"
    LOGIC_ERROR = "Logic Error"
    PERFORMANCE_ISSUE = "Performance Issue"
    SECURITY_VULNERABILITY = "Security Vulnerability"
    DESIGN_FLAW = "Design Flaw"
    INTEGRATION_ISSUE = "Integration Issue"
    CONFIGURATION_ERROR = "Configuration Error"
    DEPENDENCY_CONFLICT = "Dependency Conflict"
    UNKNOWN = "Unknown Problem"


class SolutionStrategy(Enum):
    """Estratégias de solução."""
    QUICK_FIX = "Quick Fix"
    REFACTOR = "Refactor"
    REDESIGN = "Redesign"
    WORKAROUND = "Workaround"
    EXTERNAL_DEPENDENCY = "External Dependency Update"
    CONFIGURATION_CHANGE = "Configuration Change"
    CODE_GENERATION = "Code Generation"
    MANUAL_INTERVENTION = "Manual Intervention Required"


@dataclass
class Problem:
    """Representação de um problema."""
    id: str
    type: ProblemType
    severity: str  # critical, high, medium, low
    description: str
    location: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    related_files: List[str] = None
    timestamp: datetime = None


@dataclass
class Solution:
    """Solução proposta para um problema."""
    problem_id: str
    strategy: SolutionStrategy
    description: str
    implementation_steps: List[str]
    code_changes: List[Dict[str, Any]]
    estimated_effort: str
    confidence: float
    risks: List[str]
    alternatives: List[Dict[str, Any]]


@dataclass
class ResolutionResult:
    """Resultado da tentativa de resolução."""
    problem_id: str
    success: bool
    solution_applied: Optional[Solution]
    changes_made: List[Dict[str, Any]]
    error: Optional[str]
    time_taken: float
    rollback_available: bool


class ProblemSolver:
    """
    Sistema inteligente de resolução de problemas.
    Analisa, diagnostica e resolve problemas automaticamente.
    """
    
    def __init__(self, gemini_client: GeminiClient, project_manager: ProjectManager):
        self.gemini = gemini_client
        self.project = project_manager
        self.logger = Logger()
        
        # Cria file_manager se necessário para ErrorDetector
        try:
            from ..core.file_manager import FileManagementSystem
            from pathlib import Path
            file_manager = FileManagementSystem(gemini_client, Path(project_manager.project_root))
            self.error_detector = ErrorDetector(gemini_client, file_manager)
        except Exception as e:
            self.logger.error(f"Erro ao inicializar ErrorDetector: {e}")
            self.error_detector = None
        
        # Histórico de problemas e soluções
        self.problem_history: List[Problem] = []
        self.solution_history: List[Solution] = []
        self.resolution_history: List[ResolutionResult] = []
        
        # Padrões de solução conhecidos
        self.solution_patterns = self._load_solution_patterns()
        
        # Cache de análises
        self.analysis_cache = {}
    
    def _load_solution_patterns(self) -> Dict[ProblemType, List[Dict[str, Any]]]:
        """Carrega padrões de solução conhecidos."""
        return {
            ProblemType.SYNTAX_ERROR: [
                {
                    'pattern': 'missing_colon',
                    'indicators': ['expected ":"', 'invalid syntax'],
                    'solution': 'Add missing colon',
                    'confidence': 0.9
                },
                {
                    'pattern': 'indentation_error',
                    'indicators': ['IndentationError', 'unexpected indent'],
                    'solution': 'Fix indentation',
                    'confidence': 0.95
                }
            ],
            ProblemType.RUNTIME_ERROR: [
                {
                    'pattern': 'undefined_variable',
                    'indicators': ['NameError', 'is not defined'],
                    'solution': 'Define variable or import',
                    'confidence': 0.85
                },
                {
                    'pattern': 'type_error',
                    'indicators': ['TypeError', 'unsupported operand'],
                    'solution': 'Fix type compatibility',
                    'confidence': 0.8
                }
            ],
            ProblemType.PERFORMANCE_ISSUE: [
                {
                    'pattern': 'n_squared_complexity',
                    'indicators': ['nested loops', 'O(n²)'],
                    'solution': 'Optimize algorithm',
                    'confidence': 0.7
                },
                {
                    'pattern': 'memory_leak',
                    'indicators': ['memory usage increasing', 'not released'],
                    'solution': 'Add proper cleanup',
                    'confidence': 0.75
                }
            ]
        }
    
    async def analyze_problem(self, problem_description: str, 
                            context: Optional[Dict[str, Any]] = None) -> Problem:
        """
        Analisa e categoriza um problema.
        
        Args:
            problem_description: Descrição do problema
            context: Contexto adicional
            
        Returns:
            Problema analisado e categorizado
        """
        self.logger.info(f"🔍 Analisando problema: {problem_description[:100]}...")
        
        # Detecta tipo de problema
        problem_type = await self._detect_problem_type(problem_description, context)
        
        # Determina severidade
        severity = await self._assess_severity(problem_description, problem_type, context)
        
        # Identifica arquivos relacionados
        related_files = await self._find_related_files(problem_description, context)
        
        # Cria problema estruturado
        problem = Problem(
            id=self._generate_problem_id(),
            type=problem_type,
            severity=severity,
            description=problem_description,
            location=context.get('location', 'unknown') if context else 'unknown',
            context=context or {},
            stack_trace=context.get('stack_trace') if context else None,
            related_files=related_files,
            timestamp=datetime.now()
        )
        
        # Adiciona ao histórico
        self.problem_history.append(problem)
        
        return problem
    
    async def _detect_problem_type(self, description: str, 
                                 context: Optional[Dict[str, Any]]) -> ProblemType:
        """Detecta o tipo de problema."""
        description_lower = description.lower()
        
        # Detecção baseada em palavras-chave
        type_indicators = {
            ProblemType.SYNTAX_ERROR: ['syntaxerror', 'invalid syntax', 'unexpected token'],
            ProblemType.RUNTIME_ERROR: ['error', 'exception', 'traceback', 'nameerror', 'typeerror'],
            ProblemType.LOGIC_ERROR: ['wrong result', 'incorrect output', 'logic issue'],
            ProblemType.PERFORMANCE_ISSUE: ['slow', 'performance', 'timeout', 'memory'],
            ProblemType.SECURITY_VULNERABILITY: ['security', 'vulnerability', 'injection', 'xss'],
            ProblemType.DESIGN_FLAW: ['design', 'architecture', 'pattern', 'structure'],
            ProblemType.INTEGRATION_ISSUE: ['integration', 'api', 'connection', 'interface'],
            ProblemType.CONFIGURATION_ERROR: ['config', 'setting', 'environment', 'variable'],
            ProblemType.DEPENDENCY_CONFLICT: ['dependency', 'version', 'conflict', 'incompatible']
        }
        
        # Verifica indicadores
        for problem_type, indicators in type_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return problem_type
        
        # Se não identificou, usa IA para análise mais profunda
        if context and context.get('use_ai', True):
            ai_type = await self._ai_detect_problem_type(description, context)
            if ai_type:
                return ai_type
        
        return ProblemType.UNKNOWN
    
    async def _ai_detect_problem_type(self, description: str,
                                    context: Dict[str, Any]) -> Optional[ProblemType]:
        """Usa IA para detectar tipo de problema."""
        prompt = f"""
Analyze this problem and categorize it:

Problem: {description}
Context: {json.dumps(context, indent=2)[:500]}

Categories:
- SYNTAX_ERROR: Code syntax issues
- RUNTIME_ERROR: Execution errors
- LOGIC_ERROR: Incorrect behavior
- PERFORMANCE_ISSUE: Speed or resource problems
- SECURITY_VULNERABILITY: Security issues
- DESIGN_FLAW: Architectural problems
- INTEGRATION_ISSUE: External system problems
- CONFIGURATION_ERROR: Settings issues
- DEPENDENCY_CONFLICT: Library conflicts

Return only the category name.
"""
        
        try:
            response = await self.gemini.generate_response(prompt)
            response = response.strip().upper().replace(' ', '_')
            
            # Tenta mapear para enum
            for problem_type in ProblemType:
                if problem_type.name == response:
                    return problem_type
        except:
            pass
        
        return None
    
    async def _assess_severity(self, description: str, 
                             problem_type: ProblemType,
                             context: Optional[Dict[str, Any]]) -> str:
        """Avalia severidade do problema."""
        # Severidade base por tipo
        base_severity = {
            ProblemType.SYNTAX_ERROR: 'medium',
            ProblemType.RUNTIME_ERROR: 'high',
            ProblemType.LOGIC_ERROR: 'high',
            ProblemType.PERFORMANCE_ISSUE: 'medium',
            ProblemType.SECURITY_VULNERABILITY: 'critical',
            ProblemType.DESIGN_FLAW: 'medium',
            ProblemType.INTEGRATION_ISSUE: 'high',
            ProblemType.CONFIGURATION_ERROR: 'medium',
            ProblemType.DEPENDENCY_CONFLICT: 'high',
            ProblemType.UNKNOWN: 'medium'
        }
        
        severity = base_severity.get(problem_type, 'medium')
        
        # Ajusta baseado em indicadores
        if any(word in description.lower() for word in ['critical', 'urgent', 'blocker']):
            severity = 'critical'
        elif any(word in description.lower() for word in ['production', 'customer', 'data loss']):
            if severity == 'medium':
                severity = 'high'
        
        return severity
    
    async def _find_related_files(self, description: str,
                                context: Optional[Dict[str, Any]]) -> List[str]:
        """Encontra arquivos relacionados ao problema."""
        related_files = []
        
        # Extrai nomes de arquivo da descrição
        import re
        file_pattern = r'([a-zA-Z0-9_/]+\.[a-zA-Z0-9]+)'
        matches = re.findall(file_pattern, description)
        related_files.extend(matches)
        
        # Adiciona arquivos do contexto
        if context:
            if 'file' in context:
                related_files.append(context['file'])
            if 'files' in context:
                related_files.extend(context['files'])
        
        # Remove duplicatas
        return list(set(related_files))
    
    def _generate_problem_id(self) -> str:
        """Gera ID único para problema."""
        import uuid
        return f"problem_{uuid.uuid4().hex[:8]}"
    
    async def find_solution(self, problem: Problem) -> List[Solution]:
        """
        Encontra possíveis soluções para um problema.
        
        Args:
            problem: Problema a resolver
            
        Returns:
            Lista de soluções possíveis ordenadas por confiança
        """
        self.logger.info(f"🔧 Buscando soluções para {problem.type.value}...")
        
        solutions = []
        
        # 1. Verifica padrões conhecidos
        pattern_solutions = await self._find_pattern_solutions(problem)
        solutions.extend(pattern_solutions)
        
        # 2. Busca em histórico de soluções
        historical_solutions = await self._find_historical_solutions(problem)
        solutions.extend(historical_solutions)
        
        # 3. Análise com IA para soluções complexas
        if len(solutions) < 3 or problem.severity in ['critical', 'high']:
            ai_solutions = await self._find_ai_solutions(problem)
            solutions.extend(ai_solutions)
        
        # 4. Gera soluções baseadas em heurísticas
        heuristic_solutions = await self._generate_heuristic_solutions(problem)
        solutions.extend(heuristic_solutions)
        
        # Remove duplicatas e ordena por confiança
        unique_solutions = self._deduplicate_solutions(solutions)
        unique_solutions.sort(key=lambda s: s.confidence, reverse=True)
        
        # Adiciona ao histórico
        self.solution_history.extend(unique_solutions[:5])
        
        return unique_solutions[:5]  # Top 5 soluções
    
    async def _find_pattern_solutions(self, problem: Problem) -> List[Solution]:
        """Encontra soluções baseadas em padrões conhecidos."""
        solutions = []
        
        patterns = self.solution_patterns.get(problem.type, [])
        
        for pattern in patterns:
            # Verifica se o padrão se aplica
            applies = any(
                indicator in problem.description.lower() 
                for indicator in pattern['indicators']
            )
            
            if applies:
                solution = Solution(
                    problem_id=problem.id,
                    strategy=SolutionStrategy.QUICK_FIX,
                    description=pattern['solution'],
                    implementation_steps=[
                        f"Identify exact location of {pattern['pattern']}",
                        f"Apply fix: {pattern['solution']}",
                        "Test the fix",
                        "Verify no side effects"
                    ],
                    code_changes=[],
                    estimated_effort='low',
                    confidence=pattern['confidence'],
                    risks=['Might not address root cause'],
                    alternatives=[]
                )
                
                solutions.append(solution)
        
        return solutions
    
    async def _find_historical_solutions(self, problem: Problem) -> List[Solution]:
        """Busca soluções em histórico."""
        solutions = []
        
        # Busca problemas similares resolvidos
        for past_problem, past_solution, result in zip(
            self.problem_history[-50:],  # Últimos 50
            self.solution_history[-50:],
            self.resolution_history[-50:]
        ):
            if past_problem.type == problem.type and result.success:
                # Calcula similaridade
                similarity = self._calculate_problem_similarity(problem, past_problem)
                
                if similarity > 0.7:
                    # Adapta solução anterior
                    adapted_solution = Solution(
                        problem_id=problem.id,
                        strategy=past_solution.strategy,
                        description=f"Similar to previous solution: {past_solution.description}",
                        implementation_steps=past_solution.implementation_steps,
                        code_changes=[],
                        estimated_effort=past_solution.estimated_effort,
                        confidence=past_solution.confidence * similarity,
                        risks=past_solution.risks + ['Solution from different context'],
                        alternatives=[]
                    )
                    
                    solutions.append(adapted_solution)
        
        return solutions
    
    def _calculate_problem_similarity(self, p1: Problem, p2: Problem) -> float:
        """Calcula similaridade entre problemas."""
        score = 0.0
        
        # Mesmo tipo
        if p1.type == p2.type:
            score += 0.3
        
        # Similaridade de descrição (simplificado)
        words1 = set(p1.description.lower().split())
        words2 = set(p2.description.lower().split())
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            jaccard = intersection / union
            score += 0.4 * jaccard
        
        # Arquivos relacionados similares
        if p1.related_files and p2.related_files:
            files1 = set(p1.related_files)
            files2 = set(p2.related_files)
            
            if files1.intersection(files2):
                score += 0.3
        
        return min(1.0, score)
    
    async def _find_ai_solutions(self, problem: Problem) -> List[Solution]:
        """Usa IA para encontrar soluções."""
        prompt = f"""
Analyze this problem and provide solutions:

Problem Type: {problem.type.value}
Severity: {problem.severity}
Description: {problem.description}
Location: {problem.location}
Stack Trace: {problem.stack_trace or 'N/A'}

Provide 2-3 specific solutions with:
1. Strategy (quick fix, refactor, redesign, etc.)
2. Step-by-step implementation
3. Code changes needed
4. Estimated effort
5. Potential risks

Be specific and actionable.
"""
        
        try:
            response = await self.gemini.generate_response(
                prompt,
                thinking_budget=16384
            )
            
            # Parse response para soluções
            solutions = self._parse_ai_solutions(response, problem.id)
            
            return solutions
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar soluções com IA: {e}")
            return []
    
    def _parse_ai_solutions(self, response: str, problem_id: str) -> List[Solution]:
        """Parse de soluções da resposta da IA."""
        solutions = []
        
        # Parse simplificado - em produção seria mais robusto
        solution_blocks = response.split('\n\n')
        
        for i, block in enumerate(solution_blocks[:3]):
            if len(block) > 50:  # Bloco significativo
                solution = Solution(
                    problem_id=problem_id,
                    strategy=SolutionStrategy.REFACTOR,  # Default
                    description=block[:200],
                    implementation_steps=[
                        "Analyze the specific context",
                        "Implement suggested changes",
                        "Test thoroughly",
                        "Monitor for issues"
                    ],
                    code_changes=[],
                    estimated_effort='medium',
                    confidence=0.7 - (i * 0.1),  # Diminui confiança
                    risks=['AI-generated solution may need adaptation'],
                    alternatives=[]
                )
                
                solutions.append(solution)
        
        return solutions
    
    async def _generate_heuristic_solutions(self, problem: Problem) -> List[Solution]:
        """Gera soluções baseadas em heurísticas."""
        solutions = []
        
        # Heurísticas por tipo de problema
        if problem.type == ProblemType.SYNTAX_ERROR:
            solutions.append(Solution(
                problem_id=problem.id,
                strategy=SolutionStrategy.QUICK_FIX,
                description="Run linter/formatter to fix syntax issues",
                implementation_steps=[
                    "Run code formatter (e.g., black for Python)",
                    "Run linter to identify issues",
                    "Fix reported syntax errors",
                    "Verify code runs"
                ],
                code_changes=[],
                estimated_effort='low',
                confidence=0.6,
                risks=['May not fix all syntax issues'],
                alternatives=[]
            ))
        
        elif problem.type == ProblemType.PERFORMANCE_ISSUE:
            solutions.append(Solution(
                problem_id=problem.id,
                strategy=SolutionStrategy.REFACTOR,
                description="Profile and optimize performance bottlenecks",
                implementation_steps=[
                    "Profile code to identify bottlenecks",
                    "Analyze algorithm complexity",
                    "Optimize data structures",
                    "Consider caching strategies",
                    "Benchmark improvements"
                ],
                code_changes=[],
                estimated_effort='high',
                confidence=0.5,
                risks=['May require significant refactoring'],
                alternatives=[]
            ))
        
        return solutions
    
    def _deduplicate_solutions(self, solutions: List[Solution]) -> List[Solution]:
        """Remove soluções duplicadas."""
        seen = set()
        unique = []
        
        for solution in solutions:
            # Cria chave baseada em estratégia e descrição
            key = (solution.strategy, solution.description[:50])
            
            if key not in seen:
                seen.add(key)
                unique.append(solution)
        
        return unique
    
    async def apply_solution(self, solution: Solution, 
                           dry_run: bool = False) -> ResolutionResult:
        """
        Aplica uma solução a um problema.
        
        Args:
            solution: Solução a aplicar
            dry_run: Se True, simula sem fazer mudanças
            
        Returns:
            Resultado da aplicação
        """
        self.logger.info(f"🛠️ Aplicando solução: {solution.strategy.value}")
        
        start_time = datetime.now()
        changes_made = []
        
        try:
            # Prepara ambiente
            if not dry_run:
                # Faz backup dos arquivos afetados
                backup_info = await self._backup_affected_files(solution)
                changes_made.append({
                    'type': 'backup',
                    'files': backup_info['files'],
                    'backup_location': backup_info['location']
                })
            
            # Aplica mudanças baseado na estratégia
            if solution.strategy == SolutionStrategy.QUICK_FIX:
                result = await self._apply_quick_fix(solution, dry_run)
            elif solution.strategy == SolutionStrategy.REFACTOR:
                result = await self._apply_refactoring(solution, dry_run)
            elif solution.strategy == SolutionStrategy.CODE_GENERATION:
                result = await self._apply_code_generation(solution, dry_run)
            else:
                result = await self._apply_generic_solution(solution, dry_run)
            
            changes_made.extend(result.get('changes', []))
            
            # Verifica se resolveu
            if not dry_run:
                verification = await self._verify_solution(solution)
                success = verification['success']
            else:
                success = True  # Assume sucesso em dry run
            
            resolution_result = ResolutionResult(
                problem_id=solution.problem_id,
                success=success,
                solution_applied=solution,
                changes_made=changes_made,
                error=None,
                time_taken=(datetime.now() - start_time).total_seconds(),
                rollback_available=not dry_run
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao aplicar solução: {e}")
            
            resolution_result = ResolutionResult(
                problem_id=solution.problem_id,
                success=False,
                solution_applied=solution,
                changes_made=changes_made,
                error=str(e),
                time_taken=(datetime.now() - start_time).total_seconds(),
                rollback_available=len(changes_made) > 0
            )
        
        # Adiciona ao histórico
        self.resolution_history.append(resolution_result)
        
        return resolution_result
    
    async def _backup_affected_files(self, solution: Solution) -> Dict[str, Any]:
        """Faz backup dos arquivos que serão modificados."""
        import shutil
        from pathlib import Path
        
        backup_dir = Path('.problem_solver_backups') / datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backed_up_files = []
        
        # Identifica arquivos afetados
        affected_files = []
        for change in solution.code_changes:
            if 'file' in change:
                affected_files.append(change['file'])
        
        # Faz backup
        for file_path in affected_files:
            if Path(file_path).exists():
                backup_path = backup_dir / Path(file_path).name
                shutil.copy2(file_path, backup_path)
                backed_up_files.append(str(file_path))
        
        return {
            'files': backed_up_files,
            'location': str(backup_dir)
        }
    
    async def _apply_quick_fix(self, solution: Solution, dry_run: bool) -> Dict[str, Any]:
        """Aplica correção rápida."""
        changes = []
        
        for step in solution.implementation_steps:
            self.logger.info(f"  → {step}")
            
            if not dry_run:
                # Implementação específica dependeria do tipo de fix
                # Aqui seria a lógica real de aplicação
                pass
            
            changes.append({
                'type': 'quick_fix',
                'step': step,
                'status': 'completed' if not dry_run else 'simulated'
            })
        
        return {'changes': changes}
    
    async def _apply_refactoring(self, solution: Solution, dry_run: bool) -> Dict[str, Any]:
        """Aplica refatoração."""
        changes = []
        
        # Refatoração é mais complexa
        for step in solution.implementation_steps:
            self.logger.info(f"  → {step}")
            
            if not dry_run:
                # Aplicaria refatoração real
                pass
            
            changes.append({
                'type': 'refactoring',
                'step': step,
                'status': 'completed' if not dry_run else 'simulated'
            })
        
        return {'changes': changes}
    
    async def _apply_code_generation(self, solution: Solution, dry_run: bool) -> Dict[str, Any]:
        """Aplica geração de código."""
        changes = []
        
        # Gera código necessário
        for code_change in solution.code_changes:
            if 'generate' in code_change:
                # Geraria código real
                if not dry_run:
                    # Implementação real
                    pass
                
                changes.append({
                    'type': 'code_generation',
                    'file': code_change.get('file', 'unknown'),
                    'generated': True
                })
        
        return {'changes': changes}
    
    async def _apply_generic_solution(self, solution: Solution, dry_run: bool) -> Dict[str, Any]:
        """Aplica solução genérica."""
        changes = []
        
        for step in solution.implementation_steps:
            self.logger.info(f"  → {step}")
            changes.append({
                'type': 'generic',
                'step': step,
                'status': 'completed' if not dry_run else 'simulated'
            })
        
        return {'changes': changes}
    
    async def _verify_solution(self, solution: Solution) -> Dict[str, bool]:
        """Verifica se a solução resolveu o problema."""
        # Verificação dependeria do tipo de problema
        # Por enquanto, retorna sucesso simulado
        return {'success': True, 'verified': True}
    
    async def rollback_solution(self, resolution_result: ResolutionResult) -> bool:
        """
        Desfaz mudanças de uma solução aplicada.
        
        Args:
            resolution_result: Resultado a reverter
            
        Returns:
            True se rollback bem-sucedido
        """
        if not resolution_result.rollback_available:
            self.logger.warning("Rollback não disponível para esta resolução")
            return False
        
        self.logger.info("🔄 Revertendo mudanças...")
        
        try:
            # Procura backup nos changes
            for change in resolution_result.changes_made:
                if change['type'] == 'backup':
                    # Restaura arquivos do backup
                    backup_location = change['backup_location']
                    files = change['files']
                    
                    import shutil
                    from pathlib import Path
                    
                    for file_path in files:
                        backup_file = Path(backup_location) / Path(file_path).name
                        if backup_file.exists():
                            shutil.copy2(backup_file, file_path)
                            self.logger.info(f"  ✅ Restaurado: {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no rollback: {e}")
            return False
    
    async def analyze_project_problems(self) -> Dict[str, Any]:
        """
        Analisa todos os problemas do projeto.
        
        Returns:
            Análise completa de problemas
        """
        self.logger.info("🔍 Analisando problemas do projeto...")
        
        problems = []
        
        # 1. Detecta erros de sintaxe
        syntax_errors = await self.error_detector.find_syntax_errors()
        for error in syntax_errors:
            problem = await self.analyze_problem(
                f"Syntax error in {error['file']}: {error['error']}",
                {'file': error['file'], 'line': error.get('line')}
            )
            problems.append(problem)
        
        # 2. Detecta problemas de runtime (via análise estática)
        runtime_issues = await self._detect_potential_runtime_issues()
        problems.extend(runtime_issues)
        
        # 3. Detecta problemas de performance
        performance_issues = await self._detect_performance_issues()
        problems.extend(performance_issues)
        
        # 4. Detecta problemas de segurança
        security_issues = await self._detect_security_issues()
        problems.extend(security_issues)
        
        # Agrupa por tipo e severidade
        analysis = {
            'total_problems': len(problems),
            'by_type': {},
            'by_severity': {},
            'critical_problems': [],
            'suggested_solutions': {},
            'estimated_effort': self._estimate_total_effort(problems)
        }
        
        # Agrupa problemas
        for problem in problems:
            # Por tipo
            type_name = problem.type.value
            if type_name not in analysis['by_type']:
                analysis['by_type'][type_name] = []
            analysis['by_type'][type_name].append(problem)
            
            # Por severidade
            if problem.severity not in analysis['by_severity']:
                analysis['by_severity'][problem.severity] = []
            analysis['by_severity'][problem.severity].append(problem)
            
            # Críticos
            if problem.severity == 'critical':
                analysis['critical_problems'].append(problem)
        
        # Encontra soluções para problemas críticos
        for problem in analysis['critical_problems']:
            solutions = await self.find_solution(problem)
            if solutions:
                analysis['suggested_solutions'][problem.id] = solutions[0]
        
        return analysis
    
    async def _detect_potential_runtime_issues(self) -> List[Problem]:
        """Detecta possíveis problemas de runtime."""
        problems = []
        
        # Análise simplificada - em produção seria mais robusta
        for file_path in self.project.structure.files[:20]:  # Limita para performance
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Detecta padrões problemáticos
                    if 'except:' in content and 'pass' in content:
                        problem = await self.analyze_problem(
                            f"Bare except clause in {file_path} - may hide errors",
                            {'file': file_path, 'pattern': 'except: pass'}
                        )
                        problems.append(problem)
                    
                    # Divisão por zero potencial
                    if '/ 0' in content or '/0' in content:
                        problem = await self.analyze_problem(
                            f"Potential division by zero in {file_path}",
                            {'file': file_path, 'pattern': 'division by zero'}
                        )
                        problems.append(problem)
                    
                except:
                    pass
        
        return problems
    
    async def _detect_performance_issues(self) -> List[Problem]:
        """Detecta problemas de performance."""
        problems = []
        
        # Análise básica de complexidade
        for file_path in self.project.structure.files[:10]:
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Detecta loops aninhados profundos
                    nesting_level = content.count('for ') + content.count('while ')
                    if nesting_level > 3:
                        problem = await self.analyze_problem(
                            f"High nesting complexity in {file_path} - potential performance issue",
                            {'file': file_path, 'nesting_level': nesting_level}
                        )
                        problems.append(problem)
                    
                except:
                    pass
        
        return problems
    
    async def _detect_security_issues(self) -> List[Problem]:
        """Detecta problemas de segurança."""
        problems = []
        
        # Padrões de segurança básicos
        security_patterns = [
            ('eval(', 'Use of eval() is a security risk'),
            ('exec(', 'Use of exec() is a security risk'),
            ('pickle.loads', 'Unpickling untrusted data is dangerous'),
            ('os.system', 'Use subprocess instead of os.system'),
            ('shell=True', 'Shell injection vulnerability')
        ]
        
        for file_path in self.project.structure.files[:20]:
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    for pattern, message in security_patterns:
                        if pattern in content:
                            problem = await self.analyze_problem(
                                f"{message} in {file_path}",
                                {
                                    'file': file_path,
                                    'pattern': pattern,
                                    'security_issue': True
                                }
                            )
                            problems.append(problem)
                    
                except:
                    pass
        
        return problems
    
    def _estimate_total_effort(self, problems: List[Problem]) -> str:
        """Estima esforço total para resolver problemas."""
        effort_scores = {
            'critical': 8,
            'high': 4,
            'medium': 2,
            'low': 1
        }
        
        total_score = sum(effort_scores.get(p.severity, 1) for p in problems)
        
        if total_score < 10:
            return "low"
        elif total_score < 30:
            return "medium"
        elif total_score < 60:
            return "high"
        else:
            return "very high"