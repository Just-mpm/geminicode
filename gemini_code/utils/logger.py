"""Sistema de logging."""
import logging
from pathlib import Path


class Logger:
    def __init__(self, name: str = 'gemini_code'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Cria handler se não existe
        if not self.logger.handlers:
            log_dir = Path('.gemini_code/logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            
            handler = logging.FileHandler(log_dir / 'gemini_code.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)