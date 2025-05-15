import pandas as pd
import re
import numpy as np
from utils import get_encoding

def preprocess_brte(uploaded_file)->pd.DataFrame:
    # para Banorte, se recibe como .csv
    encoding = get_encoding(uploaded_file)
    uploaded_file.seek(0)  # reiniciar el puntero del archivo
    df = pd.read_csv(uploaded_file, encoding=encoding, sep=",")
    # DEPóSITOS, RETIROS y SALDO son columnas que contienen valores numéricos
    # convertimos las columnas "DEPÓSITOS", "RETIROS" y "SALDO" a tipo numérico rellenando los nulos y '-' con 0
    df["DEPÓSITOS"] = pd.to_numeric(df["DEPÓSITOS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    df["RETIROS"] = pd.to_numeric(df["RETIROS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    df["SALDO"] = pd.to_numeric(df["SALDO"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    # REFERENCIA, DESCRIPCIÓN, COD. TRANSAC, MOVIMIENTO y DESCRIPCIÓN DETALLADA a string
    df["REFERENCIA"] = df["REFERENCIA"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["DESCRIPCIÓN"] = df["DESCRIPCIÓN"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["COD. TRANSAC"] = df["COD. TRANSAC"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["MOVIMIENTO"] = df["MOVIMIENTO"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["DESCRIPCIÓN DETALLADA"] = df["DESCRIPCIÓN DETALLADA"].fillna("").astype(str).str.replace("'", "", regex=False)

    return df

def asign_cve_brte(row):
    cve = row["MOVIMIENTO"].strip()
    desc = row["DESCRIPCIÓN"].strip()
    if 'IVA' in desc:
        cve += "_IVA"
    elif 'COM' in desc:
        cve += "_COM"    
    return cve

def format_brte(edo_cta:pd.DataFrame, cta:str)->pd.DataFrame:
    # formateamos el DataFrame para que tenga las columnas necesarias
    # y renombramos las columnas
    edo_cta = edo_cta.rename(columns={
        "cve": "CLAVE",
        "DEPÓSITOS": "ABONO",
        "RETIROS": "CARGO",
        "DESCRIPCIÓN": "CONCEPTO",
        "DESCRIPCIÓN DETALLADA": "DESCRIPCIÓN",
    })
    # fecha a datetime
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"].astype(str), format="%d/%m/%Y", errors="raise")
    # armamos la referencia bancaria con el código de transacción y la sucursal
    edo_cta["REFERENCIA BANCARIA"] = 'Cód. Transacción: ' + edo_cta["COD. TRANSAC"].str + 'Sucursal: ' + edo_cta["SUCURSAL"].str
    # tratamos de extraer la cuenta y RFC del beneficiario de la descripción
    cuenta = re.search(r"CUENTA:\s*(\d+)", edo_cta["DESCRIPCIÓN"])
    # el rfc puede venir como " RFC: [RFC]" o "R.F.C. [RFC]", buscaremos ambos
    rfc = re.search(r"RFC:\s*([A-Z0-9]{12,13})|R\.F\.C\.\s*([A-Z0-9]{12,13})", edo_cta["DESCRIPCIÓN"])
    # armamos la columna de beneficiario como "CUENTA: [cuenta] RFC: [RFC]" (si existen)
    if cuenta:
        cuenta = cuenta.group(1)
    else:
        cuenta = ""
    if rfc:
        rfc = rfc.group(1) if rfc.group(1) else rfc.group(2)
    else:
        rfc = ""
    edo_cta["BENEFICIARIO"] = ("CUENTA: " + cuenta +" " if cuenta!="" else "") + ("RFC: " + rfc if rfc!="" else "")
    
    return edo_cta