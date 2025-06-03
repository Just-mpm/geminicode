"""
Gerenciador de deploy automático para diferentes plataformas.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..core.gemini_client import GeminiClient
from ..execution.command_executor import CommandExecutor, CommandContext


@dataclass
class DeploymentConfig:
    """Configuração de deployment."""
    platform: str
    environment: str  # 'development', 'staging', 'production'
    settings: Dict[str, Any]


@dataclass
class DeploymentResult:
    """Resultado de um deployment."""
    success: bool
    platform: str
    environment: str
    url: Optional[str]
    deployment_time: float
    logs: List[str]
    error_message: Optional[str] = None


class DeploymentManager:
    """Gerencia deployments automáticos."""
    
    def __init__(self, gemini_client: GeminiClient, command_executor: CommandExecutor):
        self.gemini_client = gemini_client
        self.command_executor = command_executor
        self.platforms = self._init_platforms()
    
    def _init_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa configurações de plataformas suportadas."""
        return {
            'heroku': {
                'commands': {
                    'login': 'heroku login',
                    'create': 'heroku create {app_name}',
                    'deploy': 'git push heroku main',
                    'logs': 'heroku logs --tail'
                },
                'files_required': ['requirements.txt', 'Procfile'],
                'env_vars': ['HEROKU_API_KEY']
            },
            'vercel': {
                'commands': {
                    'login': 'vercel login',
                    'deploy': 'vercel --prod',
                    'logs': 'vercel logs'
                },
                'files_required': ['package.json'],
                'env_vars': ['VERCEL_TOKEN']
            },
            'netlify': {
                'commands': {
                    'login': 'netlify login',
                    'deploy': 'netlify deploy --prod',
                    'logs': 'netlify logs'
                },
                'files_required': [],
                'env_vars': ['NETLIFY_AUTH_TOKEN']
            },
            'docker': {
                'commands': {
                    'build': 'docker build -t {image_name} .',
                    'run': 'docker run -p 80:80 {image_name}',
                    'push': 'docker push {image_name}'
                },
                'files_required': ['Dockerfile'],
                'env_vars': []
            }
        }
    
    async def detect_platform(self, project_path: str) -> Optional[str]:
        """Detecta plataforma apropriada baseada no projeto."""
        project_path = Path(project_path)
        
        # Verifica arquivos específicos
        if (project_path / 'package.json').exists():
            return 'vercel'
        elif (project_path / 'requirements.txt').exists():
            return 'heroku'
        elif (project_path / 'Dockerfile').exists():
            return 'docker'
        elif any((project_path).rglob('*.html')):
            return 'netlify'
        
        return None
    
    async def prepare_deployment(self, project_path: str, platform: str, 
                               environment: str = 'production') -> bool:
        """Prepara projeto para deployment."""
        platform_config = self.platforms.get(platform)
        if not platform_config:
            return False
        
        project_path = Path(project_path)
        
        # Verifica arquivos necessários
        for required_file in platform_config['files_required']:
            if not (project_path / required_file).exists():
                await self._create_required_file(project_path, required_file, platform)
        
        # Cria configurações específicas da plataforma
        if platform == 'heroku':
            await self._prepare_heroku(project_path)
        elif platform == 'vercel':
            await self._prepare_vercel(project_path)
        elif platform == 'netlify':
            await self._prepare_netlify(project_path)
        elif platform == 'docker':
            await self._prepare_docker(project_path)
        
        return True
    
    async def _create_required_file(self, project_path: Path, filename: str, platform: str) -> None:
        """Cria arquivo necessário para deployment."""
        if filename == 'Procfile' and platform == 'heroku':
            # Detecta arquivo principal Python
            main_files = ['app.py', 'main.py', 'server.py', 'wsgi.py']
            main_file = None
            
            for file in main_files:
                if (project_path / file).exists():
                    main_file = file
                    break
            
            if main_file:
                procfile_content = f"web: python {main_file}"
            else:
                procfile_content = "web: python app.py"
            
            with open(project_path / 'Procfile', 'w') as f:
                f.write(procfile_content)
        
        elif filename == 'Dockerfile' and platform == 'docker':
            await self._generate_dockerfile(project_path)
        
        elif filename == 'requirements.txt':
            await self._generate_requirements(project_path)
    
    async def _generate_dockerfile(self, project_path: Path) -> None:
        """Gera Dockerfile usando IA."""
        try:
            # Analisa estrutura do projeto
            project_files = [f.name for f in project_path.iterdir() if f.is_file()]
            
            prompt = f"""
            Gere um Dockerfile otimizado para este projeto Python:
            
            Arquivos no projeto: {', '.join(project_files)}
            
            Considere:
            - Uso de Python slim ou alpine
            - Multi-stage build se necessário
            - Caching de dependências
            - Usuário não-root
            - Porta apropriada
            
            Retorne apenas o conteúdo do Dockerfile.
            """
            
            response = await self.gemini_client.generate_response(prompt)
            
            # Remove markdown se houver
            dockerfile_content = response.strip()
            if dockerfile_content.startswith('```'):
                dockerfile_content = '\n'.join(dockerfile_content.split('\n')[1:-1])
            
            with open(project_path / 'Dockerfile', 'w') as f:
                f.write(dockerfile_content)
                
        except Exception:
            # Dockerfile básico
            basic_dockerfile = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]"""
            
            with open(project_path / 'Dockerfile', 'w') as f:
                f.write(basic_dockerfile)
    
    async def _generate_requirements(self, project_path: Path) -> None:
        """Gera requirements.txt analisando imports."""
        try:
            imports = set()
            
            # Analisa arquivos Python
            for py_file in project_path.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extrai imports
                    import re
                    import_patterns = [
                        r'import\s+(\w+)',
                        r'from\s+(\w+)\s+import'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        imports.update(matches)
                        
                except:
                    continue
            
            # Remove built-ins
            builtin_modules = {
                'os', 'sys', 'json', 're', 'time', 'datetime', 'math',
                'random', 'collections', 'itertools', 'functools', 'pathlib'
            }
            
            external_imports = imports - builtin_modules
            
            # Mapeia para nomes PyPI conhecidos
            pypi_mapping = {
                'flask': 'Flask',
                'django': 'Django',
                'fastapi': 'fastapi',
                'requests': 'requests',
                'numpy': 'numpy',
                'pandas': 'pandas',
                'matplotlib': 'matplotlib'
            }
            
            requirements = []
            for imp in external_imports:
                if imp in pypi_mapping:
                    requirements.append(pypi_mapping[imp])
                elif len(imp) > 2:  # Evita imports muito curtos
                    requirements.append(imp)
            
            if requirements:
                with open(project_path / 'requirements.txt', 'w') as f:
                    f.write('\n'.join(sorted(requirements)))
            
        except Exception:
            # Requirements básico
            with open(project_path / 'requirements.txt', 'w') as f:
                f.write('flask\nrequests\n')
    
    async def _prepare_heroku(self, project_path: Path) -> None:
        """Prepara projeto para Heroku."""
        # Cria runtime.txt se necessário
        if not (project_path / 'runtime.txt').exists():
            with open(project_path / 'runtime.txt', 'w') as f:
                f.write('python-3.9.18')
    
    async def _prepare_vercel(self, project_path: Path) -> None:
        """Prepara projeto para Vercel."""
        # Cria vercel.json se necessário
        vercel_config = {
            "version": 2,
            "builds": [
                {"src": "*.py", "use": "@vercel/python"}
            ],
            "routes": [
                {"src": "/(.*)", "dest": "/app.py"}
            ]
        }
        
        if not (project_path / 'vercel.json').exists():
            with open(project_path / 'vercel.json', 'w') as f:
                json.dump(vercel_config, f, indent=2)
    
    async def _prepare_netlify(self, project_path: Path) -> None:
        """Prepara projeto para Netlify."""
        # Cria _redirects se necessário
        if not (project_path / '_redirects').exists():
            with open(project_path / '_redirects', 'w') as f:
                f.write('/*    /index.html   200')
    
    async def _prepare_docker(self, project_path: Path) -> None:
        """Prepara projeto para Docker."""
        # Cria .dockerignore
        dockerignore_content = """__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
README.md
.env
.venv
venv/"""
        
        if not (project_path / '.dockerignore').exists():
            with open(project_path / '.dockerignore', 'w') as f:
                f.write(dockerignore_content)
    
    async def deploy(self, project_path: str, platform: str, environment: str = 'production',
                    app_name: Optional[str] = None) -> DeploymentResult:
        """Executa deployment."""
        start_time = datetime.now()
        logs = []
        
        # Prepara deployment
        prep_success = await self.prepare_deployment(project_path, platform, environment)
        if not prep_success:
            return DeploymentResult(
                success=False,
                platform=platform,
                environment=environment,
                url=None,
                deployment_time=0,
                logs=[],
                error_message="Falha na preparação do deployment"
            )
        
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=300.0,  # 5 minutos
            safe_mode=True
        )
        
        try:
            if platform == 'heroku':
                result = await self._deploy_heroku(context, app_name, logs)
            elif platform == 'vercel':
                result = await self._deploy_vercel(context, logs)
            elif platform == 'netlify':
                result = await self._deploy_netlify(context, logs)
            elif platform == 'docker':
                result = await self._deploy_docker(context, app_name or 'app', logs)
            else:
                result = DeploymentResult(
                    success=False,
                    platform=platform,
                    environment=environment,
                    url=None,
                    deployment_time=0,
                    logs=[],
                    error_message=f"Plataforma {platform} não suportada"
                )
            
            result.deployment_time = (datetime.now() - start_time).total_seconds()
            result.logs = logs
            
            return result
            
        except Exception as e:
            return DeploymentResult(
                success=False,
                platform=platform,
                environment=environment,
                url=None,
                deployment_time=(datetime.now() - start_time).total_seconds(),
                logs=logs,
                error_message=str(e)
            )
    
    async def _deploy_heroku(self, context: CommandContext, app_name: Optional[str], logs: List[str]) -> DeploymentResult:
        """Deploy para Heroku."""
        # Login (assume que já está logado ou tem token)
        
        # Cria app se nome fornecido
        if app_name:
            create_result = await self.command_executor.execute_command(
                f"heroku create {app_name}", context
            )
            logs.append(f"Create app: {create_result.exit_code}")
        
        # Deploy via Git
        deploy_result = await self.command_executor.execute_command(
            "git push heroku main", context
        )
        
        success = deploy_result.exit_code == 0
        url = f"https://{app_name}.herokuapp.com" if app_name and success else None
        
        return DeploymentResult(
            success=success,
            platform='heroku',
            environment='production',
            url=url,
            deployment_time=0,
            logs=[],
            error_message=deploy_result.stderr if not success else None
        )
    
    async def _deploy_vercel(self, context: CommandContext, logs: List[str]) -> DeploymentResult:
        """Deploy para Vercel."""
        deploy_result = await self.command_executor.execute_command(
            "vercel --prod", context
        )
        
        success = deploy_result.exit_code == 0
        
        # Extrai URL da saída
        url = None
        if success and deploy_result.stdout:
            import re
            url_match = re.search(r'https://[^\s]+\.vercel\.app', deploy_result.stdout)
            if url_match:
                url = url_match.group()
        
        return DeploymentResult(
            success=success,
            platform='vercel',
            environment='production',
            url=url,
            deployment_time=0,
            logs=[],
            error_message=deploy_result.stderr if not success else None
        )
    
    async def _deploy_netlify(self, context: CommandContext, logs: List[str]) -> DeploymentResult:
        """Deploy para Netlify."""
        deploy_result = await self.command_executor.execute_command(
            "netlify deploy --prod", context
        )
        
        success = deploy_result.exit_code == 0
        
        # Extrai URL da saída
        url = None
        if success and deploy_result.stdout:
            import re
            url_match = re.search(r'https://[^\s]+\.netlify\.app', deploy_result.stdout)
            if url_match:
                url = url_match.group()
        
        return DeploymentResult(
            success=success,
            platform='netlify',
            environment='production',
            url=url,
            deployment_time=0,
            logs=[],
            error_message=deploy_result.stderr if not success else None
        )
    
    async def _deploy_docker(self, context: CommandContext, image_name: str, logs: List[str]) -> DeploymentResult:
        """Deploy usando Docker."""
        # Build da imagem
        build_result = await self.command_executor.execute_command(
            f"docker build -t {image_name} .", context
        )
        
        if build_result.exit_code != 0:
            return DeploymentResult(
                success=False,
                platform='docker',
                environment='production',
                url=None,
                deployment_time=0,
                logs=[],
                error_message=f"Falha no build: {build_result.stderr}"
            )
        
        # Run da imagem
        run_result = await self.command_executor.execute_command(
            f"docker run -d -p 8000:8000 {image_name}", context
        )
        
        success = run_result.exit_code == 0
        url = "http://localhost:8000" if success else None
        
        return DeploymentResult(
            success=success,
            platform='docker',
            environment='production',
            url=url,
            deployment_time=0,
            logs=[],
            error_message=run_result.stderr if not success else None
        )
    
    async def generate_deployment_report(self, result: DeploymentResult) -> str:
        """Gera relatório de deployment."""
        status_emoji = "✅" if result.success else "❌"
        
        report = f"{status_emoji} **Relatório de Deploy**\n\n"
        report += f"🚀 **Plataforma**: {result.platform}\n"
        report += f"🌍 **Ambiente**: {result.environment}\n"
        report += f"⏱️ **Tempo**: {result.deployment_time:.1f}s\n"
        
        if result.success:
            report += f"🎉 **Status**: Sucesso!\n"
            if result.url:
                report += f"🔗 **URL**: {result.url}\n"
        else:
            report += f"💥 **Status**: Falhou\n"
            if result.error_message:
                report += f"❗ **Erro**: {result.error_message}\n"
        
        if result.logs:
            report += f"\n📋 **Logs**:\n"
            for log in result.logs[-5:]:  # Últimos 5 logs
                report += f"- {log}\n"
        
        return report