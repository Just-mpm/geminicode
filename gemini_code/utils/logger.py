"""Sistema de logging."""
import logging
import sys
from pathlib import Path


class Logger:
    def __init__(self, name: str = 'gemini_code'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Cria handler se não existe
        if not self.logger.handlers:
            log_dir = Path('.gemini_code/logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Handler para arquivo com encoding UTF-8
            file_handler = logging.FileHandler(
                log_dir / 'gemini_code.log', 
                encoding='utf-8'
            )
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            
            # Handler para console com encoding seguro
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.ERROR)  # Só erros críticos no console
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _safe_message(self, message: str) -> str:
        """Remove emojis para compatibilidade com Windows CMD."""
        import re
        # Remove emojis Unicode
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub('', message).strip()
    
    def info(self, message: str):
        safe_msg = self._safe_message(message)
        self.logger.info(safe_msg)
    
    def error(self, message: str):
        safe_msg = self._safe_message(message)
        self.logger.error(safe_msg)
    
    def debug(self, message: str):
        safe_msg = self._safe_message(message)
        self.logger.debug(safe_msg)