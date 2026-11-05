import bcrypt
import streamlit as st
from core.db import get_session, Usuario

def hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def autenticar_usuario(email: str, senha: str):
    session = get_session()
    try:
        user = session.query(Usuario).filter(Usuario.email == email.lower().strip()).first()
        if not user:
            return None, "Utilizador não encontrado."
        
        if not verificar_senha(senha, user.senha_hash):
            return None, "Palavra-passe incorreta."
            
        if not user.is_approved:
            return None, "A sua conta aguarda aprovação pelo Administrador."
            
        return user, "OK"
    finally:
        session.close()

def criar_usuario_por_admin(admin_user_id: int, email: str, senha: str, nome: str, role: str = 'user') -> tuple[bool, str]:
    """Cria e aprova um novo utilizador diretamente pelo painel do Admin."""
    session = get_session()
    try:
        admin = session.query(Usuario).filter(Usuario.id == admin_user_id, Usuario.role == 'admin').first()
        if not admin:
            return False, "Permissão negada. Apenas administradores podem criar utilizadores."

        email_clean = email.lower().strip()
        existente = session.query(Usuario).filter(Usuario.email == email_clean).first()
        if existente:
            return False, "E-mail já registado no sistema."

        novo_user = Usuario(
            email=email_clean,
            senha_hash=hash_senha(senha),
            nome=nome.strip(),
            role=role,
            is_approved=True  # Criado pelo Admin já nasce aprovado
        )
        session.add(novo_user)
        session.commit()
        return True, "Utilizador criado com sucesso!"
    except Exception as e:
        session.rollback()
        return False, f"Erro ao criar utilizador: {str(e)}"
    finally:
        session.close()

def listar_utilizadores_pendentes(admin_user_id: int):
    session = get_session()
    try:
        return session.query(Usuario).filter(Usuario.is_approved == False).all()
    finally:
        session.close()

def aprovar_utilizador(admin_user_id: int, user_id_para_aprovar: int) -> bool:
    session = get_session()
    try:
        admin = session.query(Usuario).filter(Usuario.id == admin_user_id, Usuario.role == 'admin').first()
        if not admin:
            return False

        user = session.query(Usuario).filter(Usuario.id == user_id_para_aprovar).first()
        if user:
            user.is_approved = True
            session.commit()
            return True
        return False
    finally:
        session.close()