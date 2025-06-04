#!/usr/bin/env python3
"""
Teste simples para debugar problema de inicialização
"""

import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("1. Testando import de master_system...")
    from gemini_code.core.master_system import GeminiCodeMasterSystem
    print("✅ Import de master_system OK")
    
    print("2. Criando instância...")
    system = GeminiCodeMasterSystem()
    print("✅ Instância criada OK")
    
    print("3. Testando import de config...")
    from gemini_code.core.config import Config
    print("✅ Import de config OK")
    
    print("4. Testando import de gemini_client...")
    from gemini_code.core.gemini_client import GeminiClient
    print("✅ Import de gemini_client OK")
    
    print("5. Testando import de tool_registry...")
    from gemini_code.tools.tool_registry import get_tool_registry
    print("✅ Import de tool_registry OK")
    
    print("6. Testando registry...")
    registry = get_tool_registry()
    print(f"✅ Registry criado com {len(registry.tools)} ferramentas")
    
    print("\n🎉 TODOS OS IMPORTS FUNCIONARAM!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
