from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from fastapi_pagination import Page, add_pagination, paginate

# Configuração do banco de dados
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos
class Atleta(Base):
    __tablename__ = "atletas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    centro_treinamento = Column(String, index=True)
    categoria = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# Schemas
class AtletaBase(BaseModel):
    nome: str
    cpf: str
    centro_treinamento: str
    categoria: str

class AtletaCreate(AtletaBase):
    pass

class AtletaResponse(AtletaBase):
    id: int

    class Config:
        from_attributes = True

# CRUD
def get_atleta(db: Session, atleta_id: int):
    return db.query(Atleta).filter(Atleta.id == atleta_id).first()

def get_atleta_by_cpf(db: Session, cpf: str):
    return db.query(Atleta).filter(Atleta.cpf == cpf).first()

def get_atletas(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Atleta).offset(skip).limit(limit).all()

def create_atleta(db: Session, atleta: AtletaCreate):
    db_atleta = Atleta(**atleta.dict())
    try:
        db.add(db_atleta)
        db.commit()
        db.refresh(db_atleta)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=303, detail="Já existe um atleta cadastrado com o cpf: {}".format(atleta.cpf))
    return db_atleta

# Aplicação principal
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/atletas/", response_model=AtletaResponse)
def create_atleta_endpoint(atleta: AtletaCreate, db: Session = Depends(get_db)):
    return create_atleta(db=db, atleta=atleta)

@app.get("/atletas/", response_model=Page[AtletaResponse])
def read_atletas(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    atletas = get_atletas(db, skip=skip, limit=limit)
    return paginate(atletas)

@app.get("/atletas/{atleta_id}", response_model=AtletaResponse)
def read_atleta(atleta_id: int, db: Session = Depends(get_db)):
    db_atleta = get_atleta(db, atleta_id=atleta_id)
    if db_atleta is None:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    return db_atleta

add_pagination(app)

# Para executar a aplicação, use o comando:
# uvicorn main:app --reload