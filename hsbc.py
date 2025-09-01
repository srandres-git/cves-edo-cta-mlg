import pandas as pd
import numpy as np
import re

def preprocess_hsbc(uploaded_file)->pd.DataFrame:
    # para HSBC, se recibe como .xlsx
    df = pd.read_excel(uploaded_file, header=0, engine="openpyxl")
    # Descripción, Referencia de cliente y Referencia bancaria son columnas que contienen valores numéricos
    # convertimos las columnas "Descripción", "Referencia de cliente" y "Referencia bancaria" a tipo string
    df["Descripción"] = df["Descripción"].astype(str)
    df["Referencia de cliente"] = df["Referencia de cliente"].astype(str).str.replace(" ", "", regex=False)
    df["Referencia bancaria"] = df["Referencia bancaria"].astype(str).str.replace(" ", "", regex=False)

    return df

def asign_cve_hsbc(row):
    descripcion = row["Descripción"]
    ref_cliente = row["Referencia de cliente"]
    ref_banc = row["Referencia bancaria"]
    cve = np.nan
    if not ref_banc in ['1661', '1725', '1609']:
        # buscamos el patrón de clave de pago a proveedor o acreedor "[T o G][10 dígitos]"
        match = re.search(r"([TG]\d{10})", descripcion)
        if match:
            # si encontramos una coincidencia, extraemos la clave
            cve = match.group(1)
            return cve
        # buscamos el patrón "[palabra clave][6 dígitos]" en la descripción,
        # donde la palabra clave puede ser "TMLG", "NPRO" o "REEM" y la clave esn la palabra clave concatenada con los 6 dígitos
        # match = re.search(r"(TMLG|NPRO|REEM)\s*.*?(\d{6})\s+SPEI", descripcion)
        match = re.search(r"(TMLG|NPRO|REEM)(\d{6})", descripcion)
        if match:
            cve = match.group(1) + match.group(2)
            return cve
        # si la palabra "NOM " está en la descripción, buscamos el patrón "[banco a tres letras][un dígito][dos letras]"
        if "NOM " in descripcion:
            match = re.search(r"([A-Z]{3}\d[A-Z]{2})", descripcion)
            if match:
                cve = match.group(1)
                return cve
    #___________________________________________________________________________________________________________
    # si la descripción contiene "I.V.A." o "IVA", cve es la referencia de cliente sin espacios ni NaN ni comillas simples precedido de "IVA_"
    if ref_banc=='1501':
        cve ="IVA_"+ ref_cliente
    # # si la descripción contiene "CARGO CREDITO:", cve son los 8 dígitos posteriores precedidos de "CRED_"
    # elif "CARGO CREDITO:" in descripcion:
    #     match = re.search(r"CARGO CREDITO:\s*(\d{8})", descripcion)
    #     if match:
    #         cve = 'CRED_'+match.group(1)
    # si aparece "C TRANSF" en la descripción, cve es la referencia de cliente precedida de "COM_"
    elif ref_banc in ['1661', '1725', '1609','1523']:
        cve = 'COM_'+ ref_cliente
    # Si la referencia de cliente es "A2000 [5 dígitos]", concatenar "[5 dígitos]" con la referencia bancaria y la fecha
    elif re.search(r"A2000\d{5}", ref_cliente):
        match = re.search(r"A2000(\d{5})", ref_cliente)
        if match:
            cve = match.group(1)+ ref_banc + "_" + str(row["Fecha del apunte"]).replace("/", "")
    # # si en la descripción hay "ABONO FIPP FOLIO:", cve son los siguientes 6 dígitos precedidos de "FIPP_"
    # elif "ABONO FIPP FOLIO:" in descripcion:
    #     match = re.search(r"ABONO FIPP FOLIO:\s*(\d{6})", descripcion)
    #     if match:
    #         cve = 'FIPP_'+match.group(1)
    # si en la referencia de cliente aparece "D[5 dígitos]", cve es este patrón
    elif re.search(r"D\d{5}", ref_cliente):
        match = re.search(r"D(\d{5})", ref_cliente)
        if match:
            cve = 'D'+match.group(1)
    # si no, cve es la referencia de cliente sin espacios ni NaN ni comillas simples
    else:
        cve = ref_cliente.replace("'", "")
    # si en la descripción aparece "NETNM", agregar "_[texto posterior a NETNM sin espacios]"
    if "NETNM " in descripcion:
        cve += "_"+descripcion.split("NETNM ")[1].replace(" ", "_")
    return cve

def format_hsbc(edo_cta:pd.DataFrame, cta:str)->pd.DataFrame:
    # formateamos el DataFrame para que tenga las columnas necesarias
    # y renombramos las columnas
    edo_cta = edo_cta.rename(columns={
        "Fecha del apunte": "FECHA",
        "Descripción": "DESCRIPCIÓN",
        "Referencia de cliente": "REFERENCIA",
        "Referencia bancaria": "REFERENCIA BANCARIA",
        "Importe del débito": "CARGO",
        "Importe de crédito": "ABONO",
        "Saldo": "SALDO",
        "cve": "CLAVE"
    })
    # llenamos los valores nulos de las columnas "ABONO" y "CARGO" con 0
    edo_cta["ABONO"] = edo_cta["ABONO"].fillna(0)
    # para cargo tomamos el valor absoluto del importe del débito
    edo_cta["CARGO"] = np.abs(edo_cta["CARGO"].fillna(0))
    # convertimos la columna "Fecha" a tipo datetime
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"], format="%d/%m/%Y", errors="raise")
    # convertimos la columna "Descripción" a tipo string
    edo_cta["DESCRIPCIÓN"] = edo_cta["DESCRIPCIÓN"].astype(str)
    # asignamos una columna de "BANCO" con el nombre del banco
    edo_cta["BANCO"] = 'HSBC'
    edo_cta["CUENTA"] = cta
    # las columnas "CONCEPTO" se llena con "#"
    edo_cta["CONCEPTO"] = "#"
    edo_cta["BENEFICIARIO"] = "#"

    return edo_cta