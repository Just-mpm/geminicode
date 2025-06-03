"""
Cliente otimizado para API do Gemini
"""
import os
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
import json
import time
from pathlib import Path

# Importação condicional do Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerateContentResponse
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GenerateContentResponse = None
    GENAI_AVAILABLE = False
    print("⚠️ ERRO: google-generativeai não está instalado!")
    print("📦 Instale com: pip install google-generativeai")

from .config import ConfigManager, Config


@dataclass
class ThinkingBudget:
    """Gerencia o budget de thinking tokens"""
    default: int = 8192
    maximum: int = 24576
    current: int = 0
    
    def adjust_for_complexity(self, task_complexity: str) -> int:
        """Ajusta budget baseado na complexidade"""
        complexity_map = {
            "simple": 2048,
            "medium": 8192,
            "complex": 16384,
            "very_complex": 24576
        }
        return complexity_map.get(task_complexity, self.default)


class GeminiClient:
    """Cliente otimizado para Gemini 2.5 Flash"""
    
    def __init__(self, api_key: Optional[str] = None, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.config
        self.model = None
        self.thinking_budget = ThinkingBudget(
            default=self.config.model.thinking_budget_default,
            maximum=self.config.model.thinking_budget_max
        )
        
        # Usa api_key fornecida ou do config
        if api_key:
            self._api_key = api_key
        else:
            self._api_key = self.config_manager.get_api_key()
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializa modelo Gemini"""
        if not GENAI_AVAILABLE:
            print("⚠️ Google Generative AI não disponível - modo simulação ativado")
            self.model = None
            return
        
        api_key = self._api_key
        
        if not api_key:
            raise ValueError(
                "🔑 API Key do Gemini não encontrada!\n"
                "Configure usando:\n"
                "  export GEMINI_API_KEY='sua-chave'\n"
                "ou\n"
                "  gemini-code set-key"
            )
        
        try:
            genai.configure(api_key=api_key)
            # Valida se a API key é válida tentando listar modelos
            list(genai.list_models())
        except Exception as e:
            print(f"⚠️ Erro ao configurar Gemini (chave inválida?): {e}")
            self.model = None
            return
        
        # Configuração do modelo com thinking
        generation_config = {
            "temperature": self.config.model.temperature,
            "max_output_tokens": self.config.model.max_output_tokens,
            "response_mime_type": "text/plain",
        }
        
        # Sistema de segurança
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        self.model = genai.GenerativeModel(
            model_name=self.config.model.name,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
    
    def _detect_complexity(self, prompt: str) -> str:
        """Detecta complexidade da tarefa"""
        # Análise simples baseada em palavras-chave
        complex_keywords = [
            "sistema completo", "arquitetura", "refatorar tudo",
            "análise profunda", "otimização", "debug complexo",
            "múltiplos arquivos", "integração", "deploy"
        ]
        
        medium_keywords = [
            "criar função", "adicionar feature", "corrigir bug",
            "implementar", "modificar", "atualizar"
        ]
        
        prompt_lower = prompt.lower()
        
        # Conta keywords
        complex_count = sum(1 for kw in complex_keywords if kw in prompt_lower)
        medium_count = sum(1 for kw in medium_keywords if kw in prompt_lower)
        
        if complex_count >= 2:
            return "very_complex"
        elif complex_count >= 1 or medium_count >= 3:
            return "complex"
        elif medium_count >= 1:
            return "medium"
        else:
            return "simple"
    
    async def generate_response(
        self, 
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        thinking_budget: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """Gera resposta usando Gemini"""
        
        # Verifica se modelo está disponível
        if not GENAI_AVAILABLE or self.model is None:
            return self._simulate_response(prompt)
        
        # Detecta complexidade e ajusta thinking
        if thinking_budget is None:
            complexity = self._detect_complexity(prompt)
            thinking_budget = self.thinking_budget.adjust_for_complexity(complexity)
        
        # Constrói prompt completo
        full_prompt = self._build_prompt(prompt, context, thinking_budget)
        
        try:
            if stream:
                return await self._generate_streaming(full_prompt)
            else:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt
                )
                return response.text
                
        except Exception as e:
            return f"❌ Erro ao gerar resposta: {str(e)}"
    
    def _simulate_response(self, prompt: str) -> str:
        """Simula resposta quando Gemini não está disponível."""
        return f"""🤖 [MODO SIMULAÇÃO - Instale google-generativeai para funcionalidade completa]

Para sua solicitação: "{prompt[:100]}..."

💡 Resposta simulada:
Entendo sua solicitação. Para que eu possa processar adequadamente sua solicitação, você precisa:

1. Instalar a biblioteca do Google Generative AI:
   pip install google-generativeai

2. Configurar sua API key:
   export GEMINI_API_KEY="sua_chave_aqui"

3. Obter uma chave API gratuita em:
   https://makersuite.google.com/app/apikey

Após a instalação, eu poderei processar sua solicitação adequadamente.
"""
    
    def _build_prompt(
        self, 
        prompt: str, 
        context: Optional[List[Dict[str, str]]] = None,
        thinking_budget: int = 8192
    ) -> str:
        """Constrói prompt com contexto e instruções"""
        
        # Instruções base para modo non-programmer
        if self.config.user.mode == "non-programmer":
            system_instructions = """
Você é o Gemini Code, um assistente de desenvolvimento que:
- Responde SEMPRE em português brasileiro
- Usa linguagem simples e clara, sem jargões técnicos
- Explica tudo de forma que não-programadores entendam
- Executa comandos automaticamente sem pedir confirmação
- Corrige erros sozinho
- Mostra progresso visual com emojis
- Faz perguntas apenas quando essencial

IMPORTANTE:
- Trabalhe DENTRO do projeto existente
- Modifique arquivos reais
- Mantenha contexto de conversas anteriores
- Seja proativo em correções
"""
        else:
            system_instructions = """
Você é o Gemini Code, um assistente de desenvolvimento avançado.
Responda de forma técnica e precisa, assumindo conhecimento de programação.
"""
        
        # Monta prompt completo
        parts = [system_instructions]
        
        # Adiciona contexto se existir
        if context:
            parts.append("\n## Contexto anterior:")
            for msg in context[-10:]:  # Últimas 10 mensagens
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                parts.append(f"{role}: {content}")
        
        # Adiciona thinking budget
        parts.append(f"\n<thinking_mode budget={thinking_budget}>")
        parts.append("Analise cuidadosamente antes de responder.")
        parts.append("</thinking_mode>")
        
        # Adiciona prompt do usuário
        parts.append(f"\nUsuário: {prompt}")
        
        return "\n".join(parts)
    
    async def _generate_streaming(self, prompt: str) -> AsyncGenerator[str, None]:
        """Gera resposta em streaming"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"❌ Erro no streaming: {str(e)}"
    
    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        task: str = "analyze"
    ) -> Dict[str, Any]:
        """Analisa código e retorna insights"""
        
        analysis_prompt = f"""
Analise o seguinte código {language}:

```{language}
{code}
```

Tarefa: {task}

Retorne a análise em formato JSON com:
- summary: resumo do que o código faz
- issues: lista de problemas encontrados
- suggestions: lista de sugestões de melhoria
- complexity: simple/medium/complex
"""
        
        response = await self.generate_response(analysis_prompt)
        
        # Tenta extrair JSON da resposta
        try:
            # Procura por JSON na resposta
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback para formato estruturado
        return {
            "summary": "Análise em processamento",
            "issues": [],
            "suggestions": [],
            "complexity": "medium",
            "raw_response": response
        }
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context_files: Optional[List[str]] = None
    ) -> str:
        """Gera código baseado em descrição"""
        
        prompt = f"""
Gere código {language} para: {description}

Requisitos:
- Código limpo e bem estruturado
- Seguir convenções da linguagem
- Incluir tratamento de erros
- Sem comentários desnecessários
"""
        
        if context_files:
            prompt += f"\nArquivos de contexto: {', '.join(context_files)}"
        
        response = await self.generate_response(
            prompt,
            thinking_budget=self.thinking_budget.adjust_for_complexity("complex")
        )
        
        # Extrai código da resposta
        code_blocks = self._extract_code_blocks(response)
        return code_blocks[0] if code_blocks else response
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extrai blocos de código da resposta"""
        import re
        
        # Procura por code blocks
        pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        return matches
    
    async def fix_error(
        self,
        error_message: str,
        code_context: str,
        file_path: str
    ) -> Dict[str, Any]:
        """Corrige erro automaticamente"""
        
        prompt = f"""
Corrija o seguinte erro:

Arquivo: {file_path}
Erro: {error_message}

Código com problema:
```python
{code_context}
```

Retorne:
1. Explicação simples do erro
2. Código corrigido
3. Como evitar no futuro
"""
        
        response = await self.generate_response(
            prompt,
            thinking_budget=self.thinking_budget.adjust_for_complexity("medium")
        )
        
        # Processa resposta
        code_blocks = self._extract_code_blocks(response)
        
        return {
            "explanation": self._extract_explanation(response),
            "fixed_code": code_blocks[0] if code_blocks else "",
            "prevention_tips": self._extract_tips(response),
            "raw_response": response
        }
    
    def _extract_explanation(self, response: str) -> str:
        """Extrai explicação da resposta"""
        lines = response.split('\n')
        explanation = []
        
        for line in lines:
            if line.strip() and not line.startswith('```'):
                explanation.append(line)
                if len(explanation) >= 3:
                    break
        
        return ' '.join(explanation)
    
    def _extract_tips(self, response: str) -> List[str]:
        """Extrai dicas da resposta"""
        tips = []
        lines = response.split('\n')
        
        capturing = False
        for line in lines:
            if 'evitar' in line.lower() or 'dica' in line.lower():
                capturing = True
            elif capturing and line.strip().startswith(('-', '*', '•')):
                tips.append(line.strip()[1:].strip())
        
        return tips[:3]  # Máximo 3 dicas
    
    def estimate_tokens(self, text: str) -> int:
        """Estima número de tokens"""
        # Estimativa simples: ~4 caracteres por token
        return len(text) // 4
    
    def validate_response(self, response: str) -> bool:
        """Valida se resposta é válida"""
        if not response or len(response) < 10:
            return False
        
        # Verifica se não é erro
        error_indicators = ['error', 'exception', 'failed', 'erro', 'falhou']
        response_lower = response.lower()
        
        for indicator in error_indicators:
            if indicator in response_lower and len(response) < 100:
                return False
        
        return True