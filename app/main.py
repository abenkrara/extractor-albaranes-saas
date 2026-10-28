"""
Servidor API REST FastAPI para el Micro-SaaS B2B de Extracción de Documentos.
Endpoints para procesar PDFs, estructurar datos mediante IA y exportar hojas Excel/CSV.
"""

from urllib.parse import quote
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.config import settings
from app.schemas.document import DocumentData
from app.services.pdf_service import PDFService, PDFProcessingError
from app.services.ai_service import AIService, AIServiceError
from app.services.excel_service import ExcelService

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="Extractor de Albaranes y Facturas B2B API",
    description="Micro-SaaS para extraer, validar y exportar datos de PDFs contables y logísticos a Excel/CSV con IA.",
    version="1.0.0",
)

# Habilitar CORS para permitir peticiones desde Streamlit, React, Vue o clientes externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["Salud del Sistema"])
async def health_check():
    """Verifica el estado del servicio y la configuración activa del proveedor LLM."""
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "max_pages_limit": settings.MAX_PAGES_TO_PROCESS,
        "service": "B2B Document Extractor API",
    }


@app.post(
    "/api/v1/extract",
    response_model=DocumentData,
    summary="Extraer y estructurar datos de un PDF",
    tags=["Extracción"],
)
async def extract_pdf_data(file: UploadFile = File(...)):
    """
    Recibe un archivo PDF de albarán, factura o parte de trabajo, extrae su contenido
    y devuelve los datos limpios y estructurados en formato JSON validado por Pydantic.
    """
    # 1. Validación de tipo de archivo
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo inválido. Solo se admiten archivos PDF (.pdf).",
        )

    # 2. Lectura y validación de tamaño
    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido de {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # 3. Extracción de texto y tablas del PDF
    try:
        extraction_result = PDFService.extract_text_and_tables(file_bytes)
    except PDFProcessingError as pdf_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(pdf_err),
        )

    # 4. Procesamiento mediante IA (OpenAI / Groq)
    try:
        ai_service = AIService()
        structured_data = ai_service.extract_document_data(extraction_result["full_text"])
        return structured_data
    except AIServiceError as ai_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(ai_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la estructuración: {str(exc)}",
        )


@app.post(
    "/api/v1/export-excel",
    summary="Exportar datos estructurados a archivo Excel (.xlsx)",
    tags=["Exportación"],
)
async def export_to_excel(document: DocumentData):
    """
    Recibe el objeto JSON con los datos del documento y genera un archivo Excel (.xlsx)
    profesional con formato contable, bordes estilizados y fórmulas/totales.
    """
    try:
        excel_bytes = ExcelService.generate_excel_bytes(document)
        clean_num = "".join(c for c in document.numero_documento if c.isalnum() or c in ("-", "_")).strip() or "documento"
        filename = f"Extraccion_{clean_num}.xlsx"
        encoded_filename = quote(filename)

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No fue posible generar el archivo Excel: {str(exc)}",
        )


@app.post(
    "/api/v1/export-csv",
    summary="Exportar ítems del documento a archivo CSV",
    tags=["Exportación"],
)
async def export_to_csv(document: DocumentData):
    """Genera un archivo CSV codificado en UTF-8 con BOM a partir de las líneas del documento."""
    try:
        csv_bytes = ExcelService.generate_csv_bytes(document)
        clean_num = "".join(c for c in document.numero_documento if c.isalnum() or c in ("-", "_")).strip() or "documento"
        filename = f"Lineas_{clean_num}.csv"
        encoded_filename = quote(filename)

        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No fue posible generar el archivo CSV: {str(exc)}",
        )


@app.post(
    "/api/v1/process-and-download",
    summary="Pipeline completo directo: PDF a Excel",
    tags=["Pipeline Directo"],
)
async def process_and_download(file: UploadFile = File(...)):
    """
    Endpoint todo en uno: Sube el PDF y descarga directamente el archivo Excel generado.
    Ideal para integraciones directas o automatizaciones desatendidas (cURL, Make, Zapier).
    """
    # 1. Extraer datos con IA
    doc_data = await extract_pdf_data(file)
    # 2. Generar Excel
    return await export_to_excel(doc_data)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

