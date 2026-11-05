import streamlit as st

def aplicar_tema():
    """Aplica o tema visual otimizado para o Denário."""
    st.markdown("""
        <style>
        /* Esconde o menu padrão e rodapé do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Ajustes de margem superior para ecrã táctil / mobile */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        /* Botões mais largos e fáceis de tocar no telemóvel */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 2.8rem;
            font-weight: 600;
        }

        /* Estilo dos menus de navegação superior */
        div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)