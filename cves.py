import re
import pandas as pd
from bnx import asign_cve_bnx, preprocess_bnx, format_bnx
from stder import asign_cve_stder, preprocess_stder, format_stder
from hsbc import asign_cve_hsbc, preprocess_hsbc, format_hsbc
from bbva import asign_cve_bbva, preprocess_bbva, format_bbva
from pnc import asign_cve_pnc, preprocess_pnc, format_pnc
from brte import asign_cve_brte, preprocess_brte, format_brte
from config import COLS_EDO_CTA

def asign_tipo_movimiento(row: pd.Series) -> str:
    """
    Asigna el tipo de movimiento a cada fila del DataFrame edo_cta
    dependiendo del formato de la clave asignada u otros criterios.
    """
    # si la clave tiene formato "T[10 dígitos]" es un PAGO A PROVEEDOR
    if re.match(r"T\d{10}", row["CLAVE"]):
        return "PAGO A PROVEEDOR"
    # si la clave tiene formato "G[10 dígitos]" es un PAGO A ACREEDOR
    elif re.match(r"G\d{10}", row["CLAVE"]):
        return "PAGO A ACREEDOR"
    # si el banco es HSBC y la descripción empieza con "CGO SPEI A " es un PAGO POR XML    
    elif row["BANCO"] == "HSBC" and row["DESCRIPCIÓN"].startswith("CGO SPEI A "):
        return "PAGO POR XML"
    # si el banco es HSBC y la clave empieza con "FIPP_", es DISPOSICIÓN DE CRÉDITO
    # si empieza con "CRE_", es PAGO DE CRÉDITO CON INTERESES
    elif row["BANCO"] == "HSBC" and row["CLAVE"].startswith("FIPP_"):
        return "DISPOSICIÓN DE CRÉDITO"
    elif row["BANCO"] == "HSBC" and row["CLAVE"].startswith("CRE_"):
        return "PAGO DE CRÉDITO CON INTERESES"
    # si la clave tiene formato "TMLG[6 dígitos]" es un TRASPASO ENTRE CUENTAS MLG
    elif re.match(r"TMLG\d{6}", row["CLAVE"]):
        return "TRASPASO ENTRE CUENTAS MLG"
    # si la clave tiene formato "NPRO[6 dígitos]" es un PAGO NO PROGRAMADO
    elif re.match(r"NPRO\d{6}", row["CLAVE"]):
        return "PAGO NO PROGRAMADO"
    # si la clave tiene formato "REEM[6 dígitos]" es un REEMBOLSO DE GASTOS
    elif re.match(r"REEM\d{6}", row["CLAVE"]):
        return "REEMBOLSO DE GASTOS"
    elif row["BANCO"] == "Banamex" and "XX 000" in row["CONCEPTO"]:
        # si el concepto contiene "XX 00000000"
        # y si es abono, es DISPOSICIÓN DE CRÉDITO
        # y si es cargo, es PAGO DE CRÉDITO CON INTERESES        
        if row["ABONO"] > 0:
            return "DISPOSICIÓN DE CRÉDITO"
        elif row["CARGO"] > 0:
            return "PAGO DE CRÉDITO CON INTERESES"
    # si el banco es Banamex y la clave tiene formato 88MIN[15 caracteres alfanuméricos] o Y[16 dígitos], es pago de IMPUESTOS
    elif row["BANCO"] == "Banamex" and (re.match(r"88MIN[A-Za-z0-9]{15}", row["CLAVE"]) or re.match(r"Y\d{16}", row["CLAVE"])):
        return "PAGO DE IMPUESTOS"
    # si la clave contiene "COM", es una COMISIÓN
    elif "COM" in row["CLAVE"]:
        return "COMISIÓN"
    # si la clave contiene "IVA", es IVA DE COMISIÓN
    elif "IVA" in row["CLAVE"]:
        return "IVA DE COMISIÓN"
    # si la palabra "NOM " está en el detalle, y la clave tiene formato "[tres letras][un dígito][dos letras]", es un PAGO DE NÓMINA
    elif "NOM " in row["DETALLE"] and re.match(r"[A-Z]{3}\d[A-Z]{2}", row["CLAVE"]):
        return "PAGO DE NÓMINA"
    elif "COMPRA INVERSION" in row["DETALLE"]:
        # si la palabra "COMPRA INVERSION" está en el detalle, es una COMPRA DE INVERSIONES
        return "COMPRA DE INVERSIONES"
    # si aparece "VENTA USD", "VENTA DOLARES" "VENTA DE DOLARES" en el detalle, es una VENTA DE DOLARES
    elif re.match(r"VENTA (USD|DOLARES|DE DOLARES)", row["DETALLE"].upper()):
        return "VENTA DE DOLARES"
    # si el banco es banamex y el concepto tiene patrón "PAGO A TERCEROS\s+([A-Z0-9]+)\s+PAGO DE SERVI", es PAGO REFERENCIADO
    elif row["BANCO"] == "Banamex" and re.search(r"PAGO A TERCEROS\s+([A-Z0-9]+)[\s$]", row["CONCEPTO"].upper()) and row["CARGO"] > 0:
        return "PAGO REFERENCIADO"
    # si el banco es banamex y el concepto es una sola palabra de caracteres alfanuméricos, también es PAGO REFERENCIADO
    elif row["BANCO"] == "Banamex" and re.match(r"^(?=[A-Z0-9]*\d)[A-Z0-9]+$", row["CONCEPTO"]) and row["CARGO"] > 0:
        return "PAGO REFERENCIADO"
    # si el banco es PNC y la descripción contiene "WIRE TRANSFER IN" o "ACH CREDIT RECIEVED", es un ABONO DE CLIENTE
    elif row["BANCO"] == "PNC" and ("WIRE TRANSFER IN" in row["DESCRIPCIÓN"] or "ACH CREDIT RECEIVED" in row["DESCRIPCIÓN"]):
        return "ABONO DE CLIENTE"
    # si el banco es PNC, es un abono y la descripción contiene "SWEEP" o "TRNSFR FR INVESTMENT", es INVERSIÓN
    elif row["BANCO"] == "PNC" and row["ABONO"] > 0 and ("SWEEP" in row["DESCRIPCIÓN"] or "TRNSFR FR INVESTMENT" in row["DESCRIPCIÓN"]):
        return "INVERSIÓN"
    # si el banco es PNC y la descripción contiene "ACCOUNT TRANSFER FROM [0]*4954859906", es un TRASPASO DE MLG LLC
    elif row["BANCO"] == "PNC" and re.match(r"ACCOUNT TRANSFER FROM [0]*4954859906", row["DESCRIPCIÓN"]):
        return "TRASPASO DE MLG LLC"
    # si el banco es Santander y el concepto contiene la palabra crédito, es LÍNEA DE CRÉDITO
    elif row["BANCO"] == 'Santander' and re.match(r"CREDITO", row['CONCEPTO']):
        return "LÍNEA DE CRÉDITO"
    else:
        # si no se cumple ninguna de las condiciones anteriores, es OTRO
        return "OTRO"
    

def asign_cve(path_edo_cta: str, bank: str, cta: str) -> pd.DataFrame:
    """
    Asigna la clave de la operación a cada fila del DataFrame edo_cta
    dependiendo del banco que se esté procesando.
    """
    if bank == "Banamex":
        edo_cta = preprocess_bnx(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_bnx, axis=1)
        edo_cta = format_bnx(edo_cta, cta)
    elif bank == "Santander":
        edo_cta = preprocess_stder(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_stder, axis=1)
        edo_cta = format_stder(edo_cta, cta)
    elif bank == "HSBC":
        edo_cta = preprocess_hsbc(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_hsbc, axis=1)
        # agrupamos todos los abonos fipp (referencia bancaria '5203') por día (fecha del apunte)
        # sumamos sus importes y sustituimos a todos estos movimientos por uno solo asignando la clave FIPP_[fecha]
        # hacemos lo mismo con los créditos (referencia bancaria '1065'), asignando la clave "CRE_[fecha]"
        fipps = edo_cta.groupby(["Referencia bancaria", "Fecha del apunte"]).agg({"Importe de crédito": "sum","Importe del débito": "sum"}).reset_index()
        creds = fipps[fipps["Referencia bancaria"] == "1065"]
        fipps = fipps[fipps["Referencia bancaria"] == "5203"]
        fipps["cve"] = "FIPP_" + fipps["Fecha del apunte"].astype(str).str.replace("/", "").str.replace(" ", "").str.replace(":", "")
        creds["cve"] = "CRE_" + creds["Fecha del apunte"].astype(str).str.replace("/", "").str.replace(" ", "").str.replace(":", "")
        # eliminamos los fipps originales
        edo_cta = edo_cta[edo_cta["Referencia bancaria"] != "5203"]
        edo_cta = edo_cta[edo_cta["Referencia bancaria"] != "1065"]
        # unimos los fipps agrupados al dataframe original
        edo_cta = pd.concat([edo_cta, fipps, creds], ignore_index=True)
        # formateamos el dataframe
        edo_cta = format_hsbc(edo_cta, cta)     

    elif bank == "BBVA":
        edo_cta = preprocess_bbva(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_bbva, axis=1)
        edo_cta = format_bbva(edo_cta, cta)
    elif bank == "PNC":
        edo_cta = preprocess_pnc(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_pnc, axis=1)
        edo_cta = format_pnc(edo_cta, cta)
    elif bank == "Banorte":
        edo_cta = preprocess_brte(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_brte, axis=1)
        edo_cta = format_brte(edo_cta, cta)
    else:
        raise ValueError(f"Banco no soportado: {bank}")
    # convertimos las columnas "DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO" y "CLAVE" a string
    edo_cta[["DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO", "CLAVE"]] = edo_cta[["DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO", "CLAVE"]].astype(str)
    # eliminamos los espacios iniciales y finales de las columnas "CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN" y "CLAVE"
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN", "CLAVE"]] = edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN", "CLAVE"]].apply(lambda x: x.str.strip())
    # quitamos espacios múltiples y los cambiamos por uno solo
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN", "CLAVE"]].replace(r"\s+",r"\s", inplace=True, )
    # en la columna "DETALLE" se concatenan todos los datos descriptores
    edo_cta["DETALLE"] = edo_cta.apply(lambda x: '|'.join([x["DESCRIPCIÓN"], x["CONCEPTO"], x["REFERENCIA"], x["REFERENCIA BANCARIA"],x["BENEFICIARIO"]]), axis=1)
    # eliminamos los ceros a la izquierda de la clave
    edo_cta['CLAVE'] = edo_cta['CLAVE'].apply(lambda x: re.sub(r'^[0]+', '', x) if isinstance(x, str) else x)
    # para abonos, recortamos la clave hasta los últimos 12 caracteres
    edo_cta['CLAVE'] = edo_cta.apply(acortar_cve, axis=1)
    # asignamos el tipo de movimiento a cada fila
    edo_cta["TIPO MOVIMIENTO"] = edo_cta.apply(asign_tipo_movimiento, axis=1)
    # eliminamos las columnas que no necesitamos
    edo_cta = edo_cta[COLS_EDO_CTA]
    return edo_cta

def acortar_cve(row):
    if float(row['ABONO'])>0:
        return row['CLAVE'][-12:]
    else:
        return row['CLAVE']