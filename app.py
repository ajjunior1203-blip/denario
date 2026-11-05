import sys
import os
import streamlit as st
import importlib.util

# Garante que a raiz do projeto está no path do Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configuração da página para Mobile-First
st.set_page_config(
    page_title="Denário",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Carregamento direto do ficheiro ui/theme.py
theme_path = os.path.join(BASE_DIR, "ui", "theme.py")
spec = importlib.util.spec_from_file_location("theme_module", theme_path)
theme_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme_module)

# Injeta metadados de PWA para telemóvel
st.markdown("""
    <link rel="manifest" href="/app/static/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# Aplica o tema visual chamando a função 'aplicar' do theme.py
theme_module.aplicar("azul")

# Importação dos restantes módulos internos
from core.db import init_db
from ui import v_login, v_lancamentos, v_orcamento, v_relatorios, v_perfil, v_admin

# Inicializa a base de dados (Supabase / PostgreSQL)
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