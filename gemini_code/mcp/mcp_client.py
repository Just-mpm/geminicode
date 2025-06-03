"""
MCP Client - Cliente para Model Context Protocol
Permite integração com servidores MCP externos para extensibilidade
"""

import asyncio
import json
import subprocess
import os
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import uuid

# Websockets é opcional para MCP
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from ..tools.base_tool import BaseTool, ToolInput, ToolResult


@dataclass
class MCPServer:
    """Configuração de um servidor MCP."""
    name: str
    command: List[str]
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None
    timeout: int = 30
    auto_restart: bool = True
    enabled: bool = True


@dataclass
class MCPTool:
    """Ferramenta disponível via MCP."""
    name: str
    description: str
    server_name: str
    input_schema: Dict[str, Any]
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)


@dataclass
class MCPResource:
    """Recurso disponível via MCP."""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = None
    server_name: str = ""


class MCPProtocolError(Exception):
    """Erro de protocolo MCP."""
    pass


class MCPClient:
    """
    Cliente MCP que replica o comportamento do Claude Code.
    Permite conectar com servidores MCP para estender funcionalidades.
    """
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or ".")
        self.servers: Dict[str, MCPServer] = {}
        self.connections: Dict[str, Any] = {}  # Conexões ativas
        self.available_tools: Dict[str, MCPTool] = {}
        self.available_resources: Dict[str, MCPResource] = {}
        
        # Estado do protocolo
        self.request_id = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Configurações
        self.max_servers = 10
        self.connection_timeout = 30
        self.request_timeout = 60
        
        # Callbacks
        self.tool_callbacks: Dict[str, Callable] = {}
        self.resource_callbacks: Dict[str, Callable] = {}
        
        # Carrega configuração
        self._load_server_config()
    
    def _load_server_config(self):
        """Carrega configuração de servidores MCP."""
        config_file = self.project_path / '.gemini_code' / 'mcp_servers.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                for server_data in config.get('servers', []):
                    server = MCPServer(**server_data)
                    self.servers[server.name] = server
                    
            except Exception as e:
                print(f"Erro carregando configuração MCP: {e}")
    
    def register_server(self, server: MCPServer):
        """Registra um novo servidor MCP."""
        if len(self.servers) >= self.max_servers:
            raise ValueError(f"Máximo de {self.max_servers} servidores atingido")
        
        self.servers[server.name] = server
        print(f"🔌 Servidor MCP '{server.name}' registrado")
    
    async def start_server(self, server_name: str) -> bool:
        """Inicia um servidor MCP."""
        if server_name not in self.servers:
            return False
        
        server = self.servers[server_name]
        if not server.enabled:
            return False
        
        try:
            # Inicia processo do servidor
            env = os.environ.copy()
            env.update(server.env)
            
            process = await asyncio.create_subprocess_exec(
                *server.command,
                *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=server.working_dir,
                env=env
            )
            
            # Estabelece conexão MCP
            connection = MCPConnection(server_name, process, self)
            await connection.initialize()
            
            self.connections[server_name] = connection
            
            # Descobre ferramentas e recursos
            await self._discover_server_capabilities(server_name)
            
            print(f"✅ Servidor MCP '{server_name}' iniciado")
            return True
            
        except Exception as e:
            print(f"❌ Erro iniciando servidor MCP '{server_name}': {e}")
            return False
    
    async def stop_server(self, server_name: str):
        """Para um servidor MCP."""
        if server_name in self.connections:
            connection = self.connections[server_name]
            await connection.close()
            del self.connections[server_name]
            
            # Remove ferramentas do servidor
            tools_to_remove = [name for name, tool in self.available_tools.items() 
                             if tool.server_name == server_name]
            for tool_name in tools_to_remove:
                del self.available_tools[tool_name]
            
            print(f"🔌 Servidor MCP '{server_name}' parado")
    
    async def _discover_server_capabilities(self, server_name: str):
        """Descobre ferramentas e recursos disponíveis no servidor."""
        connection = self.connections.get(server_name)
        if not connection:
            return
        
        try:
            # Lista ferramentas
            tools_response = await connection.send_request("tools/list", {})
            if tools_response.get("tools"):
                for tool_data in tools_response["tools"]:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        server_name=server_name,
                        input_schema=tool_data.get("inputSchema", {}),
                        required_params=tool_data.get("inputSchema", {}).get("required", []),
                        optional_params=list(tool_data.get("inputSchema", {}).get("properties", {}).keys())
                    )
                    self.available_tools[f"{server_name}:{tool.name}"] = tool
            
            # Lista recursos
            resources_response = await connection.send_request("resources/list", {})
            if resources_response.get("resources"):
                for resource_data in resources_response["resources"]:
                    resource = MCPResource(
                        uri=resource_data["uri"],
                        name=resource_data.get("name", ""),
                        description=resource_data.get("description", ""),
                        mime_type=resource_data.get("mimeType"),
                        server_name=server_name
                    )
                    self.available_resources[resource.uri] = resource
            
            print(f"📡 Descobriu {len([t for t in self.available_tools.values() if t.server_name == server_name])} ferramentas e {len([r for r in self.available_resources.values() if r.server_name == server_name])} recursos do servidor '{server_name}'")
            
        except Exception as e:
            print(f"⚠️ Erro descobrindo capacidades do servidor '{server_name}': {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Chama ferramenta via MCP."""
        if tool_name not in self.available_tools:
            return ToolResult(
                success=False,
                error=f"Ferramenta MCP '{tool_name}' não encontrada"
            )
        
        tool = self.available_tools[tool_name]
        server_name = tool.server_name
        
        if server_name not in self.connections:
            return ToolResult(
                success=False,
                error=f"Servidor MCP '{server_name}' não conectado"
            )
        
        connection = self.connections[server_name]
        
        try:
            # Valida argumentos
            validation_error = self._validate_tool_arguments(tool, arguments)
            if validation_error:
                return ToolResult(
                    success=False,
                    error=f"Argumentos inválidos: {validation_error}"
                )
            
            # Chama ferramenta
            actual_tool_name = tool_name.split(":", 1)[1]  # Remove prefixo do servidor
            response = await connection.send_request("tools/call", {
                "name": actual_tool_name,
                "arguments": arguments
            })
            
            # Processa resposta
            if response.get("isError"):
                return ToolResult(
                    success=False,
                    error=response.get("content", [{}])[0].get("text", "Erro desconhecido")
                )
            
            # Extrai conteúdo da resposta
            content = response.get("content", [])
            if content:
                result_data = {
                    "content": content,
                    "raw_response": response
                }
            else:
                result_data = response
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "server_name": server_name,
                    "tool_name": actual_tool_name,
                    "mcp_version": connection.server_info.get("protocolVersion", "unknown")
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro chamando ferramenta MCP '{tool_name}': {str(e)}"
            )
    
    async def read_resource(self, uri: str) -> ToolResult:
        """Lê recurso via MCP."""
        if uri not in self.available_resources:
            return ToolResult(
                success=False,
                error=f"Recurso MCP '{uri}' não encontrado"
            )
        
        resource = self.available_resources[uri]
        server_name = resource.server_name
        
        if server_name not in self.connections:
            return ToolResult(
                success=False,
                error=f"Servidor MCP '{server_name}' não conectado"
            )
        
        connection = self.connections[server_name]
        
        try:
            response = await connection.send_request("resources/read", {
                "uri": uri
            })
            
            return ToolResult(
                success=True,
                data={
                    "content": response.get("contents", []),
                    "resource_info": {
                        "uri": uri,
                        "name": resource.name,
                        "mime_type": resource.mime_type
                    }
                },
                metadata={
                    "server_name": server_name,
                    "resource_uri": uri
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Erro lendo recurso MCP '{uri}': {str(e)}"
            )
    
    def _validate_tool_arguments(self, tool: MCPTool, arguments: Dict[str, Any]) -> Optional[str]:
        """Valida argumentos de ferramenta."""
        # Verifica parâmetros obrigatórios
        for required_param in tool.required_params:
            if required_param not in arguments:
                return f"Parâmetro obrigatório '{required_param}' não fornecido"
        
        # Verifica parâmetros extras
        schema_props = tool.input_schema.get("properties", {})
        for arg_name in arguments:
            if arg_name not in schema_props and schema_props:
                return f"Parâmetro '{arg_name}' não reconhecido"
        
        return None
    
    async def start_all_servers(self):
        """Inicia todos os servidores habilitados."""
        results = []
        for server_name, server in self.servers.items():
            if server.enabled:
                result = await self.start_server(server_name)
                results.append((server_name, result))
        
        successful = sum(1 for _, success in results if success)
        print(f"🚀 Iniciados {successful}/{len(results)} servidores MCP")
        
        return results
    
    async def stop_all_servers(self):
        """Para todos os servidores."""
        for server_name in list(self.connections.keys()):
            await self.stop_server(server_name)
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """Lista todas as ferramentas MCP disponíveis."""
        return [
            {
                "name": name,
                "description": tool.description,
                "server": tool.server_name,
                "required_params": tool.required_params,
                "optional_params": tool.optional_params
            }
            for name, tool in self.available_tools.items()
        ]
    
    def list_available_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os recursos MCP disponíveis."""
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type,
                "server": resource.server_name
            }
            for resource in self.available_resources.values()
        ]
    
    def get_server_status(self) -> Dict[str, Any]:
        """Retorna status de todos os servidores."""
        status = {}
        for server_name, server in self.servers.items():
            status[server_name] = {
                "enabled": server.enabled,
                "connected": server_name in self.connections,
                "tools_count": len([t for t in self.available_tools.values() if t.server_name == server_name]),
                "resources_count": len([r for r in self.available_resources.values() if r.server_name == server_name])
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde das conexões MCP."""
        health = {
            "overall_status": "healthy",
            "total_servers": len(self.servers),
            "connected_servers": len(self.connections),
            "total_tools": len(self.available_tools),
            "total_resources": len(self.available_resources),
            "server_health": {}
        }
        
        for server_name in self.servers:
            if server_name in self.connections:
                try:
                    # Testa ping
                    connection = self.connections[server_name]
                    await connection.send_request("ping", {})
                    health["server_health"][server_name] = "healthy"
                except Exception:
                    health["server_health"][server_name] = "unhealthy"
            else:
                health["server_health"][server_name] = "disconnected"
        
        # Determina status geral
        unhealthy_count = sum(1 for status in health["server_health"].values() if status != "healthy")
        if unhealthy_count > 0:
            health["overall_status"] = "degraded" if unhealthy_count < len(self.servers) / 2 else "critical"
        
        return health


class MCPConnection:
    """Representa uma conexão com um servidor MCP."""
    
    def __init__(self, server_name: str, process: asyncio.subprocess.Process, client: MCPClient):
        self.server_name = server_name
        self.process = process
        self.client = client
        self.server_info: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize(self):
        """Inicializa conexão MCP."""
        try:
            # Envia handshake inicial
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "gemini-code",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send_message(init_request)
            response = await self._receive_message()
            
            if response.get("result"):
                self.server_info = response["result"]
                self.initialized = True
                
                # Envia initialized notification
                await self._send_message({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                })
            
        except Exception as e:
            raise MCPProtocolError(f"Falha na inicialização: {e}")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Envia request e aguarda resposta."""
        if not self.initialized:
            raise MCPProtocolError("Conexão não inicializada")
        
        request_id = self.client.request_id
        self.client.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Cria future para resposta
        future = asyncio.Future()
        self.client.pending_requests[str(request_id)] = future
        
        try:
            await self._send_message(request)
            
            # Aguarda resposta com timeout
            response = await asyncio.wait_for(future, timeout=self.client.request_timeout)
            
            if "error" in response:
                raise MCPProtocolError(f"Erro MCP: {response['error']}")
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            raise MCPProtocolError(f"Timeout na requisição {method}")
        finally:
            self.client.pending_requests.pop(str(request_id), None)
    
    async def _send_message(self, message: Dict[str, Any]):
        """Envia mensagem para o servidor."""
        json_str = json.dumps(message) + "\\n"
        self.process.stdin.write(json_str.encode())
        await self.process.stdin.drain()
    
    async def _receive_message(self) -> Dict[str, Any]:
        """Recebe mensagem do servidor."""
        line = await self.process.stdout.readline()
        if not line:
            raise MCPProtocolError("Conexão fechada pelo servidor")
        
        try:
            return json.loads(line.decode().strip())
        except json.JSONDecodeError as e:
            raise MCPProtocolError(f"JSON inválido recebido: {e}")
    
    async def close(self):
        """Fecha conexão."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()


# Instância global do cliente MCP
_global_mcp_client: Optional[MCPClient] = None


def get_mcp_client(project_path: str = None) -> MCPClient:
    """Obtém instância global do cliente MCP."""
    global _global_mcp_client
    
    if _global_mcp_client is None:
        _global_mcp_client = MCPClient(project_path)
    
    return _global_mcp_client