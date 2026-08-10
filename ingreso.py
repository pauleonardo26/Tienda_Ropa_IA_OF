import streamlit as st


def mostrar_ingreso(conexion):

    st.title("📦 Ingreso de Mercadería")

    with st.form("form_producto", clear_on_submit=True):

        nombre = st.text_input("Nombre")
        categoria = st.text_input("Categoría")
        precio = st.number_input("Precio", min_value=0.0)
        talla = st.text_input("Talla")
        color = st.text_input("Color")
        cantidad = st.number_input("Cantidad", min_value=1, step=1)

        guardar = st.form_submit_button("Guardar")

        if guardar:

            cursor = conexion.cursor()

            try:
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
                        INSERT INTO productos(nombre, categoria, precio)
                        VALUES (%s, %s, %s)
                        RETURNING id_producto
                        """,
                        (nombre, categoria, precio)
                    )

                    id_producto = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT id_variante
                    FROM variantes_producto
                    WHERE id_producto = %s
                      AND talla = %s
                      AND LOWER(color) = LOWER(%s)
                    """,
                    (id_producto, talla, color)
                )

                variante = cursor.fetchone()

                if variante:
                    cursor.execute(
                        """
                        UPDATE variantes_producto
                        SET stock = stock + %s
                        WHERE id_variante = %s
                        """,
                        (cantidad, variante[0])
                    )

                else:
                    cursor.execute(
                        """
                        INSERT INTO variantes_producto
                            (id_producto, talla, color, stock)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (id_producto, talla, color, cantidad)
                    )

                conexion.commit()
                st.success("Producto y stock registrados correctamente")

            except Exception as error:
                conexion.rollback()
                st.error(f"No se pudo registrar: {error}")

            finally:
                cursor.close()