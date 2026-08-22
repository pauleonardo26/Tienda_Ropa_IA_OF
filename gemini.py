# =========================================================
# 01 - IMPORTACIONES
# =========================================================

import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from conexion import conexion
from prompts import construir_prompt_pedido


# =========================================================
# 02 - CONFIGURACION GEMINI
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

cliente = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# 20 - GENERAR CON REINTENTOS SI GEMINI ESTA SATURADO
# =========================================================

def generar_con_reintentos(prompt, esquema, max_intentos=3):

    for intento in range(1, max_intentos + 1):

        try:

            print(
                f"Intento Gemini {intento} de {max_intentos}"
            )

            respuesta = cliente.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=esquema
                )
            )

            return json.loads(respuesta.text)

        except Exception as error:

            texto_error = str(error)

            print(
                f"Error Gemini intento {intento}:",
                texto_error
            )

            es_temporal = (
                "503" in texto_error
                or "UNAVAILABLE" in texto_error.upper()
                or "HIGH DEMAND" in texto_error.upper()
            )

            if not es_temporal:
                raise

            if intento < max_intentos:

                segundos = intento * 2

                print(
                    f"Gemini saturado. "
                    f"Reintentando en {segundos} segundos..."
                )

                time.sleep(segundos)

    return None


# =========================================================
# 21 - INTERPRETAR PEDIDO DEL CLIENTE CON GEMINI
# =========================================================

def interpretar_pedido(mensaje_cliente):

    prompt = construir_prompt_pedido(
        mensaje_cliente
    )

    esquema = {
        "type": "object",
        "properties": {

            "es_pedido": {
                "type": "boolean"
            },

            "productos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {

                        "producto": {
                            "type": "string"
                        },

                        "cantidad": {
                            "type": "integer"
                        },

                        "tallas": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },

                        "colores": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }

                    },

                    "required": [
                        "producto",
                        "cantidad",
                        "tallas",
                        "colores"
                    ]
                }
            }

        },

        "required": [
            "es_pedido",
            "productos"
        ]
    }

    datos = generar_con_reintentos(
        prompt,
        esquema,
        max_intentos=3
    )

    if datos is None:

        return {
            "es_pedido": False,
            "productos": [],
            "error_temporal": True
        }

    datos["error_temporal"] = False

    return datos


# =========================================================
# 22 - CONSULTAR INVENTARIO REAL
# =========================================================

def consultar_inventario():

    cursor = conexion.cursor()

    try:

        cursor.execute(
            """
            SELECT
                p.nombre,
                p.categoria,
                p.precio,
                v.talla,
                v.color,
                v.stock,
                v.foto
            FROM variantes_producto v
            JOIN productos p
                ON p.id_producto = v.id_producto
            WHERE v.stock > 0
            ORDER BY p.nombre, v.talla, v.color
            """
        )

        return cursor.fetchall()

    finally:

        cursor.close()


# =========================================================
# 23 - RESPONDER CONSULTAS GENERALES CON GEMINI
# =========================================================

def responder_con_gemini(mensaje_cliente):

    inventario = consultar_inventario()

    if not inventario:

        return {
            "encontrado": False,
            "respuesta": (
                "En este momento no tenemos "
                "productos disponibles."
            ),
            "foto": ""
        }

    inventario_texto = ""

    for producto in inventario:

        nombre, categoria, precio, talla, color, stock, foto = producto

        inventario_texto += (
            f"Producto: {nombre}\n"
            f"Categoría: {categoria}\n"
            f"Precio: S/ {precio}\n"
            f"Talla: {talla}\n"
            f"Color: {color}\n"
            f"Stock: {stock}\n"
            f"Foto: {foto}\n"
            f"---\n"
        )

    prompt = f"""
Eres un asistente de ventas de una tienda de ropa infantil.

REGLAS:

- Usa únicamente productos del inventario real.
- Nunca inventes productos.
- Nunca inventes precios.
- Nunca inventes tallas.
- Nunca inventes colores.
- Nunca inventes stock.
- Si encuentras exactamente o razonablemente
  el producto solicitado, devuelve encontrado=true.
- Si no existe, devuelve encontrado=false.
- Si encuentras un producto,
  devuelve exactamente su valor de Foto.
- Si no encuentras producto o no hay foto,
  devuelve foto="".
- La respuesta al cliente debe ser breve y directa.
- Máximo 3 líneas.

INVENTARIO REAL:

{inventario_texto}

MENSAJE DEL CLIENTE:

{mensaje_cliente}
"""

    esquema = {
        "type": "object",
        "properties": {

            "encontrado": {
                "type": "boolean"
            },

            "respuesta": {
                "type": "string"
            },

            "foto": {
                "type": "string"
            }

        },

        "required": [
            "encontrado",
            "respuesta",
            "foto"
        ]
    }

    datos = generar_con_reintentos(
        prompt,
        esquema,
        max_intentos=3
    )

    if datos is None:

        return {
            "encontrado": False,
            "respuesta": (
                "Estoy teniendo una pequeña demora. "
                "Inténtalo nuevamente en unos segundos."
            ),
            "foto": ""
        }

    return datos