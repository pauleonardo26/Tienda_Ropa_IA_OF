from flask import Flask, request
import requests

app = Flask(__name__)



from config_whatsapp import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_VERIFY_TOKEN
)

ACCESS_TOKEN = WHATSAPP_TOKEN
PHONE_NUMBER_ID = WHATSAPP_PHONE_NUMBER_ID
VERIFY_TOKEN = WHATSAPP_VERIFY_TOKEN
VERIFY_TOKEN = "valentina_token_2026"


def enviar_mensaje(numero_destino, mensaje):

    print("Enviando a:", numero_destino)

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

    print("Código de respuesta:", respuesta.status_code)
    print("Respuesta de WhatsApp:", respuesta.text)


@app.route("/webhook", methods=["GET"])
def verificar_webhook():

    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado correctamente")
        return challenge, 200

    return "Token incorrecto", 403


@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    print("ENTRO AL WEBHOOK POST")

    datos = request.get_json()

    print("\n========== EVENTO RECIBIDO ==========")
    print(datos)

    try:
        valor = datos["entry"][0]["changes"][0]["value"]

        # Solo procesamos eventos que realmente contienen mensajes
        if "messages" not in valor:
            print("El evento no contiene un mensaje de cliente.")
            return "EVENT_RECEIVED", 200

        mensaje = valor["messages"][0]

        numero_cliente = mensaje["from"]

        print("Número del cliente:", numero_cliente)
        print("Tipo de mensaje:", mensaje["type"])

        # Por ahora solo procesamos texto
        if mensaje["type"] != "text":
            print("Por ahora solo procesamos mensajes de texto.")
            return "EVENT_RECEIVED", 200

        texto_cliente = (
            mensaje["text"]["body"]
            .strip()
            .lower()
        )

        print("Texto recibido:", texto_cliente)

        if texto_cliente in ["catalogo", "catálogo"]:

            respuesta = (
                "👋 Bienvenido a Outlet Valentina Kids Perú.\n\n"
                "Tenemos:\n"
                "👕 Ropa para niños\n"
                "👶 Ropa para bebés\n"
                "👧 Accesorios para niñas\n"
                "👟 Zapatillas\n\n"
                "¿Qué producto estás buscando?"
            )

        elif texto_cliente in [
            "hola",
            "buenas",
            "buenos dias",
            "buenos días"
        ]:

            respuesta = (
                "Hola 👋\n\n"
                "Escribe *catálogo* para conocer "
                "nuestros productos."
            )

        else:

            respuesta = (
                "Por ahora escribe *catálogo* "
                "para empezar."
            )

        enviar_mensaje(
            numero_cliente,
            respuesta
        )

    except Exception as error:
        print("Error procesando el mensaje:", error)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(
        port=5001,
        debug=True
    )

# meta 
#3E1XYUHozkyqZzqQDAu7CKbwOzF_6THbSWMuGsk1as7xSHNgD NGROK
#web https://www.facebook.com/outletvalentinakidsperu