import streamlit as st
from core.auth import criar_usuario_por_admin, listar_utilizadores_pendentes, aprovar_utilizador

def render():
    st.markdown("### 🛡️ Painel Administrativo")

    user_id = st.session_state.get("user_id")
    role = st.session_state.get("user_role")

    if role != "admin":
        st.error("Acesso restrito a Administradores.")
        return

    st.markdown("#### ➕ Registar Novo Utilizador")
    with st.form("form_novo_user"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail")
        senha = st.text_input("Palavra-passe Inicial", type="password")
        tipo_conta = st.selectbox("Perfil de Acesso", options=["user", "admin"])
        
        btn_criar = st.form_submit_button("Criar Utilizador", use_container_width=True)

        if btn_criar:
            if not nome or not email or not senha:
                st.warning("Preencha todos os campos.")
            else:
                ok, msg = criar_usuario_por_admin(user_id, email, senha, nome, tipo_conta)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("---")
    st.markdown("#### ⏳ Solicitantes Pendentes")
    pendentes = listar_utilizadores_pendentes(user_id)

    if not pendentes:
        st.info("Nenhum utilizador aguarda aprovação no momento.")
    else:
        for u in pendentes:
            col_u, col_btn = st.columns([3, 1])
            with col_u:
                st.write(f"**{u.nome}** ({u.email})")
            with col_btn:
                if st.button("Aprovar", key=f"aprov_{u.id}"):
                    if aprovar_utilizador(user_id, u.id):
                        st.success(f"{u.nome} aprovado!")
                        st.rerun()