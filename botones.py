# =========================================================
# botones.py
# Control central de botones WhatsApp
# =========================================================

import requests

from config_whatsapp import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID
)


# =========================================================
# BOTONES ACTIVOS POR CLIENTE
# =========================================================
#
# Aquí guardamos únicamente los botones que pueden
# utilizarse actualmente.
#
# Si el cliente pulsa un botón viejo que ya no está
# registrado aquí, será rechazado por el webhook.
#
# Ejemplo:
#
# {
#     "51999999999": {
#         "continuar_pedido",
#         "finalizar_pedido"
#     }
# }
#
# =========================================================

BOTONES_ACTIVOS_CLIENTES = {}


# =========================================================
# OBTENER DESTINO WHATSAPP
# =========================================================

def obtener_destino_whatsapp(numero_destino):
    """
    WhatsApp puede entregar identificadores que comienzan
    con PE. o números telefónicos normales.
    """

    if str(numero_destino).startswith("PE."):
        return {
            "recipient": numero_destino
        }

    return {
        "to": numero_destino
    }


# =========================================================
# REGISTRAR BOTONES ACTIVOS
# =========================================================

def registrar_botones_activos(numero_cliente, botones):
    """
    Reemplaza los botones activos anteriores del cliente
    por los nuevos botones.

    Esto es importante para bloquear botones antiguos.
    """

    if not numero_cliente:
        return

    BOTONES_ACTIVOS_CLIENTES[numero_cliente] = set(botones)


# =========================================================
# AGREGAR BOTONES ACTIVOS
# =========================================================

def agregar_botones_activos(numero_cliente, botones):
    """
    Agrega botones sin borrar los que ya están activos.

    Se utiliza cuando una tarjeta envía varios grupos
    de botones y todos deben seguir siendo válidos.
    """

    if not numero_cliente:
        return

    actuales = BOTONES_ACTIVOS_CLIENTES.setdefault(
        numero_cliente,
        set()
    )

    actuales.update(botones)


# =========================================================
# INVALIDAR TODOS LOS BOTONES
# =========================================================

def invalidar_botones(numero_cliente):
    """
    Bloquea todos los botones anteriores del cliente.
    """

    if not numero_cliente:
        return

    BOTONES_ACTIVOS_CLIENTES.pop(
        numero_cliente,
        None
    )


# =========================================================
# COMPROBAR SI UN BOTÓN SIGUE ACTIVO
# =========================================================

def boton_esta_activo(numero_cliente, boton_id):
    """
    Devuelve True únicamente si el botón todavía
    pertenece a la etapa actual del pedido.
    """

    if not numero_cliente or not boton_id:
        return False

    botones = BOTONES_ACTIVOS_CLIENTES.get(
        numero_cliente,
        set()
    )

    return boton_id in botones


# =========================================================
# CONSUMIR UN BOTÓN
# =========================================================

def consumir_boton(numero_cliente, boton_id):
    """
    Elimina un botón después de utilizarlo.

    Se utiliza para evitar que el mismo botón pueda
    ejecutarse repetidamente.
    """

    if not numero_cliente or not boton_id:
        return

    botones = BOTONES_ACTIVOS_CLIENTES.get(
        numero_cliente
    )

    if not botones:
        return

    botones.discard(boton_id)

    if not botones:
        BOTONES_ACTIVOS_CLIENTES.pop(
            numero_cliente,
            None
        )


# =========================================================
# ENVIAR BOTONES CONTINUAR / FINALIZAR
# =========================================================

def enviar_botones_continuar_finalizar(numero_destino):

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        **obtener_destino_whatsapp(numero_destino),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "¿Qué deseas hacer con tu pedido?"
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "continuar_pedido",
                            "title": "➕ CONTINUAR PEDIDO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "finalizar_pedido",
                            "title": "✅ FINALIZAR PEDIDO"
                        }
                    }
                ]
            }
        }
    }

    try:

        respuesta = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )

        print(
            "BOTONES CONTINUAR/FINALIZAR:",
            respuesta.status_code,
            respuesta.text
        )

        # Registrar únicamente estos botones.
        registrar_botones_activos(
            numero_cliente=numero_destino,
            botones=[
                "continuar_pedido",
                "finalizar_pedido"
            ]
        )

        return respuesta

    except Exception as e:

        print(
            "ERROR ENVIANDO BOTONES CONTINUAR/FINALIZAR:",
            e
        )

        return None


# =========================================================
# ENVIAR BOTONES DE CONFIRMACIÓN
# =========================================================

def enviar_botones_confirmacion(numero_destino):

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        **obtener_destino_whatsapp(numero_destino),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "Revisa tu pedido antes de continuar:"
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "confirmar_pedido",
                            "title": "✅ CONFIRMAR PEDIDO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "corregir_pedido",
                            "title": "✏️ CORREGIR PEDIDO"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "cancelar_pedido",
                            "title": "❌ CANCELAR PEDIDO"
                        }
                    }
                ]
            }
        }
    }

    try:

        respuesta = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )

        print(
            "BOTONES CONFIRMACIÓN:",
            respuesta.status_code,
            respuesta.text
        )

        registrar_botones_activos(
            numero_cliente=numero_destino,
            botones=[
                "confirmar_pedido",
                "corregir_pedido",
                "cancelar_pedido"
            ]
        )

        return respuesta

    except Exception as e:

        print(
            "ERROR ENVIANDO BOTONES CONFIRMACIÓN:",
            e
        )

        return None


# =========================================================
# BOTÓN CORREGIR PAGO
# =========================================================
#
# Se conserva por compatibilidad con el código existente.
# No debe utilizarse en el nuevo flujo de pago salvo que
# posteriormente decidamos activarlo.
#
# =========================================================

def enviar_boton_corregir_pago(numero_destino):

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        **obtener_destino_whatsapp(numero_destino),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "Si necesitas corregir tu pedido,"
                    " puedes hacerlo antes de confirmar."
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "corregir_pedido",
                            "title": "✏️ CORREGIR PEDIDO"
                        }
                    }
                ]
            }
        }
    }

    try:

        respuesta = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )

        print(
            "BOTÓN CORREGIR PAGO:",
            respuesta.status_code,
            respuesta.text
        )

        registrar_botones_activos(
            numero_cliente=numero_destino,
            botones=[
                "corregir_pedido"
            ]
        )

        return respuesta

    except Exception as e:

        print(
            "ERROR ENVIANDO BOTÓN CORREGIR PAGO:",
            e
        )

        return None
