"""
Sistema de chunking automático para processar projetos grandes.
"""

import json
from typing import List, Dict, Any, Iterator, Tuple
from pathlib import Path
import tiktoken


class ChunkingSystem:
    """Divide tarefas grandes em chunks processáveis."""
    
    def __init__(self, max_chunk_size: int = 50000, overlap: int = 1000):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.encoding_for_model("gpt-4")  # Aproximação
    
    def count_tokens(self, text: str) -> int:
        """Conta tokens em um texto."""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str) -> List[str]:
        """Divide texto em chunks com overlap."""
        tokens = self.encoding.encode(text)
        chunks = []
        
        if len(tokens) <= self.max_chunk_size:
            return [text]
        
        # Divide em chunks com overlap
        start = 0
        while start < len(tokens):
            end = min(start + self.max_chunk_size, len(tokens))
            
            # Tenta encontrar um ponto de quebra natural
            if end < len(tokens):
                # Volta até encontrar fim de linha
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)
                
                # Procura último \n
                last_newline = chunk_text.rfind('\n')
                if last_newline > self.max_chunk_size * 0.8:  # Se está nos últimos 20%
                    # Reajusta end para o fim da linha
                    chunk_text = chunk_text[:last_newline]
                    chunk_tokens = self.encoding.encode(chunk_text)
                    end = start + len(chunk_tokens)
            
            chunk = self.encoding.decode(tokens[start:end])
            chunks.append(chunk)
            
            # Próximo chunk com overlap
            start = end - self.overlap if end < len(tokens) else end
        
        return chunks
    
    def chunk_files(self, files: List[Path]) -> Iterator[Tuple[List[Path], str]]:
        """Agrupa arquivos em chunks processáveis."""
        current_chunk = []
        current_size = 0
        current_content = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_tokens = self.count_tokens(content)
                
                # Se arquivo sozinho é muito grande, processa individualmente
                if file_tokens > self.max_chunk_size:
                    # Yield chunk atual se houver
                    if current_chunk:
                        yield current_chunk, '\n'.join(current_content)
                        current_chunk = []
                        current_content = []
                        current_size = 0
                    
                    # Processa arquivo grande em chunks
                    chunks = self.chunk_text(content)
                    for i, chunk in enumerate(chunks):
                        yield [file_path], f"# Chunk {i+1}/{len(chunks)} de {file_path.name}\n{chunk}"
                
                # Se adicionar arquivo excede limite
                elif current_size + file_tokens > self.max_chunk_size:
                    # Yield chunk atual
                    yield current_chunk, '\n'.join(current_content)
                    
                    # Começa novo chunk
                    current_chunk = [file_path]
                    current_content = [f"# {file_path}\n{content}"]
                    current_size = file_tokens
                
                # Adiciona ao chunk atual
                else:
                    current_chunk.append(file_path)
                    current_content.append(f"# {file_path}\n{content}")
                    current_size += file_tokens
                    
            except Exception as e:
                print(f"Erro ao processar {file_path}: {e}")
        
        # Yield último chunk
        if current_chunk:
            yield current_chunk, '\n'.join(current_content)
    
    def chunk_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide tarefa complexa em sub-tarefas."""
        task_type = task.get('type', 'generic')
        
        if task_type == 'refactor_project':
            return self._chunk_refactor_task(task)
        elif task_type == 'add_feature':
            return self._chunk_feature_task(task)
        elif task_type == 'analyze_project':
            return self._chunk_analysis_task(task)
        else:
            # Tarefa simples, não precisa chunking
            return [task]
    
    def _chunk_refactor_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide tarefa de refatoração."""
        files = task.get('files', [])
        chunks = []
        
        # Agrupa arquivos relacionados
        for i, file_group in enumerate(self._group_related_files(files)):
            chunks.append({
                'type': 'refactor_chunk',
                'chunk_id': i + 1,
                'total_chunks': len(files) // 10 + 1,
                'files': file_group,
                'original_task': task.get('description', ''),
                'preserve_functionality': True
            })
        
        return chunks
    
    def _chunk_feature_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide implementação de feature."""
        feature = task.get('feature', {})
        
        # Divide em etapas lógicas
        chunks = [
            {
                'type': 'feature_analysis',
                'chunk_id': 1,
                'description': f"Analisar requisitos: {feature.get('description', '')}",
                'output': 'requirements_doc'
            },
            {
                'type': 'feature_design',
                'chunk_id': 2,
                'description': 'Criar design e arquitetura',
                'input': 'requirements_doc',
                'output': 'design_doc'
            },
            {
                'type': 'feature_backend',
                'chunk_id': 3,
                'description': 'Implementar backend/API',
                'input': 'design_doc',
                'output': 'backend_code'
            },
            {
                'type': 'feature_frontend',
                'chunk_id': 4,
                'description': 'Implementar interface',
                'input': 'design_doc',
                'output': 'frontend_code'
            },
            {
                'type': 'feature_tests',
                'chunk_id': 5,
                'description': 'Criar testes automatizados',
                'input': ['backend_code', 'frontend_code'],
                'output': 'test_suite'
            },
            {
                'type': 'feature_integration',
                'chunk_id': 6,
                'description': 'Integrar e validar feature completa',
                'input': ['backend_code', 'frontend_code', 'test_suite'],
                'output': 'integrated_feature'
            }
        ]
        
        return chunks
    
    def _chunk_analysis_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide tarefa de análise."""
        project_path = task.get('project_path', '.')
        
        chunks = [
            {
                'type': 'analysis_structure',
                'chunk_id': 1,
                'description': 'Analisar estrutura do projeto',
                'focus': ['arquitetura', 'organização', 'dependências']
            },
            {
                'type': 'analysis_code_quality',
                'chunk_id': 2,
                'description': 'Analisar qualidade do código',
                'focus': ['padrões', 'complexidade', 'duplicação']
            },
            {
                'type': 'analysis_performance',
                'chunk_id': 3,
                'description': 'Analisar performance',
                'focus': ['gargalos', 'otimizações', 'recursos']
            },
            {
                'type': 'analysis_security',
                'chunk_id': 4,
                'description': 'Analisar segurança',
                'focus': ['vulnerabilidades', 'boas práticas', 'exposições']
            },
            {
                'type': 'analysis_summary',
                'chunk_id': 5,
                'description': 'Gerar relatório consolidado',
                'consolidate': True
            }
        ]
        
        return chunks
    
    def _group_related_files(self, files: List[str], group_size: int = 10) -> List[List[str]]:
        """Agrupa arquivos relacionados."""
        # Agrupa por diretório
        by_dir = {}
        for file in files:
            dir_path = str(Path(file).parent)
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(file)
        
        # Cria grupos respeitando diretórios
        groups = []
        current_group = []
        
        for dir_path, dir_files in by_dir.items():
            for file in dir_files:
                current_group.append(file)
                if len(current_group) >= group_size:
                    groups.append(current_group)
                    current_group = []
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def merge_chunk_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mescla resultados de chunks processados."""
        merged = {
            'success': all(r.get('success', False) for r in results),
            'total_chunks': len(results),
            'processed_chunks': sum(1 for r in results if r.get('success', False)),
            'results': [],
            'errors': [],
            'summary': ''
        }
        
        # Mescla resultados específicos por tipo
        if results and results[0].get('type') == 'analysis':
            merged['analysis'] = self._merge_analysis_results(results)
        elif results and results[0].get('type') == 'refactor':
            merged['changes'] = self._merge_refactor_results(results)
        elif results and results[0].get('type') == 'feature':
            merged['feature'] = self._merge_feature_results(results)
        
        # Coleta erros
        for result in results:
            if result.get('errors'):
                merged['errors'].extend(result['errors'])
        
        return merged
    
    def _merge_analysis_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mescla resultados de análise."""
        analysis = {
            'issues': [],
            'metrics': {},
            'recommendations': []
        }
        
        for result in results:
            if 'issues' in result:
                analysis['issues'].extend(result['issues'])
            if 'metrics' in result:
                analysis['metrics'].update(result['metrics'])
            if 'recommendations' in result:
                analysis['recommendations'].extend(result['recommendations'])
        
        # Remove duplicatas
        analysis['recommendations'] = list(set(analysis['recommendations']))
        
        return analysis
    
    def _merge_refactor_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mescla resultados de refatoração."""
        all_changes = []
        
        for result in results:
            if 'changes' in result:
                all_changes.extend(result['changes'])
        
        return all_changes
    
    def _merge_feature_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mescla resultados de implementação de feature."""
        feature = {
            'components': [],
            'files_created': [],
            'files_modified': [],
            'tests': [],
            'documentation': []
        }
        
        for result in results:
            for key in feature:
                if key in result:
                    if isinstance(result[key], list):
                        feature[key].extend(result[key])
                    else:
                        feature[key].append(result[key])
        
        return feature