# Asignador de Claves de Estado de Cuenta

## Descripción del Proyecto
Aplicación Streamlit que automatiza la lectura, procesamiento y asignación de claves a estados de cuenta bancarios de múltiples instituciones financieras (Banamex, Santander, HSBC, BBVA, Banorte, PNC). Valida movimientos, asigna claves de clasificación y exporta los resultados en formato Excel con formato personalizado.

## Flujo de Entrada/Salida

| Input/Output | Nombre | Descripción | Fuente |
|---|---|---|---|
| Input | Estados de Cuenta Banamex | Archivo CSV con movimientos de Banamex | Carga del usuario (Streamlit) |
| Input | Estados de Cuenta Santander | Archivo CSV con movimientos de Santander | Carga del usuario (Streamlit) |
| Input | Estados de Cuenta HSBC | Archivo Excel con movimientos de HSBC | Carga del usuario (Streamlit) |
| Input | Estados de Cuenta BBVA | Archivo de texto con movimientos de BBVA | Carga del usuario (Streamlit) |
| Input | Estados de Cuenta Banorte | Archivo CSV con movimientos de Banorte | Carga del usuario (Streamlit) |
| Input | Estados de Cuenta PNC | Archivo CSV con movimientos de PNC | Carga del usuario (Streamlit) |
| Output | Estados Procesados | Archivo Excel con claves asignadas y tipo de movimiento | Descargado desde Streamlit (`claves_{nombre_archivo}.xlsx`) |

---

## Diccionario de Archivos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `main.py` | Principal | Aplicación Streamlit - Interfaz de usuario, carga de archivos y descarga de resultados |
| `config.py` | Configuración | Definiciones de cuentas bancarias, tipos de archivo y columnas esperadas |
| `cves.py` | Lógica Core | Función principal `asign_cve()` que enruta según banco y asigna claves y tipo de movimiento |
| `export.py` | Utilidad | Función `export_to_excel()` que formatea y exporta resultados a Excel |
| `bnx.py` | Módulo Banco | Procesamiento de estados de Santander (preproceso, formato, asignación de claves) |
| `stder.py` | Módulo Banco | Procesamiento de estados de Santander (preproceso, formato, asignación de claves) |
| `hsbc.py` | Módulo Banco | Procesamiento de estados de HSBC (preproceso, formato, asignación de claves) |
| `bbva.py` | Módulo Banco | Procesamiento de estados de BBVA (preproceso, formato, asignación de claves) |
| `pnc.py` | Módulo Banco | Procesamiento de estados de PNC (preproceso, formato, asignación de claves) |
| `brte.py` | Módulo Banco | Procesamiento de estados de Banorte (preproceso, formato, asignación de claves) |
| `utils.py` | Utilidad | Funciones auxiliares (detección de encoding, conversión CSV a DataFrame) |
| `requirements.txt` | Dependencias | Librerías necesarias para ejecutar el proyecto |

---

## Cuentas por Banco

| Banco | Cuentas Soportadas |
|-------|-------------------|
| Banamex | 828, 829, 434 |
| Santander | 383, 383 (INV), 357 |
| HSBC | 019, 455 |
| BBVA | 389, 844 |
| Banorte | 858 |
| PNC | 865, 891 |

---

## Columnas de Salida

```
BANCO, CUENTA, FECHA, DESCRIPCIÓN, CONCEPTO, REFERENCIA, 
REFERENCIA BANCARIA, BENEFICIARIO, DETALLE, CARGO, ABONO, 
SALDO, CLAVE, TIPO MOVIMIENTO
```

### Claves Asignadas

- **Formato T[10 dígitos]**: Pago a Proveedor
- **Formato G[10 dígitos]**: Pago a Acreedor
- **Contiene "COM"**: Comisión
- **Contiene "IVA"**: IVA de Comisión
- **HSBC + "CGO SPEI A"**: Pago por XML
- Otras claves específicas según reglas de negocio por banco

---

## Instrucciones de Uso

1. Ejecutar: `streamlit run main.py`
2. Seleccionar banco y cuenta desde la barra lateral
3. Cargar uno o más archivos de estado de cuenta
4. Descargar el archivo procesado en Excel
