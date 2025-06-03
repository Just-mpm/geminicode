"""
Navegador de código que ajuda a entender e explorar projetos.
"""

import ast
import re
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem


@dataclass
class CodeElement:
    """Representa um elemento do código (função, classe, etc.)."""
    name: str
    type: str  # 'function', 'class', 'method', 'variable', 'import'
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    complexity: int = 0
    dependencies: List[str] = None


@dataclass
class CodeRelationship:
    """Representa uma relação entre elementos de código."""
    source: str
    target: str
    relationship_type: str  # 'calls', 'inherits', 'imports', 'uses'
    file_path: str
    line_number: int


class CodeNavigator:
    """Navega e analisa estrutura de código."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.code_map: Dict[str, List[CodeElement]] = {}
        self.relationships: List[CodeRelationship] = []
    
    async def map_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Mapeia estrutura completa do projeto."""
        self.code_map.clear()
        self.relationships.clear()
        
        # Analisa todos os arquivos Python
        python_files = list(Path(project_path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                await self._analyze_file(file_path)
            except Exception as e:
                print(f"Erro ao analisar {file_path}: {e}")
        
        # Gera mapa estrutural
        structure_map = {
            'files': len(python_files),
            'elements': sum(len(elements) for elements in self.code_map.values()),
            'relationships': len(self.relationships),
            'modules': self._get_module_info(),
            'classes': self._get_class_hierarchy(),
            'functions': self._get_function_map(),
            'imports': self._get_import_graph()
        }
        
        return structure_map
    
    async def _analyze_file(self, file_path: Path) -> None:
        """Analisa um arquivo específico."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extrai elementos
            elements = []
            visitor = CodeVisitor()
            visitor.visit(tree)
            
            for node_info in visitor.elements:
                element = CodeElement(
                    name=node_info['name'],
                    type=node_info['type'],
                    file_path=str(file_path),
                    line_number=node_info['line'],
                    docstring=node_info.get('docstring'),
                    parameters=node_info.get('parameters'),
                    return_type=node_info.get('return_type'),
                    complexity=node_info.get('complexity', 0)
                )
                elements.append(element)
            
            # Extrai relacionamentos
            for rel_info in visitor.relationships:
                relationship = CodeRelationship(
                    source=rel_info['source'],
                    target=rel_info['target'],
                    relationship_type=rel_info['type'],
                    file_path=str(file_path),
                    line_number=rel_info['line']
                )
                self.relationships.append(relationship)
            
            self.code_map[str(file_path)] = elements
            
        except Exception as e:
            print(f"Erro ao analisar arquivo {file_path}: {e}")
    
    def _get_module_info(self) -> Dict[str, Any]:
        """Obtém informações sobre módulos."""
        modules = {}
        
        for file_path, elements in self.code_map.items():
            module_name = Path(file_path).stem
            
            classes = [e for e in elements if e.type == 'class']
            functions = [e for e in elements if e.type == 'function']
            
            modules[module_name] = {
                'file_path': file_path,
                'classes': len(classes),
                'functions': len(functions),
                'total_elements': len(elements),
                'complexity': sum(e.complexity for e in elements)
            }
        
        return modules
    
    def _get_class_hierarchy(self) -> Dict[str, Any]:
        """Obtém hierarquia de classes."""
        classes = {}
        
        for elements in self.code_map.values():
            for element in elements:
                if element.type == 'class':
                    # Encontra herança
                    inherits_from = []
                    for rel in self.relationships:
                        if rel.source == element.name and rel.relationship_type == 'inherits':
                            inherits_from.append(rel.target)
                    
                    classes[element.name] = {
                        'file_path': element.file_path,
                        'line_number': element.line_number,
                        'inherits_from': inherits_from,
                        'docstring': element.docstring
                    }
        
        return classes
    
    def _get_function_map(self) -> Dict[str, Any]:
        """Obtém mapeamento de funções."""
        functions = {}
        
        for elements in self.code_map.values():
            for element in elements:
                if element.type in ['function', 'method']:
                    # Encontra chamadas
                    calls = []
                    for rel in self.relationships:
                        if rel.source == element.name and rel.relationship_type == 'calls':
                            calls.append(rel.target)
                    
                    functions[element.name] = {
                        'file_path': element.file_path,
                        'line_number': element.line_number,
                        'parameters': element.parameters or [],
                        'return_type': element.return_type,
                        'complexity': element.complexity,
                        'calls': calls,
                        'docstring': element.docstring
                    }
        
        return functions
    
    def _get_import_graph(self) -> Dict[str, List[str]]:
        """Obtém grafo de importações."""
        imports = defaultdict(list)
        
        for rel in self.relationships:
            if rel.relationship_type == 'imports':
                file_name = Path(rel.file_path).stem
                imports[file_name].append(rel.target)
        
        return dict(imports)
    
    async def find_element(self, query: str) -> List[CodeElement]:
        """Encontra elementos por nome ou padrão."""
        results = []
        
        for elements in self.code_map.values():
            for element in elements:
                # Busca exata
                if element.name.lower() == query.lower():
                    results.append(element)
                # Busca por padrão
                elif re.search(query, element.name, re.IGNORECASE):
                    results.append(element)
                # Busca na docstring
                elif element.docstring and re.search(query, element.docstring, re.IGNORECASE):
                    results.append(element)
        
        return results
    
    async def trace_function_calls(self, function_name: str) -> Dict[str, Any]:
        """Rastreia chamadas de uma função."""
        # Encontra a função
        function = None
        for elements in self.code_map.values():
            for element in elements:
                if element.name == function_name and element.type in ['function', 'method']:
                    function = element
                    break
        
        if not function:
            return {'error': f'Função {function_name} não encontrada'}
        
        # Encontra o que esta função chama
        calls = []
        called_by = []
        
        for rel in self.relationships:
            if rel.source == function_name and rel.relationship_type == 'calls':
                calls.append({
                    'target': rel.target,
                    'file': rel.file_path,
                    'line': rel.line_number
                })
            elif rel.target == function_name and rel.relationship_type == 'calls':
                called_by.append({
                    'source': rel.source,
                    'file': rel.file_path,
                    'line': rel.line_number
                })
        
        return {
            'function': {
                'name': function.name,
                'file': function.file_path,
                'line': function.line_number,
                'parameters': function.parameters,
                'complexity': function.complexity
            },
            'calls': calls,
            'called_by': called_by
        }
    
    async def get_code_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Obtém dependências de um arquivo."""
        dependencies = {
            'imports': [],
            'internal_calls': [],
            'external_calls': [],
            'classes_used': [],
            'functions_defined': []
        }
        
        if file_path not in self.code_map:
            return dependencies
        
        elements = self.code_map[file_path]
        
        # Elementos definidos no arquivo
        for element in elements:
            if element.type == 'function':
                dependencies['functions_defined'].append(element.name)
        
        # Relacionamentos do arquivo
        for rel in self.relationships:
            if rel.file_path == file_path:
                if rel.relationship_type == 'imports':
                    dependencies['imports'].append(rel.target)
                elif rel.relationship_type == 'calls':
                    # Verifica se é chamada interna ou externa
                    is_internal = any(
                        rel.target == elem.name 
                        for elem in elements
                    )
                    
                    if is_internal:
                        dependencies['internal_calls'].append(rel.target)
                    else:
                        dependencies['external_calls'].append(rel.target)
        
        return dependencies
    
    async def explain_code_section(self, file_path: str, start_line: int, end_line: int) -> str:
        """Explica uma seção específica do código usando IA."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extrai seção
            section = ''.join(lines[start_line-1:end_line])
            
            # Obtém contexto (classes e funções no arquivo)
            context = []
            if file_path in self.code_map:
                for element in self.code_map[file_path]:
                    if element.type in ['class', 'function']:
                        context.append(f"{element.type} {element.name}")
            
            prompt = f"""
            Explique esta seção de código Python de forma simples e clara:

            Arquivo: {Path(file_path).name}
            Linhas: {start_line}-{end_line}

            Contexto do arquivo:
            {chr(10).join(context)}

            Código:
            ```python
            {section}
            ```

            Explique:
            1. O que este código faz
            2. Como funciona
            3. Quais variáveis/funções importantes
            4. Se há algo que pode ser melhorado

            Use linguagem simples em português.
            """
            
            explanation = await self.gemini_client.generate_response(prompt)
            return explanation
            
        except Exception as e:
            return f"Erro ao explicar código: {e}"
    
    async def find_similar_code(self, code_snippet: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Encontra código similar no projeto."""
        similar_sections = []
        
        try:
            # Usa IA para encontrar semelhanças
            for file_path, elements in self.code_map.items():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Análise com IA (simplificada para demonstração)
                if len(content) < 20000:  # Evita arquivos muito grandes
                    prompt = f"""
                    Compare este trecho de código com o arquivo completo e encontre seções similares:

                    Trecho de referência:
                    ```python
                    {code_snippet}
                    ```

                    Arquivo completo:
                    ```python
                    {content}
                    ```

                    Retorne seções similares em JSON:
                    [
                      {{
                        "similarity_score": 0.8,
                        "start_line": 10,
                        "end_line": 20,
                        "description": "descrição da similaridade"
                      }}
                    ]

                    Apenas se similaridade > {threshold}
                    """
                    
                    response = await self.gemini_client.generate_response(prompt)
                    
                    # Extrai JSON (simplificado)
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        matches = json.loads(json_match.group())
                        for match in matches:
                            match['file_path'] = file_path
                            similar_sections.append(match)
                            
        except Exception as e:
            print(f"Erro ao buscar código similar: {e}")
        
        return sorted(similar_sections, key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    async def get_project_overview(self) -> str:
        """Gera visão geral do projeto."""
        if not self.code_map:
            return "Projeto não foi mapeado ainda. Execute map_project_structure() primeiro."
        
        total_files = len(self.code_map)
        total_elements = sum(len(elements) for elements in self.code_map.values())
        
        # Conta tipos de elementos
        classes = sum(1 for elements in self.code_map.values() 
                     for element in elements if element.type == 'class')
        functions = sum(1 for elements in self.code_map.values() 
                       for element in elements if element.type == 'function')
        
        # Complexidade média
        total_complexity = sum(element.complexity for elements in self.code_map.values() 
                              for element in elements)
        avg_complexity = total_complexity / max(total_elements, 1)
        
        # Top arquivos por complexidade
        file_complexity = {}
        for file_path, elements in self.code_map.items():
            file_complexity[file_path] = sum(e.complexity for e in elements)
        
        top_complex = sorted(file_complexity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        overview = f"""🗺️ **Visão Geral do Projeto**

📊 **Estatísticas:**
- Arquivos Python: {total_files}
- Total de elementos: {total_elements}
- Classes: {classes}
- Funções: {functions}
- Relacionamentos: {len(self.relationships)}
- Complexidade média: {avg_complexity:.1f}

🏗️ **Arquivos mais complexos:**"""
        
        for file_path, complexity in top_complex:
            file_name = Path(file_path).name
            overview += f"\n- {file_name}: {complexity} pontos"
        
        # Importações mais usadas
        import_count = defaultdict(int)
        for rel in self.relationships:
            if rel.relationship_type == 'imports':
                import_count[rel.target] += 1
        
        top_imports = sorted(import_count.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if top_imports:
            overview += "\n\n📦 **Imports mais usados:**"
            for import_name, count in top_imports:
                overview += f"\n- {import_name}: {count}x"
        
        return overview


class CodeVisitor(ast.NodeVisitor):
    """Visitor para extrair elementos e relacionamentos do AST."""
    
    def __init__(self):
        self.elements = []
        self.relationships = []
        self.current_class = None
    
    def visit_ClassDef(self, node):
        """Visita definições de classe."""
        self.current_class = node.name
        
        # Adiciona classe
        self.elements.append({
            'name': node.name,
            'type': 'class',
            'line': node.lineno,
            'docstring': ast.get_docstring(node),
            'complexity': self._calculate_complexity(node)
        })
        
        # Adiciona herança
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.relationships.append({
                    'source': node.name,
                    'target': base.id,
                    'type': 'inherits',
                    'line': node.lineno
                })
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Visita definições de função."""
        function_type = 'method' if self.current_class else 'function'
        
        # Extrai parâmetros
        parameters = [arg.arg for arg in node.args.args]
        
        # Extrai tipo de retorno
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        self.elements.append({
            'name': node.name,
            'type': function_type,
            'line': node.lineno,
            'docstring': ast.get_docstring(node),
            'parameters': parameters,
            'return_type': return_type,
            'complexity': self._calculate_complexity(node)
        })
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Visita chamadas de função."""
        if isinstance(node.func, ast.Name):
            # Encontra função que está fazendo a chamada
            current_function = getattr(self, '_current_function', None)
            if current_function:
                self.relationships.append({
                    'source': current_function,
                    'target': node.func.id,
                    'type': 'calls',
                    'line': node.lineno
                })
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Visita imports."""
        for alias in node.names:
            self.relationships.append({
                'source': 'module',
                'target': alias.name,
                'type': 'imports',
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visita imports from."""
        module = node.module or 'local'
        for alias in node.names:
            import_name = f"{module}.{alias.name}" if module != 'local' else alias.name
            self.relationships.append({
                'source': 'module',
                'target': import_name,
                'type': 'imports',
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def _calculate_complexity(self, node):
        """Calcula complexidade ciclomática de um nó."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity