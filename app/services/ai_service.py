"""
Servicio de Inteligencia Artificial para la extracción y estructuración de datos.
Integra OpenAI y Groq con Structured Outputs / JSON Mode respaldado por Pydantic.
"""

import json
from typing import Optional
from openai import OpenAI
from groq import Groq

from app.core.config import settings
from app.schemas.document import DocumentData


class AIServiceError(Exception):
    """Excepción para fallos en la llamada o estructuración del LLM."""
    pass


class AIService:
    """Gestiona la comunicación con modelos LLM para convertir texto no estructurado en DocumentData."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.api_key = api_key
        self.model = model

        # Configuración por proveedor
        if self.provider == "groq":
            self.api_key = self.api_key or settings.GROQ_API_KEY
            self.model = self.model or settings.GROQ_MODEL
            self.groq_client = Groq(api_key=self.api_key) if self.api_key else None
        elif self.provider == "openai":
            self.api_key = self.api_key or settings.OPENAI_API_KEY
            self.model = self.model or settings.OPENAI_MODEL
            self.openai_client = OpenAI(api_key=self.api_key) if self.api_key else None
        else:
            raise AIServiceError(f"Proveedor '{self.provider}' no soportado. Usa 'groq' o 'openai'.")

    def extract_document_data(self, extracted_text: str) -> DocumentData:
        """
        Envía el texto extraído al LLM y obtiene un objeto DocumentData fuertemente tipado.

        Args:
            extracted_text: Texto plano y tablas extraídas del PDF.

        Returns:
            Instancia de DocumentData con los datos estructurados y validados.
        """
        if not extracted_text or not extracted_text.strip():
            raise AIServiceError("El texto a procesar está vacío.")

        system_prompt = self._build_system_prompt()
        user_prompt = f"Por favor procesa el siguiente documento contable/logístico y genera el JSON estructurado:\n\n{extracted_text}"

        try:
            if self.provider == "groq":
                raw_json = self._call_groq(system_prompt, user_prompt)
                document_dict = json.loads(raw_json)
                document = DocumentData.model_validate(document_dict)
            else:
                document = self._call_openai(system_prompt, user_prompt)

            # Autocorrección de totales si el documento no traía subtotal explícito
            document.recomputar_totales_si_faltan()
            return document

        except Exception as exc:
            raise AIServiceError(f"Error procesando documento con {self.provider.upper()}: {str(exc)}") from exc

    def _call_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Llama a la API de Groq en modo JSON con reintentos y fallback automático de modelos."""
        if not self.groq_client:
            raise AIServiceError("GROQ_API_KEY no configurada. Define la variable en el archivo .env.")

        # Lista priorizada de modelos de respaldo en caso de que el configurado no esté disponible
        model_candidates = [self.model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        # Eliminar duplicados preservando el orden
        seen = set()
        unique_models = [m for m in model_candidates if m and not (m in seen or seen.add(m))]

        last_error = None
        for candidate in unique_models:
            try:
                response = self.groq_client.chat.completions.create(
                    model=candidate,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=4096,
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as err:
                last_error = err
                # Si el error es 404 o modelo no encontrado, probamos con el siguiente candidato
                if "model_not_found" in str(err) or "404" in str(err) or "does not exist" in str(err):
                    continue
                else:
                    raise err

        raise AIServiceError(f"No fue posible consultar los modelos de Groq. Último error: {last_error}")

    def _call_openai(self, system_prompt: str, user_prompt: str) -> DocumentData:
        """Llama a la API de OpenAI utilizando Structured Outputs nativo."""
        if not self.openai_client:
            raise AIServiceError("OPENAI_API_KEY no configurada. Define la variable en el archivo .env.")

        try:
            # Uso de client.beta.chat.completions.parse para validación estricta Pydantic
            completion = self.openai_client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=DocumentData,
                temperature=0.1,
            )
            parsed_result = completion.choices[0].message.parsed
            if parsed_result is None:
                raise AIServiceError("OpenAI no pudo estructurar el esquema solicitado.")
            return parsed_result

        except AttributeError:
            # Fallback en caso de versiones de cliente sin soporte beta.parse
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_json = response.choices[0].message.content or "{}"
            return DocumentData.model_validate_json(raw_json)

    def _build_system_prompt(self) -> str:
        """Construye las instrucciones precisas para la extracción contable y de albaranes."""
        schema_json = json.dumps(DocumentData.model_json_schema(), indent=2, ensure_ascii=False)

        return f"""Eres un Asistente Experto en Extracción y Auditoría de Documentos B2B (Albaranes de entrega, Facturas, Partes de Trabajo y Pedidos).
Tu misión es leer el texto extraído de un documento comercial y convertirlo en un objeto JSON estructurado con la máxima precisión contable.

DEBES SEGUIR RIGUROSAMENTE ESTAS REGLAS:
1. IDENTIFICACIÓN DE ACTORES:
   - "proveedor": Es la empresa emisora que vende o entrega la mercancía/servicio.
   - "cif_nif_proveedor": CIF/NIF/NIF-IVA de la empresa emisora.
   - "cliente": La empresa o persona que recibe los materiales o el servicio.
   - "cif_nif_cliente": CIF/NIF del receptor (si aparece).

2. METADATOS DEL DOCUMENTO:
   - "tipo_documento": Especifica si es 'Albarán', 'Factura', 'Parte de Trabajo' o 'Presupuesto'.
   - "fecha": Extrae la fecha de emisión en formato YYYY-MM-DD. Si no es posible, mantén la fecha textual original.
   - "numero_documento": El identificador único del albarán o factura (ej. 'ALB-2024-0012', 'F24/099').

3. TABLA DE ÍTEMS / LÍNEAS DE ARTÍCULO:
   - Extrae todas y cada una de las líneas detalladas de productos, servicios, horas trabajadas o materiales.
   - "descripcion": Nombre o descripción del artículo sin abreviaturas confusas.
   - "cantidad": Número flotante (si no consta cantidad explícita, asume 1.0).
   - "precio_unitario": Precio unitario sin impuestos como número decimal (convierte comas decimales a puntos, ej: '12,50 €' -> 12.50).
   - "total": Importe total neto de la línea. Si no viene explícito, calcula cantidad * precio_unitario.

4. TOTALES ECONÓMICOS:
   - "subtotal": Base imponible o total antes de impuestos.
   - "impuestos": Cuantía total de impuestos (IVA, IGIC, retenciones). Si no viene explícito, calcula total_general - subtotal.
   - "total_general": Importe total final a abonar.
   - "moneda": 'EUR', 'USD', etc.
   - "observaciones": Notas de transporte, matrícula del vehículo, condiciones de entrega o pago si existen.

5. FORMATO DE SALIDA ESTRICTO:
   Debes devolver EXCLUSIVAMENTE un objeto JSON válido conforme a este esquema JSON Schema:
{schema_json}
No incluyas markdown alrededor del JSON como ```json ... ``` a menos que sea obligatorio; devuelve el JSON limpio y parseable.
"""

