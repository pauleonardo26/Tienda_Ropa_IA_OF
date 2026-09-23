# =========================================================
# gemini.py
# Motor de IA para interpretar pedidos y responder consultas
# =========================================================

import os
import json
import time

import google.generativeai as genai

from prompts import construir_prompt_pedido


# =========================================================
# CONFIGURACIÓN
# =========================================================

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

if API_KEY:
    genai.configure(api_key=API_KEY)


MODELO_IA = "gemini-3.6-flash"


# =========================================================
# CREAR MODELO
# =========================================================

def obtener_modelo():
    if not API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY no está configurada."
        )

    return genai.GenerativeModel(MODELO_IA)


# =========================================================
# LIMPIAR RESPUESTA JSON
# =========================================================

def limpiar_json(texto):
    """
    Limpia posibles bloques Markdown antes de convertir
    la respuesta de la IA a JSON.
    """

    if not texto:
        return ""

    texto = texto.strip()

    if texto.startswith("```json"):
        texto = texto[7:]

    elif texto.startswith("```"):
        texto = texto[3:]

    if texto.endswith("```"):
        texto = texto[:-3]

    return texto.strip()


# =========================================================
# GENERAR RESPUESTA CON REINTENTOS
# =========================================================

def generar_con_reintentos(prompt, max_intentos=3):
    """
    Ejecuta la consulta a la IA.

    Maneja especialmente:
    - 429 RESOURCE_EXHAUSTED
    - 503 UNAVAILABLE
    - HIGH DEMAND

    No repite indefinidamente una petición que claramente
    tiene un problema de cuota.
    """

    modelo = obtener_modelo()

    ultimo_error = None

    for intento in range(1, max_intentos + 1):

        try:

            respuesta = modelo.generate_content(prompt)

            if not respuesta:
                raise RuntimeError(
                    "La IA no devolvió ninguna respuesta."
                )

            texto = getattr(
                respuesta,
                "text",
                None
            )

            if not texto:
                raise RuntimeError(
                    "La IA devolvió una respuesta vacía."
                )

            return texto.strip()

        except Exception as error:

            ultimo_error = error

            texto_error = str(error)

            texto_mayusculas = texto_error.upper()

            es_cuota = (
                "429" in texto_error
                or "RESOURCE_EXHAUSTED" in texto_mayusculas
                or "QUOTA" in texto_mayusculas
            )

            es_temporal = (
                "503" in texto_error
                or "UNAVAILABLE" in texto_mayusculas
                or "HIGH DEMAND" in texto_mayusculas
                or "SERVICE UNAVAILABLE" in texto_mayusculas
            )

            print(
                f"⚠️ Error IA intento "
                f"{intento}/{max_intentos}: {texto_error}"
            )

            # -------------------------------------------------
            # ERROR DE CUOTA
            # -------------------------------------------------

            if es_cuota:

                print(
                    "⚠️ La API de IA alcanzó una cuota o límite."
                )

                # No tiene sentido hacer tres llamadas
                # adicionales si el proveedor ya informó
                # que se alcanzó una cuota.
                raise RuntimeError(
                    "CUOTA_IA_AGOTADA"
                )

            # -------------------------------------------------
            # ERROR TEMPORAL
            # -------------------------------------------------

            if es_temporal and intento < max_intentos:

                espera = intento * 3

                print(
                    f"⏳ Reintentando en {espera} segundos..."
                )

                time.sleep(espera)

                continue

            # -------------------------------------------------
            # OTROS ERRORES
            # -------------------------------------------------

            raise

    raise RuntimeError(
        f"Error de IA después de varios intentos: {ultimo_error}"
    )


# =========================================================
# NORMALIZAR RESPUESTA DE PEDIDO
# =========================================================

def normalizar_pedido(datos):
    """
    Garantiza que la estructura recibida desde la IA tenga
    siempre las claves esperadas por Python.
    """

    if not isinstance(datos, dict):
        return {
            "es_pedido": True,
            "necesita_aclaracion": True,
            "motivo_aclaracion": (
                "No pude interpretar correctamente el pedido."
            ),
            "productos": []
        }

    es_pedido = datos.get(
        "es_pedido",
        True
    )

    necesita_aclaracion = datos.get(
        "necesita_aclaracion",
        False
    )

    motivo_aclaracion = datos.get(
        "motivo_aclaracion",
        ""
    )

    productos = datos.get(
        "productos",
        []
    )

    if not isinstance(productos, list):
        productos = []

    productos_normalizados = []

    for producto in productos:

        if not isinstance(producto, dict):
            continue

        nombre = producto.get(
            "producto",
            ""
        )

        cantidad = producto.get(
            "cantidad",
            1
        )

        tallas = producto.get(
            "tallas",
            []
        )

        colores = producto.get(
            "colores",
            []
        )

        if not isinstance(tallas, list):
            tallas = [tallas] if tallas else []

        if not isinstance(colores, list):
            colores = [colores] if colores else []

        try:
            cantidad = int(cantidad)
        except Exception:
            cantidad = 1

        productos_normalizados.append(
            {
                "producto": str(
                    nombre or ""
                ).strip(),

                "cantidad": cantidad,

                "tallas": tallas,

                "colores": colores
            }
        )

    return {
        "es_pedido": bool(es_pedido),

        "necesita_aclaracion": bool(
            necesita_aclaracion
        ),

        "motivo_aclaracion": str(
            motivo_aclaracion or ""
        ).strip(),

        "productos": productos_normalizados
    }


# =========================================================
# INTERPRETAR PEDIDO
# =========================================================

def interpretar_pedido(mensaje_cliente):

    prompt = construir_prompt_pedido(
        mensaje_cliente
    )

    texto = generar_con_reintentos(
        prompt
    )

    texto_limpio = limpiar_json(
        texto
    )

    try:

        datos = json.loads(
            texto_limpio
        )

    except json.JSONDecodeError as error:

        print(
            "❌ Error convirtiendo respuesta de IA a JSON:"
        )

        print(
            texto_limpio
        )

        print(
            f"Detalle JSON: {error}"
        )

        return {
            "es_pedido": True,
            "necesita_aclaracion": True,
            "motivo_aclaracion": (
                "No pude interpretar correctamente "
                "tu pedido."
            ),
            "productos": []
        }

    datos = normalizar_pedido(
        datos
    )

    print(
        "🧠 Pedido interpretado:"
    )

    print(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2
        )
    )

    return datos


# =========================================================
# RESPONDER CONSULTAS GENERALES
# =========================================================

def responder_con_gemini(
    mensaje_cliente,
    inventario_texto=""
):
    """
    Responde consultas generales del cliente.

    Esta función se mantiene por compatibilidad con el
    webhook actual.

    No modifica pedidos ni stock.
    """

    prompt = f"""
Eres un vendedor de Outlet Valentina Kids Perú.

Responde de manera clara, amable y breve.

El cliente escribió:

{mensaje_cliente}

Información del inventario disponible:

{inventario_texto}

IMPORTANTE:

- No inventes productos.
- No inventes precios.
- No inventes stock.
- No inventes tallas.
- No inventes colores.
- Si la información no está disponible, indícalo claramente.
- No modifiques ningún pedido.
- No descuentes stock.
- No confirmes un pago.

Responde en español.
"""

    texto = generar_con_reintentos(
        prompt
    )

    return {
        "encontrado": True,
        "respuesta": texto,
        "foto": None
    }
