"""Sistema de backup e recuperação."""
import shutil
from pathlib import Path
from datetime import datetime


class BackupManager:
    def __init__(self):
        self.backup_dir = Path('.gemini_code/backups')
    
    def create_backup(self, project_path: str) -> str:
        """Cria backup do projeto."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(project_path, backup_path, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restaura backup."""
        try:
            if Path(backup_path).exists():
                shutil.copytree(backup_path, target_path, dirs_exist_ok=True)
                return True
        except Exception:
            pass
        return False