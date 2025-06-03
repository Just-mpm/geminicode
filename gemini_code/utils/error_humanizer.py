"""
Humanizador de erros para o modo non-programmer
Converte erros técnicos em mensagens amigáveis
"""

import re
import traceback
from typing import Dict, Any, Optional


class ErrorHumanizer:
    """Converte erros técnicos em mensagens amigáveis para usuários não-programadores"""
    
    def __init__(self):
        self.error_patterns = {
            # Erros de arquivo/pasta
            'FileNotFoundError': {
                'pattern': r"FileNotFoundError.*'([^']+)'",
                'message': "❌ Não consegui encontrar o arquivo '{file}'. Verifique se o caminho está correto.",
                'suggestion': "💡 Dica: Certifique-se de que o arquivo existe e que você tem permissão para acessá-lo."
            },
            'PermissionError': {
                'pattern': r"PermissionError.*'([^']+)'",
                'message': "❌ Não tenho permissão para acessar '{file}'. Verifique as permissões.",
                'suggestion': "💡 Dica: Execute como administrador ou verifique as permissões do arquivo."
            },
            'IsADirectoryError': {
                'pattern': r"IsADirectoryError.*'([^']+)'",
                'message': "❌ '{file}' é uma pasta, não um arquivo. Preciso de um arquivo específico.",
                'suggestion': "💡 Dica: Especifique o nome de um arquivo dentro da pasta."
            },
            
            # Erros de API/Conexão
            'ConnectionError': {
                'pattern': r"ConnectionError",
                'message': "❌ Problema de conexão com a internet. Verifique sua conexão.",
                'suggestion': "💡 Dica: Aguarde um momento e tente novamente. Se persistir, verifique sua conexão."
            },
            'TimeoutError': {
                'pattern': r"TimeoutError",
                'message': "❌ A operação demorou muito para responder. Vou tentar novamente.",
                'suggestion': "💡 Dica: Isso pode acontecer com arquivos muito grandes ou conexão lenta."
            },
            'requests.exceptions.ConnectionError': {
                'pattern': r"requests\.exceptions\.ConnectionError",
                'message': "❌ Não consegui conectar com o serviço. Verifique sua internet.",
                'suggestion': "💡 Dica: Certifique-se de que está conectado à internet."
            },
            
            # Erros de API Gemini
            'google.api_core.exceptions.Unauthenticated': {
                'pattern': r"Unauthenticated",
                'message': "❌ Problema com a chave da API do Gemini. Verifique sua configuração.",
                'suggestion': "💡 Dica: Confirme se sua API_KEY está correta no arquivo de configuração."
            },
            'google.api_core.exceptions.QuotaExceeded': {
                'pattern': r"QuotaExceeded",
                'message': "❌ Limite de uso da API atingido. Aguarde um pouco antes de tentar novamente.",
                'suggestion': "💡 Dica: O Gemini tem limites de uso. Tente novamente em alguns minutos."
            },
            
            # Erros de código Python
            'SyntaxError': {
                'pattern': r"SyntaxError.*line (\d+)",
                'message': "❌ Há um erro de sintaxe no código na linha {line}.",
                'suggestion': "💡 Dica: Verifique parênteses, aspas e indentação na linha indicada."
            },
            'IndentationError': {
                'pattern': r"IndentationError",
                'message': "❌ Problema com a indentação (espaçamento) do código.",
                'suggestion': "💡 Dica: Em Python, a indentação é importante. Use sempre a mesma quantidade de espaços."
            },
            'ModuleNotFoundError': {
                'pattern': r"ModuleNotFoundError.*'([^']+)'",
                'message': "❌ Não encontrei o módulo '{module}'. Pode ser que não esteja instalado.",
                'suggestion': "💡 Dica: Tente instalar com 'pip install {module}' ou verifique se está escrito corretamente."
            },
            
            # Erros do sistema
            'OSError': {
                'pattern': r"OSError",
                'message': "❌ Problema do sistema operacional. Algo não está funcionando como esperado.",
                'suggestion': "💡 Dica: Tente reiniciar o programa ou verificar as permissões."
            },
            'MemoryError': {
                'pattern': r"MemoryError",
                'message': "❌ Memória insuficiente. O arquivo ou operação é muito grande.",
                'suggestion': "💡 Dica: Tente com arquivos menores ou feche outros programas."
            },
            
            # Erros de valor/tipo
            'ValueError': {
                'pattern': r"ValueError.*'([^']*)'",
                'message': "❌ Valor inválido fornecido: '{value}'.",
                'suggestion': "💡 Dica: Verifique se os valores estão no formato correto."
            },
            'TypeError': {
                'pattern': r"TypeError",
                'message': "❌ Tipo de dado incorreto. Algo não está no formato esperado.",
                'suggestion': "💡 Dica: Verifique se está usando texto onde deveria ser número, ou vice-versa."
            },
            'KeyError': {
                'pattern': r"KeyError.*'([^']+)'",
                'message': "❌ Não encontrei a chave '{key}' nos dados.",
                'suggestion': "💡 Dica: Verifique se o nome está escrito corretamente."
            },
            
            # Erros específicos do Gemini Code
            'NoneType.*generate_response': {
                'pattern': r"'NoneType'.*'generate_response'",
                'message': "❌ Problema interno de comunicação. Vou tentar reinicializar.",
                'suggestion': "💡 Dica: Isso pode acontecer no início. Aguarde um momento."
            },
            'database disk image is malformed': {
                'pattern': r"database disk image is malformed",
                'message': "❌ Banco de dados corrompido. Vou tentar recuperar automaticamente.",
                'suggestion': "💡 Dica: Não se preocupe, posso restaurar de um backup."
            }
        }
        
        self.encouragement_messages = [
            "🤗 Não se preocupe, vamos resolver isso juntos!",
            "💪 Todo problema tem solução. Vamos encontrar uma forma!",
            "😊 Isso acontece com todos. Vou te ajudar a corrigir!",
            "🚀 Vamos superar isso e continuar nosso trabalho!",
            "🌟 Cada erro é uma oportunidade de aprender algo novo!"
        ]
    
    def humanize_error(self, error: Exception, context: Optional[str] = None) -> Dict[str, str]:
        """
        Converte um erro técnico em uma mensagem humanizada
        
        Args:
            error: A exceção capturada
            context: Contexto adicional sobre o que estava sendo feito
            
        Returns:
            Dict com 'message', 'suggestion' e 'encouragement'
        """
        error_str = str(error)
        error_type = type(error).__name__
        
        # Tenta encontrar um padrão conhecido
        for pattern_name, pattern_info in self.error_patterns.items():
            if re.search(pattern_info['pattern'], error_str, re.IGNORECASE):
                # Extrai variáveis do erro (como nome do arquivo, linha, etc.)
                match = re.search(pattern_info['pattern'], error_str, re.IGNORECASE)
                variables = {}
                
                if match and match.groups():
                    if 'file' in pattern_info['message']:
                        variables['file'] = match.group(1)
                    elif 'line' in pattern_info['message']:
                        variables['line'] = match.group(1)
                    elif 'module' in pattern_info['message']:
                        variables['module'] = match.group(1)
                    elif 'key' in pattern_info['message']:
                        variables['key'] = match.group(1)
                    elif 'value' in pattern_info['message']:
                        variables['value'] = match.group(1)
                
                # Formata a mensagem com as variáveis
                message = pattern_info['message'].format(**variables)
                suggestion = pattern_info['suggestion'].format(**variables)
                
                return {
                    'message': message,
                    'suggestion': suggestion,
                    'encouragement': self._get_random_encouragement(),
                    'context': context or "Durante a operação solicitada"
                }
        
        # Se não encontrou um padrão específico, usa uma mensagem genérica baseada no tipo
        generic_messages = {
            'AttributeError': "❌ Algo não está configurado corretamente internamente.",
            'ImportError': "❌ Não consegui carregar um componente necessário.",
            'RuntimeError': "❌ Algo deu errado durante a execução.",
            'Exception': "❌ Ocorreu um erro inesperado."
        }
        
        generic_message = generic_messages.get(error_type, "❌ Encontrei um problema técnico.")
        
        return {
            'message': generic_message,
            'suggestion': "💡 Dica: Tente novamente ou me conte mais detalhes sobre o que estava fazendo.",
            'encouragement': self._get_random_encouragement(),
            'context': context or "Durante a operação solicitada",
            'technical_details': f"Erro técnico: {error_type}: {error_str}" if error_str else f"Erro técnico: {error_type}"
        }
    
    def _get_random_encouragement(self) -> str:
        """Retorna uma mensagem de encorajamento aleatória"""
        import random
        return random.choice(self.encouragement_messages)
    
    def format_user_friendly_error(self, error: Exception, context: Optional[str] = None, 
                                  show_technical: bool = False) -> str:
        """
        Formata um erro completo para exibição ao usuário
        
        Args:
            error: A exceção capturada
            context: Contexto do que estava sendo feito
            show_technical: Se deve mostrar detalhes técnicos
            
        Returns:
            String formatada para exibição
        """
        humanized = self.humanize_error(error, context)
        
        result = []
        
        # Contexto
        if humanized['context']:
            result.append(f"📍 **{humanized['context']}**")
            result.append("")
        
        # Mensagem principal
        result.append(humanized['message'])
        result.append("")
        
        # Sugestão
        result.append(humanized['suggestion'])
        result.append("")
        
        # Encorajamento
        result.append(humanized['encouragement'])
        
        # Detalhes técnicos (opcional)
        if show_technical and 'technical_details' in humanized:
            result.append("")
            result.append("🔧 **Detalhes técnicos:**")
            result.append(f"```\n{humanized['technical_details']}\n```")
        
        return "\n".join(result)


# Instância global para uso fácil
error_humanizer = ErrorHumanizer()


def humanize_error(error: Exception, context: Optional[str] = None, 
                  show_technical: bool = False) -> str:
    """
    Função de conveniência para humanizar erros
    
    Args:
        error: A exceção capturada
        context: Contexto do que estava sendo feito
        show_technical: Se deve mostrar detalhes técnicos
        
    Returns:
        String formatada para exibição amigável
    """
    return error_humanizer.format_user_friendly_error(error, context, show_technical)