"""Aba Relatórios: gastos por período, categoria, forma de pagamento e rótulo."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import calc, repo
from ui import graficos, theme


def _periodos(ref: str) -> dict[str, tuple[str, str]]:
    ano = ref[:4]
    return {"Mês": (ref, ref), "3 meses": (calc.mes_add(ref, -2), ref), "6 meses": (calc.mes_add(ref, -5), ref),
            "12 meses": (calc.mes_add(ref, -11), ref), "Ano": (f"{ano}-01", f"{ano}-12")}


def pagina_relatorios(uid: int, mes: str) -> None:
    theme.mostrar_aviso()
    opcoes = _periodos(mes)
    with st.container(key="seg"):
        escolha = theme.segmentado("Período", list(opcoes), "rel_periodo", padrao="3 meses")
    ini, fim = opcoes[escolha]
    modo = st.radio("Considerar pelo(a)", ["Vencimento", "Data da compra"], horizontal=True, key="rel_base",
                    help="Vencimento: compras no cartão contam no mês da fatura. Data da compra: contam no dia em que foram feitas.")
    base = "vencimento" if modo == "Vencimento" else "data"
    meses = calc.intervalo_meses(ini, fim)
    df = repo.listar_lancamentos(uid, ini, fim, base=base)
    st.markdown(f'<div class="mc-nota">{calc.rotulo_mes(ini)} a {calc.rotulo_mes(fim)} · {len(df)} lançamentos</div>',
                unsafe_allow_html=True)
    if df.empty:
        theme.vazio("Sem lançamentos neste período.")
        return

    entradas = round(float(df.loc[df["tipo"] == "entrada", "valor"].sum()), 2)
    gastos = round(float(df.loc[df["tipo"] == "saida", "valor"].sum()), 2)
    aba_resumo, aba_cat, aba_evo, aba_det = st.tabs(["Resumo", "Categorias", "Evolução", "Detalhes"])

    with aba_resumo:
        theme.hero("Saldo do período", entradas - gastos, f"Média de gastos por mês: {theme.brl(gastos / max(len(meses), 1))}")
        theme.kpis([("Entradas", entradas, "mc-in"), ("Gastos", gastos, "mc-out"),
                    ("A pagar", float(df.loc[(df["tipo"] == "saida") & (~df["pago"]), "valor"].sum()), "mc-warn")])
        theme.secao("Gastos por forma de pagamento")
        formas = calc.por_forma(df)
        if formas.empty:
            theme.vazio("Sem gastos no período.")
        else:
            st.altair_chart(graficos.barras_horizontais(formas, "forma", "total"))
        theme.secao("Maiores gastos")
        maiores = df[df["tipo"] == "saida"].nlargest(5, "valor")
        with st.container(key="lista_maiores"):
            for r in maiores.itertuples():
                with st.container(key=f"fila_item_maior_{r.id}"):
                    c1, c2 = st.columns([7, 4])
                    c1.markdown(f'<div style="font-weight:700">{theme.esc(r.descricao)}</div>'
                                f'<div class="mc-sub">{theme.esc(r.categoria)} · {r.data:%d/%m/%Y}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="mc-valor mc-out">{theme.brl(r.valor)}</div>', unsafe_allow_html=True)

    with aba_cat:
        cats = calc.por_categoria(df)
        if cats.empty:
            theme.vazio("Sem gastos no período.")
        else:
            st.altair_chart(graficos.rosca(cats))
            tabela = cats[["categoria", "total", "pct", "qtd", "media"]].rename(
                columns={"categoria": "Categoria", "total": "Total (R$)", "pct": "% dos gastos", "qtd": "Qtd", "media": "Média (R$)"})
            theme.com_largura(st.dataframe, tabela, hide_index=True, column_config={
                "Total (R$)": st.column_config.NumberColumn(format="%.2f"),
                "% dos gastos": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "Média (R$)": st.column_config.NumberColumn(format="%.2f")})
            theme.secao("Lançamentos de uma categoria")
            escolha_cat = st.selectbox("Categoria", cats["categoria"], key="rel_cat_detalhe", label_visibility="collapsed")
            sub = df[(df["tipo"] == "saida") & (df["categoria"] == escolha_cat)].sort_values(base)
            theme.com_largura(st.dataframe, _tabela_detalhe(sub), hide_index=True)

    with aba_evo:
        serie = calc.serie_mensal(df, base, meses)
        theme.secao("Entradas e gastos por mês")
        st.altair_chart(graficos.entradas_vs_gastos(serie))
        por_mes = calc.categorias_por_mes(df, base)
        if not por_mes.empty:
            theme.secao("Gastos por categoria", "As 6 maiores categorias do período; o restante em “Outras”.")
            st.altair_chart(graficos.categorias_empilhadas(por_mes, meses))
        tabela = serie.assign(mes=serie["mes"].map(calc.rotulo_mes)).rename(
            columns={"mes": "Mês", "entradas": "Entradas", "saidas": "Gastos", "saldo": "Saldo"})
        theme.com_largura(st.dataframe, tabela, hide_index=True)

    with aba_det:
        theme.secao("Gastos por rótulo")
        com_rotulo = df[(df["tipo"] == "saida") & (df["rotulos"] != "")].assign(
            rotulo=lambda d: d["rotulos"].str.split(", ")).explode("rotulo")
        if com_rotulo.empty:
            theme.vazio("Nenhum gasto com rótulo no período. Use rótulos ao lançar.")
        else:
            por_rotulo = (com_rotulo.groupby("rotulo", as_index=False)["valor"].sum()
                          .rename(columns={"valor": "total"}).sort_values("total", ascending=False))
            st.altair_chart(graficos.barras_horizontais(por_rotulo, "rotulo", "total", graficos.PALETA[1]))
        theme.secao("Todos os lançamentos do período")
        theme.com_largura(st.dataframe, _tabela_detalhe(df), hide_index=True)
        st.download_button("Baixar período em CSV", _tabela_detalhe(df).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           file_name=f"denario_{ini}_{fim}.csv", mime="text/csv", key="rel_csv")


def _tabela_detalhe(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Tipo": df["tipo"].map({"saida": "Gasto", "entrada": "Entrada"}),
        "Descrição": df["descricao"],
        "Categoria": df["categoria"],
        "Forma": df["forma"].fillna(""),
        "Valor (R$)": df["valor"],
        "Data": df["data"].dt.strftime("%d/%m/%Y"),
        "Vencimento": df["vencimento"].dt.strftime("%d/%m/%Y"),
        "Pago": df["pago"].map({True: "Sim", False: "Não"}),
        "Rótulos": df["rotulos"],
    })
