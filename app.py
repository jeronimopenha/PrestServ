import streamlit as st
import sqlite3

st.title("Sistema de Atendimento Social")
st.write("Protótipo inicial funcionando!")

conexao = sqlite3.connect(":memory:")
st.success("SQLite funcionando corretamente!")
conexao.close()