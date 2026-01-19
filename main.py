import streamlit as st
import pandas as pd
import io
from config import CUENTAS, TYPES_EDO_CTA
from cves import asign_cve
from export import export_to_excel

st.title("Asignador de Claves de Estado de Cuenta")

# Sidebar
bank = st.sidebar.selectbox("Selecciona banco", list(CUENTAS.keys()))
cuentas = CUENTAS[bank]
account = st.sidebar.selectbox("Selecciona cuenta", cuentas)

def load_file(uploaded_file):
    return uploaded_file

uploaded_files = st.file_uploader(
    "Arrastra uno o más archivos de estados de cuenta",
    type=TYPES_EDO_CTA[bank],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for f in uploaded_files:
        # guarda temporal
        df = asign_cve(f, bank, account)
        dfs.append(df)
    result = pd.concat(dfs, ignore_index=True)
    exp_file_name = "claves_"+uploaded_files[0].name.split(".")[0]

    # Guardar Excel en memoria
    output = io.BytesIO()
    export_to_excel(df=result, output_file=output, bank=bank, account=account)
    output.seek(0)  # mover el puntero al inicio del archivo

    st.dataframe(result)
    st.download_button(
        "Descargar",
        data=output,
        file_name=f"{exp_file_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )