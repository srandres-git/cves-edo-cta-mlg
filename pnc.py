import pandas as pd
import numpy as np
from io import StringIO
from config import COLS_EDO_CTA
from utils import get_encoding

def preprocess_pnc(uploaded_file)->pd.DataFrame:
    # para PNC, se recibe como .csv
    encoding = get_encoding(uploaded_file=uploaded_file)
    content = uploaded_file.read()               # bytes
    text = content.decode(encoding)              # str
    data = text.splitlines()                    # lista de líneas
    data_str = "\n".join(data)
    df = pd.read_csv(StringIO(data_str), encoding=encoding, sep=",")
    # Reference a string sin "'" y sin espacios
    df["Reference"] = df["Reference"].astype(str).str.replace("'", "", regex=False).str.replace(" ", "", regex=False)
    
    return df

def asign_cve_pnc(row):
    ref = row["Reference"]
    cve = np.nan
    # Capturar [AsOfDate]_[BaiControl] para movimientos con referencia genérica ('00000000000). Ejemplo: 03022025_293
    if ref == "00000000000":
        # fecha hasta día (sin hora) en formato DDMMYYYY, dado que viene como "2025-02-26  12:00:00 AM"
        fecha = str(row["AsOfDate"]).split(" ")[0]
        if "-" in fecha:
            fecha = fecha.split("-")
        else:
            fecha = fecha.split("/")
        # print(fecha)
        fecha = fecha[2] + fecha[1] + fecha[0]
        cve =  str(row["BaiControl"]) + "_" + fecha
    else:
        # Si la referencia es diferente de "00000000000", asignamos la referencia a cve
        cve = ref

    return cve    

def format_pnc(edo_cta:pd.DataFrame)->pd.DataFrame:
    # formateamos el DataFrame para que tenga las columnas necesarias
    # y renombramos las columnas
    edo_cta = edo_cta.rename(columns={
        "AsOfDate": "FECHA",
        "Description": "DESCRIPCIÓN",
        "Transaction": "CONCEPTO",
        "Reference": "REFERENCIA",
        "BaiControl": "REFERENCIA BANCARIA",
        "cve": "CLAVE"
    })
    # transformamos Amount a numérico y llenamos los nulos con 0
    edo_cta["Amount"] = pd.to_numeric(edo_cta["Amount"].astype(str).str.replace(",", "").str.replace(" ", "").str.replace("'",""), errors="coerce").fillna(0)
    # determinamos si es cargo o abono
    cargo_kw = ['Debits', 'DB', 'Fees']
    abono_kw = ['Credits', 'CR']
    # CARGO es el importe si "CONCEPTO" contiene alguna de las palabras clave de cargo, si no, es 0
    edo_cta["CARGO"] = np.where(edo_cta["CONCEPTO"].str.contains('|'.join(cargo_kw), case=False, na=False), edo_cta["Amount"], 0)
    # ABONO es el importe si "CONCEPTO" contiene alguna de las palabras clave de abono, si no, es 0
    edo_cta["ABONO"] = np.where(edo_cta["CONCEPTO"].str.contains('|'.join(abono_kw), case=False, na=False), edo_cta["Amount"], 0)
    # verificar que no haya filas donde CARGO y ABONO sean ambos 0
    if len(edo_cta[(edo_cta["CARGO"] == 0) & (edo_cta["ABONO"] == 0)]) > 0:
        print("Hay filas donde CARGO y ABONO son ambos 0")
        print(edo_cta[(edo_cta["CARGO"] == 0) & (edo_cta["ABONO"] == 0)])
    
    # unificamos el formato de fecha
    edo_cta["FECHA"] = edo_cta["FECHA"].astype(str).str.replace(r'(\d{2})-(\d{2})-(\d{2})', r'\1/\2/20\3', regex=True)
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"], format="%m/%d/%Y", errors="raise")
    
    # convertimos la columna "Descripción" a tipo string
    edo_cta["DESCRIPCIÓN"] = edo_cta["DESCRIPCIÓN"].astype(str)
    # asignamos una columna de "BANCO" con el nombre del banco
    edo_cta["BANCO"] = 'PNC'
    # las columnas "CONCEPTO" y "SALDO" se llenan con "#"
    edo_cta["CONCEPTO"] = "#"
    edo_cta["SALDO"] = "#"
    # eliminamos las columnas que no necesitamos
    edo_cta = edo_cta[COLS_EDO_CTA]

    return edo_cta