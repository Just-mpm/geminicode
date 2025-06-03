#!/usr/bin/env python3
"""
Gemini Code REPL - Interface de linha de comando estilo Claude Code
Entrada principal para o Terminal REPL nativo com TODOS os sistemas integrados
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_code.core.master_system import initialize_gemini_code, get_master_system


async def start_full_system(project_path: str, headless: bool = False):
    """Inicia sistema completo com todas as funcionalidades."""
    # Inicializa sistema principal
    system = await initialize_gemini_code(project_path)
    
    # Inicia REPL
    await system.start_repl(headless=headless)


async def execute_single_command(project_path: str, command: str):
    """Executa comando único."""
    system = await initialize_gemini_code(project_path)
    return await system.execute_command(command)


def main():
    """Função principal do REPL."""
    parser = argparse.ArgumentParser(
        description='Gemini Code - Terminal REPL Interface',
        epilog='''
Exemplos:
  gemini_repl.py                    # Inicia REPL interativo
  gemini_repl.py --headless         # Modo headless (CI/CD)
  gemini_repl.py --project /path    # Especifica diretório do projeto
  
Comandos no REPL:
  /help                             # Ajuda completa
  /cost                             # Monitoramento de custos
  /doctor                           # Diagnósticos do sistema
  /clear                            # Limpar sessão
  "crie um agente para vendas"      # Comando natural
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--project', '-p',
        type=str,
        default=None,
        help='Caminho para o diretório do projeto (padrão: diretório atual)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Executa em modo headless (não-interativo, para CI/CD)'
    )
    
    parser.add_argument(
        '--command', '-c',
        type=str,
        help='Executa comando único e sai'
    )
    
    parser.add_argument(
        '--session',
        type=str,
        help='ID da sessão para retomar'
    )
    
    parser.add_argument(
        '--vim-mode',
        action='store_true',
        help='Inicia em modo Vim'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativa modo debug'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Gemini Code REPL v1.0.0 - Claude Code Style Interface'
    )
    
    args = parser.parse_args()
    
    # Configura diretório do projeto
    project_path = args.project or str(Path.cwd())
    
    try:
        # Inicia o sistema completo
        if args.command:
            # Modo comando único
            print(f"🚀 Executando comando: {args.command}")
            result = asyncio.run(execute_single_command(project_path, args.command))
            if result.get('success'):
                print("✅ Comando executado com sucesso!")
            else:
                print(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
        else:
            # Modo interativo - inicializa sistema completo
            asyncio.run(start_full_system(project_path, args.headless))
            
    except KeyboardInterrupt:
        print("\n👋 Gemini Code REPL interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()