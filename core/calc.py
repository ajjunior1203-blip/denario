"""Regras de negócio: datas, cartão, parcelas, orçamentos e relatórios."""
from __future__ import annotations

import calendar
import uuid
from datetime import date

import pandas as pd

from . import repo

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]


# -------------------------------------------------------------------- meses
def mes_atual() -> str:
    return date.today().strftime("%Y-%m")


def mes_add(mes: str, n: int) -> str:
    y, m = int(mes[:4]), int(mes[5:7])
    idx = y * 12 + (m - 1) + n
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def rotulo_mes(mes: str) -> str:
    return f"{MESES[int(mes[5:7]) - 1]} {mes[:4]}"


def rotulo_mes_curto(mes: str) -> str:
    return f"{MESES[int(mes[5:7]) - 1][:3]}/{mes[2:4]}"


def rotulo_dia(d) -> str:
    """SEXTA-FEIRA, 06 DE NOV"""
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day:02d} de {MESES[d.month - 1][:3]}".upper()


def intervalo_meses(ini: str, fim: str) -> list[str]:
    out, m = [], ini
    while m <= fim:
        out.append(m)
        m = mes_add(m, 1)
    return out


def add_months(d: date, n: int, dia: int | None = None) -> date:
    mes = mes_add(d.strftime("%Y-%m"), n)
    y, m = int(mes[:4]), int(mes[5:7])
    return date(y, m, min(dia or d.day, calendar.monthrange(y, m)[1]))


# ------------------------------------------------------------------- cartão
def calcular_vencimento(data: date, forma: dict | None) -> date:
    """Vencimento da fatura para compras no crédito; nas demais formas, a própria data."""
    if not forma or forma.get("tipo") != "credito" or not forma.get("dia_vencimento"):
        return data
    venc, fech = int(forma["dia_vencimento"]), forma.get("dia_fechamento")
    avanco = 0
    if fech:
        fech = int(fech)
        if data.day >= fech:          # compra após o fechamento cai na fatura seguinte
            avanco += 1
        if venc <= fech:              # vencimento acontece no mês seguinte ao fechamento
            avanco += 1
    elif data.day > venc:             # sem fechamento cadastrado: usa o vencimento como referência
        avanco += 1
    return add_months(data, avanco, dia=venc)


def dividir_valor(total: float, n: int) -> list[float]:
    """Divide em n parcelas em centavos; a última absorve a diferença."""
    centavos = round(total * 100)
    base = centavos // n
    partes = [base] * n
    partes[-1] += centavos - base * n
    return [p / 100 for p in partes]


def gerar_itens(*, tipo: str, descricao: str, valor: float, data: date, categoria_id: int, forma: dict | None,
                natureza: str, pago: bool, parcelas: int = 1, valor_e_total: bool = False) -> list[dict]:
    """Monta os lançamentos (um ou vários, se parcelado) prontos para gravar."""
    parcelas = max(1, int(parcelas))
    primeiro = calcular_vencimento(data, forma)
    base = {"tipo": tipo, "data": data, "categoria_id": categoria_id,
            "forma_id": forma["id"] if forma else None, "natureza": natureza}
    if parcelas == 1:
        return [{**base, "descricao": descricao, "valor": valor, "vencimento": primeiro, "pago": pago,
                 "parcela_num": None, "parcela_total": None, "grupo_parcelas": None}]
    valores = dividir_valor(valor, parcelas) if valor_e_total else [round(valor, 2)] * parcelas
    grupo = uuid.uuid4().hex
    dia = int(forma["dia_vencimento"]) if forma and forma.get("tipo") == "credito" and forma.get("dia_vencimento") \
        else data.day
    return [{**base, "descricao": f"{descricao} - Parcela {i + 1}/{parcelas}", "valor": valores[i],
             "vencimento": add_months(primeiro, i, dia=dia), "pago": pago if i == 0 else False,
             "parcela_num": i + 1, "parcela_total": parcelas, "grupo_parcelas": grupo}
            for i in range(parcelas)]


# --------------------------------------------------------------- orçamentos
def _soma(serie) -> float:
    return round(float(serie.sum()), 2)


def resumo_mes(uid: int, mes: str, df: pd.DataFrame | None = None) -> dict:
    df = repo.listar_lancamentos(uid, mes, mes) if df is None else df
    ent, sai = df[df["tipo"] == "entrada"], df[df["tipo"] == "saida"]
    return {
        "entradas": _soma(ent["valor"]),
        "saidas": _soma(sai["valor"]),
        "saldo": round(_soma(ent["valor"]) - _soma(sai["valor"]), 2),
        "saidas_pagas": _soma(sai.loc[sai["pago"], "valor"]),
        "a_pagar": _soma(sai.loc[~sai["pago"], "valor"]),
        "a_receber": _soma(ent.loc[~ent["pago"], "valor"]),
    }


def _nomes_categorias(uid: int) -> dict[int, dict]:
    return {c["id"]: c for c in repo.listar(uid, "categorias")}


def orcamento_fixo(uid: int, mes: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = repo.listar_lancamentos(uid, mes, mes) if df is None else df
    _, orc = repo.obter_orcamento(uid, "orcamento_fixo", mes)
    cats = _nomes_categorias(uid)
    sai = df[df["tipo"] == "saida"]
    linhas = []
    for cid, orcado in orc.items():
        if cid not in cats:
            continue
        do_cat = sai[sai["categoria_id"] == cid]
        lancado = _soma(do_cat["valor"])
        linhas.append({"categoria_id": cid, "categoria": cats[cid]["nome"], "orcado": round(orcado, 2),
                       "lancado": lancado, "pago": _soma(do_cat.loc[do_cat["pago"], "valor"]),
                       "desvio": round(orcado - lancado, 2)})
    linhas.sort(key=lambda r: -r["orcado"])
    return pd.DataFrame(linhas, columns=["categoria_id", "categoria", "orcado", "lancado", "pago", "desvio"])


def orcamento_volatil(uid: int, mes: str, df: pd.DataFrame | None = None) -> dict:
    """Sobra = entradas fixas − orçamento fixo, distribuída pelos percentuais configurados."""
    df = repo.listar_lancamentos(uid, mes, mes) if df is None else df
    fixo = orcamento_fixo(uid, mes, df)
    _, pcts = repo.obter_orcamento(uid, "orcamento_volatil", mes)
    cats = _nomes_categorias(uid)
    ent_fixas = _soma(df.loc[(df["tipo"] == "entrada") & (df["natureza"] == "fixa"), "valor"])
    fixos = round(float(fixo["orcado"].sum()), 2)
    base = round(ent_fixas - fixos, 2)
    disponivel = max(base, 0.0)
    sai = df[df["tipo"] == "saida"]
    linhas = []
    for cid, pct in pcts.items():
        if cid not in cats:
            continue
        orcado = round(disponivel * pct / 100, 2)
        gasto = _soma(sai.loc[sai["categoria_id"] == cid, "valor"])
        linhas.append({"categoria_id": cid, "categoria": cats[cid]["nome"], "percentual": pct, "orcado": orcado,
                       "gasto": gasto, "desvio": round(orcado - gasto, 2)})
    linhas.sort(key=lambda r: -r["percentual"])
    com = set(pcts) | set(fixo["categoria_id"])
    fora = sai[~sai["categoria_id"].isin(com)]
    sem = (fora.groupby("categoria", as_index=False)["valor"].sum().rename(columns={"valor": "gasto"})
           .sort_values("gasto", ascending=False)
           if not fora.empty else pd.DataFrame(columns=["categoria", "gasto"]))
    return {"entradas_fixas": ent_fixas, "fixos_orcados": fixos, "base": base,
            "pct_alocado": round(sum(pcts.values()), 2),
            "linhas": pd.DataFrame(linhas, columns=["categoria_id", "categoria", "percentual", "orcado", "gasto", "desvio"]),
            "sem_orcamento": sem}


# --------------------------------------------------------------- relatórios
def coluna_mes(df: pd.DataFrame, base: str) -> pd.Series:
    return df[base].dt.strftime("%Y-%m")


def por_categoria(df: pd.DataFrame, tipo: str = "saida") -> pd.DataFrame:
    sub = df[df["tipo"] == tipo]
    if sub.empty:
        return pd.DataFrame(columns=["categoria", "total", "qtd", "pct", "media"])
    g = sub.groupby("categoria", as_index=False).agg(total=("valor", "sum"), qtd=("valor", "size"), media=("valor", "mean"))
    g["total"] = g["total"].round(2)
    g["media"] = g["media"].round(2)
    g["pct"] = (g["total"] / g["total"].sum() * 100).round(1)
    return g.sort_values("total", ascending=False).reset_index(drop=True)


def por_forma(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["tipo"] == "saida"].copy()
    if sub.empty:
        return pd.DataFrame(columns=["forma", "total"])
    sub["forma"] = sub["forma"].fillna("Sem forma")
    return (sub.groupby("forma", as_index=False)["valor"].sum().rename(columns={"valor": "total"})
            .sort_values("total", ascending=False).reset_index(drop=True))


def serie_mensal(df: pd.DataFrame, base: str, meses: list[str]) -> pd.DataFrame:
    """Entradas, gastos e saldo por mês, incluindo meses sem movimento."""
    if df.empty:
        agg = pd.DataFrame(index=pd.Index(meses, name="mes"), columns=["entrada", "saida"], dtype=float)
    else:
        agg = df.assign(mes=coluna_mes(df, base)).pivot_table(index="mes", columns="tipo", values="valor", aggfunc="sum")
    for c in ("entrada", "saida"):
        if c not in agg.columns:
            agg[c] = 0.0
    agg = agg.reindex(meses).fillna(0.0).round(2)
    agg["saldo"] = (agg["entrada"] - agg["saida"]).round(2)
    return agg.reset_index().rename(columns={"index": "mes", "entrada": "entradas", "saida": "saidas"})


def categorias_por_mes(df: pd.DataFrame, base: str, top: int = 6) -> pd.DataFrame:
    """Gastos por mês e categoria; categorias fora do top viram 'Outras'."""
    sai = df[df["tipo"] == "saida"]
    if sai.empty:
        return pd.DataFrame(columns=["mes", "categoria", "total"])
    principais = sai.groupby("categoria")["valor"].sum().nlargest(top).index
    tmp = sai.assign(mes=coluna_mes(sai, base), categoria=sai["categoria"].where(sai["categoria"].isin(principais), "Outras"))
    return tmp.groupby(["mes", "categoria"], as_index=False)["valor"].sum().rename(columns={"valor": "total"})
