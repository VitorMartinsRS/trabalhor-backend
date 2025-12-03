# api_fast.py
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from database import Database

# Inicializar o banco de dados
db = Database()

# Inicializar FastAPI
app = FastAPI(
    title="Biblioteca API",
    description="API para gerenciamento de livros da biblioteca",
    version="1.0.0"
)

# Modelos Pydantic
class LivroCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200, example="Dom Casmurro")
    autor: str = Field(..., min_length=1, max_length=100, example="Machado de Assis")
    ano_publicacao: int = Field(..., ge=1000, le=2100, example=1899)
    disponivel: bool = Field(default=True, example=True)

class LivroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200, example="Dom Casmurro")
    autor: Optional[str] = Field(None, min_length=1, max_length=100, example="Machado de Assis")
    ano_publicacao: Optional[int] = Field(None, ge=1000, le=2100, example=1899)
    disponivel: Optional[bool] = Field(None, example=True)

class LivroResponse(BaseModel):
    id: int
    titulo: str
    autor: str
    ano_publicacao: int
    disponivel: bool
    
    class Config:
        from_attributes = True

# Endpoints
@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Bem-vindo à API da Biblioteca",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/livros", response_model=List[LivroResponse], status_code=status.HTTP_200_OK)
async def listar_livros():
    """Lista todos os livros"""
    livros = db.get_all_livros()
    return livros

@app.get("/livros/{livro_id}", response_model=LivroResponse, status_code=status.HTTP_200_OK)
async def obter_livro(livro_id: int):
    """Obtém um livro específico pelo ID"""
    livro = db.get_livro_by_id(livro_id)
    if not livro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro com ID {livro_id} não encontrado"
        )
    return livro

@app.post("/livros", response_model=LivroResponse, status_code=status.HTTP_201_CREATED)
async def criar_livro(livro: LivroCreate):
    """Adiciona um novo livro"""
    livro_id = db.create_livro(
        titulo=livro.titulo,
        autor=livro.autor,
        ano_publicacao=livro.ano_publicacao,
        disponivel=livro.disponivel
    )
    
    novo_livro = db.get_livro_by_id(livro_id)
    return novo_livro

@app.put("/livros/{livro_id}", response_model=LivroResponse, status_code=status.HTTP_200_OK)
async def atualizar_livro(livro_id: int, livro_update: LivroUpdate):
    """Atualiza um livro existente"""
    # Verificar se o livro existe
    if not db.livro_exists(livro_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro com ID {livro_id} não encontrado"
        )
    
    # Filtrar campos que não são None
    update_data = livro_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado fornecido para atualização"
        )
    
    # Atualizar o livro
    success = db.update_livro(livro_id, **update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao atualizar o livro"
        )
    
    # Retornar o livro atualizado
    livro_atualizado = db.get_livro_by_id(livro_id)
    return livro_atualizado

@app.delete("/livros/{livro_id}", status_code=status.HTTP_200_OK)
async def deletar_livro(livro_id: int):
    """Exclui um livro pelo ID"""
    # Verificar se o livro existe
    if not db.livro_exists(livro_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro com ID {livro_id} não encontrado"
        )
    
    # Excluir o livro
    success = db.delete_livro(livro_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao excluir o livro"
        )
    
    return {"message": f"Livro com ID {livro_id} excluído com sucesso"}

# Adicionar alguns livros de exemplo na inicialização
@app.on_event("startup")
async def startup_event():
    """Adiciona alguns livros de exemplo quando a API inicia"""
    try:
        # Verificar se já existem livros
        livros = db.get_all_livros()
        if len(livros) == 0:
            # Adicionar livros de exemplo
            db.create_livro(
                titulo="Dom Casmurro",
                autor="Machado de Assis",
                ano_publicacao=1899,
                disponivel=True
            )
            db.create_livro(
                titulo="1984",
                autor="George Orwell",
                ano_publicacao=1949,
                disponivel=False
            )
            db.create_livro(
                titulo="O Senhor dos Anéis",
                autor="J.R.R. Tolkien",
                ano_publicacao=1954,
                disponivel=True
            )
            print("Livros de exemplo adicionados com sucesso!")
    except Exception as e:
        print(f"Erro ao adicionar livros de exemplo: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_fast:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )