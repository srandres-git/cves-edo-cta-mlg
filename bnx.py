import pandas as pd
import numpy as np
import re
import chardet

def preprocess_bnx(uploaded_file)->pd.DataFrame:
    # # para Banamex, se recibe como .csv    
    # primero leemos el archivo csv y guardamos todas las filas
    content = uploaded_file.read()               # bytes
    encoding = chardet.detect(content)['encoding']
    if encoding is None:
        print("No se pudo detectar la codificación del archivo.")
        encoding = "latin-1"
    text = content.decode(encoding)              # str
    lines = text.splitlines()                    # lista de líneas

    
    # buscamos la fila que contiene "Detalle de Movimientos - Depósitos y Retiros"
    header_row = next(i for i, line in enumerate(lines) if "Detalle de Movimientos - Depósitos y Retiros" in line)+1
    data = lines[header_row:]
    # creamos un DataFrame a partir de las líneas del archivo csv
    from io import StringIO
    data_str = "\n".join(data)
    df = pd.read_csv(StringIO(data_str), sep=",", encoding=encoding)
    print(df.columns)
    # Depósitos, Retiros y Saldo son columnas que contienen valores numéricos
    # convertimos las columnas "Depósitos" y "Retiros" a tipo numérico rellenando los nulos con 0
    df["Depósitos"] = pd.to_numeric(df["Depósitos"].astype(str).str.replace(",", "").str.replace(" ", ""), errors="coerce").fillna(0)
    df["Retiros"] = pd.to_numeric(df["Retiros"].astype(str).str.replace(",", "").str.replace(" ", ""), errors="coerce").fillna(0)
    df["Saldo"] = pd.to_numeric(df["Saldo"].astype(str).str.replace(",", "").str.replace(" ", ""), errors="coerce").fillna(0)

    # Descripción a string
    df["Descripción"] = df["Descripción"].astype(str)

    return df


def asign_cve_bnx(row):
    descripcion = row["Descripción"]
    # buscamos el patrón de clave de pago a proveedor o acreedor "[T o G][10 dígitos]"
    match = re.search(r"([TG]\d{10})", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = match.group(1)
        return clave
    # buscamos el patrón # "[palabra clave][6 dígitos]" en la columna "Descripción"
    # donde la palabra clave puede ser "TMLG", "NPRO" o "REEM" y la clave es la palabra clave concatenada con los 6 dígitos
    # match = re.search(r"(TMLG|NPRO|REEM).*\s+Referencia Númerica:\s+.+(\d{6})\s+Autorización", descripcion)
    match = re.search(r"(TMLG|NPRO|REEM)(\d{6})", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = match.group(1) + match.group(2)
        return clave
    # si es abono, se pone el número de autorización
    if row["Depósitos"] > 0:
        # buscamos el patrón "Autorización: [dígitos]"
        match = re.search(r"Autorización:\s*(\d+)", descripcion)
        if match:
            # si encontramos una coincidencia, extraemos la clave
            clave = match.group(1)
            return clave
    # si la palabra "NOM " está en la descripción, buscamos el patrón "[banco a tres letras][un dígito][dos letras]"
    if "NOM " in descripcion:
        match = re.search(r"([A-Z]{3}\d[A-Z]{2})", descripcion)
        if match:
            # si encontramos una coincidencia, extraemos la clave
            clave = match.group(1)
            return clave
    # buscamos el patrón "PAGO TERCEROS NO.AU Y[10 dígitos] [6 dígitos]", la clave será Y[10 dígitos][6 dígitos]
    match = re.search(r"PAGO TERCEROS\s+NO\.AU\s+Y(\d{10})\s+(\d{6})", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = "Y" + match.group(1) + match.group(2)
        return clave
    # buscamos el patrón "Nominas Vig 88MIN[15 caracteres alfanuméricos]", la clave será "88MIN" + los 15 caracteres alfanuméricos
    match = re.search(r"Nominas Vig (88MIN[A-Za-z0-9]{15})", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = match.group(1)
        return clave
    # buscamos el patrón "PAGO A TERCEROS\s+[caracteres alfanuméricos]+\s+PAGO DE SERVI", la clave serán los caracteres alfanuméricos
    match = re.search(r"PAGO A TERCEROS\s+([A-Z0-9]+)[\s$]", descripcion.upper())
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = match.group(1)
        return clave
    # buscamos el patrón "[inicio][caracteres alfanuméricos, al menos un dígito]\s+Referencia Númerica:" (i.e., solo una palabra antes de la referencia numérica)
    # la clave será los caracteres alfanuméricos
    match = re.search(r"^(?=[A-Z0-9]*\d)([A-Z0-9]+)\s+Referencia Númerica:", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        clave = match.group(1)
        return clave
    #__________________________________________________________________________________________________________
    # buscamos el formato "LY[6 dígitos]_[dígitos]" en la columna "Descripción"
    match = re.search(r"(LY\d{6}_\d+)", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        # y concatenamos "D" o "R" dependiendo del valor de "Depósitos" o "Retiros"
        clave = match.group(0)
        return clave
    # buscamos el texto PAGOS FACTS MULTILOG en la columna "Descripción"
    match = re.search(r"PAGOS FACTS MULTILOG",descripcion)
    if match:
        # si encontramos una coincidencia, la clave estará formada por la fecha y el importe
        # de la transacción, separados por un guion bajo
        # formato 03-03-25
        try:
            fecha = str(row["Fecha"]).split("-")
            if len(fecha) != 3:
                fecha = str(row["Fecha"]).split("/")
            fecha = f"{fecha[0]}{fecha[1]}20{fecha[2]}"
        except Exception as e:
            print(f"Error al procesar la fecha ({str(row["Fecha"])}): {e}")
            return np.nan
        try:    
            importe = row["Retiros"] if row["Retiros"] > 0 else row["Depósitos"]
            clave = f"{fecha}_{str(importe).replace('.', '').replace(',', '')}"
        except Exception as e:
            print(f"Error al procesar el importe({row["Depósitos"]},{row["Retiros"]}): {e}")
            return np.nan        
        return clave

    # buscamos la clave numérica que aparace en el campo "Descripción"
    # después de "Autorización:"
    match = re.search(r"Autorización:\s*(\d+)", descripcion)
    if match:
        # si encontramos una coincidencia, extraemos la clave
        # y concatenamos "D" o "R" dependiendo del valor de "Depósitos" o "Retiros"
        clave = match.group(1)
        # if row["Depósitos"] > 0:
        #     clave = "D_" + clave
        # elif row["Retiros"] > 0:
        #     clave = "R_" + clave
        
        # si la palabra "IVA" está en la descripción, le agregamos "IVA" a la clave
        if re.match(r"(^| )IVA(COM| |$)", descripcion, re.IGNORECASE):
            clave += "_IVA"
        # si no, si la palabra "COM." o "COMISION" está en la descripción, le agregamos "COM" a la clave
        elif "COM." in descripcion or "COMISION" in descripcion:
            clave += "_COM"
        
        return clave
    else:
        # si no encontramos una coincidencia, devolvemos NaN
        return np.nan
    
def format_bnx(edo_cta:pd.DataFrame, cta:str)->pd.DataFrame:
    # formateamos el DataFrame para que tenga las columnas necesarias
    # y renombramos las columnas
    edo_cta = edo_cta.rename(columns={
        "Fecha": "FECHA",
        "Descripción": "DESCRIPCIÓN",
        "Depósitos": "ABONO",
        "Retiros": "CARGO",
        "Saldo": "SALDO",
        "cve": "CLAVE"
    })
    # llenamos los valores nulos de las columnas "ABONO" y "CARGO" con 0
    edo_cta["ABONO"] = edo_cta["ABONO"].fillna(0)
    edo_cta["CARGO"] = edo_cta["CARGO"].fillna(0)
    # convertimos la columna "Fecha" a tipo datetime
    edo_cta["FECHA"] = edo_cta["FECHA"].str.replace('/', '-')
    edo_cta["FECHA"] = edo_cta["FECHA"].str.replace(r'(\d{2}-\d{2})-(\d{2})$', r'\1-20\2', regex=True)
    # verificamos si la fecha tiene el formato correcto
    if not all(re.match(r'^\d{2}-\d{2}-\d{4}$', str(date)) for date in edo_cta["FECHA"]):
        raise ValueError("Formato de fecha incorrecto en la columna 'FECHA'")
    edo_cta["FECHA"] = pd.to_datetime(edo_cta["FECHA"], format="%d-%m-%Y", errors="raise")
    # convertimos la columna "Descripción" a tipo string
    edo_cta["DESCRIPCIÓN"] = edo_cta["DESCRIPCIÓN"].astype(str)
    # extraemos de la descripción el patrón "(.+)Referencia N[úu]m[ée]rica:\s*(.+)(Autorización:\s*\d+)"
    # y asignamos los grupos a las columnas "CONCEPTO", "REFERENCIA" y "REFERENCIA BANCARIA"
    # si no se encuentra el patrón, se asigna NaN a las columnas
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA"]] = edo_cta["DESCRIPCIÓN"].str.extract(r"(.+)Referencia N[úu]m[ée]rica:\s*(.+)Autorización:\s*(\d+)")
    # si no se encuentra el patrón, se asigna '#' a las columnas "CONCEPTO", "REFERENCIA" y "REFERENCIA BANCARIA"
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA"]] = edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA"]].fillna("#")
    # eliminamos los espacios iniciales y finales de las columnas "CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA" y "DESCRIPCIÓN"
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN"]] = edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN"]].apply(lambda x: x.str.strip())

    # asignamos una columna de "BANCO" con el nombre del banco
    edo_cta["BANCO"] = 'Banamex'
    edo_cta["CUENTA"] = cta
    edo_cta["BENEFICIARIO"] = "#"
    # la descripcion ya está impícita en el concepto, la referencia y la referencia bancaria 
    edo_cta["DESCRIPCIÓN"] = "#"

    return edo_cta