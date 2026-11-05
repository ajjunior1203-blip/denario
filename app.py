import sys
import os
import streamlit as st

# Garante que a raiz do projeto está no caminho de importação do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração da página para Mobile-First
st.set_page_config(
    page_title="Denário",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Importação dos módulos internos após o ajuste do sys.path
from core.db import init_db
from ui import theme
from ui import v_login, v_lancamentos, v_orcamento, v_relatorios, v_perfil, v_admin

# Injeta metadados de PWA para telemóvel
st.markdown("""
    <link rel="manifest" href="/app/static/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# Aplica o tema visual chamando a função 'aplicar' do theme.py
theme.aplicar("azul")

# Inicializa o banco de dados (Supabase / PostgreSQL)
init_db()

# Gestão de Sessão do Utilizador
if "usuario_autenticado" not in st.session_state:
    st.session_state["usuario_autenticado"] = False

if not st.session_state["usuario_autenticado"]:
    v_login.render()
else:
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