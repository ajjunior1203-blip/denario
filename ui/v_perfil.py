"""Aba Perfil: conta, cor do app, categorias, formas de pagamento, rótulos e segurança."""
from __future__ import annotations

import streamlit as st

from core import auth, repo
from ui import dialogos, theme

TIPO_FORMA = dialogos.TIPO_FORMA


def _excluir(uid: int, tabela: str, id_: int) -> None:
    try:
        repo.excluir(uid, tabela, id_)
        theme.aviso("Excluído.", "info")
    except ValueError as e:
        theme.aviso(f"{e} Toque em editar e desative.", "erro")


def _linha(uid: int, tabela: str, item: dict, detalhe: str | None, chave: str) -> bool:
    """Linha de cadastro com nome, editar e excluir. Devolve True se tocou em editar."""
    with st.container(key=f"fila_item_{chave}_{item['id']}"):
        c1, c2, c3 = st.columns([10, 1, 1])
        sub = " · ".join(x for x in (detalhe, None if item["ativo"] else "inativa") if x)
        c1.markdown(f'<div style="font-weight:700;{"" if item["ativo"] else "color:#6B7A90"}">{theme.esc(item["nome"])}</div>'
                    + (f'<div class="mc-sub">{theme.esc(sub)}</div>' if sub else ""), unsafe_allow_html=True)
        with c2:
            editar = st.button(":material/edit:", key=f"ic_ed_{chave}_{item['id']}", type="tertiary", help="Editar")
        with c3:
            st.button(":material/delete:", key=f"ic_del_{chave}_{item['id']}", type="tertiary", help="Excluir",
                      on_click=_excluir, args=(uid, tabela, item["id"]))
    return editar


def pagina_perfil(usuario: dict, sair) -> None:
    uid = usuario["id"]
    theme.mostrar_aviso()
    abrir = None

    theme.secao("Meu perfil")
    with st.container(key="cartao_perfil"):
        st.markdown(f'<div class="mc-perfil"><div class="mc-avatar">{theme.esc(theme.inicial(usuario["nome"]))}</div>'
                    f'<div><b>{theme.esc(usuario["nome"])}</b><span>{theme.esc(usuario["email"])}</span></div></div>',
                    unsafe_allow_html=True)
        with st.container(key="fila_nome"):
            c1, c2 = st.columns([4, 2])
            novo_nome = c1.text_input("Nome", value=usuario["nome"], key="perfil_nome", label_visibility="collapsed")
            if c2.button("Salvar", type="primary", key="perfil_salvar"):
                try:
                    auth.atualizar(uid, nome=novo_nome)
                    theme.aviso("Nome atualizado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        st.markdown('<div style="font-weight:700;margin-top:.4rem">Cor do app</div>'
                    '<div class="mc-nota">Vale para todos os aparelhos em que você entrar.</div>', unsafe_allow_html=True)
        with st.container(key="fila_temas"):
            colunas = st.columns(3)
            for col, (chave, paleta) in zip(colunas, theme.PALETAS.items()):
                with col:
                    selecionado = usuario["cor_tema"] == chave
                    if st.button(paleta["nome"], key=f"tema_{chave}{'_sel' if selecionado else ''}") and not selecionado:
                        auth.atualizar(uid, cor_tema=chave)
                        st.rerun()

    # ---- categorias
    theme.secao("Categorias")
    tipo = theme.segmentado("Tipo de categoria", ["saida", "entrada"], "perfil_cat_tipo",
                            format_func=lambda t: "Gastos" if t == "saida" else "Entradas")
    categorias = repo.listar(uid, "categorias", tipo=tipo)
    if categorias:
        with st.container(key="lista_cadastro_cat"):
            for c in categorias:
                if _linha(uid, "categorias", c, None, "cat"):
                    abrir = (dialogos.dialogo_categoria, (uid, c["id"]))
    if st.button("Nova categoria", key="perfil_nova_cat", icon=":material/add:"):
        abrir = (dialogos.dialogo_categoria, (uid, None, tipo))

    # ---- formas de pagamento
    theme.secao("Formas de pagamento")
    formas = repo.listar(uid, "formas_pagamento")
    if formas:
        with st.container(key="lista_cadastro_forma"):
            for f in formas:
                detalhe = TIPO_FORMA[f["tipo"]]
                if f["tipo"] == "credito" and f["dia_vencimento"]:
                    detalhe += f" · vence dia {f['dia_vencimento']}" + (f" · fecha dia {f['dia_fechamento']}" if f["dia_fechamento"] else "")
                if _linha(uid, "formas_pagamento", f, detalhe, "forma"):
                    abrir = (dialogos.dialogo_forma, (uid, f["id"]))
    if st.button("Nova forma de pagamento", key="perfil_nova_forma", icon=":material/add:"):
        abrir = (dialogos.dialogo_forma, (uid, None))

    # ---- rótulos
    theme.secao("Rótulos", "Etiquetas livres (Viagem, Trabalho…) para cruzar gastos nos relatórios.")
    rotulos = repo.listar(uid, "rotulos")
    if rotulos:
        with st.container(key="lista_cadastro_rotulo"):
            for r in rotulos:
                if _linha(uid, "rotulos", r, None, "rot"):
                    abrir = (dialogos.dialogo_rotulo, (uid, r["id"]))
    if st.button("Novo rótulo", key="perfil_novo_rotulo", icon=":material/add:"):
        abrir = (dialogos.dialogo_rotulo, (uid, None))

    # ---- dados e segurança
    theme.secao("Meus dados")
    todos = repo.listar_lancamentos(uid)
    if not todos.empty:
        csv = todos.assign(data=todos["data"].dt.strftime("%d/%m/%Y"), vencimento=todos["vencimento"].dt.strftime("%d/%m/%Y"))[
            ["tipo", "descricao", "valor", "data", "vencimento", "categoria", "forma", "natureza", "pago", "rotulos"]]
        st.download_button("Exportar todos os lançamentos (CSV)", csv.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           file_name="denario_lancamentos.csv", mime="text/csv", key="perfil_csv")
    if usuario["tem_senha"]:
        with st.expander("Alterar senha"):
            atual = st.text_input("Senha atual", type="password", key="senha_atual")
            nova = st.text_input("Nova senha", type="password", key="senha_nova", help=f"Mínimo de {auth.SENHA_MINIMA} caracteres.")
            if st.button("Alterar senha", key="senha_salvar"):
                try:
                    auth.alterar_senha(uid, atual, nova)
                    theme.aviso("Senha alterada. Os outros aparelhos precisarão entrar de novo.")
                    sair(manter_aviso=True)
                except ValueError as e:
                    st.error(str(e))
    if st.button("Sair da conta", key="perfil_sair", icon=":material/logout:"):
        sair()

    if abrir:
        st.session_state["dlg_n"] = st.session_state.get("dlg_n", 0) + 1
        funcao, args = abrir
        funcao(*args)
