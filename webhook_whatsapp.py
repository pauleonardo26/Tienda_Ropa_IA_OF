from flask import Flask, request
import requests
import os
import boto3
from gemini import responder_con_gemini

from dotenv import load_dotenv
from conexion import conexion

from config_whatsapp import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_VERIFY_TOKEN
)

load_dotenv()

app = Flask(__name__)

# Evita procesar dos veces el mismo mensaje si Meta reintenta el webhook.
MENSAJES_PROCESADOS = set()

ACCESS_TOKEN = WHATSAPP_TOKEN
PHONE_NUMBER_ID = WHATSAPP_PHONE_NUMBER_ID
VERIFY_TOKEN = WHATSAPP_VERIFY_TOKEN


# =========================================================
# ENVIAR MENSAJE DE TEXTO
# =========================================================

def enviar_mensaje(numero_destino, mensaje):

    print("Enviando texto a:", numero_destino)

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # =========================================================
    # DESTINATARIO - TELEFONO O BSUID
    # =========================================================

    if str(numero_destino).startswith("PE."):
        destino = {
        "recipient": numero_destino
    }
    else:
        destino = {
        "to": numero_destino
    }

    datos = {
    "messaging_product": "whatsapp",
    **destino,
    "type": "text",
    "text": {
        "body": mensaje
        }
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Código texto:", respuesta.status_code)
    print("Respuesta WhatsApp:", respuesta.text)


# =========================================================
# TARJETA 1 - BIENVENIDA / NIÑO O NIÑA
# =========================================================

def enviar_tarjeta_bienvenida(numero_destino):

    print("Enviando Tarjeta 1 a:", numero_destino)

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # =========================================================
    # DESTINATARIO TARJETA 1 - TELEFONO O BSUID
    # =========================================================

    if str(numero_destino).startswith("PE."):
        destino = {
            "recipient": numero_destino
        }
    else:
        destino = {
            "to": numero_destino
        }

    datos = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "🛍️ OUTLET VALENTINA KIDS"
            },
            "body": {
                "text": (
                    "👋 *¡Bienvenido a Outlet Valentina Kids Perú!*\n\n"
                    "Tenemos prendas para los peques de la casa 💕\n"
                    "¿Qué deseas ver?"
                )
            },
            "footer": {
                "text": "✨ Toca una opción para continuar"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "catalogo_nino",
                            "title": "👦 NIÑO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "catalogo_nina",
                            "title": "👧 NIÑA"
                        }
                    }
                ]
            }
        }
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Código Tarjeta 1:", respuesta.status_code)
    print("Respuesta Tarjeta 1:", respuesta.text)

    respuesta.raise_for_status()

# =========================================================
# TARJETA 2 - ROPA PARA NIÑA
# =========================================================

def enviar_tarjeta_nina(numero_destino):

    print("Enviando Tarjeta 2 - Ropa para niña a:", numero_destino)

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # =========================================================
    # DESTINATARIO TARJETA 2 - TELEFONO O BSUID
    # =========================================================

    if str(numero_destino).startswith("PE."):
        destino = {
            "recipient": numero_destino
        }
    else:
        destino = {
            "to": numero_destino
        }

    datos = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🌸 ROPA PARA NIÑA"
            },
            "body": {
                "text": (
                    "Elige la prenda que deseas ver 💕\n\n"
                    "Tenemos modelos, tallas y colores disponibles."
                )
            },
            "footer": {
                "text": "✨ Toca el botón para ver las opciones"
            },
            "action": {
                "button": "VER PRENDAS 👇",
                "sections": [
                    {
                        "title": "CATÁLOGO NIÑA",
                        "rows": [
                            {
                                "id": "nina_legging",
                                "title": "🌸 LEGGING",
                                "description": "Ver leggings para niña"
                            },
                            {
                                "id": "nina_short",
                                "title": "🩳 SHORT",
                                "description": "Ver shorts para niña"
                            },
                            {
                                "id": "nina_palazo",
                                "title": "👖 PALAZO",
                                "description": "Ver palazos para niña"
                            },
                            {
                                "id": "nina_conjunto",
                                "title": "👗 CONJUNTO",
                                "description": "Ver conjuntos para niña"
                            },
                            {
                                "id": "nina_polo",
                                "title": "👕 POLO",
                                "description": "Ver polos para niña"
                            }
                        ]
                    },
                    {
                        "title": "OTRO CATÁLOGO",
                        "rows": [
                            {
                                "id": "catalogo_nino",
                                "title": "👦 VER NIÑO",
                                "description": "Cambiar al catálogo para niño"
                            }
                        ]
                    }
                ]
            }
        }
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Código Tarjeta 2:", respuesta.status_code)
    print("Respuesta Tarjeta 2:", respuesta.text)

    respuesta.raise_for_status()

# =========================================================
# SUBMENÚ - ROPA PARA NIÑO
# =========================================================

def enviar_tarjeta_nino(numero_destino):

    print("Enviando menú Ropa para niño a:", numero_destino)

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # =========================================================
    # DESTINATARIO SUBMENÚ NIÑO - TELEFONO O BSUID
    # =========================================================

    if str(numero_destino).startswith("PE."):
        destino = {
            "recipient": numero_destino
        }
    else:
        destino = {
            "to": numero_destino
        }

    datos = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "💙 ROPA PARA NIÑO"
            },
            "body": {
                "text": "Elige la prenda que deseas ver 👇"
            },
            "footer": {
                "text": "✨ Toca el botón para continuar"
            },
            "action": {
                "button": "VER PRENDAS 👇",
                "sections": [
                    {
                        "title": "CATÁLOGO NIÑO",
                        "rows": [
                            {
                                "id": "nino_polos",
                                "title": "👕 POLOS",
                                "description": "Ver polos para niño"
                            },
                            {
                                "id": "nino_joggers",
                                "title": "👖 JOGGERS",
                                "description": "Ver joggers para niño"
                            },
                            {
                                "id": "nino_conjunto",
                                "title": "🧢 CONJUNTO",
                                "description": "Ver conjuntos para niño"
                            }
                        ]
                    },
                    {
                        "title": "OTRO CATÁLOGO",
                        "rows": [
                            {
                                "id": "catalogo_nina",
                                "title": "👧 VER NIÑA",
                                "description": "Cambiar al catálogo para niña"
                            }
                        ]
                    }
                ]
            }
        }
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Código menú niño:", respuesta.status_code)
    print("Respuesta menú niño:", respuesta.text)

    respuesta.raise_for_status()

# =========================================================
# TARJETA 3 - LEGGING NIÑA
# =========================================================

def enviar_tarjeta_legging(numero_destino):

    print("Enviando Tarjeta 3 REAL - Legging a:", numero_destino)

    url = f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # =========================================================
    # DESTINATARIO TARJETA 3 - TELEFONO O BSUID
    # =========================================================

    if str(numero_destino).startswith("PE."):
        destino = {
            "recipient": numero_destino
        }
    else:
        destino = {
            "to": numero_destino
        }

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/leggins_nina.png"
    )

    # =========================================================
    # TARJETA 3 - ENVIAR IMAGEN
    # =========================================================

    datos_imagen = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "image",
        "image": {
            "link": imagen_url
        }
    }

    respuesta_imagen = requests.post(
        url,
        headers=headers,
        json=datos_imagen,
        timeout=30
    )

    print("Código imagen Legging:", respuesta_imagen.status_code)
    print("Respuesta imagen Legging:", respuesta_imagen.text)

    respuesta_imagen.raise_for_status()

    # =========================================================
    # TARJETA 3 - BOTONES GRUPO 1
    # =========================================================

    datos_botones_1 = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "🌸 Sigue viendo prendas para niña:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "nina_short",
                            "title": "🩳 SHORT"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "nina_palazo",
                            "title": "👖 PALAZO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "nina_conjunto",
                            "title": "👗 CONJUNTO"
                        }
                    }
                ]
            }
        }
    }

    respuesta_botones_1 = requests.post(
        url,
        headers=headers,
        json=datos_botones_1,
        timeout=30
    )

    print("Código botones 1:", respuesta_botones_1.status_code)
    print("Respuesta botones 1:", respuesta_botones_1.text)

    respuesta_botones_1.raise_for_status()

    # =========================================================
    # TARJETA 3 - BOTONES GRUPO 2
    # =========================================================

    datos_botones_2 = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "🛍️ ¿Qué deseas hacer?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "nina_polo",
                            "title": "👕 POLO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "hacer_pedido",
                            "title": "🛍️ HACER PEDIDO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "catalogo_nino",
                            "title": "👦 VER NIÑO"
                        }
                    }
                ]
            }
        }
    }

    respuesta_botones_2 = requests.post(
        url,
        headers=headers,
        json=datos_botones_2,
        timeout=30
    )

    print("Código botones 2:", respuesta_botones_2.status_code)
    print("Respuesta botones 2:", respuesta_botones_2.text)

    respuesta_botones_2.raise_for_status()

# =========================================================
# CONSULTAR PRODUCTO REAL EN POSTGRESQL
# =========================================================

def obtener_producto_catalogo():

    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT
                p.nombre,
                p.precio,
                v.talla,
                v.color,
                v.stock,
                v.foto
            FROM variantes_producto v
            JOIN productos p
                ON p.id_producto = v.id_producto
            WHERE v.stock > 0
            ORDER BY p.id_producto, v.id_variante
            LIMIT 1
            """
        )

        producto = cursor.fetchone()

        return producto

    finally:
        cursor.close()


# =========================================================
# DESCARGAR FOTO DESDE CLOUDFLARE R2
# =========================================================

def obtener_foto_r2(ruta_foto):

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY")
    )

    respuesta = s3.get_object(
        Bucket=os.getenv("R2_BUCKET_NAME"),
        Key=ruta_foto
    )

    return respuesta["Body"].read()


# =========================================================
# SUBIR FOTO A META
# =========================================================

def subir_foto_meta(foto_bytes):

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/media"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    files = {
        "file": (
            "producto.jpg",
            foto_bytes,
            "image/jpeg"
        )
    }

    data = {
        "messaging_product": "whatsapp",
        "type": "image/jpeg"
    }

    respuesta = requests.post(
        url,
        headers=headers,
        files=files,
        data=data,
        timeout=30
    )

    print("Subida foto Meta:", respuesta.status_code)
    print("Respuesta Meta:", respuesta.text)

    respuesta.raise_for_status()

    return respuesta.json()["id"]


# =========================================================
# ENVIAR FOTO POR WHATSAPP
# =========================================================

def enviar_imagen(numero_destino, media_id, texto):

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    datos = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "image",
        "image": {
            "id": media_id,
            "caption": texto
        }
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Envío imagen:", respuesta.status_code)
    print("Respuesta WhatsApp:", respuesta.text)


# =========================================================
# POLÍTICA DE PRIVACIDAD
# =========================================================

@app.route("/privacidad", methods=["GET"])
def politica_privacidad():

    return """
    <!DOCTYPE html>
    <html lang="es">

    <head>
        <meta charset="UTF-8">
        <title>
            Política de Privacidad - Outlet Valentina Kids Perú
        </title>
    </head>

    <body>

        <h1>Política de Privacidad</h1>

        <p>
        Outlet Valentina Kids Perú utiliza la información
        proporcionada por sus clientes únicamente para atender
        consultas, gestionar pedidos, pagos y entregas.
        </p>

        <p>
        Los datos que pueden solicitarse incluyen nombre,
        número de teléfono, documento de identidad y datos
        necesarios para realizar la entrega del pedido.
        </p>

        <p>
        La información no será vendida ni utilizada para fines
        distintos a la atención y gestión de los pedidos.
        </p>

        <p>
        Los usuarios pueden solicitar información,
        actualización o eliminación de sus datos contactándose
        con Outlet Valentina Kids Perú.
        </p>

        <p>
        Última actualización: agosto de 2026.
        </p>

    </body>

    </html>
    """


# =========================================================
# VERIFICAR WEBHOOK
# =========================================================

@app.route("/webhook", methods=["GET"])
def verificar_webhook():

    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN:

        print("Webhook verificado correctamente")

        return challenge, 200

    return "Token incorrecto", 403


# =========================================================
# RECIBIR MENSAJES DE WHATSAPP
# =========================================================

@app.route("/webhook", methods=["POST"])
def recibir_mensaje():

    print("ENTRO AL WEBHOOK POST")
    datos = request.get_json()
    print("\n========== EVENTO RECIBIDO ==========")
    print(datos)

    try:
        valor = datos["entry"][0]["changes"][0]["value"]

        # =========================================================
        # IGNORAR ESTADOS DE ENTREGA
        # =========================================================
        if "messages" not in valor:
            print("El evento no contiene un mensaje de cliente.")
            return "EVENT_RECEIVED", 200

        mensaje = valor["messages"][0]

        # =========================================================
        # EVITAR MENSAJES DUPLICADOS
        # =========================================================
        mensaje_id = mensaje.get("id")

        if mensaje_id and mensaje_id in MENSAJES_PROCESADOS:
            print("Mensaje duplicado ignorado:", mensaje_id)
            return "EVENT_RECEIVED", 200

        if mensaje_id:
            MENSAJES_PROCESADOS.add(mensaje_id)

        # =========================================================
        # IDENTIFICAR CLIENTE - TELEFONO O BSUID
        # =========================================================
        numero_cliente = mensaje.get("from")
        bsuid_cliente = mensaje.get("from_user")
        contactos = valor.get("contacts", [])

        if contactos:
            contacto = contactos[0]

            if not numero_cliente:
                numero_cliente = contacto.get("wa_id")

            if not bsuid_cliente:
                bsuid_cliente = contacto.get("user_id")

        if numero_cliente:
            cliente_destino = numero_cliente
            tipo_cliente = "telefono"
        elif bsuid_cliente:
            cliente_destino = bsuid_cliente
            tipo_cliente = "bsuid"
        else:
            print("No se pudo identificar al cliente.")
            return "EVENT_RECEIVED", 200

        # =========================================================
        # DESTINATARIO UNIFICADO - TELEFONO O BSUID
        # =========================================================
        numero_cliente = cliente_destino

        print("Cliente destino:", cliente_destino)
        print("Tipo identificador:", tipo_cliente)

        tipo_mensaje = mensaje.get("type")
        print("Tipo de mensaje:", tipo_mensaje)

        # =========================================================
        # RESPUESTA A BOTONES INTERACTIVOS
        # =========================================================
        if tipo_mensaje == "interactive":
            interactive = mensaje.get("interactive", {})
            tipo_interactivo = interactive.get("type")

            # =========================================================
            # BOTONES DIRECTOS
            # =========================================================
            if tipo_interactivo == "button_reply":
                boton = interactive.get("button_reply", {})
                boton_id = boton.get("id", "")
                boton_titulo = boton.get("title", "")
                print("Botón recibido:", boton_id, "-", boton_titulo)

                if boton_id == "catalogo_nina":
                    enviar_tarjeta_nina(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if boton_id == "catalogo_nino":
                    enviar_tarjeta_nino(numero_cliente)
                    return "EVENT_RECEIVED", 200

                respuestas_botones = {
                    "nina_short": "🩳 Elegiste *SHORT*.\n\nPróxima tarjeta a conectar.",
                    "nina_palazo": "👖 Elegiste *PALAZO*.\n\nPróxima tarjeta a conectar.",
                    "nina_conjunto": "👗 Elegiste *CONJUNTO*.\n\nPróxima tarjeta a conectar.",
                    "nina_polo": "👕 Elegiste *POLO*.\n\nPróxima tarjeta a conectar."
                }

                if boton_id in respuestas_botones:
                    enviar_mensaje(numero_cliente, respuestas_botones[boton_id])
                    return "EVENT_RECEIVED", 200

                if boton_id == "hacer_pedido":
                    enviar_mensaje(
                        numero_cliente,
                        "🛍️ *HACER MI PEDIDO*\n\n"
                        "Escríbeme todo lo que deseas pedir en un solo mensaje.\n\n"
                        "Ejemplo:\n"
                        "3 leggings negros talla 8 y 2 polos talla 10."
                    )
                    return "EVENT_RECEIVED", 200

            # =========================================================
            # LISTAS INTERACTIVAS
            # =========================================================
            if tipo_interactivo == "list_reply":
                opcion = interactive.get("list_reply", {})
                opcion_id = opcion.get("id", "")
                opcion_titulo = opcion.get("title", "")
                print("Opción recibida:", opcion_id, "-", opcion_titulo)

                if opcion_id == "nina_legging":
                    enviar_tarjeta_legging(numero_cliente)
                    return "EVENT_RECEIVED", 200

                respuestas = {
                    "nina_short": "🩳 Elegiste *SHORT*.\n\nPróxima tarjeta a conectar.",
                    "nina_palazo": "👖 Elegiste *PALAZO*.\n\nPróxima tarjeta a conectar.",
                    "nina_conjunto": "👗 Elegiste *CONJUNTO*.\n\nPróxima tarjeta a conectar.",
                    "nina_polo": "👕 Elegiste *POLO*.\n\nPróxima tarjeta a conectar.",
                    "nino_polos": "👕 Elegiste *POLOS DE NIÑO*.\n\nPróxima tarjeta a conectar.",
                    "nino_joggers": "👖 Elegiste *JOGGERS DE NIÑO*.\n\nPróxima tarjeta a conectar.",
                    "nino_conjunto": "🧢 Elegiste *CONJUNTO DE NIÑO*.\n\nPróxima tarjeta a conectar."
                }

                if opcion_id in respuestas:
                    enviar_mensaje(numero_cliente, respuestas[opcion_id])
                    return "EVENT_RECEIVED", 200

                if opcion_id == "catalogo_nino":
                    enviar_tarjeta_nino(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "catalogo_nina":
                    enviar_tarjeta_nina(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "hacer_pedido":
                    enviar_mensaje(
                        numero_cliente,
                        "🛍️ *HACER MI PEDIDO*\n\n"
                        "Escríbeme todo lo que deseas pedir en un solo mensaje.\n\n"
                        "Ejemplo:\n"
                        "3 leggings negros talla 8 y 2 polos talla 10."
                    )
                    return "EVENT_RECEIVED", 200

            print("Interacción no reconocida.")
            return "EVENT_RECEIVED", 200

        # =========================================================
        # MENSAJES QUE NO SON TEXTO
        # =========================================================
        if tipo_mensaje != "text":
            print("Tipo de mensaje todavía no procesado:", tipo_mensaje)
            return "EVENT_RECEIVED", 200

        # =========================================================
        # LEER TEXTO DEL CLIENTE
        # =========================================================
        texto_cliente = mensaje["text"]["body"].strip().lower()
        print("Texto recibido:", texto_cliente)

        # =========================================================
        # CATÁLOGO REAL
        # =========================================================

        if texto_cliente in ["catalogo", "catálogo"]:
            enviar_tarjeta_bienvenida(numero_cliente)
            return "EVENT_RECEIVED", 200

        # =========================================================
        # SALUDO
        # =========================================================
        elif texto_cliente in ["hola", "buenas", "buenos dias", "buenos días"]:
            enviar_mensaje(
                numero_cliente,
                "Hola 👋\n\nEscribe *catálogo* para conocer nuestros productos."
            )
            return "EVENT_RECEIVED", 200

        # =========================================================
        # OTROS MENSAJES - GEMINI
        # =========================================================
        else:
            respuesta_gemini = responder_con_gemini(texto_cliente)
            enviar_mensaje(numero_cliente, respuesta_gemini)
            return "EVENT_RECEIVED", 200

    except Exception as error:
        print("Error procesando el mensaje:", error)
        return "EVENT_RECEIVED", 200


# =========================================================
# INICIAR FLASK
# =========================================================

if __name__ == "__main__":

    print("Token cargado:", bool(ACCESS_TOKEN))
    print("Phone ID:", PHONE_NUMBER_ID)
    print("Verify token:", VERIFY_TOKEN)

    app.run(
        port=5002,
        debug=False
    )



# meta 
#3E1XYUHozkyqZzqQDAu7CKbwOzF_6THbSWMuGsk1as7xSHNgD NGROK
#web https://www.facebook.com/outletvalentinakidsperufrom flask import Flask, request
