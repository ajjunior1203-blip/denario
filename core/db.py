import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    nome = Column(String(100), nullable=False)
    role = Column(String(20), default='user')
    is_approved = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    lancamentos = relationship("Lancamento", back_populates="usuario", cascade="all, delete-orphan")
    orcamentos = relationship("Orcamento", back_populates="usuario", cascade="all, delete-orphan")

class Lancamento(Base):
    __tablename__ = 'lancamentos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    descricao = Column(String(255), nullable=False)
    valor = Column(Float, nullable=False)
    tipo = Column(String(10), nullable=False)
    categoria = Column(String(50), nullable=False)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="lancamentos")

class Orcamento(Base):
    __tablename__ = 'orcamentos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    categoria = Column(String(50), nullable=False)
    limite_mensal = Column(Float, nullable=False)

    usuario = relationship("Usuario", back_populates="orcamentos")

@st.cache_resource
def get_engine():
    db_url = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///denario.db"))
    
    # Padroniza a URL para utilizar explicitamente o driver postgresql+psycopg2
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg2://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    return create_engine(db_url, pool_pre_ping=True)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)