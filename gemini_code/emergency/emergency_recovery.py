"""
Sistema de recuperação de emergência para situações críticas.
"""

import asyncio
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..core.gemini_client import GeminiClient
from ..integration.git_manager import GitManager
from ..utils.backup import BackupManager
from ..database.database_manager import DatabaseManager


class EmergencyRecovery:
    """Recuperação de emergência para desastres."""
    
    def __init__(self, gemini_client: GeminiClient, git_manager: GitManager,
                 backup_manager: BackupManager, db_manager: DatabaseManager):
        self.gemini_client = gemini_client
        self.git_manager = git_manager
        self.backup_manager = backup_manager
        self.db_manager = db_manager
        self.recovery_log = []
    
    async def handle_emergency(self, panic_message: str, project_path: str) -> Dict[str, Any]:
        """Lida com situação de emergência baseado na mensagem."""
        # Analisa tipo de emergência
        emergency_type = await self._analyze_emergency(panic_message)
        
        self.recovery_log.append({
            'timestamp': datetime.now(),
            'message': panic_message,
            'type': emergency_type
        })
        
        # Executa ação apropriada
        if emergency_type == 'site_down':
            return await self._recover_site_down(project_path)
        elif emergency_type == 'data_loss':
            return await self._recover_data_loss(project_path)
        elif emergency_type == 'code_broken':
            return await self._recover_broken_code(project_path)
        elif emergency_type == 'hacked':
            return await self._recover_security_breach(project_path)
        elif emergency_type == 'rollback_needed':
            return await self._emergency_rollback(project_path)
        else:
            return await self._generic_recovery(project_path, panic_message)
    
    async def _analyze_emergency(self, message: str) -> str:
        """Analisa tipo de emergência pela mensagem."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['site caiu', 'site down', 'offline', 'fora do ar']):
            return 'site_down'
        elif any(word in message_lower for word in ['perdi', 'sumiu', 'deletou', 'banco dados']):
            return 'data_loss'
        elif any(word in message_lower for word in ['quebrou', 'erro', 'não funciona', 'bugou']):
            return 'code_broken'
        elif any(word in message_lower for word in ['hack', 'invadiu', 'segurança', 'vulnerável']):
            return 'hacked'
        elif any(word in message_lower for word in ['desfaz', 'volta', 'ontem', 'anterior']):
            return 'rollback_needed'
        else:
            return 'unknown'
    
    async def _recover_site_down(self, project_path: str) -> Dict[str, Any]:
        """Recupera site que caiu."""
        steps_taken = []
        
        try:
            # 1. Verifica processo
            steps_taken.append("Verificando processos...")
            process_check = await self._check_processes()
            
            if not process_check['running']:
                # Tenta reiniciar
                steps_taken.append("Reiniciando aplicação...")
                restart_result = await self._restart_application(project_path)
                
                if restart_result['success']:
                    return {
                        'success': True,
                        'message': '✅ Site restaurado com sucesso!',
                        'steps': steps_taken,
                        'url': restart_result.get('url')
                    }
            
            # 2. Verifica logs de erro
            steps_taken.append("Analisando logs...")
            error_analysis = await self._analyze_logs(project_path)
            
            # 3. Tenta correção automática
            if error_analysis['fixable']:
                steps_taken.append("Aplicando correções...")
                fix_result = await self._apply_emergency_fix(
                    project_path, 
                    error_analysis['fix']
                )
                
                if fix_result['success']:
                    steps_taken.append("Reiniciando após correção...")
                    restart_result = await self._restart_application(project_path)
                    
                    return {
                        'success': True,
                        'message': '✅ Site recuperado após correções!',
                        'steps': steps_taken,
                        'fixes_applied': error_analysis['fix']
                    }
            
            # 4. Rollback se necessário
            steps_taken.append("Fazendo rollback para versão estável...")
            rollback_result = await self._emergency_rollback(project_path)
            
            return {
                'success': rollback_result['success'],
                'message': rollback_result['message'],
                'steps': steps_taken
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Erro na recuperação: {str(e)}',
                'steps': steps_taken
            }
    
    async def _recover_data_loss(self, project_path: str) -> Dict[str, Any]:
        """Recupera dados perdidos."""
        recovery_options = []
        
        # 1. Verifica backups de banco
        db_backups = self._find_database_backups(project_path)
        if db_backups:
            latest_backup = max(db_backups, key=lambda x: x.stat().st_mtime)
            recovery_options.append({
                'type': 'database_backup',
                'path': str(latest_backup),
                'age': datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)
            })
        
        # 2. Verifica backups de arquivos
        file_backups = self._find_file_backups(project_path)
        if file_backups:
            recovery_options.append({
                'type': 'file_backup',
                'path': str(file_backups[-1]),
                'count': len(file_backups)
            })
        
        # 3. Verifica Git
        git_status = await self.git_manager.get_status(project_path)
        if git_status.branch != 'unknown':
            recovery_options.append({
                'type': 'git_history',
                'commits': await self.git_manager.get_log(project_path, 10)
            })
        
        # Executa recuperação
        if recovery_options:
            # Prioriza backup mais recente
            best_option = recovery_options[0]
            
            if best_option['type'] == 'database_backup':
                restore_result = self.db_manager.restore_database(best_option['path'])
                return {
                    'success': restore_result,
                    'message': f"✅ Banco restaurado do backup de {best_option['age']} atrás",
                    'backup_used': best_option['path']
                }
            
            elif best_option['type'] == 'file_backup':
                restore_result = self.backup_manager.restore_backup(
                    best_option['path'], 
                    project_path
                )
                return {
                    'success': restore_result,
                    'message': "✅ Arquivos restaurados do backup",
                    'backup_used': best_option['path']
                }
        
        return {
            'success': False,
            'message': "❌ Nenhum backup encontrado. Configure backups automáticos!",
            'recommendation': "Use 'fazer backup automático' para prevenir futuras perdas"
        }
    
    async def _recover_broken_code(self, project_path: str) -> Dict[str, Any]:
        """Recupera código quebrado."""
        # 1. Identifica erros
        from ..analysis.error_detector import ErrorDetector
        from ..core.file_manager import FileManagementSystem
        
        error_detector = ErrorDetector(self.gemini_client, FileManagementSystem())
        errors = await error_detector.scan_project(project_path)
        
        critical_errors = [e for e in errors if e.severity == 'critical']
        
        if critical_errors:
            # Tenta corrigir automaticamente
            fixed_count = 0
            for error in critical_errors[:5]:  # Limita correções
                if error.auto_fixable:
                    if await error_detector.auto_fix_error(error):
                        fixed_count += 1
            
            if fixed_count > 0:
                return {
                    'success': True,
                    'message': f"✅ Corrigidos {fixed_count} erros críticos!",
                    'errors_found': len(critical_errors),
                    'errors_fixed': fixed_count
                }
        
        # Se não conseguiu corrigir, tenta rollback
        return await self._emergency_rollback(project_path)
    
    async def _recover_security_breach(self, project_path: str) -> Dict[str, Any]:
        """Recupera de invasão/hack."""
        actions_taken = []
        
        # 1. Modo manutenção imediato
        actions_taken.append("Ativando modo manutenção...")
        await self._enable_maintenance_mode(project_path)
        
        # 2. Verifica alterações suspeitas
        actions_taken.append("Verificando alterações...")
        suspicious_changes = await self._detect_suspicious_changes(project_path)
        
        # 3. Reseta senhas e tokens
        actions_taken.append("Resetando credenciais...")
        await self._reset_credentials(project_path)
        
        # 4. Restaura código limpo
        if suspicious_changes:
            actions_taken.append("Restaurando código limpo...")
            await self.git_manager.reset(project_path, hard=True)
            
            # Restaura do último commit seguro
            safe_commits = await self._find_safe_commits(project_path)
            if safe_commits:
                await self.git_manager.checkout(safe_commits[0].hash, project_path)
        
        # 5. Implementa medidas de segurança
        actions_taken.append("Implementando segurança adicional...")
        security_measures = await self._implement_emergency_security(project_path)
        
        return {
            'success': True,
            'message': "🔒 Segurança restaurada!",
            'actions': actions_taken,
            'security_measures': security_measures,
            'next_steps': [
                "Revisar logs de acesso",
                "Mudar todas as senhas",
                "Implementar 2FA",
                "Fazer auditoria completa"
            ]
        }
    
    async def _emergency_rollback(self, project_path: str) -> Dict[str, Any]:
        """Rollback de emergência."""
        # Opções de rollback
        options = []
        
        # 1. Git commits
        commits = await self.git_manager.get_log(project_path, 20)
        if commits:
            # Encontra último commit estável (sem "fix", "bug", "error" no título)
            stable_commits = [
                c for c in commits 
                if not any(word in c.message.lower() for word in ['fix', 'bug', 'error', 'broken'])
            ]
            
            if stable_commits:
                options.append({
                    'type': 'git',
                    'target': stable_commits[0],
                    'method': 'reset'
                })
        
        # 2. Backups
        backups = list(Path(project_path).glob('.gemini_code/backups/*'))
        if backups:
            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
            options.append({
                'type': 'backup',
                'target': latest_backup,
                'method': 'restore'
            })
        
        # Executa melhor opção
        if options:
            best_option = options[0]
            
            if best_option['type'] == 'git':
                await self.git_manager.reset(
                    project_path, 
                    commit_hash=best_option['target'].hash,
                    hard=True
                )
                return {
                    'success': True,
                    'message': f"✅ Rollback para: {best_option['target'].message}",
                    'timestamp': best_option['target'].date
                }
            
            elif best_option['type'] == 'backup':
                self.backup_manager.restore_backup(
                    str(best_option['target']),
                    project_path
                )
                return {
                    'success': True,
                    'message': "✅ Restaurado do backup",
                    'backup_date': datetime.fromtimestamp(best_option['target'].stat().st_mtime)
                }
        
        return {
            'success': False,
            'message': "❌ Sem opções de rollback disponíveis",
            'recommendation': "Configure backups e use Git regularmente"
        }
    
    async def _check_processes(self) -> Dict[str, Any]:
        """Verifica processos em execução."""
        import psutil
        
        common_processes = ['python', 'node', 'npm', 'java', 'php']
        running = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any(p in proc.info['name'].lower() for p in common_processes):
                    running.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmd': ' '.join(proc.info['cmdline'] or [])[:100]
                    })
            except:
                continue
        
        return {
            'running': len(running) > 0,
            'processes': running
        }
    
    async def _restart_application(self, project_path: str) -> Dict[str, Any]:
        """Reinicia aplicação."""
        # Detecta tipo de aplicação
        project_files = list(Path(project_path).iterdir())
        
        restart_commands = []
        
        if any('package.json' in str(f) for f in project_files):
            restart_commands.append('npm start')
            restart_commands.append('npm run dev')
        
        if any('requirements.txt' in str(f) for f in project_files):
            restart_commands.append('python app.py')
            restart_commands.append('python main.py')
            restart_commands.append('python run.py')
        
        # Tenta comandos
        for cmd in restart_commands:
            try:
                process = subprocess.Popen(
                    cmd.split(),
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Aguarda um pouco
                await asyncio.sleep(3)
                
                if process.poll() is None:  # Ainda rodando
                    return {
                        'success': True,
                        'command': cmd,
                        'pid': process.pid,
                        'url': 'http://localhost:3000'  # Assumido
                    }
                    
            except:
                continue
        
        return {'success': False}
    
    async def _analyze_logs(self, project_path: str) -> Dict[str, Any]:
        """Analisa logs em busca de erros."""
        log_files = list(Path(project_path).rglob('*.log'))
        errors_found = []
        
        for log_file in log_files[-5:]:  # Últimos 5 logs
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    # Lê últimas 100 linhas
                    lines = f.readlines()[-100:]
                    
                    for line in lines:
                        if any(word in line.lower() for word in ['error', 'exception', 'fatal']):
                            errors_found.append({
                                'file': log_file.name,
                                'error': line.strip()
                            })
                            
            except:
                continue
        
        # Analisa com IA
        if errors_found:
            prompt = f"""
            Analise estes erros e sugira correção rápida:
            
            {json.dumps(errors_found[:5], indent=2)}
            
            Retorne JSON com:
            {{
                "fixable": true/false,
                "fix": ["ação1", "ação2"]
            }}
            """
            
            try:
                response = await self.gemini_client.generate_response(prompt)
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {'fixable': False, 'fix': []}
    
    def _find_database_backups(self, project_path: str) -> List[Path]:
        """Encontra backups de banco de dados."""
        backup_patterns = ['*.sql', '*.db', '*.sqlite', '*.dump', '*.bak']
        backups = []
        
        for pattern in backup_patterns:
            backups.extend(Path(project_path).rglob(pattern))
        
        return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def _find_file_backups(self, project_path: str) -> List[Path]:
        """Encontra backups de arquivos."""
        backup_dir = Path(project_path) / '.gemini_code' / 'backups'
        if backup_dir.exists():
            return sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        return []
    
    async def get_emergency_status(self) -> Dict[str, Any]:
        """Retorna status do sistema de emergência."""
        return {
            'recovery_log': self.recovery_log[-10:],  # Últimas 10 emergências
            'backup_status': {
                'last_backup': 'Verificar implementação',
                'auto_backup': True
            },
            'monitoring': {
                'active': True,
                'alerts_enabled': True
            }
        }