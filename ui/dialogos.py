"""Janelas (diálogos) de criação e edição."""
from __future__ import annotations

from datetime import date

import streamlit as st

from core import calc, repo
from ui import theme

TIPO_FORMA = {"debito": "Débito", "credito": "Crédito", "pix": "Pix", "boleto": "Boleto",
              "dinheiro": "Dinheiro", "outro": "Outro"}
TIPO_CATEGORIA = {"saida": "Gasto", "entrada": "Entrada"}


def _nonce() -> int:
    return st.session_state.get("dlg_n", 0)


def _com_atual(opcoes: list[dict], atual_id: int | None, uid: int, tabela: str) -> list[dict]:
    """Inclui a opção atual mesmo que esteja inativa, para não perder o valor ao editar."""
    if atual_id and atual_id not in [o["id"] for o in opcoes]:
        extra = repo.obter(uid, tabela, atual_id)
        if extra:
            return opcoes + [extra]
    return opcoes


# ------------------------------------------------------------------ lançamento
def _form_lancamento(uid: int, existente: dict | None) -> None:
    n = _nonce()

    def k(nome: str) -> str:
        return f"dlg_{nome}_{existente['id'] if existente else 'novo'}_{n}"

    editando = existente is not None
    if editando:
        tipo = existente["tipo"]
        st.caption("Gasto" if tipo == "saida" else "Entrada")
    else:
        escolha = st.segmented_control("Tipo", ["Gasto", "Entrada"], default="Gasto", key=k("tipo"),
                                       label_visibility="collapsed") or "Gasto"
        tipo = "saida" if escolha == "Gasto" else "entrada"

    valor = st.number_input("Valor (R$)", min_value=0.0, value=float(existente["valor"]) if editando else None, step=1.0,
                            format="%.2f", placeholder="0,00", key=k("valor"))
    descricao = st.text_input("Descrição", value=existente["descricao"] if editando else "",
                              placeholder="Ex.: Almoço, Spotify, Salário", key=k("desc"))

    categorias = _com_atual(repo.listar(uid, "categorias", so_ativos=True, tipo=tipo),
                            existente["categoria_id"] if editando else None, uid, "categorias")
    if not categorias:
        st.error("Cadastre uma categoria no Perfil antes de lançar.")
        return
    ids_cat = [c["id"] for c in categorias]
    nomes_cat = {c["id"]: c["nome"] for c in categorias}
    categoria_id = st.selectbox("Categoria", ids_cat, format_func=nomes_cat.get, key=k(f"cat_{tipo}"),
                                index=ids_cat.index(existente["categoria_id"]) if editando and existente["categoria_id"] in ids_cat else 0)

    forma = None
    if tipo == "saida":
        formas = _com_atual(repo.listar(uid, "formas_pagamento", so_ativos=True),
                            existente.get("forma_id") if editando else None, uid, "formas_pagamento")
        if not formas:
            st.error("Cadastre uma forma de pagamento no Perfil antes de lançar.")
            return
        ids_forma = [f["id"] for f in formas]
        por_forma = {f["id"]: f for f in formas}
        forma_id = st.selectbox("Forma de pagamento", ids_forma, format_func=lambda i: por_forma[i]["nome"], key=k("forma"),
                                index=ids_forma.index(existente["forma_id"]) if editando and existente.get("forma_id") in ids_forma else 0)
        forma = por_forma[forma_id]

    data_ref = date.fromisoformat(existente["data"]) if editando else date.today()
    data = st.date_input("Data", value=data_ref, format="DD/MM/YYYY", key=k("data"))
    vencimento = None
    if editando and tipo == "saida":
        vencimento = st.date_input("Vencimento", value=date.fromisoformat(existente["vencimento"]), format="DD/MM/YYYY",
                                   key=k("venc"))

    fixa = st.toggle("Conta fixa (se repete todo mês)" if tipo == "saida" else "Entrada fixa (ex.: salário, aluguel recebido)",
                     value=editando and existente["natureza"] == "fixa", key=k("fixa"))

    parcelas, valor_e_total = 1, False
    if tipo == "saida" and not editando:
        parcelas = int(st.number_input("Parcelas", min_value=1, max_value=60, value=1, step=1, key=k("parc")))
        if parcelas > 1:
            valor_e_total = st.radio("O valor informado é", ["De cada parcela", "Do total"], horizontal=True,
                                     key=k("modo")) == "Do total"

    rotulos = repo.listar(uid, "rotulos", so_ativos=True)
    rotulos_sel: list[int] = []
    if rotulos or (editando and existente["rotulos_ids"]):
        todos = _com_atual_rotulos(uid, rotulos, existente["rotulos_ids"] if editando else [])
        nomes = {r["id"]: r["nome"] for r in todos}
        rotulos_sel = st.multiselect("Rótulos", list(nomes), format_func=nomes.get,
                                     default=existente["rotulos_ids"] if editando else [], key=k("rot"))

    if editando:
        padrao_pago = bool(existente["pago"])
    else:
        padrao_pago = True if tipo == "entrada" else forma["tipo"] not in ("credito", "boleto")
    pago = st.toggle("Já recebi" if tipo == "entrada" else "Já paguei", value=padrao_pago,
                     key=k(f"pago_{forma['id'] if forma else 0}"))

    if tipo == "saida" and not editando and valor:
        venc = calc.calcular_vencimento(data, forma)
        if parcelas > 1:
            dia = forma["dia_vencimento"] if forma["tipo"] == "credito" and forma.get("dia_vencimento") else data.day
            ultimo = calc.add_months(venc, parcelas - 1, dia=dia)
            cada = calc.dividir_valor(valor, parcelas)[0] if valor_e_total else valor
            st.caption(f"{parcelas}× de {theme.brl(cada)} · de {venc:%m/%Y} até {ultimo:%m/%Y}")
        elif venc != data:
            st.caption(f"Entra na fatura que vence em {venc:%d/%m/%Y}.")

    if st.button("Salvar", type="primary", key=k("salvar")):
        if not valor or valor <= 0:
            st.error("Informe um valor maior que zero.")
            return
        texto = (descricao or "").strip() or nomes_cat[categoria_id]
        try:
            if editando:
                repo.atualizar_lancamento(uid, existente["id"], descricao=texto, valor=float(valor), data=data,
                                          vencimento=vencimento or data, categoria_id=categoria_id,
                                          forma_id=forma["id"] if forma else None,
                                          natureza="fixa" if fixa else "eventual", pago=pago)
                repo.definir_rotulos(uid, existente["id"], rotulos_sel)
                theme.aviso("Lançamento atualizado.")
            else:
                itens = calc.gerar_itens(tipo=tipo, descricao=texto, valor=float(valor), data=data, categoria_id=categoria_id,
                                         forma=forma, natureza="fixa" if fixa else "eventual", pago=pago,
                                         parcelas=parcelas, valor_e_total=valor_e_total)
                repo.inserir_lancamentos(uid, itens, rotulos_sel)
                theme.aviso(f"{'Entrada' if tipo == 'entrada' else 'Gasto'} de {theme.brl(valor)} lançado"
                            + (f" em {parcelas} parcelas." if parcelas > 1 else "."))
        except ValueError as e:
            st.error(str(e))
            return
        st.rerun()

    if editando:
        if st.session_state.get(k("confirma")):
            st.warning("Excluir este lançamento? Não dá para desfazer.")
            if st.button("Sim, excluir", key=k("excluir_sim")):
                repo.excluir_lancamentos(uid, [existente["id"]])
                theme.aviso("Lançamento excluído.", "info")
                st.rerun()
        elif st.button("Excluir lançamento", key=k("excluir")):
            st.session_state[k("confirma")] = True
            st.rerun(scope="fragment")


def _com_atual_rotulos(uid: int, ativos: list[dict], selecionados: list[int]) -> list[dict]:
    faltando = [i for i in selecionados if i not in [r["id"] for r in ativos]]
    return ativos + [r for r in (repo.obter(uid, "rotulos", i) for i in faltando) if r]


@st.dialog("Novo lançamento")
def dialogo_novo(uid: int) -> None:
    _form_lancamento(uid, None)


@st.dialog("Editar lançamento")
def dialogo_editar(uid: int, lancamento_id: int) -> None:
    existente = repo.obter_lancamento(uid, lancamento_id)
    if existente is None:
        st.error("Lançamento não encontrado.")
        return
    _form_lancamento(uid, existente)


# ------------------------------------------------------------------ orçamentos
def _form_orcamento(uid: int, tabela: str, mes: str, categoria_id: int | None) -> None:
    fixo = tabela == "orcamento_fixo"
    n = _nonce()
    _, atual = repo.obter_orcamento(uid, tabela, mes)
    editando = categoria_id is not None
    cats = repo.listar(uid, "categorias", so_ativos=True, tipo="saida")
    if editando:
        cats = [c for c in repo.listar(uid, "categorias", tipo="saida") if c["id"] == categoria_id]
    else:
        cats = [c for c in cats if c["id"] not in atual]
    if not cats:
        st.info("Todas as categorias de gasto já estão neste orçamento.")
        return
    nomes = {c["id"]: c["nome"] for c in cats}
    cid = st.selectbox("Categoria", list(nomes), format_func=nomes.get, disabled=editando, key=f"orc_cat_{tabela}_{n}")
    if fixo:
        valor = st.number_input("Valor orçado por mês (R$)", min_value=0.0, step=10.0, format="%.2f",
                                value=float(atual.get(cid, 0.0)) or None, placeholder="0,00", key=f"orc_val_{tabela}_{n}")
        limite_info = None
    else:
        outros = round(sum(v for c, v in atual.items() if c != cid), 2)
        livre = round(100 - outros, 2)
        valor = st.number_input("Percentual da sobra (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
                                value=float(atual.get(cid, 0.0)) or None, placeholder="0", key=f"orc_val_{tabela}_{n}")
        limite_info = livre
        st.caption(f"Disponível: {livre:g}% (os outros orçamentos somam {outros:g}%).")
    st.caption(f"Vale a partir de {calc.rotulo_mes(mes)} e continua nos meses seguintes. Meses anteriores não mudam.")
    if st.button("Salvar", type="primary", key=f"orc_salvar_{tabela}_{n}"):
        if not valor or valor <= 0:
            st.error("Informe um valor maior que zero.")
            return
        if limite_info is not None and valor > limite_info + 0.0001:
            st.error(f"O total passaria de 100%. Você pode usar até {limite_info:g}%.")
            return
        repo.definir_item_orcamento(uid, tabela, mes, cid, float(valor))
        theme.aviso("Orçamento salvo.")
        st.rerun()


@st.dialog("Orçamento fixo")
def dialogo_orc_fixo(uid: int, mes: str, categoria_id: int | None = None) -> None:
    _form_orcamento(uid, "orcamento_fixo", mes, categoria_id)


@st.dialog("Orçamento volátil")
def dialogo_orc_volatil(uid: int, mes: str, categoria_id: int | None = None) -> None:
    _form_orcamento(uid, "orcamento_volatil", mes, categoria_id)


# -------------------------------------------------------------------- cadastros
def _salvar_cadastro(uid: int, tabela: str, id_: int | None, **campos) -> None:
    try:
        if id_ is None:
            repo.inserir(uid, tabela, **campos)
        else:
            repo.atualizar(uid, tabela, id_, **campos)
    except ValueError as e:
        st.error(str(e))
        return
    theme.aviso("Salvo.")
    st.rerun()


@st.dialog("Categoria")
def dialogo_categoria(uid: int, id_: int | None = None, tipo: str = "saida") -> None:
    n, atual = _nonce(), (repo.obter(uid, "categorias", id_) if id_ else None)
    nome = st.text_input("Nome", value=atual["nome"] if atual else "", key=f"cat_nome_{n}")
    if atual:
        tipo = atual["tipo"]
        st.caption("Categoria de gasto" if tipo == "saida" else "Categoria de entrada")
    else:
        tipo = "saida" if st.radio("Tipo", list(TIPO_CATEGORIA), format_func=TIPO_CATEGORIA.get, horizontal=True,
                                    index=0 if tipo == "saida" else 1, key=f"cat_tipo_{n}") == "saida" else "entrada"
    ativa = st.toggle("Ativa", value=bool(atual["ativo"]) if atual else True, key=f"cat_ativa_{n}",
                      help="Desative para esconder dos lançamentos novos sem perder o histórico.")
    if st.button("Salvar", type="primary", key=f"cat_salvar_{n}"):
        _salvar_cadastro(uid, "categorias", id_, nome=nome, tipo=tipo, ativo=ativa)


@st.dialog("Forma de pagamento")
def dialogo_forma(uid: int, id_: int | None = None) -> None:
    n, atual = _nonce(), (repo.obter(uid, "formas_pagamento", id_) if id_ else None)
    nome = st.text_input("Nome", value=atual["nome"] if atual else "", placeholder="Ex.: Cartão Nubank", key=f"fp_nome_{n}")
    tipos = list(TIPO_FORMA)
    tipo = st.selectbox("Tipo", tipos, format_func=TIPO_FORMA.get, index=tipos.index(atual["tipo"]) if atual else 0,
                        key=f"fp_tipo_{n}")
    fech = venc = 0
    if tipo == "credito":
        st.caption("Informe o dia de vencimento da fatura. Com o dia de fechamento, compras feitas a partir dele "
                   "caem na fatura seguinte.")
        fech = st.number_input("Dia de fechamento (0 = não informar)", min_value=0, max_value=31, step=1,
                               value=int(atual["dia_fechamento"] or 0) if atual else 0, key=f"fp_fech_{n}")
        venc = st.number_input("Dia de vencimento (0 = não informar)", min_value=0, max_value=31, step=1,
                               value=int(atual["dia_vencimento"] or 0) if atual else 0, key=f"fp_venc_{n}")
    ativa = st.toggle("Ativa", value=bool(atual["ativo"]) if atual else True, key=f"fp_ativa_{n}")
    if st.button("Salvar", type="primary", key=f"fp_salvar_{n}"):
        _salvar_cadastro(uid, "formas_pagamento", id_, nome=nome, tipo=tipo, ativo=ativa,
                         dia_fechamento=fech or None, dia_vencimento=venc or None)


@st.dialog("Rótulo")
def dialogo_rotulo(uid: int, id_: int | None = None) -> None:
    n, atual = _nonce(), (repo.obter(uid, "rotulos", id_) if id_ else None)
    nome = st.text_input("Nome", value=atual["nome"] if atual else "", placeholder="Ex.: Viagem", key=f"rot_nome_{n}")
    ativa = st.toggle("Ativo", value=bool(atual["ativo"]) if atual else True, key=f"rot_ativa_{n}")
    if st.button("Salvar", type="primary", key=f"rot_salvar_{n}"):
        _salvar_cadastro(uid, "rotulos", id_, nome=nome, ativo=ativa)
