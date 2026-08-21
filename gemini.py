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

    prompt = f"""
Eres un intérprete de pedidos para una tienda de ropa infantil.

Tu única tarea es convertir el mensaje del cliente en datos estructurados.

REGLAS:

- NO calcules precios.
- NO inventes stock.
- NO confirmes disponibilidad.
- NO cambies cantidades.
- NO agregues productos que el cliente no haya pedido.
- Conserva todas las tallas indicadas por el cliente.
- Conserva todos los colores indicados por el cliente.
- El cliente puede escribir de manera informal.
- Si menciona varias tallas, sepáralas en una lista.
- Si menciona varias tallas sin escribir la palabra "talla" cada vez,
  igualmente debes reconocerlas como tallas.
- No juntes varias tallas en un solo texto como "4 y 6".
- No conviertas "4 6 8" en "468".
- Devuelve cada talla como texto separado: ["4", "6", "8"].

Ejemplo 1:

"casera 2 leggins talla 8 negro y
2 polos manga corta talla 4 verde y pastel"

Interpretación:

Producto: legging
Cantidad: 2
Tallas: ["8"]
Colores: ["negro"]

Producto: polo manga corta
Cantidad: 2
Tallas: ["4"]
Colores: ["verde", "pastel"]

Ejemplo 2:

"2 polos manga larga pequeño talla 4 y 6 verde y rosado"

Interpretación:

Producto: polo manga larga pequeño
Cantidad: 2
Tallas: ["4", "6"]
Colores: ["verde", "rosado"]

Ejemplo 3:

"3 leggins tallas 4 6 8 negro lila rosado"

Interpretación:

Producto: legging
Cantidad: 3
Tallas: ["4", "6", "8"]
Colores: ["negro", "lila", "rosado"]

MENSAJE DEL CLIENTE:

{mensaje_cliente}
"""

    esquema = {
        "type": "object",
        "properties": {
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
            "foto": None
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