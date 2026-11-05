"""Aba Lançamentos: saldo do mês, lista de gastos e entradas agrupada por dia."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import calc, repo
from ui import dialogos, theme

_ESPECIAIS = "\\`*_{}[]()#+-.!~<>$|"


def _md(texto: str) -> str:
    """Escapa caracteres de Markdown para usar o texto como rótulo de botão."""
    return "".join("\\" + c if c in _ESPECIAIS else c for c in str(texto))


def _alternar(uid: int, lancamento_id: int) -> None:
    repo.alternar_pago(uid, lancamento_id)


def pagina_lancamentos(uid: int, mes: str) -> None:
    theme.mostrar_aviso()
    df = repo.listar_lancamentos(uid, mes, mes)
    resumo = calc.resumo_mes(uid, mes, df)

    theme.hero("Saldo do mês", resumo["saldo"], "Entradas − todos os gastos lançados")
    theme.kpis([("Entradas", resumo["entradas"], "mc-in"), ("Gastos", resumo["saidas"], "mc-out"),
                ("A pagar", resumo["a_pagar"], "mc-warn")])

    n_gastos, n_entradas = int((df["tipo"] == "saida").sum()), int((df["tipo"] == "entrada").sum())
    with st.container(key="fila_seg"):
        c1, c2 = st.columns([9, 1])
        with c1:
            with st.container(key="seg"):
                tipo = theme.segmentado("Lista", ["saida", "entrada"], "lista_tipo",
                                        format_func=lambda t: f"Gastos ({n_gastos})" if t == "saida" else f"Entradas ({n_entradas})")
        with c2:
            copiar = st.button(":material/content_copy:", key="ic_copiar", type="tertiary",
                               help="Copiar as contas fixas do mês anterior")
    if copiar:
        anterior = calc.mes_add(mes, -1)
        n = repo.copiar_fixos(uid, anterior, mes)
        theme.aviso(f"{n} lançamento(s) fixo(s) copiado(s) de {calc.rotulo_mes(anterior)}." if n
                    else "Não há lançamentos fixos novos para copiar do mês anterior.", "ok" if n else "info")
        st.rerun()

    sub = df[df["tipo"] == tipo]
    rotulos_status = ["Todos", "A pagar", "Pagos"] if tipo == "saida" else ["Todos", "A receber", "Recebidos"]
    with st.container(key="fila_chips"):
        status = theme.chips("Situação", rotulos_status, "lista_status", padrao="Todos")
        categorias = sorted(sub["categoria"].unique())
        categoria = theme.chips("Categoria", categorias, "lista_cat") if categorias else None
    if status == rotulos_status[1]:
        sub = sub[~sub["pago"]]
    elif status == rotulos_status[2]:
        sub = sub[sub["pago"]]
    if categoria:
        sub = sub[sub["categoria"] == categoria]

    editar = None
    if sub.empty:
        theme.vazio("Nada por aqui ainda. Toque em + para lançar." if df.empty
                    else "Nenhum lançamento com esses filtros.")
    for dia, grupo in sub.groupby(sub["vencimento"].dt.date, sort=True):
        st.markdown(f'<div class="mc-dia">{theme.esc(calc.rotulo_dia(dia))}</div>', unsafe_allow_html=True)
        with st.container(key=f"lista_{dia.isoformat()}"):
            for r in grupo.itertuples():
                if _linha(uid, r):
                    editar = int(r.id)

    if editar is not None:
        st.session_state["dlg_n"] = st.session_state.get("dlg_n", 0) + 1
        dialogos.dialogo_editar(uid, editar)


def _linha(uid: int, r) -> bool:
    """Desenha um lançamento. Devolve True se o nome foi tocado (abrir edição)."""
    partes = [r.categoria]
    if pd.notna(r.forma):
        partes.append(r.forma)
    if r.natureza == "fixa":
        partes.append("Fixa")
    cor = "mc-in" if r.tipo == "entrada" else "mc-out"
    with st.container(key=f"fila_item_{r.id}"):
        c1, c2, c3 = st.columns([1, 6, 3])
        with c1:
            st.button(":material/check_circle:" if r.pago else ":material/radio_button_unchecked:",
                      key=f"{'pgok' if r.pago else 'pg'}_{r.id}", type="tertiary", on_click=_alternar, args=(uid, int(r.id)),
                      help="Marcar como pendente" if r.pago else "Marcar como pago")
        with c2:
            tocou = st.button(_md(r.descricao), key=f"nome_{r.id}", type="tertiary")
            st.markdown(f'<div class="mc-sub">{theme.esc(" · ".join(partes))}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="mc-valor {cor}">{theme.brl(r.valor)}</div>', unsafe_allow_html=True)
    return tocou
