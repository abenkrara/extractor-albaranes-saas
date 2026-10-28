"""
Servicio para la extracción de texto y tablas de documentos PDF.
Utiliza pdfplumber con fallback a pypdf para máxima robustez en albaranes y facturas.
"""

import io
import re
from typing import Dict, Any, List
import pdfplumber
from pypdf import PdfReader

from app.core.config import settings


class PDFProcessingError(Exception):
    """Excepción lanzada cuando ocurre un error al procesar o leer el PDF."""
    pass


class PDFService:
    """Clase de servicio encargada de parsear y extraer el contenido textual de archivos PDF."""

    @staticmethod
    def extract_text_and_tables(file_bytes: bytes) -> Dict[str, Any]:
        """
        Extrae texto estructurado y tablas del PDF proporcionado en memoria.

        Args:
            file_bytes: Contenido binario del archivo PDF.

        Returns:
            Dict con:
                - full_text: Texto limpio y ordenado de todas las páginas.
                - total_pages: Número de páginas analizadas.
                - tables_detected: Si se detectaron tablas tabuladas.
                - page_summaries: Lista con el texto de cada página individual.
        """
        if not file_bytes:
            raise PDFProcessingError("El archivo PDF está vacío o no contiene datos válidos.")

        full_text_parts: List[str] = []
        page_summaries: List[str] = []
        tables_found_count = 0

        # 1. Intentar extracción prioritaria mediante pdfplumber (maneja excelente tablas y layouts)
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, settings.MAX_PAGES_TO_PROCESS)

                for page_idx in range(pages_to_process):
                    page = pdf.pages[page_idx]
                    page_header = f"--- [PÁGINA {page_idx + 1} DE {total_pages}] ---"
                    page_text = page.extract_text(layout=True) or ""

                    # Extracción complementaria de tablas detectadas en la página
                    try:
                        tables = page.extract_tables()
                        if tables:
                            tables_found_count += len(tables)
                            table_strings = []
                            for tbl in tables:
                                # Convertir cada fila de tabla a una representación de texto plano delimitada por pipes
                                for row in tbl:
                                    if any(row):
                                        cleaned_row = [str(cell or "").strip().replace("\n", " ") for cell in row]
                                        table_strings.append(" | ".join(cleaned_row))
                            if table_strings:
                                page_text += "\n[TABLA ESTRUCTURADA DETECTADA]:\n" + "\n".join(table_strings)
                    except Exception:
                        # Si la extracción de tablas falla en una página particular, continuamos con el texto plano
                        pass

                    cleaned_page_text = PDFService._clean_extracted_text(page_text)
                    if cleaned_page_text.strip():
                        full_text_parts.append(f"{page_header}\n{cleaned_page_text}")
                        page_summaries.append(cleaned_page_text)

        except Exception as plumber_err:
            # 2. Fallback a pypdf si pdfplumber arroja error de renderizado
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                total_pages = len(reader.pages)
                pages_to_process = min(total_pages, settings.MAX_PAGES_TO_PROCESS)

                full_text_parts = []
                page_summaries = []

                for page_idx in range(pages_to_process):
                    page = reader.pages[page_idx]
                    raw_text = page.extract_text() or ""
                    cleaned = PDFService._clean_extracted_text(raw_text)
                    if cleaned.strip():
                        page_header = f"--- [PÁGINA {page_idx + 1} DE {total_pages}] ---"
                        full_text_parts.append(f"{page_header}\n{cleaned}")
                        page_summaries.append(cleaned)
            except Exception as pypdf_err:
                raise PDFProcessingError(
                    f"No fue posible leer el documento PDF. Error: {str(plumber_err)} | Fallback: {str(pypdf_err)}"
                ) from pypdf_err

        combined_text = "\n\n".join(full_text_parts).strip()

        if not combined_text:
            raise PDFProcessingError(
                "El PDF no contiene texto legible (podría ser un documento escaneado solo con imágenes sin OCR)."
            )

        return {
            "full_text": combined_text,
            "total_pages": len(full_text_parts),
            "tables_detected": tables_found_count > 0,
            "tables_count": tables_found_count,
            "page_summaries": page_summaries,
            "char_count": len(combined_text),
        }

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Limpia caracteres de control y normaliza espacios excesivos preservando la estructura."""
        if not text:
            return ""

        # Eliminar caracteres nulos o no imprimibles raros
        text = text.replace("\x00", "")

        # Normalizar saltos de línea continuos a máximo dos
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Normalizar espacios en blanco horizontales consecutivos
        text = re.sub(r"[ \t]{3,}", "  ", text)

        return text.strip()

