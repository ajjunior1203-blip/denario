"""Aba Orçamento: sobra para o orçamento volátil, contas fixas e percentuais."""
from __future__ import annotations

import streamlit as st

from core import calc, repo
from ui import dialogos, theme


def _remover(uid: int, tabela: str, mes: str, categoria_id: int) -> None:
    repo.definir_item_orcamento(uid, tabela, mes, categoria_id, None)
    theme.aviso(f"Removido a partir de {calc.rotulo_mes(mes)}.", "info")


def _cabecalho_item(uid: int, tabela: str, mes: str, categoria_id: int, nome: str, detalhe: str | None = None) -> bool:
    """Linha com nome e ícones de editar/excluir. Devolve True se o usuário tocou em editar."""
    c1, c2, c3 = st.columns([10, 1, 1])
    with c1:
        st.markdown(f'<div style="font-weight:700">{theme.esc(nome)}</div>'
                    + (f'<div class="mc-sub">{theme.esc(detalhe)}</div>' if detalhe else ""), unsafe_allow_html=True)
    with c2:
        editar = st.button(":material/edit:", key=f"ic_ed_{tabela}_{categoria_id}", type="tertiary", help="Editar")
    with c3:
        st.button(":material/delete:", key=f"ic_del_{tabela}_{categoria_id}", type="tertiary", help="Remover do orçamento",
                  on_click=_remover, args=(uid, tabela, mes, categoria_id))
    return editar


def pagina_orcamento(uid: int, mes: str) -> None:
    theme.mostrar_aviso()
    df = repo.listar_lancamentos(uid, mes, mes)
    fixo = calc.orcamento_fixo(uid, mes, df)
    vol = calc.orcamento_volatil(uid, mes, df)

    dica = None
    if vol["entradas_fixas"] <= 0:
        dica = "Marque suas entradas como “fixa” (ex.: salário) para calcular o orçamento volátil."
    theme.hero("Sobra para o orçamento volátil", vol["base"],
               caixas=[("Entradas fixas", vol["entradas_fixas"]), ("Orçamento fixo", vol["fixos_orcados"])], dica=dica)

    abrir = None  # (função do diálogo, argumentos)

    # ---- orçamento fixo
    theme.secao("Orçamento fixo")
    if fixo.empty:
        theme.vazio("Nenhuma conta fixa orçada. Adicione aluguel, internet, financiamento…")
    else:
        with st.container(key="lista_orc_fixo"):
            for r in fixo.itertuples():
                with st.container(key=f"fila_item_fixo_{r.categoria_id}"):
                    if _cabecalho_item(uid, "orcamento_fixo", mes, int(r.categoria_id), r.categoria):
                        abrir = (dialogos.dialogo_orc_fixo, (uid, mes, int(r.categoria_id)))
                    resta = r.desvio
                    theme.barra(r.lancado, r.orcado, f"{theme.brl(r.lancado)} de {theme.brl(r.orcado)}",
                                f"Resta {theme.brl(resta)}" if resta >= 0 else f"Passou {theme.brl(-resta)}", bom=resta >= 0)
    if st.button("Adicionar orçamento fixo", key="orc_add_fixo", icon=":material/add:"):
        abrir = (dialogos.dialogo_orc_fixo, (uid, mes, None))

    # ---- orçamento volátil
    alocado = vol["pct_alocado"]
    theme.secao("Orçamento volátil", f"Divide a sobra do mês entre as categorias. {alocado:g}% alocado"
                + ("." if abs(alocado - 100) < 0.01 else f", {100 - alocado:g}% sem destino."))
    if vol["linhas"].empty:
        theme.vazio("Nenhuma categoria no orçamento volátil. Adicione e defina o percentual de cada uma.")
    else:
        if vol["base"] <= 0 and vol["entradas_fixas"] > 0:
            st.warning("As contas fixas orçadas consomem todas as entradas fixas: não sobra nada para o orçamento volátil.")
        with st.container(key="lista_orc_volatil"):
            for r in vol["linhas"].itertuples():
                with st.container(key=f"fila_item_vol_{r.categoria_id}"):
                    if _cabecalho_item(uid, "orcamento_volatil", mes, int(r.categoria_id), r.categoria, f"{r.percentual:g}% da sobra"):
                        abrir = (dialogos.dialogo_orc_volatil, (uid, mes, int(r.categoria_id)))
                    resta = r.desvio
                    theme.barra(r.gasto, r.orcado, f"{theme.brl(r.gasto)} de {theme.brl(r.orcado)}",
                                f"Resta {theme.brl(resta)}" if resta >= 0 else f"Passou {theme.brl(-resta)}", bom=resta >= 0)
    if st.button("Adicionar orçamento volátil", key="orc_add_vol", icon=":material/add:"):
        abrir = (dialogos.dialogo_orc_volatil, (uid, mes, None))

    sem = vol["sem_orcamento"]
    if not sem.empty:
        theme.secao("Fora do orçamento", "Gastos em categorias sem orçamento fixo nem volátil.")
        with st.container(key="lista_orc_fora"):
            for i, r in enumerate(sem.itertuples()):
                with st.container(key=f"fila_item_fora_{i}"):
                    c1, c2 = st.columns([6, 4])
                    c1.markdown(f'<div style="font-weight:700">{theme.esc(r.categoria)}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="mc-valor mc-out">{theme.brl(r.gasto)}</div>', unsafe_allow_html=True)

    if abrir:
        st.session_state["dlg_n"] = st.session_state.get("dlg_n", 0) + 1
        funcao, args = abrir
        funcao(*args)
