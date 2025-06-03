"""
Sistema de gerenciamento de projetos
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import fnmatch
import mimetypes
from collections import defaultdict

from .config import ConfigManager
from .gemini_client import GeminiClient


@dataclass
class FileInfo:
    """Informações sobre um arquivo do projeto"""
    path: Path
    size: int
    modified: datetime
    content_hash: str
    language: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass
class ProjectStructure:
    """Estrutura completa do projeto"""
    root: Path
    files: Dict[str, FileInfo] = field(default_factory=dict)
    directories: Set[str] = field(default_factory=set)
    total_files: int = 0
    total_size: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    file_types: Dict[str, int] = field(default_factory=dict)
    
    def add_file(self, file_info: FileInfo):
        """Adiciona arquivo à estrutura"""
        relative_path = str(file_info.path.relative_to(self.root))
        self.files[relative_path] = file_info
        self.total_files += 1
        self.total_size += file_info.size
        
        # Atualiza contadores
        if file_info.language:
            self.languages[file_info.language] = self.languages.get(file_info.language, 0) + 1
        
        ext = file_info.path.suffix
        if ext:
            self.file_types[ext] = self.file_types.get(ext, 0) + 1


class ProjectManager:
    """Gerencia projetos e mantém contexto completo"""
    
    # Padrões para ignorar
    DEFAULT_IGNORE_PATTERNS = [
        '.git', '__pycache__', 'node_modules', '.env', 'venv',
        '*.pyc', '*.pyo', '*.pyd', '.DS_Store', 'thumbs.db',
        '.vscode', '.idea', '*.log', '*.tmp', '.gemini_code/cache',
        'dist', 'build', '*.egg-info', '.pytest_cache', '.mypy_cache',
        'coverage', '.coverage', 'htmlcov', '.tox', '.nox'
    ]
    
    # Extensões de código conhecidas
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'matlab',
        '.lua': 'lua',
        '.pl': 'perl',
        '.sh': 'bash',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'config',
        '.conf': 'config',
        '.md': 'markdown',
        '.rst': 'restructuredtext',
        '.tex': 'latex',
    }
    
    def __init__(self, gemini_client, project_root: Optional[Path] = None, config_manager: Optional[ConfigManager] = None):
        self.gemini_client = gemini_client
        self.project_root = Path(project_root or os.getcwd())
        self.config_manager = config_manager or ConfigManager(self.project_root)
        self.structure: Optional[ProjectStructure] = None
        self.file_cache: Dict[str, str] = {}
        self.analysis_cache: Dict[str, Any] = {}
        self.ignore_patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        self._load_gitignore()
        self._memory_file = self.project_root / ".gemini_code" / "project_memory.json"
        self._load_memory()
    
    def _load_gitignore(self):
        """Carrega padrões do .gitignore"""
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.ignore_patterns.append(line)
            except Exception:
                pass
    
    def _should_ignore(self, path: Path) -> bool:
        """Verifica se arquivo/diretório deve ser ignorado"""
        relative_path = path.relative_to(self.project_root)
        path_str = str(relative_path)
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
            # Verifica se algum diretório pai match
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True
        
        return False
    
    def scan_project(self, force: bool = False) -> ProjectStructure:
        """Escaneia projeto completo"""
        if self.structure and not force:
            return self.structure
        
        print("🔍 Escaneando projeto...")
        self.structure = ProjectStructure(root=self.project_root)
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # Filtra diretórios ignorados
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            # Adiciona diretórios
            for dir_name in dirs:
                dir_path = root_path / dir_name
                relative_path = dir_path.relative_to(self.project_root)
                self.structure.directories.add(str(relative_path))
            
            # Processa arquivos
            for file_name in files:
                file_path = root_path / file_name
                
                if self._should_ignore(file_path):
                    continue
                
                try:
                    file_info = self._analyze_file(file_path)
                    if file_info:
                        self.structure.add_file(file_info)
                except Exception as e:
                    print(f"⚠️  Erro ao analisar {file_path}: {e}")
        
        print(f"✅ Projeto escaneado: {self.structure.total_files} arquivos")
        self._save_memory()
        return self.structure
    
    def _analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """Analisa um arquivo individual"""
        try:
            stat = file_path.stat()
            
            # Pula arquivos muito grandes (>10MB)
            if stat.st_size > 10 * 1024 * 1024:
                return None
            
            # Calcula hash do conteúdo
            content_hash = self._calculate_file_hash(file_path)
            
            file_info = FileInfo(
                path=file_path,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                content_hash=content_hash,
                language=self._detect_language(file_path)
            )
            
            # Analisa conteúdo se for código
            if file_info.language:
                self._analyze_code_content(file_info)
            
            return file_info
            
        except Exception:
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 do arquivo"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detecta linguagem do arquivo"""
        ext = file_path.suffix.lower()
        return self.CODE_EXTENSIONS.get(ext)
    
    def _analyze_code_content(self, file_info: FileInfo):
        """Analisa conteúdo de código"""
        try:
            with open(file_info.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache o conteúdo
            relative_path = str(file_info.path.relative_to(self.project_root))
            self.file_cache[relative_path] = content
            
            # Análise específica por linguagem
            if file_info.language == 'python':
                self._analyze_python(file_info, content)
            elif file_info.language in ['javascript', 'typescript']:
                self._analyze_javascript(file_info, content)
            # Adicionar mais linguagens conforme necessário
            
        except Exception:
            pass
    
    def _analyze_python(self, file_info: FileInfo, content: str):
        """Analisa código Python"""
        import re
        
        # Imports
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            module = match.group(1) or match.group(2).split(',')[0].strip()
            file_info.imports.append(module)
        
        # Classes
        class_pattern = r'^class\s+(\w+)'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            file_info.classes.append(match.group(1))
        
        # Functions
        func_pattern = r'^def\s+(\w+)'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            file_info.functions.append(match.group(1))
    
    def _analyze_javascript(self, file_info: FileInfo, content: str):
        """Analisa código JavaScript/TypeScript"""
        import re
        
        # Imports
        import_patterns = [
            r"import\s+.*\s+from\s+['\"](.+?)['\"]",
            r"require\s*\(['\"](.+?)['\"]\)",
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                file_info.imports.append(match.group(1))
        
        # Classes
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            file_info.classes.append(match.group(1))
        
        # Functions
        func_patterns = [
            r'function\s+(\w+)',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>',
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                file_info.functions.append(match.group(1))
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Obtém conteúdo de um arquivo (com cache)"""
        # Normaliza caminho
        if not os.path.isabs(file_path):
            file_path = str(self.project_root / file_path)
        
        path = Path(file_path)
        relative_path = str(path.relative_to(self.project_root))
        
        # Verifica cache
        if relative_path in self.file_cache:
            # Verifica se arquivo mudou
            if self.structure and relative_path in self.structure.files:
                file_info = self.structure.files[relative_path]
                current_hash = self._calculate_file_hash(path)
                if current_hash == file_info.content_hash:
                    return self.file_cache[relative_path]
        
        # Lê arquivo
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.file_cache[relative_path] = content
            return content
        except Exception:
            return None
    
    def find_files(self, pattern: str) -> List[str]:
        """Encontra arquivos por padrão"""
        if not self.structure:
            self.scan_project()
        
        matching_files = []
        
        for file_path in self.structure.files:
            if fnmatch.fnmatch(file_path, pattern):
                matching_files.append(file_path)
            elif pattern.lower() in file_path.lower():
                matching_files.append(file_path)
        
        return sorted(matching_files)
    
    def search_in_files(self, pattern: str, file_pattern: Optional[str] = None) -> Dict[str, List[Tuple[int, str]]]:
        """Busca padrão em arquivos"""
        import re
        
        if not self.structure:
            self.scan_project()
        
        results = defaultdict(list)
        
        # Filtra arquivos
        files_to_search = self.structure.files.keys()
        if file_pattern:
            files_to_search = [f for f in files_to_search if fnmatch.fnmatch(f, file_pattern)]
        
        # Busca em cada arquivo
        for file_path in files_to_search:
            content = self.get_file_content(file_path)
            if not content:
                continue
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    results[file_path].append((i, line.strip()))
        
        return dict(results)
    
    def get_file_relationships(self, file_path: str) -> Dict[str, List[str]]:
        """Obtém relacionamentos de um arquivo"""
        if not self.structure:
            self.scan_project()
        
        relationships = {
            'imports': [],
            'imported_by': [],
            'similar_files': [],
            'related_files': []
        }
        
        # Normaliza caminho
        if not os.path.isabs(file_path):
            file_path = str(self.project_root / file_path)
        
        path = Path(file_path)
        relative_path = str(path.relative_to(self.project_root))
        
        if relative_path not in self.structure.files:
            return relationships
        
        file_info = self.structure.files[relative_path]
        
        # Imports diretos
        relationships['imports'] = file_info.imports.copy()
        
        # Quem importa este arquivo
        file_name = path.stem
        for other_path, other_info in self.structure.files.items():
            if other_path != relative_path:
                for imp in other_info.imports:
                    if file_name in imp or relative_path.replace('/', '.').replace('.py', '') in imp:
                        relationships['imported_by'].append(other_path)
        
        # Arquivos similares (mesma extensão, mesmo diretório)
        for other_path in self.structure.files:
            other = Path(other_path)
            if other.suffix == path.suffix and other.parent == path.parent and other_path != relative_path:
                relationships['similar_files'].append(other_path)
        
        # Arquivos relacionados (mesmo nome base)
        base_name = path.stem
        for other_path in self.structure.files:
            other = Path(other_path)
            if other.stem == base_name and other_path != relative_path:
                relationships['related_files'].append(other_path)
        
        return relationships
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do projeto"""
        if not self.structure:
            self.scan_project()
        
        return {
            'total_files': self.structure.total_files,
            'total_size': self.structure.total_size,
            'total_size_mb': round(self.structure.total_size / (1024 * 1024), 2),
            'languages': dict(self.structure.languages),
            'file_types': dict(self.structure.file_types),
            'directories': len(self.structure.directories),
            'largest_files': self._get_largest_files(10),
            'most_recent_files': self._get_most_recent_files(10),
        }
    
    def _get_largest_files(self, count: int) -> List[Dict[str, Any]]:
        """Obtém maiores arquivos"""
        if not self.structure:
            return []
        
        sorted_files = sorted(
            self.structure.files.items(),
            key=lambda x: x[1].size,
            reverse=True
        )[:count]
        
        return [
            {
                'path': path,
                'size': info.size,
                'size_kb': round(info.size / 1024, 2)
            }
            for path, info in sorted_files
        ]
    
    def _get_most_recent_files(self, count: int) -> List[Dict[str, Any]]:
        """Obtém arquivos mais recentes"""
        if not self.structure:
            return []
        
        sorted_files = sorted(
            self.structure.files.items(),
            key=lambda x: x[1].modified,
            reverse=True
        )[:count]
        
        return [
            {
                'path': path,
                'modified': info.modified.isoformat(),
                'language': info.language
            }
            for path, info in sorted_files
        ]
    
    def _save_memory(self):
        """Salva memória do projeto"""
        try:
            memory_data = {
                'last_scan': datetime.now().isoformat(),
                'file_count': self.structure.total_files if self.structure else 0,
                'project_type': self._detect_project_type(),
                'main_language': self._detect_main_language(),
            }
            
            os.makedirs(self._memory_file.parent, exist_ok=True)
            with open(self._memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
                
        except Exception:
            pass
    
    def _load_memory(self):
        """Carrega memória do projeto"""
        try:
            if self._memory_file.exists():
                with open(self._memory_file, 'r') as f:
                    self.memory = json.load(f)
            else:
                self.memory = {}
        except Exception:
            self.memory = {}
    
    def _detect_project_type(self) -> str:
        """Detecta tipo de projeto"""
        if not self.structure:
            return "unknown"
        
        # Verifica por arquivos característicos
        indicators = {
            'package.json': 'node',
            'requirements.txt': 'python',
            'setup.py': 'python-package',
            'Cargo.toml': 'rust',
            'go.mod': 'go',
            'pom.xml': 'java-maven',
            'build.gradle': 'java-gradle',
            'composer.json': 'php',
            'Gemfile': 'ruby',
            'mix.exs': 'elixir',
            'pubspec.yaml': 'flutter',
            'Package.swift': 'swift',
            '.csproj': 'dotnet',
            'Makefile': 'make-project',
            'CMakeLists.txt': 'cmake',
            'docker-compose.yml': 'docker',
            'kubernetes.yaml': 'kubernetes',
        }
        
        for indicator, project_type in indicators.items():
            if any(indicator in f for f in self.structure.files):
                return project_type
        
        # Detecta por linguagem predominante
        main_lang = self._detect_main_language()
        if main_lang:
            return f"{main_lang}-project"
        
        return "generic"
    
    def _detect_main_language(self) -> Optional[str]:
        """Detecta linguagem principal do projeto"""
        if not self.structure or not self.structure.languages:
            return None
        
        return max(self.structure.languages.items(), key=lambda x: x[1])[0]
    
    def continuous_monitoring(self):
        """Monitora projeto continuamente (para uso futuro com watchdog)"""
        # TODO: Implementar com watchdog
        pass
    
    def understand_project_deeply(self) -> Dict[str, Any]:
        """Entende projeto profundamente"""
        if not self.structure:
            self.scan_project()
        
        understanding = {
            'type': self._detect_project_type(),
            'main_language': self._detect_main_language(),
            'structure': self._analyze_project_structure(),
            'conventions': self._detect_conventions(),
            'dependencies': self._analyze_dependencies(),
            'entry_points': self._find_entry_points(),
            'test_structure': self._analyze_test_structure(),
            'documentation': self._find_documentation(),
        }
        
        return understanding
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analisa estrutura do projeto"""
        structure = {
            'has_src_folder': any('src' in d for d in self.structure.directories),
            'has_tests': any('test' in d.lower() for d in self.structure.directories),
            'has_docs': any('doc' in d.lower() for d in self.structure.directories),
            'depth': max(len(Path(f).parts) for f in self.structure.files) if self.structure.files else 0,
            'organization': 'unknown'
        }
        
        # Detecta organização
        if structure['has_src_folder']:
            structure['organization'] = 'src-based'
        elif any('app' in d for d in self.structure.directories):
            structure['organization'] = 'app-based'
        elif structure['depth'] <= 2:
            structure['organization'] = 'flat'
        else:
            structure['organization'] = 'hierarchical'
        
        return structure
    
    def _detect_conventions(self) -> Dict[str, Any]:
        """Detecta convenções do projeto"""
        conventions = {
            'naming': 'unknown',
            'indent': 'unknown',
            'quotes': 'unknown',
            'line_endings': 'unknown',
        }
        
        # Amostra alguns arquivos Python
        python_files = [f for f in self.structure.files if f.endswith('.py')][:5]
        
        for file_path in python_files:
            content = self.get_file_content(file_path)
            if content:
                # Detecta indentação
                if '\t' in content:
                    conventions['indent'] = 'tabs'
                elif '    ' in content:
                    conventions['indent'] = '4-spaces'
                elif '  ' in content:
                    conventions['indent'] = '2-spaces'
                
                # Detecta quotes
                single_quotes = content.count("'")
                double_quotes = content.count('"')
                if single_quotes > double_quotes * 2:
                    conventions['quotes'] = 'single'
                else:
                    conventions['quotes'] = 'double'
                
                break
        
        return conventions
    
    def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """Analisa dependências do projeto"""
        dependencies = {
            'python': [],
            'node': [],
            'system': [],
        }
        
        # Python dependencies
        req_files = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']
        for req_file in req_files:
            if req_file in self.structure.files:
                content = self.get_file_content(req_file)
                if content:
                    # Parse básico de requirements
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkg = line.split('=')[0].split('>')[0].split('<')[0].strip()
                            if pkg:
                                dependencies['python'].append(pkg)
        
        # Node dependencies
        if 'package.json' in self.structure.files:
            content = self.get_file_content('package.json')
            if content:
                try:
                    pkg_data = json.loads(content)
                    deps = pkg_data.get('dependencies', {})
                    dev_deps = pkg_data.get('devDependencies', {})
                    dependencies['node'] = list(deps.keys()) + list(dev_deps.keys())
                except Exception:
                    pass
        
        return dependencies
    
    def _find_entry_points(self) -> List[str]:
        """Encontra pontos de entrada do projeto"""
        entry_points = []
        
        # Padrões comuns de entry points
        common_entries = [
            'main.py', 'app.py', 'run.py', 'manage.py', '__main__.py',
            'index.js', 'index.ts', 'main.js', 'main.ts', 'app.js',
            'server.js', 'server.ts', 'index.html', 'main.go',
            'main.rs', 'Main.java', 'Program.cs', 'main.cpp',
        ]
        
        for entry in common_entries:
            matching = self.find_files(f"**/{entry}")
            entry_points.extend(matching)
        
        # Procura por if __name__ == "__main__" em Python
        for file_path in self.structure.files:
            if file_path.endswith('.py'):
                content = self.get_file_content(file_path)
                if content and 'if __name__' in content and '__main__' in content:
                    entry_points.append(file_path)
        
        return list(set(entry_points))
    
    def _analyze_test_structure(self) -> Dict[str, Any]:
        """Analisa estrutura de testes"""
        test_info = {
            'has_tests': False,
            'test_framework': 'unknown',
            'test_files': [],
            'test_coverage': 'unknown'
        }
        
        # Procura arquivos de teste
        test_patterns = ['*test*.py', '*test*.js', '*spec*.js', '*test*.ts', '*spec*.ts']
        
        for pattern in test_patterns:
            test_files = self.find_files(pattern)
            test_info['test_files'].extend(test_files)
        
        test_info['has_tests'] = len(test_info['test_files']) > 0
        
        # Detecta framework
        if test_info['test_files']:
            sample_test = self.get_file_content(test_info['test_files'][0])
            if sample_test:
                if 'pytest' in sample_test or 'import pytest' in sample_test:
                    test_info['test_framework'] = 'pytest'
                elif 'unittest' in sample_test:
                    test_info['test_framework'] = 'unittest'
                elif 'describe(' in sample_test:
                    test_info['test_framework'] = 'jest/mocha'
                elif 'test(' in sample_test:
                    test_info['test_framework'] = 'jest'
        
        return test_info
    
    def _find_documentation(self) -> List[str]:
        """Encontra documentação do projeto"""
        docs = []
        
        # Arquivos de documentação comuns
        doc_patterns = ['README*', 'readme*', 'CONTRIBUTING*', 'LICENSE*', 
                       'CHANGELOG*', 'docs/*', 'documentation/*', '*.md', '*.rst']
        
        for pattern in doc_patterns:
            matching = self.find_files(pattern)
            docs.extend(matching)
        
        return list(set(docs))