import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types
from conexion import conexion

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

cliente = genai.Client(
    api_key=GEMINI_API_KEY
)


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


def responder_con_gemini(mensaje_cliente):

    inventario = consultar_inventario()

    if not inventario:
        return {
            "encontrado": False,
            "respuesta": "En este momento no tenemos productos disponibles.",
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
- Si encuentras exactamente o razonablemente el producto solicitado,
  devuelve encontrado=true.
- Si no existe, devuelve encontrado=false.
- Si encuentras un producto, devuelve exactamente su valor de Foto.
- Si no encuentras producto o no hay foto, devuelve foto="".
- La respuesta al cliente debe ser breve y directa.
- Máximo 3 líneas.

INVENTARIO REAL:

{inventario_texto}

MENSAJE DEL CLIENTE:

{mensaje_cliente}
"""

    respuesta = cliente.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
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
        )
    )

    datos = json.loads(respuesta.text)

    return datos