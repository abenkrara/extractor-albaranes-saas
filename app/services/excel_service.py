"""
Servicio de exportación y generación de hojas de cálculo Excel y CSV.
Utiliza pandas y openpyxl para crear informes financieros con diseño visual profesional.
"""

import io
from typing import Union
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.schemas.document import DocumentData


class ExcelService:
    """Clase de servicio encargada de transformar la estructura DocumentData en archivos Excel formateados."""

    @staticmethod
    def generate_excel_bytes(document: DocumentData) -> bytes:
        """
        Crea un archivo Excel profesional en memoria con formato contable, bordes y estilos ejecutivos.

        Args:
            document: Objeto DocumentData con la información extraída.

        Returns:
            bytes del archivo .xlsx generado listo para descarga o streaming.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Documento B2B"

        # Asegurar líneas de cuadrícula visibles
        ws.views.sheetView[0].showGridLines = True

        # Paleta de Colores
        COLOR_PRIMARY_NAVY = "1E3A8A"     # Azul marino corporativo principal
        COLOR_HEADER_BLUE = "2563EB"      # Azul vibrante para cabeceras de tabla
        COLOR_ZEBRA_LIGHT = "F8FAFC"      # Gris ultra claro para filas alternas
        COLOR_SUMMARY_BG = "EFF6FF"       # Azul pastel suave para totales
        COLOR_BORDER = "CBD5E1"           # Gris suave para líneas de celda

        # Fuentes
        font_title = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
        font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
        font_section = Font(name="Segoe UI", size=11, bold=True, color=COLOR_PRIMARY_NAVY)
        font_header_table = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_data = Font(name="Segoe UI", size=10, color="1E293B")
        font_bold = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
        font_total_big = Font(name="Segoe UI", size=12, bold=True, color=COLOR_PRIMARY_NAVY)

        # Rellenos
        fill_title = PatternFill(start_color=COLOR_PRIMARY_NAVY, end_color=COLOR_PRIMARY_NAVY, fill_type="solid")
        fill_table_header = PatternFill(start_color=COLOR_HEADER_BLUE, end_color=COLOR_HEADER_BLUE, fill_type="solid")
        fill_zebra = PatternFill(start_color=COLOR_ZEBRA_LIGHT, end_color=COLOR_ZEBRA_LIGHT, fill_type="solid")
        fill_summary = PatternFill(start_color=COLOR_SUMMARY_BG, end_color=COLOR_SUMMARY_BG, fill_type="solid")

        # Alineaciones
        align_left = Alignment(horizontal="left", vertical="center")
        align_center = Alignment(horizontal="center", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")
        align_header_center = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Bordes
        thin_side = Side(style="thin", color=COLOR_BORDER)
        border_all = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        double_bottom = Side(style="double", color=COLOR_PRIMARY_NAVY)
        border_total = Border(top=thin_side, bottom=double_bottom, left=thin_side, right=thin_side)

        # Formato de Moneda
        currency_symbol = "€" if document.moneda.upper() in ["EUR", "€"] else document.moneda
        currency_format = f'#,##0.00 "{currency_symbol}"'
        number_format = "#,##0.00"

        # -------------------------------------------------------------
        # 1. BANNER PRINCIPAL DE CABECERA (Filas 1 y 2)
        # -------------------------------------------------------------
        ws.merge_cells("A1:D1")
        cell_a1 = ws["A1"]
        cell_a1.value = f"{document.tipo_documento.upper()} - {document.numero_documento}"
        cell_a1.font = font_title
        cell_a1.fill = fill_title
        cell_a1.alignment = align_left

        ws.merge_cells("A2:D2")
        cell_a2 = ws["A2"]
        cell_a2.value = f"Generado automáticamente mediante Extractor Micro-SaaS AI | Fecha: {document.fecha}"
        cell_a2.font = font_subtitle
        cell_a2.fill = fill_title
        cell_a2.alignment = align_left

        ws.row_dimensions[1].height = 30
        ws.row_dimensions[2].height = 20

        # -------------------------------------------------------------
        # 2. SECCIÓN DE METADATOS Y PARTES (Filas 4 a 8)
        # -------------------------------------------------------------
        current_row = 4
        metadata = [
            ("Proveedor / Emisor:", document.proveedor, "Fecha Documento:", document.fecha),
            ("NIF / CIF Proveedor:", document.cif_nif_proveedor or "No especificado", "Nº Documento:", document.numero_documento),
            ("Cliente / Receptor:", document.cliente or "No especificado", "Moneda:", document.moneda),
            ("NIF / CIF Cliente:", document.cif_nif_cliente or "No especificado", "Tipo:", document.tipo_documento),
        ]

        for left_lbl, left_val, right_lbl, right_val in metadata:
            ws.cell(row=current_row, column=1, value=left_lbl).font = font_bold
            ws.cell(row=current_row, column=2, value=left_val).font = font_data
            ws.cell(row=current_row, column=3, value=right_lbl).font = font_bold
            ws.cell(row=current_row, column=4, value=right_val).font = font_data
            ws.row_dimensions[current_row].height = 20
            current_row += 1

        if document.observaciones:
            ws.cell(row=current_row, column=1, value="Observaciones:").font = font_bold
            ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=4)
            obs_cell = ws.cell(row=current_row, column=2, value=document.observaciones)
            obs_cell.font = font_data
            ws.row_dimensions[current_row].height = 22
            current_row += 1

        current_row += 1  # Espaciador

        # -------------------------------------------------------------
        # 3. TABLA DE ÍTEMS / LÍNEAS
        # -------------------------------------------------------------
        headers = ["Descripción del Producto / Servicio", "Cantidad", "Precio Unitario", "Importe Total"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=header)
            cell.font = font_header_table
            cell.fill = fill_table_header
            cell.alignment = align_header_center
            cell.border = border_all

        ws.row_dimensions[current_row].height = 25
        table_start_row = current_row + 1
        current_row += 1

        # Renderizar cada ítem del documento
        for idx, item in enumerate(document.items):
            row_fill = fill_zebra if idx % 2 == 1 else None

            # Col 1: Descripción
            c1 = ws.cell(row=current_row, column=1, value=item.descripcion)
            c1.font = font_data
            c1.alignment = align_left

            # Col 2: Cantidad
            c2 = ws.cell(row=current_row, column=2, value=item.cantidad)
            c2.font = font_data
            c2.alignment = align_center
            c2.number_format = number_format

            # Col 3: Precio Unitario
            c3 = ws.cell(row=current_row, column=3, value=item.precio_unitario)
            c3.font = font_data
            c3.alignment = align_right
            c3.number_format = currency_format

            # Col 4: Total Línea
            c4 = ws.cell(row=current_row, column=4, value=item.total)
            c4.font = font_bold
            c4.alignment = align_right
            c4.number_format = currency_format

            # Aplicar bordes y relleno
            for c in [c1, c2, c3, c4]:
                c.border = border_all
                if row_fill:
                    c.fill = row_fill

            ws.row_dimensions[current_row].height = 22
            current_row += 1

        # Si no hubo ítems, colocar una fila indicativa
        if not document.items:
            ws.cell(row=current_row, column=1, value="No se desglosaron ítems individuales en el documento.")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
            current_row += 1

        # -------------------------------------------------------------
        # 4. CUADRO DE TOTALES Y CIERRE CONTABLE
        # -------------------------------------------------------------
        current_row += 1

        # Fila Subtotal
        ws.cell(row=current_row, column=3, value="Subtotal:").font = font_bold
        subtotal_cell = ws.cell(row=current_row, column=4, value=document.subtotal)
        subtotal_cell.font = font_bold
        subtotal_cell.number_format = currency_format
        subtotal_cell.alignment = align_right
        subtotal_cell.border = border_all
        ws.cell(row=current_row, column=3).border = border_all
        ws.row_dimensions[current_row].height = 22
        current_row += 1

        # Fila Impuestos / IVA
        ws.cell(row=current_row, column=3, value="Impuestos / IVA:").font = font_bold
        imp_cell = ws.cell(row=current_row, column=4, value=document.impuestos)
        imp_cell.font = font_bold
        imp_cell.number_format = currency_format
        imp_cell.alignment = align_right
        imp_cell.border = border_all
        ws.cell(row=current_row, column=3).border = border_all
        ws.row_dimensions[current_row].height = 22
        current_row += 1

        # Fila Total General Destacada
        ws.cell(row=current_row, column=3, value="TOTAL GENERAL:").font = font_total_big
        ws.cell(row=current_row, column=3).fill = fill_summary
        ws.cell(row=current_row, column=3).border = border_total

        total_cell = ws.cell(row=current_row, column=4, value=document.total_general)
        total_cell.font = font_total_big
        total_cell.fill = fill_summary
        total_cell.alignment = align_right
        total_cell.number_format = currency_format
        total_cell.border = border_total
        ws.row_dimensions[current_row].height = 28

        # -------------------------------------------------------------
        # 5. AJUSTE DINÁMICO DE ANCHOS DE COLUMNA
        # -------------------------------------------------------------
        column_widths = {
            "A": 48,  # Descripción amplia
            "B": 14,  # Cantidad
            "C": 18,  # Precio Unitario
            "D": 22,  # Importe Total
        }
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Guardar en buffer en memoria
        output_stream = io.BytesIO()
        wb.save(output_stream)
        output_stream.seek(0)
        return output_stream.getvalue()

    @staticmethod
    def generate_csv_bytes(document: DocumentData) -> bytes:
        """
        Exporta los ítems del documento a formato CSV (UTF-8 con BOM) para máxima
        compatibilidad al abrir con Excel en cualquier idioma.
        """
        rows = []
        for item in document.items:
            rows.append({
                "Documento": document.numero_documento,
                "Fecha": document.fecha,
                "Proveedor": document.proveedor,
                "Cliente": document.cliente or "",
                "Descripción": item.descripcion,
                "Cantidad": item.cantidad,
                "Precio Unitario": item.precio_unitario,
                "Total Línea": item.total,
                "Moneda": document.moneda,
            })

        df = pd.DataFrame(rows)
        # utf-8-sig añade el BOM (Byte Order Mark) para que Microsoft Excel reconozca tildes y caracteres en español
        return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

