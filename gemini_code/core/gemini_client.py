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
    """Cliente OTIMIZADO para Gemini 2.5 Flash - POTENCIAL MÁXIMO 🚀"""
    
    def __init__(self, api_key: Optional[str] = None, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.config
        self.model = None
        
        # THINKING BUDGET OTIMIZADO 🧠
        self.thinking_budget = ThinkingBudget(
            default=getattr(self.config.model, 'thinking_budget_default', 16384),
            maximum=getattr(self.config.model, 'thinking_budget_max', 32768)
        )
        
        # CONFIGURAÇÕES DE ALTA PERFORMANCE
        self.max_input_tokens = getattr(self.config.model, 'max_input_tokens', 1000000)   # 1M tokens ⚡
        self.max_output_tokens = getattr(self.config.model, 'max_output_tokens', 32768)   # 32K tokens 🚀
        self.thinking_mode = getattr(self.config.model, 'thinking_mode', True)            # Sempre ativo 🧠
        self.show_reasoning = getattr(self.config.model, 'show_reasoning', True)          # Processo visível
        
        # MÉTRICAS DE PERFORMANCE
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        
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
        
        # CONFIGURAÇÃO OTIMIZADA DO MODELO 🚀
        generation_config = {
            "temperature": getattr(self.config.model, 'temperature', 0.1),
            "max_output_tokens": self.max_output_tokens,  # 32K tokens
            "top_p": getattr(self.config.model, 'top_p', 0.8),
            "top_k": getattr(self.config.model, 'top_k', 40),
            "response_mime_type": "text/plain",
        }
        
        # CONFIGURAÇÕES AVANÇADAS
        if hasattr(self.config, 'advanced'):
            generation_config.update({
                "enable_code_execution": getattr(self.config.advanced, 'enable_code_execution', True),
                "enable_search": True,
                "candidate_count": 1,  # Uma resposta de alta qualidade
            })
        
        # SISTEMA DE SEGURANÇA OTIMIZADO PARA DESENVOLVIMENTO 🔐
        safety_level = getattr(self.config.advanced, 'safety_settings', 'minimal') if hasattr(self.config, 'advanced') else 'minimal'
        
        if safety_level == 'minimal':
            # Configuração mínima para desenvolvimento - máxima flexibilidade
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        else:
            # Configuração padrão
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            ]
        
        self.model = genai.GenerativeModel(
            model_name=self.config.model.name,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
    
    def _detect_complexity(self, prompt: str) -> str:
        """DETECÇÃO INTELIGENTE DE COMPLEXIDADE 🧠"""
        # Análise aprimorada com mais categorias
        very_complex_keywords = [
            "sistema completo", "arquitetura completa", "refatorar tudo", "redesenhar",
            "análise profunda", "otimização completa", "debug complexo", "migração",
            "múltiplos arquivos", "integração completa", "deploy completo", "escalabilidade",
            "performance crítica", "security audit", "disaster recovery"
        ]
        
        complex_keywords = [
            "arquitetura", "refatorar", "otimização", "integração", "deploy",
            "análise avançada", "debug", "performance", "security", "database",
            "api completa", "sistema", "framework", "infraestrutura"
        ]
        
        medium_keywords = [
            "criar função", "adicionar feature", "corrigir bug", "implementar",
            "modificar", "atualizar", "melhorar", "otimizar", "testar",
            "documentar", "validar", "configurar"
        ]
        
        simple_keywords = [
            "mostrar", "listar", "ver", "explicar", "help", "ajuda",
            "status", "info", "versão", "exemplo simples"
        ]
        
        prompt_lower = prompt.lower()
        
        # Análise ponderada
        very_complex_score = sum(2 for kw in very_complex_keywords if kw in prompt_lower)
        complex_score = sum(1 for kw in complex_keywords if kw in prompt_lower)
        medium_score = sum(0.5 for kw in medium_keywords if kw in prompt_lower)
        simple_score = sum(-0.5 for kw in simple_keywords if kw in prompt_lower)
        
        total_score = very_complex_score + complex_score + medium_score + simple_score
        prompt_length = len(prompt.split())
        
        # Ajuste baseado no tamanho do prompt
        if prompt_length > 100:
            total_score += 1
        elif prompt_length > 50:
            total_score += 0.5
        
        # Classificação inteligente
        if total_score >= 3:
            return "very_complex"
        elif total_score >= 1.5:
            return "complex"
        elif total_score >= 0.5:
            return "medium"
        else:
            return "simple"
    
    async def generate_response(
        self, 
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        thinking_budget: Optional[int] = None,
        stream: bool = False,
        enable_massive_context: bool = True
    ) -> str:
        """GERA RESPOSTA OTIMIZADA COM POTENCIAL MÁXIMO 🚀"""
        
        # Verifica se modelo está disponível
        if not GENAI_AVAILABLE or self.model is None:
            return self._simulate_response(prompt)
        
        # DETECÇÃO INTELIGENTE DE COMPLEXIDADE E AJUSTE DE THINKING 🧠
        if thinking_budget is None:
            complexity = self._detect_complexity(prompt)
            thinking_budget = self.thinking_budget.adjust_for_complexity(complexity)
            
            # Ajuste adicional para contexto massivo
            if enable_massive_context and context and len(context) > 20:
                thinking_budget = min(thinking_budget * 1.5, self.thinking_budget.maximum)
        
        # CONSTRUÇÃO DE PROMPT COM CONTEXTO MASSIVO
        full_prompt = self._build_prompt(prompt, context, thinking_budget)
        
        # VALIDAÇÃO DE LIMITES
        estimated_input_tokens = self.estimate_tokens(full_prompt)
        if estimated_input_tokens > self.max_input_tokens:
            print(f"⚠️ Aviso: Prompt muito longo ({estimated_input_tokens:,} tokens), pode ser truncado")
        
        # LOGGING DE PERFORMANCE
        self.request_count += 1
        print(f"🚀 Request #{self.request_count} | Complexity: {complexity} | Thinking: {thinking_budget:,} tokens")
        
        try:
            # CONFIGURAÇÃO DINÂMICA BASEADA EM CONTEXTO
            dynamic_config = {
                "max_output_tokens": self.max_output_tokens,
                "temperature": getattr(self.config.model, 'temperature', 0.1)
            }
            
            # Ajusta configuração para tarefas muito complexas
            if thinking_budget > 24576:  # Tarefas muito complexas
                dynamic_config["temperature"] = 0.05  # Mais determinístico
                dynamic_config["max_output_tokens"] = self.max_output_tokens  # Resposta completa
            
            start_time = time.time()
            
            if stream:
                response_text = await self._generate_streaming(full_prompt)
            else:
                # Aplicar configuração dinâmica temporariamente
                original_config = self.model._generation_config
                self.model._generation_config.update(dynamic_config)
                
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt
                )
                
                # Restaurar configuração original
                self.model._generation_config = original_config
                
                response_text = response.text
            
            # MÉTRICAS DE PERFORMANCE
            end_time = time.time()
            response_time = end_time - start_time
            output_tokens = self.estimate_tokens(response_text)
            self.total_output_tokens += output_tokens
            
            print(f"✅ Resposta gerada | Tempo: {response_time:.2f}s | Tokens saída: {output_tokens:,}")
            
            return response_text
                
        except Exception as e:
            error_msg = f"❌ Erro ao gerar resposta: {str(e)}"
            print(f"🔍 Debug info: Input tokens: ~{estimated_input_tokens:,}, Thinking: {thinking_budget:,}")
            return error_msg
    
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
        thinking_budget: int = 16384
    ) -> str:
        """CONSTRÓI PROMPT OTIMIZADO COM CONTEXTO MASSIVO 🚀"""
        
        # INSTRUÇÕES SYSTEM APRIMORADAS
        if self.config.user.mode == "non-programmer":
            system_instructions = f"""
🤖 GEMINI CODE - ASSISTENTE INTELIGENTE COM CONTEXTO MASSIVO

CONFIGURAÇÃO ATUAL:
- Contexto: {self.max_input_tokens:,} tokens disponíveis
- Saída: {self.max_output_tokens:,} tokens para resposta completa
- Thinking Mode: {'ATIVO' if self.thinking_mode else 'INATIVO'} 🧠
- Raciocínio: {'VISÍVEL' if self.show_reasoning else 'OCULTO'}

CAPACIDADES EXPANDIDAS:
✅ Análise de projetos COMPLETOS simultaneamente
✅ Refatorações arquiteturais massivas
✅ Geração de múltiplos arquivos em uma resposta
✅ Debugging com contexto completo do projeto
✅ Planejamento estratégico de longo prazo

COMPORTAMENTO:
- Responde SEMPRE em português brasileiro
- Usa linguagem simples e clara, sem jargões técnicos
- Explica tudo de forma que não-programadores entendam
- Executa comandos automaticamente sem pedir confirmação
- Corrige erros sozinho proativamente
- Mostra progresso visual com emojis
- Faz perguntas apenas quando absolutamente essencial
- PENSA antes de agir (thinking mode ativo)

IMPORTANTE:
- Trabalhe DENTRO do projeto existente
- Modifique arquivos reais com confiança
- Mantenha contexto COMPLETO de conversas anteriores
- Seja extremamente proativo em correções
- Use TODO o contexto disponível para decisões
"""
        else:
            system_instructions = f"""
🤖 GEMINI CODE - ASSISTENTE TÉCNICO AVANÇADO

CONFIGURAÇÃO OTIMIZADA:
- Input: {self.max_input_tokens:,} tokens (contexto massivo)
- Output: {self.max_output_tokens:,} tokens (soluções completas)
- Thinking: {thinking_budget:,} tokens (raciocínio profundo)

MODO TÉCNICO ATIVO - Assuma conhecimento avançado de programação.
Forneça soluções completas, detalhadas e tecnicamente precisas.
"""
        
        # CONSTRUÇÃO DO PROMPT COM CONTEXTO MASSIVO
        parts = [system_instructions]
        
        # CONTEXTO EXPANDIDO - Usar muito mais histórico
        if context:
            # Em vez de 10, usar até 50 mensagens anteriores se disponível
            context_limit = min(50, len(context))
            if context_limit > 0:
                parts.append(f"\n## 📚 CONTEXTO HISTÓRICO ({context_limit} mensagens):")
                for msg in context[-context_limit:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', '')
                    # Adiciona timestamp se disponível
                    if timestamp:
                        parts.append(f"[{timestamp}] {role}: {content}")
                    else:
                        parts.append(f"{role}: {content}")
        
        # THINKING MODE EXPANDIDO 🧠
        if self.thinking_mode:
            parts.append(f"\n<thinking_mode budget={thinking_budget} mode='deep_analysis'>")
            parts.append("INSTRUÇÕES DE PENSAMENTO:")
            parts.append("1. Analise PROFUNDAMENTE o contexto completo")
            parts.append("2. Considere implicações arquiteturais")
            parts.append("3. Antecipe problemas potenciais")
            parts.append("4. Planeje solução ótima")
            parts.append("5. Valide abordagem antes de implementar")
            if self.show_reasoning:
                parts.append("6. MOSTRE seu processo de raciocínio")
            parts.append("</thinking_mode>")
        
        # PROMPT DO USUÁRIO COM METADATA
        parts.append(f"\n## 🎯 SOLICITAÇÃO ATUAL:")
        parts.append(f"Usuário: {prompt}")
        
        # INSTRUÇÕES FINAIS PARA MÁXIMA QUALIDADE
        parts.append("\n## 🚀 INSTRUÇÕES PARA RESPOSTA ÓTIMA:")
        parts.append("- Use TODO o contexto disponível para uma resposta completa")
        parts.append("- Gere soluções implementáveis e testáveis")
        parts.append("- Seja proativo em melhorias além do solicitado")
        parts.append("- Mantenha consistência com padrões do projeto")
        
        final_prompt = "\n".join(parts)
        
        # TRACKING DE TOKENS
        estimated_tokens = self.estimate_tokens(final_prompt)
        self.total_input_tokens += estimated_tokens
        
        return final_prompt
    
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
    
    def enable_massive_context_mode(self):
        """ATIVA MODO DE CONTEXTO MASSIVO 🚀"""
        print(f"🚀 MODO CONTEXTO MASSIVO ATIVADO!")
        print(f"📊 Capacidade: {self.max_input_tokens:,} tokens input | {self.max_output_tokens:,} tokens output")
        print(f"🧠 Thinking Mode: {'ATIVO' if self.thinking_mode else 'INATIVO'}")
        print(f"👁️ Show Reasoning: {'ATIVO' if self.show_reasoning else 'INATIVO'}")
        
        # Otimizações adicionais
        if hasattr(self.config, 'advanced'):
            if getattr(self.config.advanced, 'preload_project', False):
                print(f"📂 Preload Project: ATIVADO")
            if getattr(self.config.advanced, 'massive_context', False):
                print(f"🌐 Massive Context: ATIVADO")
    
    def print_capabilities(self):
        """MOSTRA CAPACIDADES OTIMIZADAS 💪"""
        print("\n🤖 GEMINI CODE - CAPACIDADES OTIMIZADAS")
        print("=" * 50)
        print(f"🧠 Contexto Máximo: {self.max_input_tokens:,} tokens")
        print(f"🚀 Saída Máxima: {self.max_output_tokens:,} tokens")
        print(f"💭 Thinking Budget: {self.thinking_budget.default:,} - {self.thinking_budget.maximum:,} tokens")
        print(f"🔬 Modo Thinking: {'✅ ATIVO' if self.thinking_mode else '❌ INATIVO'}")
        print(f"👁️ Raciocínio Visível: {'✅ SIM' if self.show_reasoning else '❌ NÃO'}")
        print("\n🎯 CAPACIDADES EXPANDIDAS:")
        print("  ✅ Análise de projetos completos")
        print("  ✅ Refatorações arquiteturais massivas")
        print("  ✅ Geração de múltiplos arquivos")
        print("  ✅ Debugging com contexto completo")
        print("  ✅ Planejamento estratégico")
        print("  ✅ Raciocínio transparente")
        
        stats = self.get_performance_stats()
        if stats['total_requests'] > 0:
            print("\n📊 ESTATÍSTICAS ATUAIS:")
            print(f"  📈 Requests: {stats['total_requests']}")
            print(f"  📥 Tokens Input: {stats['total_input_tokens']:,}")
            print(f"  📤 Tokens Output: {stats['total_output_tokens']:,}")
            print(f"  📊 Média Input: {stats['avg_input_per_request']:.0f} tokens/request")
            print(f"  📊 Média Output: {stats['avg_output_per_request']:.0f} tokens/request")
        print("="*50)
    
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
        
        return tips[:5]  # Máximo 5 dicas (aumentado)
    
    def estimate_tokens(self, text: str) -> int:
        """ESTIMATIVA MELHORADA DE TOKENS"""
        # Estimativa mais precisa considerando:
        # - Palavras em português: ~5-6 caracteres por token
        # - Código: ~3-4 caracteres por token  
        # - Texto misto: ~4.5 caracteres por token
        
        if not text:
            return 0
            
        # Detecta se é principalmente código
        code_indicators = ['def ', 'class ', 'import ', 'from ', '{\n', 'function']
        is_code = any(indicator in text for indicator in code_indicators)
        
        if is_code:
            return len(text) // 3.5  # Código é mais denso
        else:
            return len(text) // 4.5  # Texto em português
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """ESTATÍSTICAS DE PERFORMANCE 📊"""
        return {
            'total_requests': self.request_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'avg_input_per_request': self.total_input_tokens / max(1, self.request_count),
            'avg_output_per_request': self.total_output_tokens / max(1, self.request_count),
            'max_input_capacity': self.max_input_tokens,
            'max_output_capacity': self.max_output_tokens,
            'thinking_mode': self.thinking_mode,
            'show_reasoning': self.show_reasoning
        }
    
    def validate_response(self, response: str) -> Dict[str, Any]:
        """VALIDAÇÃO AVANÇADA DE RESPOSTA 🔍"""
        validation_result = {
            'is_valid': False,
            'quality_score': 0,
            'issues': [],
            'strengths': [],
            'token_count': 0
        }
        
        if not response or len(response) < 10:
            validation_result['issues'].append('Resposta muito curta')
            return validation_result
        
        validation_result['token_count'] = self.estimate_tokens(response)
        
        # Indicadores de erro
        error_indicators = ['error', 'exception', 'failed', 'erro', 'falhou', 'impossível']
        response_lower = response.lower()
        
        # Verifica erros
        error_count = 0
        for indicator in error_indicators:
            if indicator in response_lower:
                error_count += 1
        
        if error_count > 0 and len(response) < 200:
            validation_result['issues'].append('Possível mensagem de erro')
        
        # Indicadores de qualidade
        quality_indicators = {
            'tem_código': ['```', 'def ', 'class ', 'import'],
            'tem_explicação': ['porque', 'pois', 'isso significa', 'funciona'],
            'tem_estrutura': ['##', '**', '1.', '2.', '-'],
            'tem_exemplos': ['exemplo', 'por exemplo', 'veja'],
            'tem_thinking': ['<thinking>', 'analisando', 'considerando']
        }
        
        quality_score = 0
        for category, indicators in quality_indicators.items():
            if any(ind in response_lower for ind in indicators):
                quality_score += 20
                validation_result['strengths'].append(category)
        
        # Ajuste baseado no tamanho
        if validation_result['token_count'] > 1000:
            quality_score += 10
            validation_result['strengths'].append('resposta_detalhada')
        
        validation_result['quality_score'] = min(quality_score, 100)
        validation_result['is_valid'] = quality_score >= 40 and error_count == 0
        
        return validation_result