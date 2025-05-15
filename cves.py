import re
import pandas as pd
from bnx import asign_cve_bnx, preprocess_bnx, format_bnx
from stder import asign_cve_stder, preprocess_stder, format_stder
from hsbc import asign_cve_hsbc, preprocess_hsbc, format_hsbc
from bbva import asign_cve_bbva, preprocess_bbva, format_bbva
from pnc import asign_cve_pnc, preprocess_pnc, format_pnc
from brte import asign_cve_brte, preprocess_brte, format_brte
from config import COLS_EDO_CTA

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
        edo_cta = preprocess_banorte(path_edo_cta)
        edo_cta["cve"] = edo_cta.apply(asign_cve_banorte, axis=1)
        edo_cta = format_banorte(edo_cta, cta)
    else:
        raise ValueError(f"Banco no soportado: {bank}")
    # convertimos las columnas "DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO" y "CLAVE" a string
    edo_cta[["DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO", "CLAVE"]] = edo_cta[["DESCRIPCIÓN", "REFERENCIA", "REFERENCIA BANCARIA", "CONCEPTO", "CLAVE"]].astype(str)
    # eliminamos los espacios iniciales y finales de las columnas "CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN" y "CLAVE"
    edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN", "CLAVE"]] = edo_cta[["CONCEPTO", "REFERENCIA", "REFERENCIA BANCARIA", "DESCRIPCIÓN", "CLAVE"]].apply(lambda x: x.str.strip())
    # en la columna "DETALLE" se concatenan todos los datos descriptores
    edo_cta["DETALLE"] = edo_cta.apply(lambda x: '|'.join([x["DESCRIPCIÓN"], x["CONCEPTO"], x["REFERENCIA"], x["REFERENCIA BANCARIA"],x["BENEFICIARIO"]]), axis=1)
    # eliminamos los ceros a la izquierda de la clave
    edo_cta['CLAVE'] = edo_cta['CLAVE'].apply(lambda x: re.sub(r'^[0]+', '', x) if isinstance(x, str) else x)
    # eliminamos las columnas que no necesitamos
    edo_cta = edo_cta[COLS_EDO_CTA]
    return edo_cta