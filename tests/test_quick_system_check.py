"""
Teste rápido para verificar componentes principais do sistema
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 Verificando componentes do Gemini Code...\n")

# 1. Verifica imports básicos
print("1️⃣ Verificando imports...")
try:
    from gemini_code.core.config import ConfigManager
    print("✅ ConfigManager")
except Exception as e:
    print(f"❌ ConfigManager: {e}")

try:
    from gemini_code.core.gemini_client import GeminiClient
    print("✅ GeminiClient")
except Exception as e:
    print(f"❌ GeminiClient: {e}")

try:
    from gemini_code.core.project_manager import ProjectManager
    print("✅ ProjectManager")
except Exception as e:
    print(f"❌ ProjectManager: {e}")

try:
    from gemini_code.core.memory_system import MemorySystem
    print("✅ MemorySystem")
except Exception as e:
    print(f"❌ MemorySystem: {e}")

try:
    from gemini_code.tools.tool_registry import ToolRegistry
    print("✅ ToolRegistry")
except Exception as e:
    print(f"❌ ToolRegistry: {e}")

# 2. Verifica módulos de cognição
print("\n2️⃣ Verificando módulos de cognição...")
try:
    from gemini_code.cognition.architectural_reasoning import ArchitecturalReasoning
    print("✅ ArchitecturalReasoning")
except Exception as e:
    print(f"❌ ArchitecturalReasoning: {e}")

try:
    from gemini_code.cognition.complexity_analyzer import ComplexityAnalyzer
    print("✅ ComplexityAnalyzer")
except Exception as e:
    print(f"❌ ComplexityAnalyzer: {e}")

try:
    from gemini_code.cognition.learning_engine import LearningEngine
    print("✅ LearningEngine")
except Exception as e:
    print(f"❌ LearningEngine: {e}")

# 3. Testa inicialização básica
print("\n3️⃣ Testando inicializações básicas...")

# Config
try:
    config = ConfigManager()
    print("✅ ConfigManager inicializado")
except Exception as e:
    print(f"❌ ConfigManager init: {e}")

# Gemini Client (sem API key vai falhar, mas é esperado)
try:
    os.environ['GEMINI_API_KEY'] = 'test-key'
    client = GeminiClient()
    print("✅ GeminiClient inicializado (modo teste)")
except Exception as e:
    if "chave inválida" in str(e) or "API Key" in str(e):
        print("⚠️ GeminiClient: Precisa de API key válida (esperado)")
    else:
        print(f"❌ GeminiClient init: {e}")

# Project Manager
try:
    pm = ProjectManager(".")
    print("✅ ProjectManager inicializado")
    stats = pm.get_project_stats()
    print(f"   📁 Arquivos no projeto: {stats['total_files']}")
except Exception as e:
    print(f"❌ ProjectManager init: {e}")

# 4. Verifica se há erros de importação circular
print("\n4️⃣ Verificando master_system...")
try:
    from gemini_code.core.master_system import GeminiCodeMasterSystem
    print("✅ GeminiCodeMasterSystem importado")
    
    # Tenta criar instância (sem inicializar)
    master = GeminiCodeMasterSystem(".")
    print("✅ GeminiCodeMasterSystem instanciado")
    print(f"   📦 Versão: {master.version}")
except Exception as e:
    print(f"❌ GeminiCodeMasterSystem: {e}")
    import traceback
    traceback.print_exc()

print("\n✨ Verificação concluída!")
print("\n💡 Dica: Se houver erros de import, verifique:")
print("   - Dependências instaladas (requirements.txt)")
print("   - Estrutura de diretórios")
print("   - Importações circulares")
