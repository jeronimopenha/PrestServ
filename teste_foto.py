import streamlit as st

from database import listar_pessoas, salvar_foto, buscar_foto
from fotos import converter_para_jpeg

st.title("Teste de fotografias - PrestServ")

pessoas = listar_pessoas()

if not pessoas:
    st.warning("Nenhuma pessoa cadastrada.")
    st.stop()

pessoa_id = st.selectbox(
    "Pessoa",
    options=[p["id"] for p in pessoas],
    format_func=lambda id: next(p["nome"] for p in pessoas if p["id"] == id),
)

arquivo = st.file_uploader("Enviar fotografia", type=["jpg", "jpeg", "png", "webp"])

if arquivo is not None:
    try:
        foto_jpeg = converter_para_jpeg(arquivo)
        st.image(foto_jpeg, caption="Prévia convertida para JPEG")

        if st.button("Salvar fotografia"):
            salvar_foto(pessoa_id, foto_jpeg)
            st.success("Fotografia salva com sucesso!")

    except ValueError as erro:
        st.error(str(erro))

foto_atual = buscar_foto(pessoa_id)

if foto_atual:
    st.subheader("Fotografia armazenada")
    st.image(foto_atual, width=200)
