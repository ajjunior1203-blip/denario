from datetime import datetime
from core.db import get_session, Lancamento

def criar_lancamento(user_id: int, descricao: str, valor: float, tipo: str, categoria: str, data: datetime) -> tuple[bool, str]:
    session = get_session()
    try:
        novo = Lancamento(
            user_id=user_id,
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            categoria=categoria,
            data=data
        )
        session.add(novo)
        session.commit()
        return True, "Lançamento efetuado."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def listar_lancamentos(user_id: int, limite: int = 20):
    session = get_session()
    try:
        return (
            session.query(Lancamento)
            .filter(Lancamento.user_id == user_id)
            .order_by(Lancamento.data.desc())
            .limit(limite)
            .all()
        )
    finally:
        session.close()

def eliminar_lancamento(user_id: int, lancamento_id: int) -> bool:
    session = get_session()
    try:
        item = session.query(Lancamento).filter(
            Lancamento.id == lancamento_id,
            Lancamento.user_id == user_id
        ).first()
        if item:
            session.delete(item)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()