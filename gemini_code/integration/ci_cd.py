"""
Gerenciador de CI/CD que automatiza pipelines de desenvolvimento.
"""

import asyncio
import yaml
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..core.gemini_client import GeminiClient
from ..execution.command_executor import CommandExecutor, CommandContext


@dataclass
class PipelineStep:
    """Passo de um pipeline CI/CD."""
    name: str
    command: str
    condition: Optional[str] = None
    timeout: float = 300.0
    allow_failure: bool = False


@dataclass
class PipelineResult:
    """Resultado de execução de pipeline."""
    success: bool
    total_time: float
    steps_executed: int
    steps_failed: int
    failed_steps: List[str]
    logs: Dict[str, str]


class CICDManager:
    """Gerencia pipelines de CI/CD."""
    
    def __init__(self, gemini_client: GeminiClient, command_executor: CommandExecutor):
        self.gemini_client = gemini_client
        self.command_executor = command_executor
        self.pipeline_templates = self._load_pipeline_templates()
    
    def _load_pipeline_templates(self) -> Dict[str, List[PipelineStep]]:
        """Carrega templates de pipeline."""
        return {
            'python': [
                PipelineStep("Setup", "pip install -r requirements.txt"),
                PipelineStep("Lint", "flake8 . --max-line-length=88"),
                PipelineStep("Type Check", "mypy ."),
                PipelineStep("Tests", "pytest -v --cov=."),
                PipelineStep("Security", "safety check"),
                PipelineStep("Build", "python setup.py sdist bdist_wheel")
            ],
            'javascript': [
                PipelineStep("Setup", "npm install"),
                PipelineStep("Lint", "npm run lint"),
                PipelineStep("Tests", "npm test"),
                PipelineStep("Build", "npm run build"),
                PipelineStep("Security", "npm audit")
            ],
            'docker': [
                PipelineStep("Build", "docker build -t app ."),
                PipelineStep("Test", "docker run --rm app pytest"),
                PipelineStep("Security Scan", "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image app")
            ]
        }
    
    async def detect_project_type(self, project_path: str) -> str:
        """Detecta tipo de projeto para CI/CD."""
        project_path = Path(project_path)
        
        if (project_path / 'requirements.txt').exists() or (project_path / 'setup.py').exists():
            return 'python'
        elif (project_path / 'package.json').exists():
            return 'javascript'
        elif (project_path / 'Dockerfile').exists():
            return 'docker'
        else:
            return 'generic'
    
    async def generate_pipeline_config(self, project_path: str, platform: str = 'github') -> str:
        """Gera configuração de pipeline CI/CD."""
        project_type = await self.detect_project_type(project_path)
        steps = self.pipeline_templates.get(project_type, [])
        
        if platform == 'github':
            return await self._generate_github_actions(steps, project_type)
        elif platform == 'gitlab':
            return await self._generate_gitlab_ci(steps, project_type)
        elif platform == 'jenkins':
            return await self._generate_jenkinsfile(steps, project_type)
        else:
            return await self._generate_generic_pipeline(steps, project_type)
    
    async def _generate_github_actions(self, steps: List[PipelineStep], project_type: str) -> str:
        """Gera workflow do GitHub Actions."""
        workflow = {
            'name': f'CI/CD Pipeline - {project_type.title()}',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main']}
            },
            'jobs': {
                'ci': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v3'
                        }
                    ]
                }
            }
        }
        
        # Adiciona setup específico
        if project_type == 'python':
            workflow['jobs']['ci']['steps'].append({
                'name': 'Setup Python',
                'uses': 'actions/setup-python@v4',
                'with': {'python-version': '3.9'}
            })
        elif project_type == 'javascript':
            workflow['jobs']['ci']['steps'].append({
                'name': 'Setup Node.js',
                'uses': 'actions/setup-node@v3',
                'with': {'node-version': '16'}
            })
        
        # Adiciona steps do pipeline
        for step in steps:
            workflow['jobs']['ci']['steps'].append({
                'name': step.name,
                'run': step.command,
                'continue-on-error': step.allow_failure
            })
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)
    
    async def _generate_gitlab_ci(self, steps: List[PipelineStep], project_type: str) -> str:
        """Gera .gitlab-ci.yml."""
        stages = ['test', 'build', 'deploy']
        
        config = {
            'stages': stages,
            'image': 'python:3.9' if project_type == 'python' else 'node:16'
        }
        
        # Mapeia steps para stages
        for i, step in enumerate(steps):
            stage = 'test' if i < 3 else 'build' if i < 5 else 'deploy'
            
            job_name = step.name.lower().replace(' ', '_')
            config[job_name] = {
                'stage': stage,
                'script': [step.command],
                'allow_failure': step.allow_failure
            }
        
        return yaml.dump(config, default_flow_style=False)
    
    async def _generate_jenkinsfile(self, steps: List[PipelineStep], project_type: str) -> str:
        """Gera Jenkinsfile."""
        jenkinsfile = f"""pipeline {{
    agent any
    
    stages {{"""
        
        for step in steps:
            jenkinsfile += f"""
        stage('{step.name}') {{
            steps {{
                sh '{step.command}'
            }}"""
            
            if step.allow_failure:
                jenkinsfile += """
            post {
                failure {
                    echo 'Step failed but continuing...'
                }
            }"""
            
            jenkinsfile += """
        }"""
        
        jenkinsfile += """
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}"""
        
        return jenkinsfile
    
    async def _generate_generic_pipeline(self, steps: List[PipelineStep], project_type: str) -> str:
        """Gera pipeline genérico."""
        script = "#!/bin/bash\n\n"
        script += f"# CI/CD Pipeline for {project_type} project\n\n"
        script += "set -e\n\n"
        
        for step in steps:
            script += f"echo 'Running: {step.name}'\n"
            if step.allow_failure:
                script += f"{step.command} || echo 'Step failed but continuing...'\n"
            else:
                script += f"{step.command}\n"
            script += "\n"
        
        script += "echo 'Pipeline completed successfully!'\n"
        
        return script
    
    async def setup_ci_cd(self, project_path: str, platform: str = 'github') -> bool:
        """Configura CI/CD no projeto."""
        config_content = await self.generate_pipeline_config(project_path, platform)
        
        # Determina arquivo e pasta de destino
        if platform == 'github':
            config_dir = Path(project_path) / '.github' / 'workflows'
            config_file = 'ci.yml'
        elif platform == 'gitlab':
            config_dir = Path(project_path)
            config_file = '.gitlab-ci.yml'
        elif platform == 'jenkins':
            config_dir = Path(project_path)
            config_file = 'Jenkinsfile'
        else:
            config_dir = Path(project_path)
            config_file = 'pipeline.sh'
        
        # Cria diretório se necessário
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Escreve arquivo de configuração
        config_path = config_dir / config_file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return True
    
    async def run_pipeline(self, project_path: str, steps: Optional[List[PipelineStep]] = None) -> PipelineResult:
        """Executa pipeline localmente."""
        if not steps:
            project_type = await self.detect_project_type(project_path)
            steps = self.pipeline_templates.get(project_type, [])
        
        start_time = datetime.now()
        
        context = CommandContext(
            working_directory=project_path,
            environment={},
            timeout=300.0,
            safe_mode=True
        )
        
        executed = 0
        failed = 0
        failed_steps = []
        logs = {}
        
        for step in steps:
            print(f"🔄 Executando: {step.name}")
            
            result = await self.command_executor.execute_command(step.command, context)
            executed += 1
            
            logs[step.name] = {
                'command': step.command,
                'exit_code': result.exit_code,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': result.execution_time
            }
            
            if not result.success:
                failed += 1
                failed_steps.append(step.name)
                
                if not step.allow_failure:
                    print(f"❌ {step.name} falhou: {result.stderr}")
                    break
                else:
                    print(f"⚠️ {step.name} falhou mas continuando...")
            else:
                print(f"✅ {step.name} concluído")
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return PipelineResult(
            success=failed == 0,
            total_time=total_time,
            steps_executed=executed,
            steps_failed=failed,
            failed_steps=failed_steps,
            logs=logs
        )
    
    async def validate_pipeline(self, project_path: str) -> Dict[str, Any]:
        """Valida configuração de pipeline."""
        validation = {
            'valid': True,
            'issues': [],
            'recommendations': []
        }
        
        project_path = Path(project_path)
        
        # Verifica arquivos de CI/CD existentes
        ci_files = [
            '.github/workflows/ci.yml',
            '.gitlab-ci.yml',
            'Jenkinsfile',
            'azure-pipelines.yml'
        ]
        
        existing_ci = []
        for ci_file in ci_files:
            if (project_path / ci_file).exists():
                existing_ci.append(ci_file)
        
        if not existing_ci:
            validation['issues'].append("Nenhum arquivo de CI/CD encontrado")
            validation['recommendations'].append("Configure CI/CD com setup_ci_cd()")
        
        # Verifica dependências necessárias
        project_type = await self.detect_project_type(project_path)
        
        if project_type == 'python':
            if not (project_path / 'requirements.txt').exists():
                validation['issues'].append("requirements.txt não encontrado")
            
            if not any((project_path).rglob('test_*.py')):
                validation['recommendations'].append("Adicione testes para CI/CD")
        
        elif project_type == 'javascript':
            if not (project_path / 'package.json').exists():
                validation['issues'].append("package.json não encontrado")
        
        # Verifica se há testes
        test_files = (
            list(project_path.rglob('test_*.py')) +
            list(project_path.rglob('*_test.py')) +
            list(project_path.rglob('*.test.js'))
        )
        
        if not test_files:
            validation['recommendations'].append("Adicione testes automatizados")
        
        validation['valid'] = len(validation['issues']) == 0
        
        return validation
    
    async def optimize_pipeline(self, project_path: str) -> List[str]:
        """Sugere otimizações para pipeline."""
        suggestions = []
        
        project_type = await self.detect_project_type(project_path)
        project_path = Path(project_path)
        
        # Análise específica por tipo
        if project_type == 'python':
            # Cache de dependências
            suggestions.append("Use cache para pip install")
            
            # Paralelização de testes
            if any(project_path.rglob('test_*.py')):
                suggestions.append("Execute testes em paralelo com pytest-xdist")
            
            # Lint e type check em paralelo
            suggestions.append("Execute lint e type check em paralelo")
        
        elif project_type == 'javascript':
            suggestions.append("Use cache para node_modules")
            suggestions.append("Execute lint, tests e build em paralelo")
        
        # Sugestões gerais
        suggestions.extend([
            "Configure build matrix para múltiplas versões",
            "Adicione cache de dependências",
            "Use artifacts para compartilhar builds",
            "Configure deploy automático para branches específicas"
        ])
        
        return suggestions[:5]  # Top 5 sugestões
    
    async def generate_ci_report(self, result: PipelineResult) -> str:
        """Gera relatório de execução CI/CD."""
        status_emoji = "✅" if result.success else "❌"
        
        report = f"{status_emoji} **Relatório CI/CD**\n\n"
        report += f"⏱️ **Tempo Total**: {result.total_time:.1f}s\n"
        report += f"📊 **Steps**: {result.steps_executed} executados\n"
        
        if result.steps_failed > 0:
            report += f"❌ **Falhas**: {result.steps_failed}\n"
            report += f"🔍 **Steps que falharam**: {', '.join(result.failed_steps)}\n"
        else:
            report += "✅ **Todos os steps passaram!**\n"
        
        # Detalhes por step
        report += "\n📋 **Detalhes por Step**:\n"
        
        for step_name, log in result.logs.items():
            emoji = "✅" if log['exit_code'] == 0 else "❌"
            report += f"{emoji} **{step_name}**: {log['duration']:.1f}s\n"
            
            if log['exit_code'] != 0 and log['stderr']:
                report += f"   Error: {log['stderr'][:100]}...\n"
        
        return report