import pandas as pd
import re
import numpy as np
from config import COLS_EDO_CTA
from utils import get_encoding

def preprocess_stder(uploaded_file)->pd.DataFrame:
    # para Santander, se recibe como .csv
    encoding = get_encoding(uploaded_file)
    uploaded_file.seek(0)  # reiniciar el puntero del archivo
    df = pd.read_csv(uploaded_file, encoding=encoding, sep=",")
    # Importe y Saldo son columnas que contienen valores numéricos
    # convertimos las columnas "Importe" y "Saldo" a tipo numérico rellenando los nulos con 0
    df["Importe"] = pd.to_numeric(df["Importe"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("'",""), errors="coerce").fillna(0)
    df["Saldo"] = pd.to_numeric(df["Saldo"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("'",""), errors="coerce").fillna(0)
    # "Referencia", "Concepto" y "Descripcion" a string
    df["Referencia"] = df["Referencia"].astype(str).str.replace("'", "", regex=False).fillna("")
    df["Concepto"] = df["Concepto"].astype(str).str.replace("'", "", regex=False).fillna("")
    df["Descripcion"] = df["Descripcion"].astype(str).str.replace("'", "", regex=False).fillna("")

    return df

def asign_cve_stder(row):
    cve = np.nan
    # Si "Referencia" no es vacío y no es NaN o espacios, asignamos "Referencia" a cve
    ref = row["Referencia"].strip()
    desc = row["Descripcion"].strip()
    concep = row["Concepto"].strip()
    # Si "Referencia" no es vacío y no es NaN o espacios o puros ceros, asignamos "Referencia" a cve
    if ref and ref.replace(" ", "").replace("0", "") != "":
        # referencia a string y eliminamos comillas simples
        cve = ref        
        # Si "Descripcion" contiene "IVA", asignamos "IVA"
        if "IVA" in desc:
            cve+= "_IVA"
        # Si "Descripcion" contiene "COM." o "COMISION", asignamos "COM"
        elif "COM " in desc or "COMISION" in desc:
            cve+= "_COM"
    # Si "Referencia" es vacío, buscamos en "Concepto" alguna coincidencia con "CRE_[dígitos]"
    else:
        match = re.search(r"(CRE_\d+)", concep)
        # print(concep)
        if match:
            # print('desc:',desc)
            cve = match.group(1)
            # Buscamos en "Descripcion" alguna coincidencia con "CAP" o "INT"
            if "CAP" in desc:
                cve += "_CAP"
            elif "INT" in desc:
                cve += "_INT"
        # Si no encontramos coincidencias, asignamos las palabras de la descripcion unidas con "_" más la fecha
        else:
            cve = "_".join(desc.split()) + "_" + row["Fecha"].replace("'", "")
    return cve

def format_stder(edo_cta:pd.DataFrame, cta:str)->pd.DataFrame:
    edo_cta = edo_cta.rename(columns={
        "Fecha": "FECHA",
        "Descripcion": "DESCRIPCIÓN",
        "Saldo": "SALDO",
        "Referencia": "REFERENCIA",
        "Concepto": "CONCEPTO",
        "cve": "CLAVE"
    })
    # corregimos el formato de la fecha, que viene como "'ddmmyyyy'"
    # y lo convertimos a "dd-mm-yyyy"
    edo_cta["FECHA"] = edo_cta["FECHA"].astype(str).str.replace("'", "", regex=False).str.strip()
    # edo_cta["FECHA"] = edo_cta["FECHA"].str.replace(r'(\d{2})(\d{2})(\d{4})', r'\1-\2-\3')
    # print(edo_cta["FECHA"].sample(10))
    # print(edo_cta["FECHA"].apply(lambda x: repr(x)).sample(10))
    # convertimos la columna "Fecha" a tipo datetime usando también la columna "Hora"
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"]+" " + edo_cta["Hora"], format="%d%m%Y %H:%M", errors="raise")

    # CARGO es el importe si "Cargo/Abono" es "-", si no, es 0
    edo_cta["CARGO"] = np.where(edo_cta["Cargo/Abono"] == "-", edo_cta["Importe"], 0)
    # ABONO es el importe si "Cargo/Abono" es "+", si no, es 0
    edo_cta["ABONO"] = np.where(edo_cta["Cargo/Abono"] == "+", edo_cta["Importe"], 0)

    # agregamos una columna de "BANCO" con el nombre del banco
    edo_cta["BANCO"] = 'Santander'
    edo_cta["CUENTA"] = cta
    # las columnas "REFERENCIA BANCARIA" se llenan con "#"
    edo_cta["REFERENCIA BANCARIA"] = "#"
    # eliminamos las columnas que no necesitamos
    edo_cta = edo_cta[COLS_EDO_CTA]

    return edo_cta