import streamlit as st
import boto3
import os
import re
import uuid
import unicodedata

from dotenv import load_dotenv

load_dotenv()


def limpiar_nombre(texto):
    texto = texto.strip().lower()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"[^a-z0-9]+", "_", texto)

    return texto.strip("_")


def conectar_r2():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    )


def subir_foto_r2(foto, nombre, talla, color):

    extension = os.path.splitext(foto.name)[1].lower()

    if not extension:
        extension = ".jpg"

    nombre_limpio = limpiar_nombre(nombre)
    talla_limpia = limpiar_nombre(str(talla))
    color_limpio = limpiar_nombre(color)

    codigo = uuid.uuid4().hex[:8]

    nombre_r2 = (
        f"productos/"
        f"{nombre_limpio}_"
        f"{talla_limpia}_"
        f"{color_limpio}_"
        f"{codigo}{extension}"
    )

    s3 = conectar_r2()

    s3.upload_fileobj(
        foto,
        os.getenv("R2_BUCKET_NAME"),
        nombre_r2,
        ExtraArgs={
            "ContentType": foto.type
        }
    )

    return nombre_r2


def mostrar_ingreso(conexion):

    st.title("📦 Ingreso de Mercadería")

    with st.form("form_producto", clear_on_submit=True):

        nombre = st.text_input("Nombre")
        categoria = st.text_input("Categoría")
        precio = st.number_input(
            "Precio",
            min_value=0.0,
            step=0.50
        )

        talla = st.text_input("Talla")
        color = st.text_input("Color")

        cantidad = st.number_input(
            "Cantidad",
            min_value=1,
            step=1
        )

        foto = st.file_uploader(
            "📷 Foto del producto",
            type=["jpg", "jpeg", "jfif", "png", "webp"]
        )

        guardar = st.form_submit_button("Guardar")

        if guardar:

            if not nombre.strip():
                st.error("Debes ingresar el nombre del producto")
                return

            if not categoria.strip():
                st.error("Debes ingresar la categoría")
                return

            if not talla.strip():
                st.error("Debes ingresar la talla")
                return

            if not color.strip():
                st.error("Debes ingresar el color")
                return

            if precio <= 0:
                st.error("El precio debe ser mayor que cero")
                return

            cursor = conexion.cursor()

            try:

                # -----------------------------
                # BUSCAR PRODUCTO
                # -----------------------------

                cursor.execute(
                    """
                    SELECT id_producto
                    FROM productos
                    WHERE LOWER(nombre) = LOWER(%s)
                    """,
                    (nombre,)
                )

                producto = cursor.fetchone()

                if producto:

                    id_producto = producto[0]

                else:

                    cursor.execute(
                        """
                        INSERT INTO productos
                            (nombre, categoria, precio)
                        VALUES (%s, %s, %s)
                        RETURNING id_producto
                        """,
                        (
                            nombre.strip(),
                            categoria.strip(),
                            precio
                        )
                    )

                    id_producto = cursor.fetchone()[0]

                # -----------------------------
                # BUSCAR VARIANTE
                # -----------------------------

                cursor.execute(
                    """
                    SELECT id_variante, foto
                    FROM variantes_producto
                    WHERE id_producto = %s
                      AND talla = %s
                      AND LOWER(color) = LOWER(%s)
                    """,
                    (
                        id_producto,
                        talla.strip(),
                        color.strip()
                    )
                )

                variante = cursor.fetchone()

                # -----------------------------
                # SUBIR FOTO A R2
                # -----------------------------

                ruta_foto = None

                if foto is not None:

                    ruta_foto = subir_foto_r2(
                        foto,
                        nombre,
                        talla,
                        color
                    )

                # -----------------------------
                # ACTUALIZAR VARIANTE
                # -----------------------------

                if variante:

                    id_variante = variante[0]
                    foto_anterior = variante[1]

                    if ruta_foto:

                        cursor.execute(
                            """
                            UPDATE variantes_producto
                            SET stock = stock + %s,
                                foto = %s
                            WHERE id_variante = %s
                            """,
                            (
                                cantidad,
                                ruta_foto,
                                id_variante
                            )
                        )

                    else:

                        cursor.execute(
                            """
                            UPDATE variantes_producto
                            SET stock = stock + %s
                            WHERE id_variante = %s
                            """,
                            (
                                cantidad,
                                id_variante
                            )
                        )

                else:

                    if foto is None:

                        conexion.rollback()

                        st.error(
                            "Para una variante nueva debes seleccionar una foto"
                        )

                        return

                    cursor.execute(
                        """
                        INSERT INTO variantes_producto
                            (
                                id_producto,
                                talla,
                                color,
                                stock,
                                foto
                            )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            id_producto,
                            talla.strip(),
                            color.strip(),
                            cantidad,
                            ruta_foto
                        )
                    )

                conexion.commit()

                st.success(
                    "✅ Producto, stock y foto registrados correctamente"
                )

            except Exception as error:

                conexion.rollback()

                st.error(
                    f"No se pudo registrar: {error}"
                )

            finally:

                cursor.close()