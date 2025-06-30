import pandas as pd
import numpy as np
import re
from utils import txt_to_df

def preprocess_bbva(uploaded_file)->pd.DataFrame:
    # para BBVA, se recibe como .txt
    df = txt_to_df(uploaded_file)
    # convertimos las columnas "Cargo", "abono", "Saldo" a tipo numérico rellenando los nulos con 0
    for col in ["cargo", "Abono", "Saldo"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", "").str.replace(" ", "").str.replace("'", ""), errors="coerce").fillna(0)
    # Corregir encabezados si están mal codificados
    df.columns = [col.replace("DÃ­a", "Día") for col in df.columns]
    try:
        df['Día'] = df['Día'].astype(str)
    except Exception as e:
        print(f"Error converting 'Día' to string: {e}")
    # print(df['Día'][0])
    # "Concepto / Referencia" a string sin el espacio inicial
    df["Concepto / Referencia"] = df["Concepto / Referencia"].astype(str).str.lstrip()

    return df

def asign_cve_bbva(row):
    ref = row["Concepto / Referencia"]
    # la referencia es la cadena de texto que aparece después de "/"
    match = re.search(r"/(.+)", ref)
    if match:
        ref = match.group(1)
    cve = np.nan
    # fecha hasta día (sin hora) en formato DDMMYYYY, dado que viene como "DD-MM-YYYY"
    fecha = str(row["Día"])
    fecha = fecha.split("-")
    fecha = fecha[0] + fecha[1] + fecha[2]

    # buscamos el patrón "[T o G][10 dígitos]" en la referencia
    if re.search(r"([TG]\d{10})", ref):
        match = re.search(r"([TG]\d{10})", ref)
        if match:
            cve = match.group(1)
    # si en ref aparece "[palabra clave][6 dígitos]", cve es la palabra clave concatenada con los 6 dígitos
    # donde la palabra clave puede ser "TMLG", "NPRO" o "REEM"
    elif re.search(r"(TMLG|NPRO|REEM)(\d{6})", ref):
        match = re.search(r"(TMLG|NPRO|REEM)(\d{6})", ref)
        if match:
            cve = match.group(1) + match.group(2)
    # si la palabra "NOM " está en la referencia, buscamos el patrón "[banco a tres letras][un dígito][dos letras]"
    elif re.search(r"NOM ", ref):
        match = re.search(r"([A-Z]{3}\d[A-Z]{2})", ref)
        if match:
            cve = match.group(1)
    #_________________________________________________________________________________________________________
    # si ref tiene formato "GUIA:[7 dígitos]", cve es "[7 dígitos]"
    elif re.search(r"GUIA:\d{7}", ref):
        match = re.search(r"GUIA:(\d{7})", ref)
        if match:
            cve = match.group(1)
    # si tiene formato "[10 dígitos] ", cve es "[10 dígitos]"
    elif re.search(r"\d{10} ", ref):
        match = re.search(r"(\d{10}) ", ref)
        if match:
            cve = match.group(1)

    elif ref == "NOTPROVIDED":
        # extraemos el importe y lo limpiamos
        if float(row["cargo"]) > 0:
            importe = str(row["cargo"]).replace(",", "").replace(".", "").replace(" ", "").strip()
        else: 
            importe = str(row["Abono"]).replace(",", "").replace(".", "").replace(" ", "").strip()
        cve = "NP_" + fecha + "_" + importe
    # si no, es la cadena de texto que aparece antes del espacio concatenado con la fecha
    else:
        # si la referencia no es vacío, asignamos la referencia a cve
        if ref and not pd.isna(ref) and ref.strip():
            if "IVA COM" in ref:
                cve = "IVA_" + fecha
            elif "COM " or "SERV " in ref:
                cve = "COM_" + fecha
            else:
                cve = ref.split(" ")[0]+"_" + fecha
        # si no, asignamos la fecha a cve
        else:
            cve = fecha
    return cve
    
def format_bbva(edo_cta:pd.DataFrame, cta: str)->pd.DataFrame:
    # formateamos el DataFrame para que tenga las columnas necesarias
    # y renombramos las columnas
    edo_cta = edo_cta.rename(columns={
        "Día": "FECHA",
        "cargo": "CARGO",
        "Abono": "ABONO",
        "Saldo": "SALDO",
        "cve": "CLAVE"
    })
    # llenamos los valores nulos de las columnas "ABONO" y "CARGO" con 0
    edo_cta["ABONO"] = edo_cta["ABONO"].fillna(0)
    edo_cta["CARGO"] = edo_cta["CARGO"].fillna(0)
    # convertimos la columna "Fecha" a tipo datetime
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"], format="%d-%m-%Y", errors="raise")
    # el concepto es lo que aparece en "Concepto / Referencia" antes de "/"
    # y referencia es lo que aparece después de "/"
    edo_cta["CONCEPTO"] = edo_cta["Concepto / Referencia"].str.split("/").str[0]
    edo_cta["REFERENCIA"] = edo_cta["Concepto / Referencia"].str.split("/").str[1]
    # asignamos una columna de "BANCO" con el nombre del banco
    edo_cta["BANCO"] = 'BBVA'
    # las columnas "REFERENCIA BANCARIA" y "DESCRIPCIÓN" se llenan con "#"
    edo_cta["REFERENCIA BANCARIA"] = "#"
    edo_cta["DESCRIPCIÓN"] = "#"
    edo_cta["BENEFICIARIO"] = "#"

    edo_cta["CUENTA"] = cta

    return edo_cta