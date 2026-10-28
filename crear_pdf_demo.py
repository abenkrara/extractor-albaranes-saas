"""
Script utilitario para generar un PDF de ejemplo realista de un Albarán / Factura B2B.
Permite realizar pruebas inmediatas de extracción sin necesitar documentos confidenciales.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generar_pdf_albaran(ruta_salida: str = "ejemplos/albaran_ejemplo.pdf"):
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    story = []

    # Estilos
    title_style = ParagraphStyle(
        "TituloAlbaran",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )
    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold")
    cell_normal = ParagraphStyle("CellNorm", parent=styles["Normal"], fontSize=9)

    # 1. Encabezado
    story.append(Paragraph("LOGÍSTICA Y SUMINISTROS IBERIA S.L.", title_style))
    story.append(Paragraph("CIF: B-98765432 | Polígono Industrial Oeste, Calle Hierro 42, 28021 Madrid", subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Datos del Documento y Cliente en dos columnas
    datos_header = [
        [
            Paragraph("<b>DATOS DEL DOCUMENTO:</b>", cell_bold),
            Paragraph("<b>DATOS DEL CLIENTE / RECEPTOR:</b>", cell_bold),
        ],
        [
            Paragraph("<b>Tipo:</b> Albarán de Entrega", cell_normal),
            Paragraph("<b>Razón Social:</b> Construcciones y Reformas Delta S.A.", cell_normal),
        ],
        [
            Paragraph("<b>Nº Albarán:</b> ALB-2024-00892", cell_normal),
            Paragraph("<b>NIF/CIF:</b> A-12345678", cell_normal),
        ],
        [
            Paragraph("<b>Fecha:</b> 15/10/2024", cell_normal),
            Paragraph("<b>Destino:</b> Obra Residencial Los Olivos, Parcela 14, Toledo", cell_normal),
        ],
        [
            Paragraph("<b>Conductor:</b> Manuel Gómez (Matrícula: 4892-KML)", cell_normal),
            Paragraph("<b>Forma de Pago:</b> Transferencia 30 días", cell_normal),
        ],
    ]

    t_header = Table(datos_header, colWidths=[260, 260])
    t_header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]
        )
    )
    story.append(t_header)
    story.append(Spacer(1, 20))

    # 3. Tabla de Productos / Líneas
    items_header = [
        Paragraph("<b>Cód.</b>", cell_bold),
        Paragraph("<b>Descripción del Material / Servicio</b>", cell_bold),
        Paragraph("<b>Cantidad</b>", cell_bold),
        Paragraph("<b>Precio Unit. (€)</b>", cell_bold),
        Paragraph("<b>Total (€)</b>", cell_bold),
    ]

    filas_items = [
        items_header,
        [
            Paragraph("CEM-01", cell_normal),
            Paragraph("Saco Cemento Portland Gris 25 Kg", cell_normal),
            Paragraph("40", cell_normal),
            Paragraph("5.20 €", cell_normal),
            Paragraph("208.00 €", cell_normal),
        ],
        [
            Paragraph("ARE-04", cell_normal),
            Paragraph("Saco de Arena Fina de Río (20 Kg)", cell_normal),
            Paragraph("25", cell_normal),
            Paragraph("2.80 €", cell_normal),
            Paragraph("70.00 €", cell_normal),
        ],
        [
            Paragraph("LAD-12", cell_normal),
            Paragraph("Palet de Ladrillo Hueco Doble 7x12x24 (400 uds)", cell_normal),
            Paragraph("3", cell_normal),
            Paragraph("145.00 €", cell_normal),
            Paragraph("435.00 €", cell_normal),
        ],
        [
            Paragraph("VAR-08", cell_normal),
            Paragraph("Varilla Corrugada Acero B500S 12mm x 6m", cell_normal),
            Paragraph("50", cell_normal),
            Paragraph("6.40 €", cell_normal),
            Paragraph("320.00 €", cell_normal),
        ],
        [
            Paragraph("POR-01", cell_normal),
            Paragraph("Servicio de Portes y Descarga con Grúa Pluma", cell_normal),
            Paragraph("1", cell_normal),
            Paragraph("85.00 €", cell_normal),
            Paragraph("85.00 €", cell_normal),
        ],
    ]

    t_items = Table(filas_items, colWidths=[55, 260, 65, 75, 65])
    t_items.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_items)
    story.append(Spacer(1, 15))

    # 4. Cuadro de Totales
    datos_totales = [
        ["", "", "Subtotal:", "1,118.00 €"],
        ["", "", "IVA (21%):", "234.78 €"],
        ["", "", "TOTAL ALBARÁN:", "1,352.78 €"],
    ]
    t_totales = Table(datos_totales, colWidths=[150, 165, 120, 85])
    t_totales.setStyle(
        TableStyle(
            [
                ("FONTNAME", (2, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("BACKGROUND", (2, 2), (3, 2), colors.HexColor("#EFF6FF")),
                ("TEXTCOLOR", (2, 2), (3, 2), colors.HexColor("#1E3A8A")),
                ("LINEABOVE", (2, 2), (3, 2), 1, colors.HexColor("#1E3A8A")),
                ("BOTTOMPADDING", (2, 0), (-1, -1), 4),
                ("TOPPADDING", (2, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_totales)
    story.append(Spacer(1, 25))

    # 5. Firma y observaciones
    obs_text = (
        "<b>Observaciones:</b> Mercancía recibida a conformidad del jefe de obra. "
        "Las reclamaciones sobre material defectuoso deben notificarse en un plazo de 48 horas tras la entrega."
    )
    story.append(Paragraph(obs_text, cell_normal))

    doc.build(story)
    print(f"PDF de prueba generado con éxito en: {ruta_salida}")


if __name__ == "__main__":
    generar_pdf_albaran()

