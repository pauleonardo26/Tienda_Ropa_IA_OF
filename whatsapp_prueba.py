import requests

from config_whatsapp import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID
)

DESTINATARIO = "51932913446"

url = (
    f"https://graph.facebook.com/v26.0/"
    f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

headers = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}

mensaje = "Hola Paul, este mensaje fue enviado desde Python."

datos = {
    "messaging_product": "whatsapp",
    "to": DESTINATARIO,
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

print("Código:", respuesta.status_code)
print("Respuesta:", respuesta.text)