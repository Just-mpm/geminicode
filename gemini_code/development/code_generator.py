"""
Gerador de código inteligente usando IA.
"""

import re
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem


@dataclass
class CodeTemplate:
    """Template de código."""
    name: str
    description: str
    template: str
    variables: List[str]


class CodeGenerator:
    """Gera código automaticamente usando IA."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Carrega templates de código."""
        return {
            'class': CodeTemplate(
                'class',
                'Classe Python básica',
                '''class {class_name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}''',
                ['class_name', 'description', 'init_params', 'init_body', 'methods']
            ),
            'function': CodeTemplate(
                'function',
                'Função Python',
                '''def {function_name}({parameters}){return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {body}''',
                ['function_name', 'parameters', 'return_type', 'description', 'args_doc', 'return_doc', 'body']
            ),
            'api_endpoint': CodeTemplate(
                'api_endpoint',
                'Endpoint de API Flask/FastAPI',
                '''@app.{method}('{route}')
def {function_name}({parameters}):
    """
    {description}
    """
    try:
        {body}
        return jsonify({success_response})
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500''',
                ['method', 'route', 'function_name', 'parameters', 'description', 'body', 'success_response']
            )
        }
    
    async def generate_code(self, description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Gera código baseado em descrição natural."""
        try:
            # Prepara contexto
            context_str = ""
            if context:
                if 'file_path' in context:
                    try:
                        with open(context['file_path'], 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        context_str = f"\nContexto do arquivo existente:\n```python\n{file_content[:2000]}\n```"
                    except:
                        pass
                
                if 'project_structure' in context:
                    context_str += f"\nEstrutura do projeto: {context['project_structure']}"
            
            prompt = f"""
            Gere código Python baseado nesta descrição:

            Descrição: {description}
            {context_str}

            Considere:
            - Boas práticas de Python
            - Docstrings adequadas
            - Tratamento de erros
            - Tipagem quando apropriado
            - Código limpo e legível

            Retorne apenas o código, sem explicações adicionais.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            # Se não há markdown, assume que toda resposta é código
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar código: {str(e)}"
    
    async def generate_class(self, class_name: str, description: str, 
                           attributes: List[str], methods: List[str]) -> str:
        """Gera uma classe completa."""
        try:
            prompt = f"""
            Gere uma classe Python completa:

            Nome: {class_name}
            Descrição: {description}
            Atributos necessários: {', '.join(attributes) if attributes else 'Nenhum específico'}
            Métodos necessários: {', '.join(methods) if methods else 'Métodos básicos'}

            Inclua:
            - __init__ method apropriado
            - Docstrings detalhadas
            - Métodos especiais se necessário (__str__, __repr__, etc.)
            - Tipagem com type hints
            - Tratamento de erros

            Retorne apenas o código da classe.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar classe: {str(e)}"
    
    async def generate_function(self, function_name: str, description: str,
                              parameters: List[Dict[str, str]], return_type: str = None) -> str:
        """Gera uma função completa."""
        try:
            # Prepara informações dos parâmetros
            params_info = ""
            for param in parameters:
                params_info += f"- {param['name']}: {param.get('type', 'Any')} - {param.get('description', '')}\n"
            
            prompt = f"""
            Gere uma função Python completa:

            Nome: {function_name}
            Descrição: {description}
            
            Parâmetros:
            {params_info}
            
            Tipo de retorno: {return_type or 'A definir baseado na lógica'}

            Inclua:
            - Docstring com Args e Returns
            - Type hints
            - Tratamento de erros apropriado
            - Implementação funcional
            - Validação de entrada se necessário

            Retorne apenas o código da função.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar função: {str(e)}"
    
    async def generate_api_endpoint(self, route: str, method: str, description: str,
                                  framework: str = 'flask') -> str:
        """Gera endpoint de API."""
        try:
            prompt = f"""
            Gere um endpoint de API {framework.title()}:

            Rota: {route}
            Método HTTP: {method.upper()}
            Descrição: {description}
            Framework: {framework}

            Inclua:
            - Decorador apropriado
            - Validação de entrada
            - Tratamento de erros
            - Resposta JSON adequada
            - Status codes apropriados
            - Documentação

            Retorne apenas o código do endpoint.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar endpoint: {str(e)}"
    
    async def generate_tests(self, code: str, test_framework: str = 'pytest') -> str:
        """Gera testes para código fornecido."""
        try:
            prompt = f"""
            Gere testes completos para este código Python usando {test_framework}:

            Código:
            ```python
            {code}
            ```

            Inclua:
            - Testes para casos normais
            - Testes para casos extremos
            - Testes para tratamento de erros
            - Mocks se necessário
            - Fixtures apropriadas
            - Cobertura abrangente

            Retorne apenas o código dos testes.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar testes: {str(e)}"
    
    async def complete_code(self, partial_code: str, cursor_position: int) -> List[str]:
        """Completa código baseado na posição do cursor."""
        try:
            # Divide código na posição do cursor
            before_cursor = partial_code[:cursor_position]
            after_cursor = partial_code[cursor_position:]
            
            prompt = f"""
            Complete este código Python na posição indicada:

            Antes do cursor:
            ```python
            {before_cursor}
            ```

            Depois do cursor:
            ```python
            {after_cursor}
            ```

            Forneça 3-5 sugestões de completação que façam sentido no contexto.
            Retorne apenas as sugestões, uma por linha.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai sugestões
            suggestions = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('```'):
                    suggestions.append(line)
            
            return suggestions[:5]  # Máximo 5 sugestões
            
        except Exception as e:
            return [f"# Erro ao completar código: {str(e)}"]
    
    async def generate_documentation(self, code: str, doc_type: str = 'docstring') -> str:
        """Gera documentação para código."""
        try:
            prompt = f"""
            Gere documentação {doc_type} para este código Python:

            ```python
            {code}
            ```

            Se for docstring:
            - Use formato Google/Sphinx
            - Inclua Args, Returns, Raises
            - Seja descritivo mas conciso

            Se for README:
            - Inclua instalação, uso, exemplos
            - Formato Markdown

            Retorne apenas a documentação.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao gerar documentação: {str(e)}"
    
    async def refactor_code(self, code: str, refactor_type: str) -> str:
        """Refatora código existente."""
        try:
            prompt = f"""
            Refatore este código Python aplicando: {refactor_type}

            Código original:
            ```python
            {code}
            ```

            Tipos de refatoração possíveis:
            - extract_method: Extrair método
            - rename_variable: Renomear variáveis
            - improve_readability: Melhorar legibilidade
            - optimize_performance: Otimizar performance
            - add_error_handling: Adicionar tratamento de erro
            - add_type_hints: Adicionar type hints

            Retorne o código refatorado mantendo a funcionalidade.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Extrai código da resposta
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            return response.strip()
            
        except Exception as e:
            return f"# Erro ao refatorar código: {str(e)}"
    
    async def explain_code(self, code: str) -> str:
        """Explica código de forma simples."""
        try:
            prompt = f"""
            Explique este código Python de forma simples e clara:

            ```python
            {code}
            ```

            Explique:
            1. O que o código faz
            2. Como funciona (passo a passo)
            3. Conceitos importantes utilizados
            4. Possíveis melhorias

            Use linguagem simples em português.
            """
            
            explanation = await self.gemini_client.generate_response(prompt)
            return explanation.strip()
            
        except Exception as e:
            return f"Erro ao explicar código: {str(e)}"