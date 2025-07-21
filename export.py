import pandas as pd

def excel_col_letter(col_idx):
    """Convierte índice de columna (0-based) a letra de Excel (A, B, ..., Z, AA, AB, ...)"""
    letters = ''
    while col_idx >= 0:
        letters = chr(col_idx % 26 + 65) + letters
        col_idx = col_idx // 26 - 1
    return letters

def export_to_excel(df: pd.DataFrame, output_file, bank, account):
    sheet_name = f"{bank}_{account}"
    with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='dd-mm-yyyy') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name, freeze_panes=(2, 0), startrow=1)

        workbook = writer.book
        # Asignamos color a la pestaña
        worksheet = writer.sheets[sheet_name]
        worksheet.set_tab_color('#C6EFCE')
        # formato comma style
        comma_format = workbook.add_format({'num_format': '#,##0.00'})
        # Formato encabezado
        header_format = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 2, 'font_color': '#000000'})
        # Formato encabezado de columna "CLAVE"
        cve_format = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'border': 2, 'font_color': '#000000'})
        # subtotales de suma
        subtotal_sum_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 2,
            'font_color': '#000000',
            'num_format': '#,##0.00'
        })
        for col_num, value in enumerate(df.columns):
            # escribimos los encabezados
            if value=='CLAVE':
                worksheet.write(1, col_num, value, cve_format)
                # subtotal para cuenta de movimientos
                # La fórmula CONTAR va de la fila 3 (índice 2) hasta la última fila
                last_row = len(df) + 2
                col_letter = excel_col_letter(col_num)
                formula = f'=SUBTOTAL(3, {col_letter}3:{col_letter}{last_row})'
                worksheet.write_formula(0, col_num, formula, subtotal_sum_format)

            else:
                worksheet.write(1, col_num, value, header_format)
                # subtotales (suma) para importes
                if value in ['CARGO', 'ABONO', 'IMPORTE']:
                    # La fórmula SUMA va de la fila 3 (índice 2) hasta la última fila
                    last_row = len(df) + 2
                    col_letter = excel_col_letter(col_num)
                    formula = f'=SUBTOTAL(9, {col_letter}3:{col_letter}{last_row})'
                    worksheet.write_formula(0, col_num, formula,subtotal_sum_format)

            # Ajusta el ancho de las columnas
            max_len = max(df[value].astype(str).map(len).max(), len(value))
            col_len = max_len + 2 if max_len < 30 else 30
            # Aplica formato comma style a columnas numéricas
            if pd.api.types.is_numeric_dtype(df[value]) and value not in ['Fecha de contabilización', 'FECHA', 'Diferencia fechas (días)', 'movimientos']:
                worksheet.set_column(col_num, col_num, col_len, comma_format)
            else:
                worksheet.set_column(col_num, col_num, col_len)