import streamlit as st
import pandas as pd
from config import CUENTAS
from cves import asign_cve

st.title("Asignador de Claves de Estado de Cuenta")

# Sidebar
bank = st.sidebar.selectbox("Selecciona banco", list(CUENTAS.keys()))
cuentas = CUENTAS[bank]
account = st.sidebar.selectbox("Selecciona cuenta", cuentas)

def load_file(uploaded_file):
    return uploaded_file

uploaded_files = st.file_uploader(
    "Arrastra uno o más archivos de estados de cuenta",
    type=['csv', 'xlsx', 'txt'],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for f in uploaded_files:
        # guarda temporal
        df = asign_cve(f, bank, account)
        dfs.append(df)
    result = pd.concat(dfs, ignore_index=True)
    st.dataframe(result)
    st.download_button(
        "Descargar resultado",
        data=result.to_csv(index=False).encode('utf-8'),
        file_name=f"resultado_{bank}.csv",
        mime='text/csv'
    )