# =========================================================
# 01 - IMPORTACIONES
# =========================================================

import os
import json
import time

from dotenv import load_dotenv
from openai import OpenAI

from prompts import construir_prompt_pedido


# =========================================================
# 02 - CONFIGURACION OPENAI
# =========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

cliente = OpenAI(
    api_key=OPENAI_API_KEY
)


# =========================================================
# 20 - GENERAR CON REINTENTOS
# =========================================================

def generar_con_reintentos(
    prompt,
    esquema,
    max_intentos=3
):

    for intento in range(1, max_intentos + 1):

        try:

            print(
                f"Intento OpenAI {intento} de {max_intentos}"
            )

            respuesta = cliente.responses.create(
                model="gpt-5.6-luna",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "pedido_interpretado",
                        "strict": True,
                        "schema": esquema
                    }
                }
            )

            return json.loads(
                respuesta.output_text
            )

        except Exception as error:

            texto_error = str(error)

            print(
                f"Error OpenAI intento {intento}:",
                texto_error
            )

            es_temporal = (
                "429" in texto_error
                or "500" in texto_error
                or "502" in texto_error
                or "503" in texto_error
                or "504" in texto_error
                or "rate limit" in texto_error.lower()
                or "temporarily" in texto_error.lower()
            )

            if not es_temporal:

                raise

            if intento < max_intentos:

                segundos = intento * 2

                print(
                    f"OpenAI temporalmente no disponible. "
                    f"Reintentando en {segundos} segundos..."
                )

                time.sleep(segundos)

    return None


# =========================================================
# 21 - INTERPRETAR PEDIDO DEL CLIENTE CON OPENAI
# =========================================================

def interpretar_pedido(
    mensaje_cliente,
    producto_seleccionado=None
):

    prompt = construir_prompt_pedido(
        mensaje_cliente
    )

    # -----------------------------------------------------
    # 21.1 - PRODUCTO DEFINIDO DESDE LA TARJETA
    # -----------------------------------------------------

    if producto_seleccionado:

        prompt += f"""

=========================================================
PRODUCTO YA SELECCIONADO DESDE LA TARJETA DEL CATÁLOGO
=========================================================

El cliente ya seleccionó previamente este producto:

PRODUCTO:
{producto_seleccionado}

IMPORTANTE:

- NO necesitas identificar el producto.
- NO cambies el producto seleccionado.
- NO inventes otro producto.
- El producto seleccionado por la tarjeta es definitivo.
- El mensaje del cliente contiene únicamente los datos
  que necesita el pedido: cantidad, talla y color.
- Interpreta correctamente cantidades, tallas y colores.
- Si el cliente escribe solamente:
  "1 talla 4 negro"
  debes entender:
  cantidad = 1
  talla = 4
  color = negro
  producto = {producto_seleccionado}

- Si escribe:
  "2 talla 4 y 6 negro y verde"
  debes interpretar las cantidades, tallas y colores
  según correspondan al pedido.

- Si escribe:
  "uno talla 4 verde"
  debes interpretar:
  cantidad = 1
  talla = 4
  color = verde
  producto = {producto_seleccionado}

El campo "producto" de TODOS los elementos de
"productos" debe ser exactamente:

{producto_seleccionado}
"""

    # =====================================================
    # 21.2 - ESQUEMA DE RESPUESTA
    # =====================================================

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
                    ],

                    "additionalProperties": False
                }
            }

        },

        "required": [
            "es_pedido",
            "productos"
        ],

        "additionalProperties": False
    }

    # =====================================================
    # 21.3 - LLAMAR A OPENAI
    # =====================================================

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

    # =====================================================
    # 21.4 - FORZAR PRODUCTO DE LA TARJETA
    # =====================================================

    if producto_seleccionado:

        for item in datos.get(
            "productos",
            []
        ):

            item["producto"] = (
                producto_seleccionado
            )

        print(
            "Producto definido por tarjeta:",
            producto_seleccionado
        )

    datos["error_temporal"] = False

    print(
        "Pedido interpretado por OpenAI:",
        datos
    )

    return datos
