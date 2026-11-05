import html
import streamlit as st

PALETAS = {
    "azul": {
        "nome": "Azul", 
        "primaria": "#14284F", 
        "hero": "linear-gradient(135deg,#0B1D45 0%,#153C7C 100%)",
        "suave": "#DCE7F8", 
        "fundo": "#F1F5FA", 
        "fundo2": "#E8EEF6"
    },
    "vermelho": {
        "nome": "Vermelho escuro", 
        "primaria": "#6A1423", 
        "hero": "linear-gradient(135deg,#4A0E19 0%,#7E1D31 100%)",
        "suave": "#F6DCE1", 
        "fundo": "#F9F3F4", 
        "fundo2": "#F1E6E8"
    },
    "preto": {
        "nome": "Preto", 
        "primaria": "#161616", 
        "hero": "linear-gradient(135deg,#0C0C0C 0%,#2C2C2C 100%)",
        "suave": "#E4E4E4", 
        "fundo": "#F5F5F5", 
        "fundo2": "#EBEBEB"
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --mc-ink: #0F1B33; --mc-mut: #6B7A90; --mc-line: #E2E8F0; --mc-card: #FFFFFF;
  --mc-in: #0F9D63;  --mc-out: #D6403F; --mc-warn: #E39B12;
  --mc-primary: __PRIM__; --mc-hero: __HERO__; --mc-soft: __SOFT__; --mc-bg: __BG__; --mc-bg2: __BG2__;
  --mc-font: 'Manrope', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
body, body *:not([data-testid="stIconMaterial"]) { font-family: var(--mc-font); }
.stApp { background: linear-gradient(180deg, var(--mc-bg) 0%, var(--mc-bg2) 100%); color: var(--mc-ink); }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { max-width: 560px; padding: 0 1rem 9rem !important; }
[data-testid="stVerticalBlock"] { gap: .75rem; }

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 12px; font-weight: 700; min-height: 2.75rem; border: 1px solid var(--mc-line); background: #fff; color: var(--mc-ink);
}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"], button[kind="primary"] {
  background: var(--mc-primary) !important; border-color: var(--mc-primary) !important; color: #fff !important;
}
</style>
"""

def aplicar(tema: str = "azul") -> None:
    p = PALETAS.get(tema, PALETAS["azul"])
    css = (CSS.replace("__PRIM__", p["primaria"])
              .replace("__HERO__", p["hero"])
              .replace("__SOFT__", p["suave"])
              .replace("__BG__", p["fundo"])
              .replace("__BG2__", p["fundo2"]))
    st.markdown(css, unsafe_allow_html=True)

# Alias de compatibilidade
aplicar_tema = aplicar