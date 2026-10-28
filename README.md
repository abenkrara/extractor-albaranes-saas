# 📄 DocuExtract AI - Micro-SaaS B2B para Extracción de Albaranes y Facturas

Micro-SaaS B2B de alto rendimiento diseñado para extraer, estructurar y validar automáticamente información de **albaranes de entrega, facturas, partes de trabajo y pedidos en PDF**, exportándolos a **Excel (.xlsx) con formato contable profesional y CSV**.

---

## 🏗️ Arquitectura del Sistema

```
Extractor de PDFs y Albaranes/
│
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py               # Gestión de variables de entorno y settings con Pydantic
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── document.py             # Esquemas Pydantic y reglas contables (Structured Outputs)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py          # Extracción híbrida de texto y tablas (pdfplumber + pypdf)
│   │   ├── ai_service.py           # Integración con Groq y OpenAI (JSON Mode / Structured Outputs)
│   │   └── excel_service.py        # Generación de Excel con openpyxl, diseño cebra y formatos de moneda
│   ├── __init__.py
│   └── main.py                     # API REST FastAPI con endpoints para extracción y descargas
│
├── frontend/
│   └── app.py                      # Interfaz visual interactiva en Streamlit (Human-in-the-loop)
│
├── .env.example                    # Plantilla de variables de entorno (Groq / OpenAI)
├── .gitignore                      # Reglas de exclusión de Git
├── requirements.txt                # Dependencias fijadas del proyecto
└── README.md                       # Documentación técnica completa
```

---

## ⚡ Requisitos Previos

- **Python 3.10 o superior**
- Una API Key de **Groq** ([console.groq.com](https://console.groq.com)) o de **OpenAI** ([platform.openai.com](https://platform.openai.com))

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar el repositorio y crear entorno virtual
En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Copia el archivo `.env.example` a `.env`:
```powershell
copy .env.example .env
```

Edita `.env` con tus credenciales:
```ini
# Configuración recomendada para velocidad ultra rápida y coste casi nulo:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_tu_clave_de_groq_aqui
GROQ_MODEL=llama-3.3-70b-versatile

# O si prefieres OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-tu_clave_de_openai_aqui
# OPENAI_MODEL=gpt-4o-mini
```

---

## 🖥️ Ejecución de la Plataforma

Para una experiencia completa, se recomienda ejecutar el Backend (FastAPI) y el Frontend (Streamlit) en dos terminales independientes:

### Terminal 1: Iniciar Servidor FastAPI
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
```
- **Documentación Swagger interactiva**: [http://localhost:8008/docs](http://localhost:8008/docs)
- **Documentación ReDoc**: [http://localhost:8008/redoc](http://localhost:8008/redoc)

### Terminal 2: Iniciar Frontend Streamlit
```bash
streamlit run frontend/app.py --server.port 8505
```
- La interfaz se abrirá en [http://localhost:8505](http://localhost:8505).

---

## 📡 Endpoints de la API REST

### 1. `POST /api/v1/extract`
Extrae el contenido de un PDF y devuelve el JSON estructurado según el modelo Pydantic `DocumentData`.

**Ejemplo cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@albaran_ejemplo.pdf"
```

**Ejemplo de Respuesta:**
```json
{
  "tipo_documento": "Albarán de Entrega",
  "proveedor": "Suministros Industriales S.L.",
  "cif_nif_proveedor": "B12345678",
  "cliente": "Construcciones del Norte S.A.",
  "cif_nif_cliente": "A87654321",
  "fecha": "2024-10-15",
  "numero_documento": "ALB-2024-0891",
  "items": [
    {
      "descripcion": "Cemento Portland gris 25kg",
      "cantidad": 50.0,
      "precio_unitario": 4.80,
      "total": 240.0
    },
    {
      "descripcion": "Arena de sílice fina (saco 20kg)",
      "cantidad": 20.0,
      "precio_unitario": 3.20,
      "total": 64.0
    }
  ],
  "subtotal": 304.0,
  "impuestos": 63.84,
  "total_general": 367.84,
  "moneda": "EUR",
  "observaciones": "Entregado en obra Calle Mayor 12. Conductor: Juan Pérez."
}
```

### 2. `POST /api/v1/export-excel`
Recibe el cuerpo JSON de `DocumentData` y genera un archivo binario `.xlsx` estilizado con:
- Paleta visual azul marino corporativo.
- Autoajuste de ancho de columnas para lectura inmediata sin cortes.
- Formato contable con moneda (`#,##0.00 €`) y números alineados.
- Fila de totales resaltada.

### 3. `POST /api/v1/export-csv`
Exporta las líneas del documento en CSV delimitado por `;` con codificación `UTF-8 con BOM` para garantizar que tildes y caracteres españoles abran perfectamente en Microsoft Excel.

### 4. `POST /api/v1/process-and-download`
Pipeline directo en un solo paso: sube un PDF y devuelve el archivo `.xlsx` listo para descargar. Ideal para webhooks, Zapier o Make.

---

## 🧪 Validación y Características "Human-in-the-Loop"

1. **Corrección Interactiva**: La interfaz de Streamlit permite modificar cantidades, precios y descripciones en la tabla interactiva antes de exportar a Excel.
2. **Autocálculo de Totales**: Si el usuario altera una celda o el documento original carece de subtotal explícito, el sistema recalcula los totales automáticamente.
3. **Multi-Página Seguro**: Límite configurable de hasta 15 páginas por documento para evitar consumos excesivos de contexto en LLM.

