import pandas as pd
import re
import numpy as np
from utils import get_encoding

def preprocess_brte(uploaded_file)->pd.DataFrame:
    # para Banorte, se recibe como .csv
    encoding = get_encoding(uploaded_file)
    uploaded_file.seek(0)  # reiniciar el puntero del archivo
    df = pd.read_csv(uploaded_file, encoding=encoding, sep=",",
                     dtype={
                            "REFERENCIA": str,
                            "DESCRIPCIÓN": str,
                            "COD. TRANSAC": str,
                            "SUCURSAL": str,
                            "MOVIMIENTO": str,
                            "DESCRIPCIÓN DETALLADA": str,
                     })
    # DEPóSITOS, RETIROS y SALDO son columnas que contienen valores numéricos
    # convertimos las columnas "DEPÓSITOS", "RETIROS" y "SALDO" a tipo numérico rellenando los nulos y '-' con 0
    df["DEPÓSITOS"] = pd.to_numeric(df["DEPÓSITOS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0").str.replace("$",""), errors="raise").fillna(0)
    df["RETIROS"] = pd.to_numeric(df["RETIROS"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0").str.replace("$",""), errors="raise").fillna(0)
    df["SALDO"] = pd.to_numeric(df["SALDO"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("-", "0").str.replace("$",""), errors="raise").fillna(0)

    return df

def asign_cve_brte(row):
    desc = row["DESCRIPCIÓN"].strip()
    det = row["DESCRIPCIÓN DETALLADA"].strip()
    # buscamos el patrón "CONCEPTO: [palabra clave] [más texto], REFERENCIA: [dígitos]" en la descripción detallada,
    # donde la palabra clave puede ser "TMLG", "NPRO" o "REEM" y la clave son los últimos 6 dígitos de [dígitos]
    match = re.search(r"CONCEPTO:\s*(TMLG|NPRO|REEM)\s*.*?(\d{6})\s", det)
    if match:
        cve = match.group(2)
        return cve
    # buscamos el patrón de clave de pago a proveedor o acreedor "[T o G][10 dígitos]"
    match = re.search(r"([TG]\d{10})", det)
    if match:
        cve = match.group(1)
        return cve
    cve = row["MOVIMIENTO"].strip() 
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
    rfc_match = re.search(r"RFC:\s*([ÑA-Z]{3,4}\s*[0-9]{6}\s*[0-9A-Z]{3})|R\.F\.C\.\s*([ÑA-Z]{3,4}\s*[0-9]{6}\s*[0-9A-Z]{3})", row["DESCRIPCIÓN"])
    if rfc_match:
        rfc = rfc_match.group(1) if rfc_match.group(1) else rfc_match.group(2)
        rfc = rfc.replace(" ", "")  # eliminar espacios
    else:
        rfc = ""
    
    # Formar el texto del beneficiario
    # armamos la columna de beneficiario como "CUENTA: [cuenta] RFC: [RFC]" (si existen)
    beneficiario = ""
    if cuenta:
        beneficiario += f"CUENTA: {cuenta} "
    if rfc:
        beneficiario += f"RFC: {rfc}"
    
    if not beneficiario:
        return "#"
    
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