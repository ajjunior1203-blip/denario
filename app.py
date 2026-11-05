import streamlit as st
from core.db import init_db

# Importação direta do módulo de tema
from ui import theme

# Importação direta das views
from ui import v_login, v_lancamentos, v_orcamento, v_relatorios, v_perfil, v_admin

# Configuração da página para Mobile First
st.set_page_config(
    page_title="Denário",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Injeta metadados de PWA na aplicação
st.markdown("""
    <link rel="manifest" href="/app/static/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# Aplica o tema visual (utilizando a função aplicar() presente no theme.py)
theme.aplicar()

# Inicializa as tabelas do banco de dados na inicialização
init_db()

# Controlo de Estado da Sessão
if "usuario_autenticado" not in st.session_state:
    st.session_state["usuario_autenticado"] = False

if not st.session_state["usuario_autenticado"]:
    v_login.render()
else:
    # Menu Superior / Barra de Navegação Compacta
    role = st.session_state.get("user_role", "user")
    
    opcoes_menu = ["⚡ Lançamentos", "📊 Relatórios", "🎯 Orçamento", "👤 Perfil"]
    if role == "admin":
        opcoes_menu.append("🛡️ Admin")

    aba_selecionada = st.radio("", opcoes_menu, horizontal=True, label_visibility="collapsed")

    if aba_selecionada == "⚡ Lançamentos":
        v_lancamentos.render()
    elif aba_selecionada == "📊 Relatórios":
        v_relatorios.render()
    elif aba_selecionada == "🎯 Orçamento":
        v_orcamento.render()
    elif aba_selecionada == "👤 Perfil":
        v_perfil.render()
    elif aba_selecionada == "🛡️ Admin" and role == "admin":
        v_admin.render()