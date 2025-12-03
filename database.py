# arquivo: database.py
# Descrição: Classe para gerenciar a persistência de livros usando SQLite.
# Comentários abaixo explicam cada seção/parte do módulo.


class Database:
    # Inicialização da classe
    # - db_name: nome do arquivo do banco SQLite (padrão "biblioteca.db")
    # - chama init_db() para garantir que a tabela exista
    def __init__(self, db_name: str = "biblioteca.db"):
        self.db_name = db_name
        self.init_db()
    
    # Cria e retorna uma nova conexão com o banco de dados
    # - configura row_factory para sqlite3.Row para poder obter dicionários
    def get_connection(self):
        """Cria uma nova conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Para retornar dicionários
        return conn
    
    # Inicializa o banco de dados criando a tabela 'livros' se não existir
    # - executa o DDL para criar a tabela com colunas id, titulo, autor, ano_publicacao, disponivel
    def init_db(self):
        """Inicializa o banco de dados criando a tabela se não existir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS livros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    ano_publicacao INTEGER NOT NULL,
                    disponivel BOOLEAN NOT NULL DEFAULT 1
                )
            ''')
            conn.commit()
    
    # Insere um novo livro e retorna o ID gerado
    # - parametros: titulo, autor, ano_publicacao, disponivel (opcional)
    # - usa parâmetros do sqlite para evitar SQL injection
    def create_livro(self, titulo: str, autor: str, ano_publicacao: int, disponivel: bool = True) -> int:
        """Insere um novo livro e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO livros (titulo, autor, ano_publicacao, disponivel)
                VALUES (?, ?, ?, ?)
            ''', (titulo, autor, ano_publicacao, disponivel))
            conn.commit()
            return cursor.lastrowid
    
    # Retorna todos os livros como lista de dicionários
    # - converte cada sqlite3.Row em dict para facilitar uso externo
    def get_all_livros(self) -> List[dict]:
        """Retorna todos os livros"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros')
            return [dict(row) for row in cursor.fetchall()]
    
    # Retorna um livro pelo ID ou None se não existir
    # - útil para buscas específicas
    def get_livro_by_id(self, livro_id: int) -> Optional[dict]:
        """Retorna um livro específico pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros WHERE id = ?', (livro_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Atualiza campos permitidos de um livro
    # - recebe kwargs com chaves autorizadas
    # - evita atualizar campos não permitidos e retorna True se alguma linha foi alterada
    def update_livro(self, livro_id: int, **kwargs) -> bool:
        """Atualiza um livro existente"""
        if not kwargs:
            return False
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['titulo', 'autor', 'ano_publicacao', 'disponivel']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(livro_id)
        query = f"UPDATE livros SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    # Remove um livro pelo ID
    # - retorna True se uma linha foi deletada
    def delete_livro(self, livro_id: int) -> bool:
        """Exclui um livro pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM livros WHERE id = ?', (livro_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Verifica existência de um livro pelo ID
    # - retorna True se encontrar pelo menos uma linha
    def livro_exists(self, livro_id: int) -> bool:
        """Verifica se um livro existe pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM livros WHERE id = ?', (livro_id,))
            return cursor.fetchone() is not None
import sqlite3
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_name: str = "biblioteca.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        """Cria uma nova conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Para retornar dicionários
        return conn
    
    def init_db(self):
        """Inicializa o banco de dados criando a tabela se não existir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS livros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    ano_publicacao INTEGER NOT NULL,
                    disponivel BOOLEAN NOT NULL DEFAULT 1
                )
            ''')
            conn.commit()
    
    def create_livro(self, titulo: str, autor: str, ano_publicacao: int, disponivel: bool = True) -> int:
        """Insere um novo livro e retorna o ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO livros (titulo, autor, ano_publicacao, disponivel)
                VALUES (?, ?, ?, ?)
            ''', (titulo, autor, ano_publicacao, disponivel))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_livros(self) -> List[dict]:
        """Retorna todos os livros"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_livro_by_id(self, livro_id: int) -> Optional[dict]:
        """Retorna um livro específico pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM livros WHERE id = ?', (livro_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_livro(self, livro_id: int, **kwargs) -> bool:
        """Atualiza um livro existente"""
        if not kwargs:
            return False
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['titulo', 'autor', 'ano_publicacao', 'disponivel']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(livro_id)
        query = f"UPDATE livros SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_livro(self, livro_id: int) -> bool:
        """Exclui um livro pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM livros WHERE id = ?', (livro_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def livro_exists(self, livro_id: int) -> bool:
        """Verifica se um livro existe pelo ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM livros WHERE id = ?', (livro_id,))
            return cursor.fetchone() is not None