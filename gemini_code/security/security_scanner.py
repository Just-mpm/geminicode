"""
Scanner de segurança completo que detecta e corrige vulnerabilidades.
"""

import re
import ast
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import subprocess

from ..core.gemini_client import GeminiClient


class SecurityIssue:
    """Representa uma questão de segurança."""
    
    def __init__(self, issue_type: str, severity: str, file_path: str,
                 line_number: int, description: str, recommendation: str,
                 cwe_id: Optional[str] = None):
        self.type = issue_type
        self.severity = severity  # critical, high, medium, low
        self.file_path = file_path
        self.line_number = line_number
        self.description = description
        self.recommendation = recommendation
        self.cwe_id = cwe_id  # Common Weakness Enumeration
        self.auto_fixable = self._determine_auto_fixable()
    
    def _determine_auto_fixable(self) -> bool:
        """Determina se o problema pode ser corrigido automaticamente."""
        auto_fixable_types = [
            'hardcoded_secret', 'weak_crypto', 'missing_validation',
            'sql_injection', 'insecure_random', 'missing_auth'
        ]
        return self.type in auto_fixable_types
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'type': self.type,
            'severity': self.severity,
            'file': self.file_path,
            'line': self.line_number,
            'description': self.description,
            'recommendation': self.recommendation,
            'cwe_id': self.cwe_id,
            'auto_fixable': self.auto_fixable
        }


class SecurityScanner:
    """Scanner de segurança abrangente."""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.security_patterns = self._load_security_patterns()
        self.safe_functions = self._load_safe_functions()
    
    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Carrega padrões de segurança conhecidos."""
        return {
            'secrets': [
                {
                    'pattern': r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
                    'type': 'hardcoded_password',
                    'severity': 'critical',
                    'cwe': 'CWE-798'
                },
                {
                    'pattern': r'(?i)(api[_\s]?key|apikey)\s*=\s*["\'][^"\']+["\']',
                    'type': 'hardcoded_api_key',
                    'severity': 'critical',
                    'cwe': 'CWE-798'
                },
                {
                    'pattern': r'(?i)(secret[_\s]?key|secret)\s*=\s*["\'][^"\']+["\']',
                    'type': 'hardcoded_secret',
                    'severity': 'critical',
                    'cwe': 'CWE-798'
                },
                {
                    'pattern': r'(?i)aws[_\s]?access[_\s]?key[_\s]?id\s*=\s*["\'][^"\']+["\']',
                    'type': 'aws_credentials',
                    'severity': 'critical',
                    'cwe': 'CWE-798'
                }
            ],
            'injections': [
                {
                    'pattern': r'f["\'].*{.*}.*["\'].*(?:execute|cursor\.execute)',
                    'type': 'sql_injection',
                    'severity': 'critical',
                    'cwe': 'CWE-89'
                },
                {
                    'pattern': r'eval\s*\([^)]*input\s*\(',
                    'type': 'code_injection',
                    'severity': 'critical',
                    'cwe': 'CWE-94'
                },
                {
                    'pattern': r'exec\s*\([^)]*input\s*\(',
                    'type': 'code_injection',
                    'severity': 'critical',
                    'cwe': 'CWE-94'
                },
                {
                    'pattern': r'os\.system\s*\([^)]*\+[^)]*\)',
                    'type': 'command_injection',
                    'severity': 'high',
                    'cwe': 'CWE-78'
                }
            ],
            'crypto': [
                {
                    'pattern': r'(?i)md5|sha1',
                    'type': 'weak_crypto',
                    'severity': 'medium',
                    'cwe': 'CWE-326'
                },
                {
                    'pattern': r'random\.random|random\.randint',
                    'type': 'insecure_random',
                    'severity': 'medium',
                    'cwe': 'CWE-330'
                },
                {
                    'pattern': r'DES|3DES',
                    'type': 'weak_encryption',
                    'severity': 'high',
                    'cwe': 'CWE-326'
                }
            ],
            'auth': [
                {
                    'pattern': r'verify\s*=\s*False',
                    'type': 'ssl_verification_disabled',
                    'severity': 'high',
                    'cwe': 'CWE-295'
                },
                {
                    'pattern': r'@app\.route.*methods.*POST.*\n(?!.*@login_required)',
                    'type': 'missing_auth',
                    'severity': 'high',
                    'cwe': 'CWE-306'
                }
            ],
            'files': [
                {
                    'pattern': r'open\s*\([^,)]*user[^,)]*\)',
                    'type': 'path_traversal',
                    'severity': 'high',
                    'cwe': 'CWE-22'
                },
                {
                    'pattern': r'pickle\.load',
                    'type': 'unsafe_deserialization',
                    'severity': 'high',
                    'cwe': 'CWE-502'
                }
            ]
        }
    
    def _load_safe_functions(self) -> Dict[str, str]:
        """Carrega funções seguras para substituição."""
        return {
            'eval': 'ast.literal_eval',
            'pickle.load': 'json.load',
            'random.random': 'secrets.SystemRandom().random',
            'random.randint': 'secrets.SystemRandom().randint',
            'md5': 'hashlib.sha256',
            'sha1': 'hashlib.sha256',
            'os.system': 'subprocess.run',
            'commands.getoutput': 'subprocess.check_output'
        }
    
    async def scan_project(self, project_path: str) -> List[SecurityIssue]:
        """Escaneia projeto completo em busca de vulnerabilidades."""
        issues = []
        project_path = Path(project_path)
        
        # Escaneia arquivos Python
        python_files = list(project_path.rglob("*.py"))
        for file_path in python_files:
            file_issues = await self._scan_file(file_path)
            issues.extend(file_issues)
        
        # Escaneia configurações
        config_issues = await self._scan_configurations(project_path)
        issues.extend(config_issues)
        
        # Escaneia dependências
        dependency_issues = await self._scan_dependencies(project_path)
        issues.extend(dependency_issues)
        
        # Análise com IA para padrões complexos
        ai_issues = await self._ai_security_analysis(project_path)
        issues.extend(ai_issues)
        
        # Remove duplicatas
        unique_issues = self._deduplicate_issues(issues)
        
        # Ordena por severidade
        return sorted(unique_issues, key=lambda x: self._severity_score(x.severity))
    
    async def _scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """Escaneia arquivo específico."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Verifica padrões de segurança
            for category, patterns in self.security_patterns.items():
                for pattern_info in patterns:
                    pattern = pattern_info['pattern']
                    
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            issue = SecurityIssue(
                                issue_type=pattern_info['type'],
                                severity=pattern_info['severity'],
                                file_path=str(file_path),
                                line_number=i,
                                description=self._get_issue_description(pattern_info['type']),
                                recommendation=self._get_recommendation(pattern_info['type']),
                                cwe_id=pattern_info.get('cwe')
                            )
                            issues.append(issue)
            
            # Análise AST para problemas mais complexos
            ast_issues = await self._ast_security_analysis(content, file_path)
            issues.extend(ast_issues)
            
        except Exception as e:
            print(f"Erro ao escanear {file_path}: {e}")
        
        return issues
    
    async def _ast_security_analysis(self, content: str, file_path: Path) -> List[SecurityIssue]:
        """Análise de segurança usando AST."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Verifica imports perigosos
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['pickle', 'marshal', 'shelve']:
                            issues.append(SecurityIssue(
                                'dangerous_import',
                                'medium',
                                str(file_path),
                                node.lineno,
                                f"Import perigoso: {alias.name}",
                                "Use alternativas seguras como JSON",
                                'CWE-502'
                            ))
                
                # Verifica uso de eval/exec
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', '__import__']:
                            issues.append(SecurityIssue(
                                'dangerous_function',
                                'critical',
                                str(file_path),
                                node.lineno,
                                f"Função perigosa: {node.func.id}",
                                f"Use {self.safe_functions.get(node.func.id, 'alternativa segura')}",
                                'CWE-94'
                            ))
                
                # Verifica strings SQL
                elif isinstance(node, ast.Str):
                    if any(keyword in node.s.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                        # Verifica se há concatenação
                        parent = self._get_parent_node(tree, node)
                        if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Add):
                            issues.append(SecurityIssue(
                                'sql_concatenation',
                                'high',
                                str(file_path),
                                node.lineno,
                                "Possível SQL injection por concatenação",
                                "Use parâmetros preparados",
                                'CWE-89'
                            ))
                            
        except Exception as e:
            print(f"Erro na análise AST de {file_path}: {e}")
        
        return issues
    
    def _get_parent_node(self, tree: ast.AST, node: ast.AST) -> Optional[ast.AST]:
        """Obtém nó pai no AST."""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                if child == node:
                    return parent
        return None
    
    async def _scan_configurations(self, project_path: Path) -> List[SecurityIssue]:
        """Escaneia arquivos de configuração."""
        issues = []
        
        # Arquivos de configuração comuns
        config_files = [
            'config.py', 'settings.py', '.env', 'config.json',
            'config.yaml', 'config.yml', 'docker-compose.yml'
        ]
        
        for config_name in config_files:
            config_path = project_path / config_name
            if config_path.exists():
                # Verifica exposição de secrets
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Procura por valores sensíveis
                    sensitive_patterns = [
                        (r'DEBUG\s*=\s*True', 'debug_enabled', 'high'),
                        (r'SECRET_KEY\s*=\s*["\'][^"\']+["\']', 'exposed_secret_key', 'critical'),
                        (r'DATABASE_URL\s*=\s*["\'][^"\']+["\']', 'exposed_database_url', 'high'),
                        (r'0\.0\.0\.0', 'bind_all_interfaces', 'medium')
                    ]
                    
                    for pattern, issue_type, severity in sensitive_patterns:
                        if re.search(pattern, content):
                            issues.append(SecurityIssue(
                                issue_type,
                                severity,
                                str(config_path),
                                0,
                                self._get_issue_description(issue_type),
                                self._get_recommendation(issue_type)
                            ))
                            
                except Exception as e:
                    print(f"Erro ao escanear configuração {config_path}: {e}")
        
        # Verifica .gitignore
        gitignore_path = project_path / '.gitignore'
        if not gitignore_path.exists() or gitignore_path.stat().st_size == 0:
            issues.append(SecurityIssue(
                'missing_gitignore',
                'medium',
                str(project_path),
                0,
                "Arquivo .gitignore ausente ou vazio",
                "Crie .gitignore para evitar commit de arquivos sensíveis"
            ))
        
        return issues
    
    async def _scan_dependencies(self, project_path: Path) -> List[SecurityIssue]:
        """Escaneia dependências em busca de vulnerabilidades."""
        issues = []
        
        # Requirements.txt
        requirements_path = project_path / 'requirements.txt'
        if requirements_path.exists():
            try:
                # Tenta usar safety para verificar vulnerabilidades
                result = subprocess.run(
                    ['safety', 'check', '--json'],
                    cwd=str(project_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0 and result.stdout:
                    try:
                        vulnerabilities = json.loads(result.stdout)
                        for vuln in vulnerabilities:
                            issues.append(SecurityIssue(
                                'vulnerable_dependency',
                                'high',
                                str(requirements_path),
                                0,
                                f"Dependência vulnerável: {vuln.get('package', 'unknown')} {vuln.get('installed_version', 'unknown')}",
                                f"Atualize para versão {vuln.get('latest_version', 'mais recente')}",
                                vuln.get('cve')
                            ))
                    except json.JSONDecodeError:
                        print("Aviso: Não foi possível interpretar a saída do safety")
                        
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
                print(f"Aviso: Safety não disponível ({e}), fazendo verificação básica")
                # Verificação básica se safety não estiver disponível
                try:
                    with open(requirements_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '==' not in line and '>=' not in line and '~=' not in line:
                                    issues.append(SecurityIssue(
                                        'unpinned_dependency',
                                        'low',
                                        str(requirements_path),
                                        line_num,
                                        f"Dependência sem versão fixa: {line}",
                                        "Fixe versões para evitar atualizações inesperadas"
                                    ))
                except Exception as inner_e:
                    print(f"Erro ao ler requirements.txt: {inner_e}")
            except Exception as e:
                print(f"Erro inesperado ao verificar dependências: {e}")
        
        return issues
    
    async def _ai_security_analysis(self, project_path: Path) -> List[SecurityIssue]:
        """Análise de segurança usando IA."""
        issues = []
        
        # Analisa arquivos principais
        main_files = list(project_path.glob("*.py"))[:5]  # Limita para performance
        
        for file_path in main_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) > 10000:  # Skip arquivos muito grandes
                    continue
                
                prompt = f"""
                Analise este código Python para vulnerabilidades de segurança:

                ```python
                {content}
                ```

                Procure por:
                1. Validação de entrada ausente
                2. Autenticação/autorização fraca
                3. Exposição de dados sensíveis
                4. Práticas inseguras
                5. OWASP Top 10

                Retorne JSON com vulnerabilidades encontradas:
                [
                  {{
                    "type": "tipo_vulnerabilidade",
                    "severity": "critical|high|medium|low",
                    "line": número_linha,
                    "description": "descrição",
                    "recommendation": "como_corrigir"
                  }}
                ]
                """
                
                response = await self.gemini_client.generate_response(prompt)
                
                # Extrai JSON
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    vulnerabilities = json.loads(json_match.group())
                    
                    for vuln in vulnerabilities:
                        issues.append(SecurityIssue(
                            vuln['type'],
                            vuln['severity'],
                            str(file_path),
                            vuln.get('line', 0),
                            vuln['description'],
                            vuln['recommendation']
                        ))
                        
            except Exception as e:
                print(f"Erro na análise IA de {file_path}: {e}")
        
        return issues
    
    def _get_issue_description(self, issue_type: str) -> str:
        """Retorna descrição detalhada do problema."""
        descriptions = {
            'hardcoded_password': "Senha hardcoded no código fonte",
            'hardcoded_api_key': "API key exposta no código",
            'hardcoded_secret': "Secret/chave secreta exposta",
            'aws_credentials': "Credenciais AWS expostas",
            'sql_injection': "Vulnerável a SQL injection",
            'code_injection': "Vulnerável a injeção de código",
            'command_injection': "Vulnerável a injeção de comandos",
            'weak_crypto': "Algoritmo criptográfico fraco",
            'insecure_random': "Gerador de números aleatórios inseguro",
            'ssl_verification_disabled': "Verificação SSL desabilitada",
            'missing_auth': "Autenticação ausente em rota sensível",
            'path_traversal': "Vulnerável a path traversal",
            'unsafe_deserialization': "Deserialização insegura de dados",
            'debug_enabled': "Debug habilitado em produção",
            'exposed_secret_key': "Secret key exposta em configuração",
            'bind_all_interfaces': "Aplicação escutando em todas interfaces"
        }
        return descriptions.get(issue_type, f"Problema de segurança: {issue_type}")
    
    def _get_recommendation(self, issue_type: str) -> str:
        """Retorna recomendação para corrigir o problema."""
        recommendations = {
            'hardcoded_password': "Use variáveis de ambiente ou gerenciador de secrets",
            'hardcoded_api_key': "Mova para arquivo .env e adicione ao .gitignore",
            'hardcoded_secret': "Use sistema de gerenciamento de secrets",
            'aws_credentials': "Use AWS IAM roles ou AWS Secrets Manager",
            'sql_injection': "Use consultas parametrizadas ou ORM",
            'code_injection': "Evite eval/exec, use ast.literal_eval se necessário",
            'command_injection': "Use subprocess com lista de argumentos",
            'weak_crypto': "Use SHA-256 ou algoritmos mais fortes",
            'insecure_random': "Use secrets.SystemRandom() para dados sensíveis",
            'ssl_verification_disabled': "Sempre verifique certificados SSL",
            'missing_auth': "Adicione decorador de autenticação",
            'path_traversal': "Valide e sanitize caminhos de arquivo",
            'unsafe_deserialization': "Use JSON ao invés de pickle",
            'debug_enabled': "Desabilite debug em produção",
            'exposed_secret_key': "Gere nova secret key e use variável de ambiente",
            'bind_all_interfaces': "Bind apenas em localhost ou interfaces específicas"
        }
        return recommendations.get(issue_type, "Revise e corrija o código")
    
    def _severity_score(self, severity: str) -> int:
        """Retorna score numérico para severidade."""
        return {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(severity, 4)
    
    def _deduplicate_issues(self, issues: List[SecurityIssue]) -> List[SecurityIssue]:
        """Remove issues duplicadas."""
        seen = set()
        unique = []
        
        for issue in issues:
            key = f"{issue.type}:{issue.file_path}:{issue.line_number}"
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        
        return unique
    
    async def auto_fix_issue(self, issue: SecurityIssue) -> bool:
        """Tenta corrigir problema de segurança automaticamente."""
        if not issue.auto_fixable:
            return False
        
        try:
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Correções específicas por tipo
            if issue.type == 'hardcoded_secret':
                fixed_content = await self._fix_hardcoded_secret(content, issue)
            elif issue.type == 'weak_crypto':
                fixed_content = self._fix_weak_crypto(content)
            elif issue.type == 'insecure_random':
                fixed_content = self._fix_insecure_random(content)
            elif issue.type == 'sql_injection':
                fixed_content = await self._fix_sql_injection(content, issue)
            else:
                return False
            
            if fixed_content and fixed_content != content:
                # Backup
                backup_path = f"{issue.file_path}.security_backup"
                import shutil
                shutil.copy2(issue.file_path, backup_path)
                
                # Aplica correção
                with open(issue.file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                # Cria/atualiza .env se necessário
                if issue.type == 'hardcoded_secret':
                    self._update_env_file(issue)
                
                return True
                
        except Exception as e:
            print(f"Erro ao corrigir {issue.type}: {e}")
        
        return False
    
    async def _fix_hardcoded_secret(self, content: str, issue: SecurityIssue) -> str:
        """Corrige secrets hardcoded."""
        lines = content.split('\n')
        
        if 0 <= issue.line_number - 1 < len(lines):
            line = lines[issue.line_number - 1]
            
            # Extrai nome da variável e valor
            match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', line)
            if match:
                var_name = match.group(1)
                
                # Substitui por variável de ambiente
                env_var_name = f"{var_name.upper()}_ENV"
                new_line = f"{var_name} = os.environ.get('{env_var_name}', '')"
                
                lines[issue.line_number - 1] = new_line
                
                # Adiciona import se necessário
                if 'import os' not in content:
                    lines.insert(0, 'import os')
        
        return '\n'.join(lines)
    
    def _fix_weak_crypto(self, content: str) -> str:
        """Corrige algoritmos fracos."""
        # Substitui MD5 e SHA1
        content = re.sub(r'hashlib\.md5\(', 'hashlib.sha256(', content)
        content = re.sub(r'hashlib\.sha1\(', 'hashlib.sha256(', content)
        
        # Substitui imports
        content = re.sub(r'from hashlib import md5', 'from hashlib import sha256', content)
        content = re.sub(r'from hashlib import sha1', 'from hashlib import sha256', content)
        
        return content
    
    def _fix_insecure_random(self, content: str) -> str:
        """Corrige geradores aleatórios inseguros."""
        # Adiciona import secrets se necessário
        if 'secrets' not in content and 'random.random' in content:
            lines = content.split('\n')
            # Adiciona após outros imports
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                else:
                    lines.insert(i, 'import secrets')
                    break
            content = '\n'.join(lines)
        
        # Substitui random por secrets
        content = re.sub(r'random\.random\(\)', 'secrets.SystemRandom().random()', content)
        content = re.sub(r'random\.randint\(', 'secrets.SystemRandom().randint(', content)
        content = re.sub(r'random\.choice\(', 'secrets.SystemRandom().choice(', content)
        
        return content
    
    async def _fix_sql_injection(self, content: str, issue: SecurityIssue) -> str:
        """Corrige SQL injection."""
        prompt = f"""
        Corrija esta vulnerabilidade de SQL injection:

        Código vulnerável (linha {issue.line_number}):
        ```python
        {content}
        ```

        Use consultas parametrizadas ou prepared statements.
        Retorne o código corrigido completo.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Extrai código
        import re
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return content
    
    def _update_env_file(self, issue: SecurityIssue) -> None:
        """Atualiza arquivo .env com secrets."""
        env_path = Path(issue.file_path).parent / '.env'
        env_example_path = Path(issue.file_path).parent / '.env.example'
        
        # Cria .env.example se não existe
        if not env_example_path.exists():
            with open(env_example_path, 'w') as f:
                f.write("# Variáveis de ambiente\n")
        
        # Adiciona variável ao .env.example
        with open(env_example_path, 'a') as f:
            f.write(f"\n# Adicione esta variável ao seu .env\n")
            f.write(f"# {issue.type.upper()}_ENV=seu_valor_aqui\n")
    
    async def generate_security_report(self, issues: List[SecurityIssue]) -> str:
        """Gera relatório de segurança."""
        if not issues:
            return "✅ **Nenhuma vulnerabilidade encontrada!**"
        
        report = "🔒 **Relatório de Segurança**\n\n"
        
        # Resumo
        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        report += "📊 **Resumo**:\n"
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                count = len(by_severity[severity])
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[severity]
                report += f"{emoji} {severity.title()}: {count} vulnerabilidades\n"
        
        report += f"\n**Total**: {len(issues)} vulnerabilidades encontradas\n"
        
        # Auto-corrigíveis
        auto_fixable = sum(1 for i in issues if i.auto_fixable)
        if auto_fixable > 0:
            report += f"🔧 **{auto_fixable}** podem ser corrigidas automaticamente\n"
        
        # Detalhes por severidade
        report += "\n📋 **Detalhes**:\n"
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                report += f"\n**{severity.title()} ({len(by_severity[severity])})**:\n"
                
                for issue in by_severity[severity][:5]:  # Máximo 5 por categoria
                    report += f"- {Path(issue.file_path).name}:{issue.line_number} - {issue.description}\n"
                    report += f"  💡 {issue.recommendation}\n"
                
                if len(by_severity[severity]) > 5:
                    report += f"  ... e mais {len(by_severity[severity]) - 5}\n"
        
        # Score de segurança
        score = self._calculate_security_score(issues)
        report += f"\n🎯 **Score de Segurança**: {score}/100"
        
        return report
    
    def _calculate_security_score(self, issues: List[SecurityIssue]) -> int:
        """Calcula score de segurança (0-100)."""
        if not issues:
            return 100
        
        # Pontos perdidos por severidade
        penalties = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3
        }
        
        score = 100
        for issue in issues:
            score -= penalties.get(issue.severity, 0)
        
        return max(0, score)