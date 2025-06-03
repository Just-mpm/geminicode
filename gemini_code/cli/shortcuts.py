"""
Shortcuts and Keybindings - Gerenciamento de atalhos estilo Claude Code
"""

import os
import sys
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class KeyAction(Enum):
    """Ações disponíveis para teclas."""
    COMPLETE = "complete"
    HISTORY_UP = "history_up"
    HISTORY_DOWN = "history_down"
    CLEAR_LINE = "clear_line"
    BEGINNING_OF_LINE = "beginning_of_line"
    END_OF_LINE = "end_of_line"
    DELETE_WORD = "delete_word"
    ACCEPT_SUGGESTION = "accept_suggestion"
    CANCEL = "cancel"
    HELP = "help"
    SEARCH_HISTORY = "search_history"


@dataclass
class KeyBinding:
    """Representa um keybinding."""
    key_sequence: str
    action: KeyAction
    description: str
    condition: Optional[str] = None  # Condição para ativar


class ShortcutManager:
    """
    Gerencia atalhos de teclado e keybindings no estilo Claude Code.
    """
    
    def __init__(self):
        self.bindings: Dict[str, KeyBinding] = {}
        self.vim_mode = False
        self.emacs_mode = True  # Default
        
        # Callbacks para ações
        self.action_callbacks: Dict[KeyAction, Callable] = {}
        
        # Setup default bindings
        self._setup_default_bindings()
    
    def _setup_default_bindings(self):
        """Configura atalhos padrão."""
        
        # Atalhos universais (funcionam em qualquer modo)
        universal_bindings = [
            KeyBinding("C-c", KeyAction.CANCEL, "Cancelar operação atual"),
            KeyBinding("C-d", KeyAction.HELP, "Sair do REPL (EOF)"),
            KeyBinding("tab", KeyAction.COMPLETE, "Autocompletar comando"),
            KeyBinding("C-r", KeyAction.SEARCH_HISTORY, "Buscar no histórico"),
        ]
        
        # Atalhos Emacs (padrão)
        emacs_bindings = [
            KeyBinding("C-a", KeyAction.BEGINNING_OF_LINE, "Ir para início da linha"),
            KeyBinding("C-e", KeyAction.END_OF_LINE, "Ir para fim da linha"),
            KeyBinding("C-k", KeyAction.CLEAR_LINE, "Limpar linha"),
            KeyBinding("C-w", KeyAction.DELETE_WORD, "Deletar palavra anterior"),
            KeyBinding("C-p", KeyAction.HISTORY_UP, "Comando anterior no histórico"),
            KeyBinding("C-n", KeyAction.HISTORY_DOWN, "Próximo comando no histórico"),
            KeyBinding("M-f", KeyAction.ACCEPT_SUGGESTION, "Aceitar sugestão"),
        ]
        
        # Atalhos Vim (quando ativado)
        vim_bindings = [
            KeyBinding("j", KeyAction.HISTORY_DOWN, "Próximo no histórico (modo normal)"),
            KeyBinding("k", KeyAction.HISTORY_UP, "Anterior no histórico (modo normal)"),
            KeyBinding("0", KeyAction.BEGINNING_OF_LINE, "Início da linha (modo normal)"),
            KeyBinding("$", KeyAction.END_OF_LINE, "Fim da linha (modo normal)"),
            KeyBinding("dd", KeyAction.CLEAR_LINE, "Deletar linha (modo normal)"),
            KeyBinding("i", KeyAction.CANCEL, "Entrar em modo inserção"),
            KeyBinding("esc", KeyAction.CANCEL, "Sair do modo inserção"),
        ]
        
        # Registra todos os bindings
        for binding in universal_bindings:
            self.bindings[binding.key_sequence] = binding
        
        for binding in emacs_bindings:
            binding.condition = "emacs_mode"
            self.bindings[binding.key_sequence] = binding
        
        for binding in vim_bindings:
            binding.condition = "vim_mode"
            self.bindings[binding.key_sequence] = binding
    
    def register_action_callback(self, action: KeyAction, callback: Callable):
        """Registra callback para uma ação."""
        self.action_callbacks[action] = callback
    
    def handle_key(self, key_sequence: str) -> bool:
        """
        Processa uma sequência de teclas.
        Retorna True se a tecla foi processada.
        """
        if key_sequence not in self.bindings:
            return False
        
        binding = self.bindings[key_sequence]
        
        # Verifica condição
        if binding.condition:
            if binding.condition == "emacs_mode" and not self.emacs_mode:
                return False
            elif binding.condition == "vim_mode" and not self.vim_mode:
                return False
        
        # Executa ação
        if binding.action in self.action_callbacks:
            try:
                self.action_callbacks[binding.action]()
                return True
            except Exception as e:
                print(f"Erro executando ação {binding.action}: {e}")
                return False
        
        return False
    
    def set_vim_mode(self, enabled: bool):
        """Ativa/desativa modo Vim."""
        self.vim_mode = enabled
        self.emacs_mode = not enabled
    
    def set_emacs_mode(self, enabled: bool):
        """Ativa/desativa modo Emacs."""
        self.emacs_mode = enabled
        self.vim_mode = not enabled
    
    def add_custom_binding(self, key_sequence: str, action: KeyAction, 
                          description: str, condition: Optional[str] = None):
        """Adiciona binding customizado."""
        binding = KeyBinding(key_sequence, action, description, condition)
        self.bindings[key_sequence] = binding
    
    def remove_binding(self, key_sequence: str):
        """Remove um binding."""
        if key_sequence in self.bindings:
            del self.bindings[key_sequence]
    
    def get_bindings_help(self) -> str:
        """Retorna texto de ajuda com todos os atalhos."""
        help_text = "# ⌨️ Atalhos de Teclado\n\n"
        
        # Agrupa por modo
        universal = []
        emacs = []
        vim = []
        
        for binding in self.bindings.values():
            if binding.condition == "emacs_mode":
                emacs.append(binding)
            elif binding.condition == "vim_mode":
                vim.append(binding)
            else:
                universal.append(binding)
        
        # Atalhos universais
        help_text += "## 🌐 Atalhos Universais\n"
        for binding in universal:
            help_text += f"- **{binding.key_sequence}**: {binding.description}\n"
        
        # Atalhos Emacs
        if self.emacs_mode:
            help_text += "\n## 📝 Modo Emacs (Ativo)\n"
            for binding in emacs:
                help_text += f"- **{binding.key_sequence}**: {binding.description}\n"
        
        # Atalhos Vim
        if self.vim_mode:
            help_text += "\n## ⚡ Modo Vim (Ativo)\n"
            for binding in vim:
                help_text += f"- **{binding.key_sequence}**: {binding.description}\n"
        
        # Como alternar modos
        help_text += "\n## 🔄 Alterar Modos\n"
        help_text += "- Use `/config set editor_mode vim` para modo Vim\n"
        help_text += "- Use `/config set editor_mode emacs` para modo Emacs\n"
        
        return help_text
    
    def get_active_bindings(self) -> Dict[str, KeyBinding]:
        """Retorna apenas os bindings ativos no modo atual."""
        active = {}
        
        for key, binding in self.bindings.items():
            if binding.condition == "emacs_mode" and not self.emacs_mode:
                continue
            elif binding.condition == "vim_mode" and not self.vim_mode:
                continue
            
            active[key] = binding
        
        return active
    
    def setup_readline_bindings(self):
        """Configura bindings no readline (se disponível)."""
        try:
            import readline
            
            # Configura modo
            if self.vim_mode:
                readline.parse_and_bind("set editing-mode vi")
            else:
                readline.parse_and_bind("set editing-mode emacs")
            
            # Configurações gerais
            readline.parse_and_bind("set completion-ignore-case on")
            readline.parse_and_bind("set show-all-if-ambiguous on")
            readline.parse_and_bind("set menu-complete-display-prefix on")
            
            # Tab completion
            readline.parse_and_bind("tab: complete")
            
            # Ctrl+R para busca
            readline.parse_and_bind("C-r: reverse-search-history")
            
            return True
            
        except ImportError:
            return False
    
    def get_key_from_input(self, prompt: str = "") -> str:
        """
        Captura input de tecla específica.
        Retorna a representação da tecla pressionada.
        """
        try:
            if sys.platform.startswith('win'):
                return self._get_key_windows()
            else:
                return self._get_key_unix()
        except Exception:
            return input(prompt)
    
    def _get_key_windows(self) -> str:
        """Captura tecla no Windows."""
        try:
            import msvcrt
            
            key = msvcrt.getch()
            
            # Teclas especiais
            if key == b'\x00' or key == b'\xe0':
                key = msvcrt.getch()
                special_keys = {
                    b'H': 'up',
                    b'P': 'down',
                    b'K': 'left',
                    b'M': 'right',
                    b'G': 'home',
                    b'O': 'end',
                    b'R': 'insert',
                    b'S': 'delete',
                    b'I': 'page_up',
                    b'Q': 'page_down',
                    b';': 'f1',
                    b'<': 'f2',
                    b'=': 'f3',
                    b'>': 'f4',
                    b'?': 'f5',
                    b'@': 'f6',
                    b'A': 'f7',
                    b'B': 'f8',
                    b'C': 'f9',
                    b'D': 'f10',
                }
                return special_keys.get(key, f'special_{ord(key)}')
            
            # Teclas de controle
            if ord(key) < 32:
                ctrl_keys = {
                    1: 'C-a', 2: 'C-b', 3: 'C-c', 4: 'C-d', 5: 'C-e',
                    6: 'C-f', 7: 'C-g', 8: 'C-h', 9: 'tab', 10: 'C-j',
                    11: 'C-k', 12: 'C-l', 13: 'enter', 14: 'C-n', 15: 'C-o',
                    16: 'C-p', 17: 'C-q', 18: 'C-r', 19: 'C-s', 20: 'C-t',
                    21: 'C-u', 22: 'C-v', 23: 'C-w', 24: 'C-x', 25: 'C-y',
                    26: 'C-z', 27: 'esc'
                }
                return ctrl_keys.get(ord(key), f'C-{chr(ord(key) + 64)}')
            
            # Teclas normais
            return key.decode('utf-8', errors='ignore')
            
        except ImportError:
            return input()
    
    def _get_key_unix(self) -> str:
        """Captura tecla no Unix/Linux."""
        try:
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                
                # Sequências especiais (começam com ESC)
                if ord(key) == 27:
                    key += sys.stdin.read(2)
                    
                    escape_sequences = {
                        '\x1b[A': 'up',
                        '\x1b[B': 'down', 
                        '\x1b[C': 'right',
                        '\x1b[D': 'left',
                        '\x1b[H': 'home',
                        '\x1b[F': 'end',
                        '\x1b[2~': 'insert',
                        '\x1b[3~': 'delete',
                        '\x1b[5~': 'page_up',
                        '\x1b[6~': 'page_down',
                    }
                    
                    if key in escape_sequences:
                        return escape_sequences[key]
                    elif len(key) == 1:
                        return 'esc'
                
                # Teclas de controle
                if ord(key) < 32:
                    ctrl_keys = {
                        1: 'C-a', 2: 'C-b', 3: 'C-c', 4: 'C-d', 5: 'C-e',
                        6: 'C-f', 7: 'C-g', 8: 'C-h', 9: 'tab', 10: 'enter',
                        11: 'C-k', 12: 'C-l', 13: 'enter', 14: 'C-n', 15: 'C-o',
                        16: 'C-p', 17: 'C-q', 18: 'C-r', 19: 'C-s', 20: 'C-t',
                        21: 'C-u', 22: 'C-v', 23: 'C-w', 24: 'C-x', 25: 'C-y',
                        26: 'C-z', 27: 'esc'
                    }
                    return ctrl_keys.get(ord(key), f'C-{chr(ord(key) + 64)}')
                
                return key
                
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except ImportError:
            return input()
    
    def create_custom_shortcut(self, name: str, key_sequence: str, 
                              command: str, description: str = ""):
        """Cria atalho customizado para comando."""
        # Implementação para atalhos personalizados
        # Permite criar atalhos como Ctrl+G para "/git status"
        pass
    
    def export_config(self) -> Dict[str, Any]:
        """Exporta configuração de atalhos."""
        return {
            'vim_mode': self.vim_mode,
            'emacs_mode': self.emacs_mode,
            'custom_bindings': {
                key: {
                    'action': binding.action.value,
                    'description': binding.description,
                    'condition': binding.condition
                }
                for key, binding in self.bindings.items()
                if not key.startswith(('C-', 'M-', 'tab', 'esc'))  # Apenas customizados
            }
        }
    
    def import_config(self, config: Dict[str, Any]):
        """Importa configuração de atalhos."""
        if 'vim_mode' in config:
            self.set_vim_mode(config['vim_mode'])
        
        if 'custom_bindings' in config:
            for key, binding_data in config['custom_bindings'].items():
                try:
                    action = KeyAction(binding_data['action'])
                    self.add_custom_binding(
                        key, 
                        action,
                        binding_data['description'],
                        binding_data.get('condition')
                    )
                except ValueError:
                    continue  # Skip invalid actions