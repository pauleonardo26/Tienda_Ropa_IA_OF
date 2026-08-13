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

    datos = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
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

        if "messages" not in valor:

            print("El evento no contiene un mensaje de cliente.")

            return "EVENT_RECEIVED", 200

        mensaje = valor["messages"][0]

        # Meta puede reenviar el mismo webhook. Evitamos responder varias veces.
        mensaje_id = mensaje.get("id")

        if mensaje_id and mensaje_id in MENSAJES_PROCESADOS:
            print("Mensaje duplicado ignorado:", mensaje_id)
            return "EVENT_RECEIVED", 200

        if mensaje_id:
            MENSAJES_PROCESADOS.add(mensaje_id)

        numero_cliente = mensaje.get("from")

        if not numero_cliente:
            numero_cliente = valor.get("metadata", {}).get("display_phone_number")


        print("Número del cliente:", numero_cliente)
        print("Tipo de mensaje:", mensaje["type"])

        if mensaje["type"] != "text":

            print("Por ahora solo procesamos mensajes de texto.")

            return "EVENT_RECEIVED", 200

        texto_cliente = (
            mensaje["text"]["body"]
            .strip()
            .lower()
        )

        print("Texto recibido:", texto_cliente)


        # =================================================
        # CATÁLOGO REAL
        # =================================================

        if texto_cliente in ["catalogo", "catálogo"]:

            producto = obtener_producto_catalogo()

            if not producto:

                enviar_mensaje(
                    numero_cliente,
                    "En este momento no tenemos productos disponibles."
                )

                return "EVENT_RECEIVED", 200


            nombre, precio, talla, color, stock, ruta_foto = producto


            texto_producto = (
                f"🛍️ *{nombre}*\n\n"
                f"💰 Precio: S/ {precio:.2f}\n"
                f"📏 Talla: {talla}\n"
                f"🎨 Color: {color}\n"
                f"📦 Stock disponible: {stock}\n\n"
                f"¿Deseas este producto?"
            )


            if ruta_foto:

                foto_bytes = obtener_foto_r2(
                    ruta_foto
                )

                media_id = subir_foto_meta(
                    foto_bytes
                )

                enviar_imagen(
                    numero_cliente,
                    media_id,
                    texto_producto
                )

                # Finaliza correctamente este webhook para que Meta no lo reintente.
                return "EVENT_RECEIVED", 200

            else:
                # Si no hay foto, enviamos la ficha del producto por texto.
                enviar_mensaje(
                    numero_cliente,
                    texto_producto
                )
                return "EVENT_RECEIVED", 200
            


        # =================================================
        # SALUDO
        # =================================================

        elif texto_cliente in [
            "hola",
            "buenas",
            "buenos dias",
            "buenos días"
        ]:

            enviar_mensaje(
                numero_cliente,
                (
                    "Hola 👋\n\n"
                    "Escribe *catálogo* para conocer "
                    "nuestros productos."
                )
            )

            return "EVENT_RECEIVED", 200


        # =================================================
        # OTROS MENSAJES
        # =================================================

        
        else:
            respuesta_gemini = responder_con_gemini(
                texto_cliente
                )

            enviar_mensaje(
                numero_cliente,
                respuesta_gemini
                )

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
#web https://www.facebook.com/outletvalentinakidsperu