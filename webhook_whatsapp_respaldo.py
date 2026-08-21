from flask import Flask, request
import requests
import os
import boto3
from gemini import (
    responder_con_gemini,
    interpretar_pedido
)

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

# =========================================================
# 01 - ESTADO DE CONVERSACION DE CADA CLIENTE
# =========================================================

ESTADO_CLIENTES = {}

ACCESS_TOKEN = WHATSAPP_TOKEN
PHONE_NUMBER_ID = WHATSAPP_PHONE_NUMBER_ID
VERIFY_TOKEN = WHATSAPP_VERIFY_TOKEN


# =========================================================
# 02 - DESTINATARIO WHATSAPP - TELEFONO O BSUID
# =========================================================

def obtener_destino_whatsapp(numero_destino):

    if str(numero_destino).startswith("PE."):
        return {"recipient": numero_destino}

    return {"to": numero_destino}



# =========================================================
# 03 - ENVIAR MENSAJE DE TEXTO
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

    destino = obtener_destino_whatsapp(numero_destino)

    datos = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "text",
        "text": {"body": mensaje}
    }

    respuesta = requests.post(
        url,
        headers=headers,
        json=datos,
        timeout=30
    )

    print("Código texto:", respuesta.status_code)
    print("Respuesta WhatsApp:", respuesta.text)
    respuesta.raise_for_status()

# =========================================================
# 04 - TARJETA 1 - BIENVENIDA / NIÑO O NIÑA
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

    destino = obtener_destino_whatsapp(numero_destino)

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
# 05 - TARJETA 2 - ROPA PARA NIÑA
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

    destino = obtener_destino_whatsapp(numero_destino)

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
                                "id": "nina_polo_mc_pequeno",
                                "title": "👕 POLO M/C PEQUEÑO",
                                "description": "Ver polo manga corta pequeño"
                            },
                            {
                                "id": "nina_polo_mc_grande",
                                "title": "👕 POLO M/C GRANDE",
                                "description": "Ver polo manga corta grande"
                            },
                            {
                                "id": "nina_polo_ml_pequeno",
                                "title": "👚 POLO M/L PEQUEÑO",
                                "description": "Ver polo manga larga pequeño"
                            },
                            {
                                "id": "nina_polo_ml_grande",
                                "title": "👚 POLO M/L GRANDE",
                                "description": "Ver polo manga larga grande"
                            }
                        ]
                    },
                    {
                        "title": "OTRAS OPCIONES",
                        "rows": [
                            {
                                "id": "catalogo_nino",
                                "title": "👦 VER NIÑO",
                                "description": "Cambiar al catálogo para niño"
                            },
                            {
                                "id": "hacer_pedido",
                                "title": "🛍️ HACER PEDIDO",
                                "description": "Continuar con mi pedido"
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
# 06 - SUBMENÚ - ROPA PARA NIÑO
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

    destino = obtener_destino_whatsapp(numero_destino)

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
                        "title": "OTRAS OPCIONES",
                        "rows": [
                            {
                                "id": "catalogo_nina",
                                "title": "👧 VER NIÑA",
                                "description": "Cambiar al catálogo para niña"
                            },
                            {
                                "id": "hacer_pedido",
                                "title": "🛍️ HACER PEDIDO",
                                "description": "Continuar con mi pedido"
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
# 07 - FUNCIÓN BASE - TARJETA DE PRODUCTO NIÑA
# =========================================================

def enviar_tarjeta_producto_nina(numero_destino, nombre_producto, imagen_url, opciones):

    print("Enviando tarjeta de producto:", nombre_producto, "a:", numero_destino)

    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    destino = obtener_destino_whatsapp(numero_destino)

    datos_imagen = {
        "messaging_product": "whatsapp",
        **destino,
        "type": "image",
        "image": {"link": imagen_url}
    }

    respuesta_imagen = requests.post(
        url,
        headers=headers,
        json=datos_imagen,
        timeout=30
    )

    print("Código imagen:", respuesta_imagen.status_code)
    print("Respuesta imagen:", respuesta_imagen.text)
    respuesta_imagen.raise_for_status()

    grupos = [opciones[:3], opciones[3:6]]

    for indice, grupo in enumerate(grupos, start=1):

        if not grupo:
            continue

        datos_botones = {
            "messaging_product": "whatsapp",
            **destino,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "🌸 Sigue viendo prendas para niña:"
                        if indice == 1
                        else "🛍️ ¿Qué deseas hacer?"
                    )
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": opcion["id"],
                                "title": opcion["title"]
                            }
                        }
                        for opcion in grupo
                    ]
                }
            }
        }

        respuesta_botones = requests.post(
            url,
            headers=headers,
            json=datos_botones,
            timeout=30
        )

        print(
            f"Código botones grupo {indice}:",
            respuesta_botones.status_code
        )
        print(
            f"Respuesta botones grupo {indice}:",
            respuesta_botones.text
        )
        respuesta_botones.raise_for_status()


# =========================================================
# 08 - TARJETA 3 - LEGGING NIÑA
# =========================================================

def enviar_tarjeta_legging(numero_destino):

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/leggins_nina.png"
    )

    opciones = [
        {"id": "nina_polo_mc_pequeno", "title": "👕 M/C PEQUEÑO"},
        {"id": "nina_polo_mc_grande", "title": "👕 M/C GRANDE"},
        {"id": "nina_polo_ml_pequeno", "title": "👚 M/L PEQUEÑO"},
        {"id": "nina_polo_ml_grande", "title": "👚 M/L GRANDE"},
        {"id": "hacer_pedido", "title": "🛍️ HACER PEDIDO"},
        {"id": "catalogo_nino", "title": "👦 VER NIÑO"}
    ]

    enviar_tarjeta_producto_nina(
        numero_destino,
        "Legging Niña",
        imagen_url,
        opciones
    )


# =========================================================
# 09 - TARJETA 3 - POLO NIÑA MANGA CORTA PEQUEÑO
# =========================================================

def enviar_polo_mc_pequeno(numero_destino):

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/polo_nina_manga_corta_pequeno.png"
    )

    opciones = [
        {"id": "nina_legging", "title": "🌸 LEGGING"},
        {"id": "nina_polo_mc_grande", "title": "👕 M/C GRANDE"},
        {"id": "nina_polo_ml_pequeno", "title": "👚 M/L PEQUEÑO"},
        {"id": "nina_polo_ml_grande", "title": "👚 M/L GRANDE"},
        {"id": "hacer_pedido", "title": "🛍️ HACER PEDIDO"},
        {"id": "catalogo_nino", "title": "👦 VER NIÑO"}
    ]

    enviar_tarjeta_producto_nina(
        numero_destino,
        "Polo Niña Manga Corta Pequeño",
        imagen_url,
        opciones
    )


# =========================================================
# 10 - TARJETA 3 - POLO NIÑA MANGA CORTA GRANDE
# =========================================================

def enviar_polo_mc_grande(numero_destino):

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/polo_nina_manga_corta_grande.png"
    )

    opciones = [
        {"id": "nina_legging", "title": "🌸 LEGGING"},
        {"id": "nina_polo_mc_pequeno", "title": "👕 M/C PEQUEÑO"},
        {"id": "nina_polo_ml_pequeno", "title": "👚 M/L PEQUEÑO"},
        {"id": "nina_polo_ml_grande", "title": "👚 M/L GRANDE"},
        {"id": "hacer_pedido", "title": "🛍️ HACER PEDIDO"},
        {"id": "catalogo_nino", "title": "👦 VER NIÑO"}
    ]

    enviar_tarjeta_producto_nina(
        numero_destino,
        "Polo Niña Manga Corta Grande",
        imagen_url,
        opciones
    )


# =========================================================
# 11 - TARJETA 3 - POLO NIÑA MANGA LARGA PEQUEÑO
# =========================================================

def enviar_polo_ml_pequeno(numero_destino):

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/polo_nina_manga_larga_pequeno.png"
    )

    opciones = [
        {"id": "nina_legging", "title": "🌸 LEGGING"},
        {"id": "nina_polo_mc_pequeno", "title": "👕 M/C PEQUEÑO"},
        {"id": "nina_polo_mc_grande", "title": "👕 M/C GRANDE"},
        {"id": "nina_polo_ml_grande", "title": "👚 M/L GRANDE"},
        {"id": "hacer_pedido", "title": "🛍️ HACER PEDIDO"},
        {"id": "catalogo_nino", "title": "👦 VER NIÑO"}
    ]

    enviar_tarjeta_producto_nina(
        numero_destino,
        "Polo Niña Manga Larga Pequeño",
        imagen_url,
        opciones
    )


# =========================================================
# 12 - TARJETA 3 - POLO NIÑA MANGA LARGA GRANDE
# =========================================================

def enviar_polo_ml_grande(numero_destino):

    imagen_url = (
        "https://pub-9aa04db1bd594751a5b8fb2654da15fd.r2.dev/"
        "productos/polo_nina_manga_larga_grande.png"
    )

    opciones = [
        {"id": "nina_legging", "title": "🌸 LEGGING"},
        {"id": "nina_polo_mc_pequeno", "title": "👕 M/C PEQUEÑO"},
        {"id": "nina_polo_mc_grande", "title": "👕 M/C GRANDE"},
        {"id": "nina_polo_ml_pequeno", "title": "👚 M/L PEQUEÑO"},
        {"id": "hacer_pedido", "title": "🛍️ HACER PEDIDO"},
        {"id": "catalogo_nino", "title": "👦 VER NIÑO"}
    ]

    enviar_tarjeta_producto_nina(
        numero_destino,
        "Polo Niña Manga Larga Grande",
        imagen_url,
        opciones
    )

# =========================================================
# 13 - CONSULTAR PRODUCTO REAL EN POSTGRESQL
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
# 14 - DESCARGAR FOTO DESDE CLOUDFLARE R2
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
# 15 - SUBIR FOTO A META
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
# 16 - ENVIAR FOTO POR WHATSAPP
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

    destino = obtener_destino_whatsapp(numero_destino)

    datos = {
        "messaging_product": "whatsapp",
        **destino,
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
    respuesta.raise_for_status()

# =========================================================
# 17 - POLÍTICA DE PRIVACIDAD
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
# 18 - VERIFICAR WEBHOOK
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
# 22 - VALIDAR PEDIDO CONTRA POSTGRESQL
# =========================================================

def validar_pedido_postgresql(pedido_interpretado):

    productos_pedido = pedido_interpretado.get("productos", [])

    resultado = []
    errores = []
    total = 0

    # ---------------------------------------------------------
    # NOMBRES QUE GEMINI PUEDE USAR -> NOMBRE REAL POSTGRESQL
    # ---------------------------------------------------------

    mapa_productos = {
        "legging": "Leggins Niña",
        "leggins": "Leggins Niña",
        "leggings": "Leggins Niña",

        "polo manga corta pequeño":
            "Polo Niña Manga Corta Pequeño",

        "polo manga corta grande":
            "Polo Niña Manga Corta Grande",

        "polo manga larga pequeño":
            "Polo Niña Manga Larga Pequeño",

        "polo manga larga grande":
            "Polo Niña Manga Larga Grande"
    }

    cursor = conexion.cursor()

    try:

        for item in productos_pedido:

            producto_gemini = (
                item.get("producto", "")
                .strip()
                .lower()
            )

            cantidad = item.get("cantidad", 0)
            talla = str(item.get("talla", "")).strip()

            colores = item.get("colores", [])

            nombre_real = mapa_productos.get(
                producto_gemini
            )

            # =================================================
            # 22.1 - PRODUCTO NO RECONOCIDO
            # =================================================

            if not nombre_real:

                errores.append(
                    f"❌ No reconocí el producto: "
                    f"{producto_gemini}"
                )

                continue

            # =================================================
            # 22.2 - BUSCAR VARIANTES DEL PRODUCTO Y TALLA
            # =================================================

            cursor.execute(
                """
                SELECT
                    v.id_variante,
                    v.talla,
                    v.color,
                    v.stock,
                    v.precio
                FROM variantes_producto v
                JOIN productos p
                    ON p.id_producto = v.id_producto
                WHERE LOWER(p.nombre) = LOWER(%s)
                  AND v.talla = %s
                """,
                (
                    nombre_real,
                    talla
                )
            )

            variantes = cursor.fetchall()

            # =================================================
            # 22.3 - TALLA NO EXISTE
            # =================================================

            if not variantes:

                cursor.execute(
                    """
                    SELECT DISTINCT v.talla
                    FROM variantes_producto v
                    JOIN productos p
                        ON p.id_producto = v.id_producto
                    WHERE LOWER(p.nombre) = LOWER(%s)
                    ORDER BY v.talla
                    """,
                    (nombre_real,)
                )

                tallas = [
                    fila[0]
                    for fila in cursor.fetchall()
                ]

                errores.append(
                    f"⚠️ {nombre_real}: "
                    f"no existe talla {talla}. "
                    f"Tallas disponibles: "
                    f"{', '.join(tallas)}"
                )

                continue

            # =================================================
            # 22.4 - PRODUCTOS CON COLOR SURTIDO
            # =================================================

            variante_surtida = None

            for variante in variantes:

                if variante[2].lower() == "surtido":
                    variante_surtida = variante
                    break

            if variante_surtida:

                (
                    id_variante,
                    talla_db,
                    color_db,
                    stock_db,
                    precio_db
                ) = variante_surtida

                if stock_db < cantidad:

                    errores.append(
                        f"⚠️ {nombre_real} talla {talla}: "
                        f"solo quedan {stock_db} unidades."
                    )

                    continue

                subtotal = float(precio_db) * cantidad
                total += subtotal

                resultado.append(
                    {
                        "id_variante": id_variante,
                        "producto": nombre_real,
                        "cantidad": cantidad,
                        "talla": talla,
                        "color": "Surtido",
                        "colores_pedidos": colores,
                        "precio": float(precio_db),
                        "subtotal": subtotal
                    }
                )

                continue

            # =================================================
            # 22.5 - PRODUCTOS CON COLORES REALES
            # =================================================

            colores_db = {
                variante[2].lower(): variante
                for variante in variantes
            }

            if not colores:

                errores.append(
                    f"⚠️ Falta indicar color para "
                    f"{nombre_real} talla {talla}."
                )

                continue

            cantidad_por_color = max(
                1,
                cantidad // len(colores)
            )

            for color in colores:

                color_normalizado = color.lower()

                if color_normalizado not in colores_db:

                    disponibles = ", ".join(
                        variante[2]
                        for variante in variantes
                    )

                    errores.append(
                        f"⚠️ {nombre_real} talla {talla}: "
                        f"no tenemos color {color}. "
                        f"Disponibles: {disponibles}"
                    )

                    continue

                variante = colores_db[color_normalizado]

                (
                    id_variante,
                    talla_db,
                    color_db,
                    stock_db,
                    precio_db
                ) = variante

                if stock_db < cantidad_por_color:

                    errores.append(
                        f"⚠️ {nombre_real} talla {talla} "
                        f"color {color_db}: "
                        f"solo quedan {stock_db} unidades."
                    )

                    continue

                subtotal = (
                    float(precio_db)
                    * cantidad_por_color
                )

                total += subtotal

                resultado.append(
                    {
                        "id_variante": id_variante,
                        "producto": nombre_real,
                        "cantidad": cantidad_por_color,
                        "talla": talla,
                        "color": color_db,
                        "precio": float(precio_db),
                        "subtotal": subtotal
                    }
                )

        return {
            "productos": resultado,
            "errores": errores,
            "total": round(total, 2)
        }

    finally:

        cursor.close()

# =========================================================
# 19 - RECIBIR MENSAJES DE WHATSAPP
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
        # 19.1 - IGNORAR ESTADOS DE ENTREGA
        # =========================================================
        if "messages" not in valor:
            print("El evento no contiene un mensaje de cliente.")
            return "EVENT_RECEIVED", 200

        mensaje = valor["messages"][0]

        # =========================================================
        # 19.2 - EVITAR MENSAJES DUPLICADOS
        # =========================================================
        mensaje_id = mensaje.get("id")

        if mensaje_id and mensaje_id in MENSAJES_PROCESADOS:
            print("Mensaje duplicado ignorado:", mensaje_id)
            return "EVENT_RECEIVED", 200

        if mensaje_id:
            MENSAJES_PROCESADOS.add(mensaje_id)

        # =========================================================
        # 19.3 - IDENTIFICAR CLIENTE - TELEFONO O BSUID
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

        numero_cliente = cliente_destino

        print("Cliente destino:", cliente_destino)
        print("Tipo identificador:", tipo_cliente)

        tipo_mensaje = mensaje.get("type")
        print("Tipo de mensaje:", tipo_mensaje)

        # =========================================================
        # 19.4 - RESPUESTA A BOTONES INTERACTIVOS
        # =========================================================
        if tipo_mensaje == "interactive":

            interactive = mensaje.get("interactive", {})
            tipo_interactivo = interactive.get("type")

            # =========================================================
            # 19.5 - BOTONES DIRECTOS
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

                if boton_id == "nina_legging":
                    enviar_tarjeta_legging(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if boton_id == "nina_polo_mc_pequeno":
                    enviar_polo_mc_pequeno(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if boton_id == "nina_polo_mc_grande":
                    enviar_polo_mc_grande(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if boton_id == "nina_polo_ml_pequeno":
                    enviar_polo_ml_pequeno(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if boton_id == "nina_polo_ml_grande":
                    enviar_polo_ml_grande(numero_cliente)
                    return "EVENT_RECEIVED", 200

                # =========================================================
                # 19.5.1 - HACER PEDIDO DESDE BOTON
                # =========================================================
                if boton_id == "hacer_pedido":

                    ESTADO_CLIENTES[numero_cliente] = "esperando_pedido"

                    enviar_mensaje(
                        numero_cliente,
                        (
                            "🛍️ *HACER MI PEDIDO*\n\n"
                            "Escríbeme todo lo que deseas pedir en un solo mensaje.\n\n"
                            "Ejemplo:\n"
                            "3 leggings negros talla 8 y 2 polos manga corta talla 4."
                        )
                    )

                    return "EVENT_RECEIVED", 200

            # =========================================================
            # 19.6 - LISTAS INTERACTIVAS
            # =========================================================
            if tipo_interactivo == "list_reply":

                opcion = interactive.get("list_reply", {})
                opcion_id = opcion.get("id", "")
                opcion_titulo = opcion.get("title", "")

                print("Opción recibida:", opcion_id, "-", opcion_titulo)

                if opcion_id == "nina_legging":
                    enviar_tarjeta_legging(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "nina_polo_mc_pequeno":
                    enviar_polo_mc_pequeno(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "nina_polo_mc_grande":
                    enviar_polo_mc_grande(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "nina_polo_ml_pequeno":
                    enviar_polo_ml_pequeno(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "nina_polo_ml_grande":
                    enviar_polo_ml_grande(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "catalogo_nino":
                    enviar_tarjeta_nino(numero_cliente)
                    return "EVENT_RECEIVED", 200

                if opcion_id == "catalogo_nina":
                    enviar_tarjeta_nina(numero_cliente)
                    return "EVENT_RECEIVED", 200

                # =========================================================
                # 19.6.1 - HACER PEDIDO DESDE LISTA
                # =========================================================
                if opcion_id == "hacer_pedido":

                    ESTADO_CLIENTES[numero_cliente] = "esperando_pedido"

                    enviar_mensaje(
                        numero_cliente,
                        (
                            "🛍️ *HACER MI PEDIDO*\n\n"
                            "Escríbeme todo lo que deseas pedir en un solo mensaje.\n\n"
                            "Ejemplo:\n"
                            "3 leggings negros talla 8 y 2 polos manga corta talla 4."
                        )
                    )

                    return "EVENT_RECEIVED", 200

                respuestas_nino = {
                    "nino_polos": "👕 Elegiste *POLOS DE NIÑO*.\n\nPróxima tarjeta a conectar.",
                    "nino_joggers": "👖 Elegiste *JOGGERS DE NIÑO*.\n\nPróxima tarjeta a conectar.",
                    "nino_conjunto": "🧢 Elegiste *CONJUNTO DE NIÑO*.\n\nPróxima tarjeta a conectar."
                }

                if opcion_id in respuestas_nino:
                    enviar_mensaje(
                        numero_cliente,
                        respuestas_nino[opcion_id]
                    )
                    return "EVENT_RECEIVED", 200

            print("Interacción no reconocida.")
            return "EVENT_RECEIVED", 200

        # =========================================================
        # 19.7 - MENSAJES QUE NO SON TEXTO
        # =========================================================
        if tipo_mensaje != "text":
            print("Tipo de mensaje todavía no procesado:", tipo_mensaje)
            return "EVENT_RECEIVED", 200

        # =========================================================
        # 19.8 - LEER TEXTO DEL CLIENTE
        # =========================================================
        texto_cliente = (
            mensaje["text"]["body"]
            .strip()
            .lower()
        )

        print("Texto recibido:", texto_cliente)


        # =========================================================
        # 19.11 - DETECTAR SI EL CLIENTE ESTA HACIENDO UN PEDIDO
        # =========================================================

        estado_actual = ESTADO_CLIENTES.get(numero_cliente)

        if estado_actual == "esperando_pedido":

            print("Cliente en modo pedido:", numero_cliente)
            print("Pedido escrito:", texto_cliente)

            pedido_interpretado = interpretar_pedido(
                texto_cliente
            )

            print(
                "Pedido interpretado:",
                pedido_interpretado
            )

            # =========================================================
            # 19.11.1 - GEMINI TEMPORALMENTE SATURADO
            # =========================================================

            if pedido_interpretado.get("error_temporal"):

                enviar_mensaje(
                    numero_cliente,
                    (
                        "⏳ Estoy teniendo una pequeña demora "
                        "para revisar tu pedido.\n\n"
                        "Por favor, vuelve a enviarlo "
                        "en unos segundos."
                    )
                )

                return "EVENT_RECEIVED", 200

            # =========================================================
            # 19.11.2 - PEDIDO INTERPRETADO CORRECTAMENTE
            # =========================================================

            productos = pedido_interpretado.get(
                "productos",
                []
            )

            if not productos:

                enviar_mensaje(
                    numero_cliente,
                    (
                        "No pude identificar correctamente "
                        "los productos de tu pedido.\n\n"
                        "Escríbelo nuevamente indicando "
                        "producto, cantidad, talla y color."
                    )
                )

                return "EVENT_RECEIVED", 200

            # =========================================================
            # 19.11.3 - VALIDAR PEDIDO CONTRA POSTGRESQL
            # =========================================================

            validacion = validar_pedido_postgresql(
                pedido_interpretado
            )

            print(
                "Validación PostgreSQL:",
                validacion
            )

            errores = validacion.get(
                "errores",
                []
            )

            productos_validos = validacion.get(
                "productos",
                []
            )

            total = validacion.get(
                "total",
                0
            )

            # =========================================================
            # 19.11.4 - SI HAY ERRORES EN EL PEDIDO
            # =========================================================

            if errores:

                mensaje_error = (
                    "⚠️ Encontré algunos detalles "
                    "que debemos corregir:\n\n"
                )

                for error in errores:
                    mensaje_error += f"{error}\n"

                mensaje_error += (
                    "\nCorrige esos datos y "
                    "vuelve a enviarme tu pedido."
                )

                enviar_mensaje(
                    numero_cliente,
                    mensaje_error
                )

                return "EVENT_RECEIVED", 200

            # =========================================================
            # 19.11.5 - ARMAR COTIZACION
            # =========================================================

            mensaje_cotizacion = (
                "🧾 *COTIZACIÓN DE TU PEDIDO*\n\n"
            )

            for item in productos_validos:

                mensaje_cotizacion += (
                    f"• {item['cantidad']} x "
                    f"{item['producto']}\n"
                    f"  Talla: {item['talla']}\n"
                    f"  Color: {item['color']}\n"
                    f"  Precio: S/ {item['precio']:.2f}\n"
                    f"  Subtotal: S/ {item['subtotal']:.2f}\n\n"
                )

            mensaje_cotizacion += (
                f"💰 *TOTAL: S/ {total:.2f}*\n\n"
                "¿Confirmas tu pedido?"
            )

            enviar_mensaje(
                numero_cliente,
                mensaje_cotizacion
            )

            return "EVENT_RECEIVED", 200

        # =========================================================
        # 19.9 - CATÁLOGO REAL
        # =========================================================
        if texto_cliente in ["catalogo", "catálogo"]:
            enviar_tarjeta_bienvenida(numero_cliente)
            return "EVENT_RECEIVED", 200

        # =========================================================
        # 19.10 - SALUDO
        # =========================================================
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
                    "Escribe *catálogo* para conocer nuestros productos."
                )
            )
            return "EVENT_RECEIVED", 200

        # =========================================================
        # 19.12 - OTROS MENSAJES - GEMINI
        # =========================================================
        else:
            respuesta_gemini = responder_con_gemini(texto_cliente)

            enviar_mensaje(
                numero_cliente,
                respuesta_gemini
            )

            return "EVENT_RECEIVED", 200

    except Exception as error:
        print("Error procesando el mensaje:", error)
        return "EVENT_RECEIVED", 200

# =========================================================
# 20 - INICIAR FLASK
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
