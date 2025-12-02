from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date
import sqlite3
from contextlib import contextmanager

app = FastAPI(
    title="API de Livros",
    description="API para gerenciamento de livros com FastAPI e SQLite",
    version="1.0.0"
)

# Configuração do banco de dados - biblioteca.db
DATABASE = "biblioteca.db"

def criar_tabela():
    """Cria a tabela livros se não existir"""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                ano_publicacao INTEGER,
                disponivel INTEGER NOT NULL CHECK(disponivel IN (0,1))
            )
        """)
        conn.commit()

# Criar tabela ao iniciar
criar_tabela()

# Context manager para conexão com banco de dados
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para retornar dicionários
    try:
        yield conn
    finally:
        conn.close()

# Modelos Pydantic para validação

class LivroBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200, example="O Senhor dos Anéis")
    autor: str = Field(..., min_length=1, max_length=100, example="J.R.R. Tolkien")
    ano_publicacao: Optional[int] = Field(None, ge=1000, le=date.today().year, example=1954)
    disponivel: bool = Field(default=True, example=True)
    
    @validator('ano_publicacao')
    def validar_ano_publicacao(cls, v):
        if v is not None and (v < 1000 or v > date.today().year):
            raise ValueError(f"Ano de publicação deve estar entre 1000 e {date.today().year}")
        return v

class LivroCreate(LivroBase):
    pass

class LivroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200, example="O Senhor dos Anéis")
    autor: Optional[str] = Field(None, min_length=1, max_length=100, example="J.R.R. Tolkien")
    ano_publicacao: Optional[int] = Field(None, ge=1000, le=date.today().year, example=1954)
    disponivel: Optional[bool] = Field(None, example=True)
    
    @validator('ano_publicacao')
    def validar_ano_publicacao(cls, v):
        if v is not None and (v < 1000 or v > date.today().year):
            raise ValueError(f"Ano de publicação deve estar entre 1000 e {date.today().year}")
        return v

class Livro(LivroBase):
    id: int
    
    class Config:
        from_attributes = True

# Funções auxiliares do banco de dados
def livro_from_row(row):
    """Converte uma linha do banco de dados para um dicionário de livro"""
    return {
        "id": row["id"],
        "titulo": row["titulo"],
        "autor": row["autor"],
        "ano_publicacao": row["ano_publicacao"],
        "disponivel": bool(row["disponivel"])
    }

# Endpoints

@app.get("/", tags=["Raiz"])
def root():
    """Endpoint raiz da API"""
    return {
        "mensagem": "Bem-vindo à API de Livros da Biblioteca",
        "documentacao": "/docs",
        "endpoints": {
            "GET /livros": "Listar todos os livros",
            "GET /livros/{id}": "Obter livro por ID",
            "POST /livros": "Adicionar novo livro",
            "PUT /livros/{id}": "Atualizar livro existente",
            "DELETE /livros/{id}": "Excluir livro",
            "GET /status": "Status da biblioteca"
        },
        "banco_dados": f"SQLite ({DATABASE})"
    }

@app.get("/livros", response_model=List[Livro], tags=["Livros"])
def listar_livros():
    """Lista todos os livros cadastrados"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM livros ORDER BY id")
        livros = [livro_from_row(row) for row in cursor.fetchall()]
    return livros

@app.get("/livros/{id}", response_model=Livro, tags=["Livros"])
def obter_livro(id: int):
    """Obtém um livro específico pelo ID"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM livros WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Livro com ID {id} não encontrado"
            )
        
        return livro_from_row(row)

@app.post("/livros", response_model=Livro, status_code=status.HTTP_201_CREATED, tags=["Livros"])
def criar_livro(livro: LivroCreate):
    """Adiciona um novo livro à biblioteca"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO livros (titulo, autor, ano_publicacao, disponivel)
            VALUES (?, ?, ?, ?)
        """, (
            livro.titulo,
            livro.autor,
            livro.ano_publicacao,
            1 if livro.disponivel else 0
        ))
        conn.commit()
        
        livro_id = cursor.lastrowid
        
        # Recupera o livro recém-criado
        cursor = conn.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
        row = cursor.fetchone()
        
        return livro_from_row(row)

@app.put("/livros/{id}", response_model=Livro, tags=["Livros"])
def atualizar_livro(id: int, livro_update: LivroUpdate):
    """Atualiza um livro existente na biblioteca"""
    # Primeiro verifica se o livro existe
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM livros WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Livro com ID {id} não encontrado na biblioteca"
            )
    
    # Prepara os campos para atualização
    campos = []
    valores = []
    
    if livro_update.titulo is not None:
        campos.append("titulo = ?")
        valores.append(livro_update.titulo)
    
    if livro_update.autor is not None:
        campos.append("autor = ?")
        valores.append(livro_update.autor)
    
    if livro_update.ano_publicacao is not None:
        campos.append("ano_publicacao = ?")
        valores.append(livro_update.ano_publicacao)
    
    if livro_update.disponivel is not None:
        campos.append("disponivel = ?")
        valores.append(1 if livro_update.disponivel else 0)
    
    # Se não há campos para atualizar, retorna erro
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo fornecido para atualização"
        )
    
    # Adiciona o ID no final dos valores
    valores.append(id)
    
    # Executa a atualização
    with get_db_connection() as conn:
        query = f"UPDATE livros SET {', '.join(campos)} WHERE id = ?"
        conn.execute(query, valores)
        conn.commit()
        
        # Recupera o livro atualizado
        cursor = conn.execute("SELECT * FROM livros WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        return livro_from_row(row)

@app.delete("/livros/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Livros"])
def excluir_livro(id: int):
    """Exclui um livro da biblioteca"""
    with get_db_connection() as conn:
        # Verifica se o livro existe
        cursor = conn.execute("SELECT id FROM livros WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Livro com ID {id} não encontrado na biblioteca"
            )
        
        # Exclui o livro
        conn.execute("DELETE FROM livros WHERE id = ?", (id,))
        conn.commit()
    
    return None

# Popula o banco de dados com alguns exemplos iniciais se estiver vazio
@app.on_event("startup")
def popular_banco():
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM livros")
        count = cursor.fetchone()["count"]
        
        if count == 0:
            exemplos = [
                ("Dom Casmurro", "Machado de Assis", 1899, 1),
                ("1984", "George Orwell", 1949, 1),
                ("A Culpa é das Estrelas", "John Green", 2012, 0),
                ("Harry Potter e a Pedra Filosofal", "J.K. Rowling", 1997, 1),
                ("O Pequeno Príncipe", "Antoine de Saint-Exupéry", 1943, 1),
                ("Orgulho e Preconceito", "Jane Austen", 1813, 1),
                ("Crime e Castigo", "Fiódor Dostoiévski", 1866, 0),
                ("Cem Anos de Solidão", "Gabriel García Márquez", 1967, 1)
            ]
            
            conn.executemany("""
                INSERT INTO livros (titulo, autor, ano_publicacao, disponivel)
                VALUES (?, ?, ?, ?)
            """, exemplos)
            conn.commit()
            print(f"✅ Banco de dados '{DATABASE}' criado com {len(exemplos)} livros iniciais.")

# Endpoint adicional para informações do banco de dados
@app.get("/status", tags=["Biblioteca"])
def status_biblioteca():
    """Retorna informações sobre o status da biblioteca"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as total FROM livros")
        total = cursor.fetchone()["total"]
        
        cursor = conn.execute("SELECT COUNT(*) as disponiveis FROM livros WHERE disponivel = 1")
        disponiveis = cursor.fetchone()["disponiveis"]
        
        cursor = conn.execute("SELECT COUNT(*) as indisponiveis FROM livros WHERE disponivel = 0")
        indisponiveis = cursor.fetchone()["disponiveis"]
        
        # Pega os livros mais recentes
        cursor = conn.execute("SELECT * FROM livros ORDER BY id DESC LIMIT 5")
        recentes = [livro_from_row(row) for row in cursor.fetchall()]
        
    return {
        "biblioteca": DATABASE,
        "total_livros": total,
        "livros_disponiveis": disponiveis,
        "livros_indisponiveis": indisponiveis,
        "livros_recentes": recentes
    }

# Novo endpoint para buscar livros por título ou autor
@app.get("/livros/buscar/{termo}", response_model=List[Livro], tags=["Livros"])
def buscar_livros(termo: str):
    """Busca livros por título ou autor"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM livros 
            WHERE titulo LIKE ? OR autor LIKE ?
            ORDER BY titulo
        """, (f"%{termo}%", f"%{termo}%"))
        
        livros = [livro_from_row(row) for row in cursor.fetchall()]
        
        if not livros:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum livro encontrado com '{termo}'"
            )
        
        return livros