"""Gráficos (Altair, já incluído no Streamlit) na paleta do Denário."""
from __future__ import annotations

import altair as alt
import pandas as pd

from core import calc

PALETA = ["#14284F", "#2F6FDE", "#0F9D63", "#E39B12", "#D6403F", "#7A5BA6", "#2A9D8F", "#9AA5B4"]
COR_ENTRADA, COR_GASTO = "#0F9D63", "#D6403F"


def _base(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(labelColor="#6B7A90", gridColor="#E9EEF5", domain=False)


def rosca(df: pd.DataFrame, categoria: str = "categoria", valor: str = "total", altura: int = 280):
    c = (alt.Chart(df).mark_arc(innerRadius=62, outerRadius=108, stroke="white", strokeWidth=2)
         .encode(theta=alt.Theta(f"{valor}:Q"),
                 color=alt.Color(f"{categoria}:N", scale=alt.Scale(range=PALETA),
                                 legend=alt.Legend(title=None, orient="bottom", columns=2)),
                 tooltip=[alt.Tooltip(f"{categoria}:N", title="Categoria"), alt.Tooltip(f"{valor}:Q", title="R$", format=",.2f")])
         .properties(height=altura))
    return _base(c)


def barras_horizontais(df: pd.DataFrame, rotulo: str, valor: str, cor: str = PALETA[0], altura: int | None = None):
    c = (alt.Chart(df).mark_bar(color=cor, cornerRadiusEnd=5)
         .encode(y=alt.Y(f"{rotulo}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160)),
                 x=alt.X(f"{valor}:Q", title=None, axis=alt.Axis(format=",.0f")),
                 tooltip=[alt.Tooltip(f"{rotulo}:N", title=""), alt.Tooltip(f"{valor}:Q", title="R$", format=",.2f")])
         .properties(height=altura or max(110, 36 * len(df))))
    return _base(c)


def entradas_vs_gastos(serie: pd.DataFrame, altura: int = 260):
    ordem = [calc.rotulo_mes_curto(m) for m in serie["mes"]]
    longo = serie.assign(rotulo=ordem).melt(id_vars=["mes", "rotulo"], value_vars=["entradas", "saidas"],
                                            var_name="tipo", value_name="valor")
    longo["tipo"] = longo["tipo"].map({"entradas": "Entradas", "saidas": "Gastos"})
    c = (alt.Chart(longo).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("rotulo:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=0)), xOffset=alt.XOffset("tipo:N"),
                 y=alt.Y("valor:Q", title=None, axis=alt.Axis(format=",.0f")),
                 color=alt.Color("tipo:N", scale=alt.Scale(domain=["Entradas", "Gastos"], range=[COR_ENTRADA, COR_GASTO]),
                                 legend=alt.Legend(title=None, orient="bottom")),
                 tooltip=[alt.Tooltip("rotulo:N", title="Mês"), alt.Tooltip("tipo:N", title=""),
                          alt.Tooltip("valor:Q", title="R$", format=",.2f")])
         .properties(height=altura))
    return _base(c)


def categorias_empilhadas(df: pd.DataFrame, meses: list[str], altura: int = 280):
    ordem = [calc.rotulo_mes_curto(m) for m in meses]
    d = df.assign(rotulo=df["mes"].map(calc.rotulo_mes_curto))
    c = (alt.Chart(d).mark_bar()
         .encode(x=alt.X("rotulo:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=0)),
                 y=alt.Y("total:Q", title=None, axis=alt.Axis(format=",.0f")),
                 color=alt.Color("categoria:N", scale=alt.Scale(range=PALETA),
                                 legend=alt.Legend(title=None, orient="bottom", columns=3)),
                 tooltip=[alt.Tooltip("rotulo:N", title="Mês"), alt.Tooltip("categoria:N", title="Categoria"),
                          alt.Tooltip("total:Q", title="R$", format=",.2f")])
         .properties(height=altura))
    return _base(c)
