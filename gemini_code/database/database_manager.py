"""
Gerenciador de banco de dados com comandos naturais.
"""

import sqlite3
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd

from ..core.gemini_client import GeminiClient


class DatabaseManager:
    """Gerencia banco de dados com linguagem natural."""
    
    def __init__(self, gemini_client: GeminiClient, db_path: str = None):
        self.gemini_client = gemini_client
        self.db_path = db_path or str(Path('.gemini_code/database.db'))
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Garante que o banco existe."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.close()
    
    async def natural_query(self, command: str) -> Dict[str, Any]:
        """Executa comandos naturais no banco."""
        # Traduz comando natural para SQL
        sql = await self._translate_to_sql(command)
        
        if not sql:
            return {
                'success': False,
                'error': 'Não consegui entender o comando',
                'suggestion': 'Tente: "Mostra os clientes" ou "Cria tabela produtos"'
            }
        
        # Executa SQL
        try:
            result = self._execute_sql(sql)
            
            # Formata resultado de forma amigável
            formatted = await self._format_result(result, command)
            
            return {
                'success': True,
                'data': formatted,
                'sql': sql,
                'rows_affected': result.get('rows_affected', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sql': sql,
                'suggestion': await self._suggest_fix(str(e), sql)
            }
    
    async def _translate_to_sql(self, natural_command: str) -> Optional[str]:
        """Traduz comando natural para SQL usando IA."""
        # Obtém schema atual
        tables = self._get_schema()
        
        prompt = f"""
        Traduza este comando em português para SQL:
        
        Comando: {natural_command}
        
        Tabelas existentes:
        {json.dumps(tables, indent=2)}
        
        Regras:
        - Se for criar tabela, use tipos apropriados
        - Se for consulta, seja específico
        - Se for inserção, valide dados
        - Para "mostra", use SELECT
        - Para "cria", use CREATE TABLE
        - Para "adiciona", use INSERT ou ALTER TABLE
        - Para "remove/deleta", use DELETE
        - Para "atualiza", use UPDATE
        
        Retorne APENAS o SQL, sem explicações.
        """
        
        response = await self.gemini_client.generate_response(prompt)
        
        # Limpa resposta
        sql = response.strip()
        if sql.startswith('```sql'):
            sql = sql.split('```sql')[1].split('```')[0].strip()
        
        return sql if sql else None
    
    def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """Executa SQL e retorna resultado."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            
            # SELECT query
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                return {
                    'type': 'query',
                    'data': data,
                    'columns': columns,
                    'row_count': len(data)
                }
            
            # Outras operações
            else:
                conn.commit()
                return {
                    'type': 'command',
                    'rows_affected': cursor.rowcount,
                    'last_id': cursor.lastrowid
                }
                
        finally:
            conn.close()
    
    def _get_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """Obtém schema do banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema = {}
        
        try:
            # Lista tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Obtém colunas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema[table_name] = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'nullable': col[3] == 0,
                        'primary_key': col[5] == 1
                    }
                    for col in columns
                ]
                
        finally:
            conn.close()
        
        return schema
    
    async def _format_result(self, result: Dict[str, Any], original_command: str) -> Union[str, List[Dict]]:
        """Formata resultado de forma amigável."""
        if result['type'] == 'query':
            if not result['data']:
                return "Nenhum resultado encontrado."
            
            # Para poucos resultados, mostra tabela
            if len(result['data']) <= 10:
                return result['data']
            
            # Para muitos resultados, resume
            else:
                summary = f"Encontrados {len(result['data'])} registros.\n"
                summary += "Primeiros 5:\n"
                summary += json.dumps(result['data'][:5], indent=2, ensure_ascii=False)
                return summary
        
        else:
            # Mensagem amigável para comandos
            if 'CREATE TABLE' in result.get('sql', '').upper():
                return "✅ Tabela criada com sucesso!"
            elif 'INSERT' in result.get('sql', '').upper():
                return f"✅ {result['rows_affected']} registro(s) adicionado(s)!"
            elif 'UPDATE' in result.get('sql', '').upper():
                return f"✅ {result['rows_affected']} registro(s) atualizado(s)!"
            elif 'DELETE' in result.get('sql', '').upper():
                return f"✅ {result['rows_affected']} registro(s) removido(s)!"
            else:
                return f"✅ Comando executado! {result['rows_affected']} linhas afetadas."
    
    async def _suggest_fix(self, error: str, sql: str) -> str:
        """Sugere correção para erro."""
        prompt = f"""
        O SQL gerou este erro:
        
        SQL: {sql}
        Erro: {error}
        
        Sugira uma correção em português simples (máximo 2 linhas).
        """
        
        suggestion = await self.gemini_client.generate_response(prompt)
        return suggestion.strip()
    
    async def create_table_natural(self, description: str) -> bool:
        """Cria tabela baseado em descrição natural."""
        prompt = f"""
        Crie um CREATE TABLE SQL baseado nesta descrição:
        
        {description}
        
        Use tipos apropriados:
        - ID sempre como INTEGER PRIMARY KEY AUTOINCREMENT
        - Textos como TEXT ou VARCHAR
        - Números como INTEGER ou REAL
        - Datas como DATE ou DATETIME
        - Booleanos como INTEGER (0/1)
        
        Adicione campos úteis como:
        - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        - updated_at DATETIME
        
        Retorne apenas o SQL.
        """
        
        sql = await self.gemini_client.generate_response(prompt)
        
        # Limpa e executa
        if sql.startswith('```sql'):
            sql = sql.split('```sql')[1].split('```')[0].strip()
        
        try:
            self._execute_sql(sql)
            return True
        except Exception as e:
            print(f"Erro ao criar tabela: {e}")
            return False
    
    def backup_database(self, backup_name: str = None) -> str:
        """Faz backup do banco."""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        backup_dir = Path('.gemini_code/backups')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_path = backup_dir / backup_name
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        return str(backup_path)
    
    def restore_database(self, backup_path: str) -> bool:
        """Restaura banco de backup."""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            print(f"Erro ao restaurar: {e}")
            return False
    
    async def analyze_data(self, table_name: str) -> Dict[str, Any]:
        """Analisa dados de uma tabela."""
        try:
            # Carrega dados
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            
            if df.empty:
                return {'error': 'Tabela vazia'}
            
            analysis = {
                'total_records': len(df),
                'columns': list(df.columns),
                'data_types': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'statistics': {}
            }
            
            # Estatísticas para colunas numéricas
            for col in df.select_dtypes(include=['int64', 'float64']).columns:
                analysis['statistics'][col] = {
                    'mean': float(df[col].mean()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'std': float(df[col].std())
                }
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    async def smart_search(self, search_term: str) -> List[Dict[str, Any]]:
        """Busca inteligente em todas as tabelas."""
        results = []
        schema = self._get_schema()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            for table_name, columns in schema.items():
                # Busca em colunas de texto
                text_columns = [col['name'] for col in columns if 'TEXT' in col['type'].upper() or 'VARCHAR' in col['type'].upper()]
                
                if text_columns:
                    where_clauses = [f"{col} LIKE '%{search_term}%'" for col in text_columns]
                    where_sql = " OR ".join(where_clauses)
                    
                    sql = f"SELECT * FROM {table_name} WHERE {where_sql}"
                    
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        results.append({
                            'table': table_name,
                            'data': dict(row)
                        })
                        
        finally:
            conn.close()
        
        return results