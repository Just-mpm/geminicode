#!/usr/bin/env python3
"""
Launcher para o REPL do Gemini Code
Launcher simples que acessa o REPL correto
"""

import sys
import asyncio
from pathlib import Path

# Adiciona o diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from gemini_code.cli.repl import GeminiREPL
    
    async def main():
        """Função principal para iniciar o REPL."""
        print("🚀 Iniciando Gemini Code REPL...")
        repl = GeminiREPL()
        await repl.start()
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    print(f"❌ Erro ao importar REPL: {e}")
    print("💡 Tentando modo de fallback...")
    
    # Fallback simples
    print("🤖 Gemini Code - REPL Simples")
    print("=" * 40)
    print("Comandos disponíveis:")
    print("- help: Mostra esta ajuda")
    print("- exit/quit/sair: Sair do REPL")
    print("=" * 40)
    
    while True:
        try:
            user_input = input("🤖 Gemini> ").strip().lower()
            
            if user_input in ['exit', 'quit', 'sair', 'bye']:
                print("👋 Até logo!")
                break
            elif user_input in ['help', 'ajuda']:
                print("🔧 REPL em modo simplificado")
                print("Para modo completo, configure as dependências corretamente")
            elif user_input == '':
                continue
            else:
                print(f"🤖 Processando: {user_input}")
                print("💡 REPL em modo simplificado - configure dependências para modo completo")
                
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break
        except EOFError:
            print("\n👋 Até logo!")
            break