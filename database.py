# database.py
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