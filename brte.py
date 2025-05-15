import pandas as pd
import re
import numpy as np
from utils import get_encoding

def preprocess_brte(uploaded_file)->pd.DataFrame:
    # para Banorte, se recibe como .csv
    encoding = get_encoding(uploaded_file)
    uploaded_file.seek(0)  # reiniciar el puntero del archivo
    df = pd.read_csv(uploaded_file, encoding=encoding, sep=",", dtype={"REFERENCIA": str})
    # DEPóSITOS, RETIROS y SALDO son columnas que contienen valores numéricos
    # convertimos las columnas "DEPÓSITOS", "RETIROS" y "SALDO" a tipo numérico rellenando los nulos y '-' con 0
    df["DEPÓSITOS"] = pd.to_numeric(df["DEPÓSITOS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    df["RETIROS"] = pd.to_numeric(df["RETIROS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    df["SALDO"] = pd.to_numeric(df["SALDO"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0"), errors="coerce").fillna(0)
    # REFERENCIA, DESCRIPCIÓN, COD. TRANSAC, SUCURSAL, MOVIMIENTO y DESCRIPCIÓN DETALLADA a string
    df["REFERENCIA"] = df["REFERENCIA"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["DESCRIPCIÓN"] = df["DESCRIPCIÓN"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["COD. TRANSAC"] = df["COD. TRANSAC"].fillna("").astype(str).str.replace("'", "", regex=False)
    df["SUCURSAL"] = df["SUCURSAL"].fillna("").astype(str).str.replace("'", "", regex=False)
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

def extract_beneficiario(row):
    # Buscar cuenta
    cuenta_match = re.search(r"CUENTA:\s*(\d+)", row["DESCRIPCIÓN"])
    cuenta = cuenta_match.group(1) if cuenta_match else ""
    
    # Buscar RFC
    # el rfc puede venir como " RFC: [RFC]" o "R.F.C. [RFC]", buscaremos ambos
    rfc_match = re.search(r"RFC:\s*([A-Z0-9]{12,13})|R\.F\.C\.\s*([A-Z0-9]{12,13})", row["DESCRIPCIÓN"])
    if rfc_match:
        rfc = rfc_match.group(1) if rfc_match.group(1) else rfc_match.group(2)
    else:
        rfc = ""
    
    # Formar el texto del beneficiario
    # armamos la columna de beneficiario como "CUENTA: [cuenta] RFC: [RFC]" (si existen)
    beneficiario = ""
    if cuenta:
        beneficiario += f"CUENTA: {cuenta} "
    if rfc:
        beneficiario += f"RFC: {rfc}"
    
    return beneficiario.strip()

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
    edo_cta["REFERENCIA BANCARIA"] = ('Cod. Transacción: ' + edo_cta["COD. TRANSAC"] +' ' + 'Sucursal: ' + edo_cta["SUCURSAL"])
    edo_cta["BENEFICIARIO"] = edo_cta.apply(extract_beneficiario, axis=1)

    edo_cta["BANCO"] = "Banorte"
    edo_cta["CUENTA"] = cta
    
    return edo_cta