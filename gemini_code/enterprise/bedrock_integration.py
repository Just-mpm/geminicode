"""
AWS Bedrock Integration - Suporte empresarial estilo Claude Code
"""

import json
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncio
from dataclasses import dataclass

# boto3 é opcional para Bedrock
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from ..core.config import ModelConfig


@dataclass
class BedrockConfig:
    """Configuração para AWS Bedrock."""
    region_name: str = "us-east-1"
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    max_tokens: int = 4096
    temperature: float = 0.1
    top_p: float = 0.9
    profile_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None


class BedrockClient:
    """
    Cliente AWS Bedrock para uso empresarial.
    Replica funcionalidade enterprise do Claude Code.
    """
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.client = None
        self.runtime_client = None
        self._initialize_clients()
        
        # Estatísticas de uso
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Cache de modelos disponíveis
        self.available_models: List[str] = []
        
    def _initialize_clients(self):
        """Inicializa clientes AWS."""
        if not BOTO3_AVAILABLE:
            print("⚠️ boto3 não disponível - funcionalidade Bedrock desabilitada")
            return
            
        try:
            # Configuração de credenciais
            session_kwargs = {
                'region_name': self.config.region_name
            }
            
            if self.config.profile_name:
                session_kwargs['profile_name'] = self.config.profile_name
            elif self.config.access_key_id and self.config.secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': self.config.access_key_id,
                    'aws_secret_access_key': self.config.secret_access_key
                })
            
            session = boto3.Session(**session_kwargs)
            
            # Clientes Bedrock
            self.client = session.client('bedrock')
            self.runtime_client = session.client('bedrock-runtime')
            
            print(f"✅ Cliente AWS Bedrock inicializado (região: {self.config.region_name})")
            
        except Exception as e:
            print(f"❌ Erro inicializando AWS Bedrock: {e}")
            raise
    
    async def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Gera conteúdo usando modelo Bedrock."""
        
        # Prepara parâmetros
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.config.temperature)
        top_p = kwargs.get('top_p', self.config.top_p)
        model_id = kwargs.get('model_id', self.config.model_id)
        
        # Constrói body da requisição
        if 'anthropic' in model_id.lower():
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        else:
            # Outros modelos (Titan, etc.)
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
        
        try:
            # Chama Bedrock
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.runtime_client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body)
                )
            )
            
            # Processa resposta
            response_body = json.loads(response['body'].read())
            
            # Extrai texto baseado no modelo
            if 'anthropic' in model_id.lower():
                text = response_body.get('content', [{}])[0].get('text', '')
                input_tokens = response_body.get('usage', {}).get('input_tokens', 0)
                output_tokens = response_body.get('usage', {}).get('output_tokens', 0)
            else:
                text = response_body.get('results', [{}])[0].get('outputText', '')
                input_tokens = response_body.get('inputTextTokenCount', 0)
                output_tokens = response_body.get('results', [{}])[0].get('tokenCount', 0)
            
            # Atualiza estatísticas
            self.request_count += 1
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cost += self._calculate_cost(model_id, input_tokens, output_tokens)
            
            return {
                'text': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model_id': model_id,
                'response_metadata': response_body
            }
            
        except Exception as e:
            print(f"❌ Erro na geração Bedrock: {e}")
            raise
    
    async def stream_content(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Gera conteúdo em streaming."""
        
        model_id = kwargs.get('model_id', self.config.model_id)
        
        # Prepara body para streaming
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        try:
            # Invoke com streaming
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.runtime_client.invoke_model_with_response_stream(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body)
                )
            )
            
            # Processa stream
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        if chunk_data.get('type') == 'content_block_delta':
                            delta = chunk_data.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                yield delta.get('text', '')
                                
        except Exception as e:
            print(f"❌ Erro no streaming Bedrock: {e}")
            raise
    
    def _calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Calcula custo estimado da requisição."""
        
        # Preços por 1K tokens (valores aproximados)
        pricing = {
            'anthropic.claude-3-sonnet-20240229-v1:0': {
                'input': 0.003,
                'output': 0.015
            },
            'anthropic.claude-3-haiku-20240307-v1:0': {
                'input': 0.00025,
                'output': 0.00125
            },
            'anthropic.claude-instant-v1': {
                'input': 0.0008,
                'output': 0.0024
            }
        }
        
        model_pricing = pricing.get(model_id, {'input': 0.001, 'output': 0.005})
        
        input_cost = (input_tokens / 1000) * model_pricing['input']
        output_cost = (output_tokens / 1000) * model_pricing['output']
        
        return input_cost + output_cost
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.list_foundation_models
            )
            
            models = []
            for model in response.get('modelSummaries', []):
                models.append({
                    'model_id': model.get('modelId'),
                    'model_name': model.get('modelName'),
                    'provider_name': model.get('providerName'),
                    'input_modalities': model.get('inputModalities', []),
                    'output_modalities': model.get('outputModalities', []),
                    'supported_languages': model.get('supportedLanguages', [])
                })
            
            self.available_models = [m['model_id'] for m in models]
            return models
            
        except Exception as e:
            print(f"❌ Erro listando modelos Bedrock: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso."""
        return {
            'request_count': self.request_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'estimated_cost_usd': self.total_cost,
            'average_input_tokens': self.total_input_tokens / max(self.request_count, 1),
            'average_output_tokens': self.total_output_tokens / max(self.request_count, 1),
            'current_model': self.config.model_id,
            'region': self.config.region_name
        }
    
    def reset_stats(self):
        """Reseta estatísticas de uso."""
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da conexão Bedrock."""
        try:
            # Testa listagem de modelos
            models = await self.list_models()
            
            # Testa geração simples
            test_response = await self.generate_content(
                "Responda apenas: OK",
                max_tokens=10
            )
            
            return {
                'status': 'healthy',
                'models_available': len(models),
                'test_generation': bool(test_response.get('text')),
                'region': self.config.region_name,
                'current_model': self.config.model_id
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'region': self.config.region_name
            }


class BedrockWorkspaceManager:
    """
    Gerenciador de workspaces empresariais para Bedrock.
    """
    
    def __init__(self):
        self.workspaces: Dict[str, BedrockClient] = {}
        self.workspace_configs: Dict[str, BedrockConfig] = {}
        self.spending_limits: Dict[str, float] = {}
        self.current_spending: Dict[str, float] = {}
    
    def create_workspace(self, workspace_name: str, config: BedrockConfig, 
                        spending_limit: float = 100.0) -> BedrockClient:
        """Cria novo workspace empresarial."""
        
        client = BedrockClient(config)
        
        self.workspaces[workspace_name] = client
        self.workspace_configs[workspace_name] = config
        self.spending_limits[workspace_name] = spending_limit
        self.current_spending[workspace_name] = 0.0
        
        print(f"🏢 Workspace '{workspace_name}' criado (limite: ${spending_limit})")
        return client
    
    def get_workspace(self, workspace_name: str) -> Optional[BedrockClient]:
        """Obtém workspace por nome."""
        return self.workspaces.get(workspace_name)
    
    def list_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """Lista todos os workspaces."""
        result = {}
        
        for name, client in self.workspaces.items():
            stats = client.get_usage_stats()
            result[name] = {
                'config': {
                    'region': client.config.region_name,
                    'model_id': client.config.model_id
                },
                'usage': stats,
                'spending_limit': self.spending_limits.get(name, 0),
                'current_spending': stats.get('estimated_cost_usd', 0),
                'spending_remaining': self.spending_limits.get(name, 0) - stats.get('estimated_cost_usd', 0)
            }
        
        return result
    
    def check_spending_limits(self) -> Dict[str, bool]:
        """Verifica limites de gastos dos workspaces."""
        results = {}
        
        for workspace_name, client in self.workspaces.items():
            current_cost = client.get_usage_stats()['estimated_cost_usd']
            limit = self.spending_limits.get(workspace_name, 0)
            
            results[workspace_name] = current_cost < limit
            
            if current_cost >= limit:
                print(f"⚠️ Workspace '{workspace_name}' atingiu limite de gastos: ${current_cost:.2f} >= ${limit}")
        
        return results
    
    async def workspace_health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os workspaces."""
        results = {}
        
        for workspace_name, client in self.workspaces.items():
            health = await client.health_check()
            results[workspace_name] = health
        
        return results


# Instância global do gerenciador
_global_bedrock_manager: Optional[BedrockWorkspaceManager] = None


def get_bedrock_manager() -> BedrockWorkspaceManager:
    """Obtém instância global do gerenciador Bedrock."""
    global _global_bedrock_manager
    
    if _global_bedrock_manager is None:
        _global_bedrock_manager = BedrockWorkspaceManager()
    
    return _global_bedrock_manager