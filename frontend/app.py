"""
Interfaz de Usuario Streamlit para el Micro-SaaS B2B.
Extractor y Validador de Albaranes, Facturas y Partes de Trabajo en PDF.
"""

import os
import json
import requests
import streamlit as st
import pandas as pd

# Configuración de página de Streamlit
st.set_page_config(
    page_title="DocuExtract AI | Extractor de Albaranes y Facturas",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para apariencia SaaS premium
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #E2E8F0;
    }
    .badge-status {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Constante de backend por defecto
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8008")

# -----------------------------------------------------------------------------
# BARRA LATERAL (CONFIGURACIÓN Y ESTADO)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bill.png", width=64)
    st.markdown("### **DocuExtract AI**")
    st.caption("Micro-SaaS para automatización contable B2B")
    st.divider()

    st.markdown("#### **⚙️ Configuración del Servidor**")
    backend_url = st.text_input("URL del Backend FastAPI", value=DEFAULT_BACKEND_URL)

    # Comprobación de salud del Backend
    api_online = False
    try:
        health_resp = requests.get(f"{backend_url}/api/v1/health", timeout=2.5)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            st.success(f"🟢 Backend Conectado ({health_data.get('llm_provider', '').upper()})")
            api_online = True
        else:
            st.warning(f"🟡 Respuesta inesperada: {health_resp.status_code}")
    except Exception:
        st.error("🔴 Backend no disponible en la URL indicada.")
        st.caption("Asegúrate de ejecutar: `uvicorn app.main:app --reload`")

    st.divider()
    st.markdown("#### **ℹ️ Documentos Soportados**")
    st.markdown(
        """
        - 📦 **Albaranes de Entrega** (materiales, transportes)
        - 🧾 **Facturas de Proveedores** (A4 estándar, bilingües)
        - 🛠️ **Partes de Trabajo** (horas y conceptos)
        - 📑 **Presupuestos y Pedidos**
        """
    )
    st.info("💡 **Consejo:** Los PDFs con texto vectorial directo se procesan en menos de 3 segundos.")

# -----------------------------------------------------------------------------
# ZONA PRINCIPAL: CABECERA Y SUBIDA DE DOCUMENTOS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">📄 Extractor de Albaranes y Facturas B2B</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Sube tus albaranes y facturas en PDF para extraer datos estructurados con IA y exportarlos a Excel con formato contable impecable.</div>',
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo PDF (Albarán o Factura)",
    type=["pdf"],
    help="Admite archivos PDF de hasta 20 MB.",
)

# Inicializar estado en sesión si no existe
if "structured_data" not in st.session_state:
    st.session_state.structured_data = None
if "items_df" not in st.session_state:
    st.session_state.items_df = None


def procesar_pdf(file_bytes: bytes, filename: str):
    """Envía el PDF a la API de FastAPI para extracción estructurada."""
    files = {"file": (filename, file_bytes, "application/pdf")}
    try:
        response = requests.post(f"{backend_url}/api/v1/extract", files=files, timeout=60)
        if response.status_code == 200:
            return response.json(), None
        else:
            try:
                error_detail = response.json().get("detail", response.text)
            except Exception:
                error_detail = response.text
            return None, f"Error {response.status_code}: {error_detail}"
    except Exception as exc:
        return None, f"Error de conexión con el backend: {str(exc)}"


# Botón de procesamiento
if uploaded_file is not None:
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        process_clicked = st.button("🚀 Procesar Documento con IA", use_container_width=True, type="primary")

    if process_clicked:
        if not api_online:
            st.error("No se puede procesar: el servidor FastAPI no está accesible.")
        else:
            with st.spinner("Leyendo PDF y analizando líneas con IA..."):
                file_bytes = uploaded_file.getvalue()
                result_json, error_msg = procesar_pdf(file_bytes, uploaded_file.name)

                if error_msg:
                    st.error(f"❌ Fallo al procesar: {error_msg}")
                else:
                    st.success("✅ ¡Documento estructurado exitosamente!")
                    st.session_state.structured_data = result_json

                    # Construir DataFrame para el editor interactivo
                    raw_items = result_json.get("items", [])
                    if raw_items:
                        st.session_state.items_df = pd.DataFrame(raw_items)
                    else:
                        st.session_state.items_df = pd.DataFrame(
                            [{"descripcion": "Sin detalle de líneas", "cantidad": 1.0, "precio_unitario": 0.0, "total": 0.0}]
                        )

# -----------------------------------------------------------------------------
# RESULTADOS Y VISTA PREVIA (HUMAN-IN-THE-LOOP)
# -----------------------------------------------------------------------------
if st.session_state.structured_data is not None:
    doc = st.session_state.structured_data

    st.markdown("---")
    st.markdown("### 📊 Datos Extraídos y Auditoría")

    # Tarjetas Métricas Superiores
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="🏢 Proveedor / Emisor", value=doc.get("proveedor", "N/D"))
        st.caption(f"CIF: {doc.get('cif_nif_proveedor') or 'No indicado'}")
    with kpi2:
        st.metric(label="📅 Fecha", value=doc.get("fecha", "N/D"))
        st.caption(f"Tipo: {doc.get('tipo_documento', 'Documento')}")
    with kpi3:
        st.metric(label="🔢 Nº Documento", value=doc.get("numero_documento", "N/D"))
        st.caption(f"Cliente: {doc.get('cliente') or 'No indicado'}")
    with kpi4:
        moneda = doc.get("moneda", "EUR")
        simbolo = "€" if moneda in ["EUR", "€"] else moneda
        st.metric(label="💰 TOTAL GENERAL", value=f"{doc.get('total_general', 0.0):,.2f} {simbolo}")
        st.caption(f"Subtotal: {doc.get('subtotal', 0.0):,.2f} {simbolo} | Impuestos: {doc.get('impuestos', 0.0):,.2f} {simbolo}")

    st.markdown("#### 📝 Desglose de Líneas e Ítems (Editable)")
    st.caption("Puedes corregir o editar directamente cualquier celda antes de generar el Excel final:")

    # Editor interactivo de datos
    edited_df = st.data_editor(
        st.session_state.items_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "descripcion": st.column_config.TextColumn("Descripción", required=True, width="large"),
            "cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f", min_value=0.0, required=True),
            "precio_unitario": st.column_config.NumberColumn("Precio Unitario", format="%.2f €", min_value=0.0, required=True),
            "total": st.column_config.NumberColumn("Total Línea", format="%.2f €", min_value=0.0, required=True),
        },
    )

    # Actualizar totales si el usuario modificó líneas
    if not edited_df.equals(st.session_state.items_df):
        st.session_state.items_df = edited_df
        # Actualizar datos en memoria
        new_items = edited_df.to_dict(orient="records")
        for it in new_items:
            it["cantidad"] = float(it.get("cantidad") or 1.0)
            it["precio_unitario"] = float(it.get("precio_unitario") or 0.0)
            it["total"] = round(it["cantidad"] * it["precio_unitario"], 2)

        nuevo_subtotal = round(sum(it["total"] for it in new_items), 2)
        doc["items"] = new_items
        doc["subtotal"] = nuevo_subtotal
        doc["total_general"] = round(nuevo_subtotal + float(doc.get("impuestos", 0.0)), 2)
        st.session_state.structured_data = doc

    # -------------------------------------------------------------------------
    # DESCARGAS Y EXPORTACIONES
    # -------------------------------------------------------------------------
    st.markdown("#### 📥 Opciones de Exportación")
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    # 1. Descargar Excel Formateado
    with col_dl1:
        try:
            excel_resp = requests.post(f"{backend_url}/api/v1/export-excel", json=doc, timeout=20)
            if excel_resp.status_code == 200:
                clean_num = "".join(c for c in doc.get("numero_documento", "doc") if c.isalnum() or c in ("-", "_"))
                st.download_button(
                    label="📊 Descargar Excel Profesional (.xlsx)",
                    data=excel_resp.content,
                    file_name=f"Albaran_{clean_num}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                )
            else:
                st.button("Excel no disponible", disabled=True)
        except Exception as exc:
            st.error(f"Error al solicitar Excel: {exc}")

    # 2. Descargar CSV
    with col_dl2:
        try:
            csv_resp = requests.post(f"{backend_url}/api/v1/export-csv", json=doc, timeout=20)
            if csv_resp.status_code == 200:
                clean_num = "".join(c for c in doc.get("numero_documento", "doc") if c.isalnum() or c in ("-", "_"))
                st.download_button(
                    label="📄 Descargar Líneas en CSV",
                    data=csv_resp.content,
                    file_name=f"Lineas_{clean_num}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        except Exception:
            pass

    # 3. Descargar JSON
    with col_dl3:
        json_str = json.dumps(doc, indent=2, ensure_ascii=False)
        st.download_button(
            label="💻 Descargar JSON Estructurado",
            data=json_str,
            file_name="documento_extraido.json",
            mime="application/json",
            use_container_width=True,
        )

    # Pestaña para inspeccionar JSON crudo
    with st.expander("🔍 Ver JSON en crudo (para desarrolladores / API)"):
        st.json(doc)

