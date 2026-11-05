"""Tela de entrada: login, criação de conta e (opcional) Google."""
from __future__ import annotations

import streamlit as st

from core import auth
from ui import theme


def _entrar(usuario: dict, manter: bool) -> None:
    st.session_state["uid"] = usuario["id"]
    if manter:
        # O token vai na URL: ao salvar/adicionar à tela inicial do celular, o aparelho continua conectado.
        st.query_params["s"] = auth.criar_sessao(usuario["id"])
    st.rerun()


def pagina_login(google_disponivel: bool) -> None:
    st.markdown(
        '<div class="mc-login">'
        '<div class="mc-brand"><div class="mc-logo">D</div>Denário</div>'
        '<div class="mc-selo">Gratuito e privado</div>'
        '<h1>Seu dinheiro organizado, mês a mês.</h1>'
        '<p>Anote gastos em segundos, defina quanto pode gastar em cada coisa e veja exatamente para onde seu dinheiro vai.</p>'
        '</div>', unsafe_allow_html=True)

    with st.container(key="cartao_login"):
        aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])
        with aba_entrar:
            with st.form("form_login"):
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                manter = st.checkbox("Manter conectado neste aparelho", value=True, key="login_manter")
                if st.form_submit_button("Entrar", type="primary"):
                    usuario = auth.autenticar(email, senha)
                    if usuario:
                        _entrar(usuario, manter)
                    else:
                        st.error("E-mail ou senha incorretos.")
        with aba_criar:
            with st.form("form_criar"):
                nome = st.text_input("Nome", key="criar_nome")
                email_novo = st.text_input("E-mail", key="criar_email")
                senha_nova = st.text_input("Senha", type="password", key="criar_senha",
                                           help=f"Mínimo de {auth.SENHA_MINIMA} caracteres.")
                manter_novo = st.checkbox("Manter conectado neste aparelho", value=True, key="criar_manter")
                if st.form_submit_button("Criar conta", type="primary"):
                    try:
                        uid = auth.criar_usuario(email_novo, nome, senha_nova)
                    except ValueError as e:
                        st.error(str(e))
                    else:
                        _entrar(auth.obter(uid), manter_novo)
        if google_disponivel:
            st.button("Entrar com Google", key="login_google", on_click=st.login)
