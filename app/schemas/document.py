"""
Esquemas Pydantic para la estructuración y validación de documentos B2B.
Diseñado para soportar Structured Outputs / JSON Mode en OpenAI y Groq.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ItemDoc(BaseModel):
    """Representa una línea o ítem individual dentro del albarán o factura."""

    descripcion: str = Field(
        ...,
        description="Descripción detallada del producto, material, concepto o servicio prestado.",
    )
    cantidad: float = Field(
        default=1.0,
        description="Cantidad numérica de unidades o servicios (admite decimales como horas o kilos).",
    )
    precio_unitario: float = Field(
        default=0.0,
        description="Precio unitario neto antes de impuestos en la moneda del documento.",
    )
    total: float = Field(
        default=0.0,
        description="Importe total de la línea (generalmente cantidad * precio_unitario).",
    )


class DocumentData(BaseModel):
    """
    Estructura integral y normalizada de un documento comercial B2B
    (albarán de entrega, factura, parte de trabajo o nota de entrega).
    """

    tipo_documento: str = Field(
        default="Factura / Albarán",
        description="Tipo identificado: 'Factura', 'Albarán', 'Parte de Trabajo' o 'Presupuesto'.",
    )
    proveedor: str = Field(
        ...,
        description="Nombre, razón social o nombre comercial del emisor o proveedor del documento.",
    )
    cif_nif_proveedor: Optional[str] = Field(
        default=None,
        description="Identificación fiscal del emisor/proveedor (CIF, NIF, NIE, VAT, TAX ID).",
    )
    cliente: Optional[str] = Field(
        default=None,
        description="Nombre de la empresa o cliente receptor del servicio o mercancía.",
    )
    cif_nif_cliente: Optional[str] = Field(
        default=None,
        description="Identificación fiscal del cliente o receptor si consta en el documento.",
    )
    fecha: str = Field(
        ...,
        description="Fecha de emisión o entrega en formato YYYY-MM-DD (o como aparezca explícitamente).",
    )
    numero_documento: str = Field(
        ...,
        description="Número identificador del albarán, factura, serie o código de entrega.",
    )
    items: List[ItemDoc] = Field(
        default_factory=list,
        description="Listado exhaustivo de todos los ítems, productos, líneas de material o servicios.",
    )
    subtotal: float = Field(
        default=0.0,
        description="Base imponible neta o suma de todos los ítems antes de impuestos.",
    )
    impuestos: float = Field(
        default=0.0,
        description="Importe total de impuestos aplicados (IVA, IGIC, retenciones, etc.).",
    )
    total_general: float = Field(
        ...,
        description="Importe total final del documento a pagar o facturado.",
    )
    moneda: str = Field(
        default="EUR",
        description="Símbolo o código ISO de la moneda (EUR, USD, etc.). Por defecto EUR.",
    )
    observaciones: Optional[str] = Field(
        default=None,
        description="Notas de entrega, condiciones de pago, transportista o comentarios relevantes.",
    )

    def recomputar_totales_si_faltan(self) -> None:
        """
        Método de autocorrección contable: si el subtotal o total general son 0
        pero hay ítems con precios, recalcula los totales automáticamente.
        """
        if self.items:
            # Asegurar que cada línea tenga un total coherente si venía en cero
            for item in self.items:
                if item.total == 0.0 and item.precio_unitario > 0:
                    item.total = round(item.cantidad * item.precio_unitario, 2)

            suma_lineas = round(sum(item.total for item in self.items), 2)
            if self.subtotal == 0.0 and suma_lineas > 0:
                self.subtotal = suma_lineas

            if self.total_general == 0.0:
                self.total_general = round(self.subtotal + self.impuestos, 2)

