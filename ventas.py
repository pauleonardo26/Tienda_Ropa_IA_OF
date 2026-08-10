import streamlit as st
import pandas as pd


def mostrar_ventas(conexion):

    # Número de versión para reconstruir y limpiar los campos de venta
    if "version_venta" not in st.session_state:
        st.session_state["version_venta"] = 0

    version = st.session_state["version_venta"]

    # Mensajes que deben mostrarse después de recargar la página
    mensaje = st.session_state.pop("mensaje_venta", None)
    if mensaje:
        st.success(mensaje)

    st.title("💰 Ventas")
    st.info("Aquí se crearán los pedidos antes del pago.")

    # ---------------------------------------------------------
    # 1. SELECCIÓN DEL PRODUCTO
    # ---------------------------------------------------------
    consulta = """
    SELECT nombre
    FROM productos
    ORDER BY nombre;
    """

    df = pd.read_sql(consulta, conexion)
    lista_productos = ["Seleccione..."] + df["nombre"].tolist()

    producto = st.selectbox(
        "Producto",
        lista_productos,
        key=f"producto_venta_{version}"
    )

    # ---------------------------------------------------------
    # 2. TALLAS DISPONIBLES
    # ---------------------------------------------------------
    if producto != "Seleccione...":

        consulta_tallas = """
        SELECT DISTINCT v.talla
        FROM variantes_producto v
        JOIN productos p
            ON p.id_producto = v.id_producto
        WHERE p.nombre = %s
        ORDER BY v.talla;
        """

        df_tallas = pd.read_sql(
            consulta_tallas,
            conexion,
            params=(producto,)
        )

        lista_tallas = (
            ["Seleccione..."]
            + df_tallas["talla"].astype(str).tolist()
        )

    else:
        lista_tallas = ["Seleccione..."]

    talla = st.selectbox(
        "Talla",
        lista_tallas,
        key=f"talla_venta_{version}"
    )

    # ---------------------------------------------------------
    # 3. COLORES DISPONIBLES
    # ---------------------------------------------------------
    if (
        producto != "Seleccione..."
        and talla != "Seleccione..."
    ):

        consulta_colores = """
        SELECT DISTINCT v.color
        FROM variantes_producto v
        JOIN productos p
            ON p.id_producto = v.id_producto
        WHERE p.nombre = %s
          AND v.talla::text = %s
        ORDER BY v.color;
        """

        df_colores = pd.read_sql(
            consulta_colores,
            conexion,
            params=(producto, talla)
        )

        lista_colores = (
            ["Seleccione..."]
            + df_colores["color"].astype(str).tolist()
        )

    else:
        lista_colores = ["Seleccione..."]

    color = st.selectbox(
        "Color",
        lista_colores,
        key=f"color_venta_{version}"
    )

    # ---------------------------------------------------------
    # 4. STOCK Y PRECIO
    # ---------------------------------------------------------
    stock_disponible = 0
    precio_unitario = 0.0

    if (
        producto != "Seleccione..."
        and talla != "Seleccione..."
        and color != "Seleccione..."
    ):

        consulta_datos = """
        SELECT
            v.stock,
            p.precio
        FROM variantes_producto v
        JOIN productos p
            ON p.id_producto = v.id_producto
        WHERE p.nombre = %s
          AND v.talla::text = %s
          AND v.color = %s;
        """

        df_datos = pd.read_sql(
            consulta_datos,
            conexion,
            params=(producto, talla, color)
        )

        if not df_datos.empty:
            stock_disponible = int(df_datos.iloc[0]["stock"])
            precio_unitario = float(df_datos.iloc[0]["precio"])

    st.write(f"Stock disponible: {stock_disponible}")
    st.write(f"Precio unitario: S/ {precio_unitario:.2f}")

    cantidad = st.number_input(
        "Cantidad",
        min_value=1,
        step=1,
        key=f"cantidad_venta_{version}"
    )

    total = cantidad * precio_unitario
    st.write(f"Total: S/ {total:.2f}")

    # ---------------------------------------------------------
    # 5. CREAR PEDIDO PENDIENTE
    # ---------------------------------------------------------
    crear_pedido = st.button(
        "Crear pedido",
        key=f"crear_pedido_{version}"
    )

    if crear_pedido:

        if producto == "Seleccione...":
            st.error("Selecciona un producto")

        elif talla == "Seleccione...":
            st.error("Selecciona una talla")

        elif color == "Seleccione...":
            st.error("Selecciona un color")

        elif stock_disponible <= 0:
            st.error("Este producto no tiene stock disponible")

        elif cantidad > stock_disponible:
            st.error("La cantidad supera el stock disponible")

        else:
            cursor = conexion.cursor()

            try:
                cursor.execute(
                    """
                    SELECT v.id_variante
                    FROM variantes_producto v
                    JOIN productos p
                        ON p.id_producto = v.id_producto
                    WHERE p.nombre = %s
                      AND v.talla::text = %s
                      AND v.color = %s
                    """,
                    (producto, talla, color)
                )

                variante = cursor.fetchone()

                if variante is None:
                    raise ValueError("No se encontró la variante seleccionada")

                id_variante = variante[0]

                cursor.execute(
                    """
                    INSERT INTO pedidos
                        (id_clientes, fecha, estado, total)
                    VALUES
                        (NULL, CURRENT_DATE, 'Pendiente', %s)
                    RETURNING id_pedido
                    """,
                    (total,)
                )

                id_pedido = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO detalle_pedido
                        (id_pedido, id_variante, cantidad, precio)
                    VALUES
                        (%s, %s, %s, %s)
                    """,
                    (
                        id_pedido,
                        id_variante,
                        cantidad,
                        precio_unitario
                    )
                )

                conexion.commit()

                st.session_state["mensaje_venta"] = (
                    f"Pedido N.º {id_pedido} creado correctamente. "
                    f"Total: S/ {total:.2f}"
                )

                # Cambiar la versión crea campos nuevos y vacíos
                st.session_state["version_venta"] += 1
                st.rerun()

            except Exception as error:
                conexion.rollback()
                st.error(f"No se pudo crear el pedido: {error}")

            finally:
                cursor.close()

    # ---------------------------------------------------------
    # 6. PEDIDOS PENDIENTES
    # ---------------------------------------------------------
    st.divider()
    st.subheader("📋 Pedidos pendientes")

    consulta_pendientes = """
    SELECT
        p.id_pedido,
        pr.nombre AS producto,
        v.talla,
        v.color,
        d.cantidad,
        d.precio,
        p.total,
        p.estado
    FROM pedidos p
    JOIN detalle_pedido d
        ON p.id_pedido = d.id_pedido
    JOIN variantes_producto v
        ON d.id_variante = v.id_variante
    JOIN productos pr
        ON v.id_producto = pr.id_producto
    WHERE p.estado = 'Pendiente'
    ORDER BY p.id_pedido DESC;
    """

    pedidos_pendientes = pd.read_sql(
        consulta_pendientes,
        conexion
    )

    st.dataframe(
        pedidos_pendientes,
        use_container_width=True
    )

    # ---------------------------------------------------------
    # 7. CONFIRMAR PAGO Y FINALIZAR VENTA
    # ---------------------------------------------------------
    if not pedidos_pendientes.empty:

        id_pedido_seleccionado = st.selectbox(
            "Selecciona el pedido pagado",
            pedidos_pendientes["id_pedido"].tolist(),
            key="pedido_seleccionado"
        )

        confirmar_pago = st.button("Confirmar pago")

        if confirmar_pago:
            st.session_state["pedido_pagado"] = int(
                id_pedido_seleccionado
            )

        if "pedido_pagado" in st.session_state:

            st.subheader("👤 Datos del cliente y envío")

            with st.form("form_cliente_pago"):

                nombre_cliente = st.text_input("Nombre completo")
                telefono = st.text_input("Teléfono")
                dni = st.text_input("DNI")
                direccion = st.text_input("Dirección")
                distrito = st.text_input("Distrito")
                sede_envio = st.text_input(
                    "Sede o agencia de envío",
                    placeholder="Ejemplo: Shalom Chorrillos"
                )

                finalizar_venta = st.form_submit_button(
                    "Guardar y finalizar venta"
                )

                if finalizar_venta:

                    if not nombre_cliente.strip():
                        st.error("Ingresa el nombre del cliente")

                    elif not telefono.strip():
                        st.error("Ingresa el teléfono")

                    elif not direccion.strip():
                        st.error("Ingresa la dirección")

                    elif not distrito.strip():
                        st.error("Ingresa el distrito")

                    elif not sede_envio.strip():
                        st.error("Ingresa la sede o agencia de envío")

                    else:
                        cursor = conexion.cursor()
                        venta_finalizada = False

                        try:
                            id_pedido_pagado = int(
                                st.session_state["pedido_pagado"]
                            )

                            cursor.execute(
                                """
                                SELECT
                                    d.id_variante,
                                    d.cantidad,
                                    v.stock
                                FROM detalle_pedido d
                                JOIN variantes_producto v
                                    ON v.id_variante = d.id_variante
                                WHERE d.id_pedido = %s
                                FOR UPDATE OF v
                                """,
                                (id_pedido_pagado,)
                            )

                            detalle = cursor.fetchone()

                            if detalle is None:
                                raise ValueError(
                                    "No se encontró el detalle del pedido"
                                )

                            id_variante_pedido = detalle[0]
                            cantidad_pedido = int(detalle[1])
                            stock_actual = int(detalle[2])

                            if stock_actual < cantidad_pedido:
                                raise ValueError(
                                    "No hay stock suficiente para finalizar la venta"
                                )

                            cursor.execute(
                                """
                                INSERT INTO clientes
                                    (nombre, telefono, dni, direccion, distrito)
                                VALUES
                                    (%s, %s, %s, %s, %s)
                                RETURNING id_clientes
                                """,
                                (
                                    nombre_cliente.strip(),
                                    telefono.strip(),
                                    dni.strip(),
                                    direccion.strip(),
                                    distrito.strip()
                                )
                            )

                            id_clientes = cursor.fetchone()[0]

                            cursor.execute(
                                """
                                UPDATE pedidos
                                SET id_clientes = %s,
                                    estado = 'Pagado'
                                WHERE id_pedido = %s
                                  AND estado = 'Pendiente'
                                """,
                                (
                                    id_clientes,
                                    id_pedido_pagado
                                )
                            )

                            if cursor.rowcount != 1:
                                raise ValueError(
                                    "El pedido ya no está pendiente"
                                )

                            cursor.execute(
                                """
                                SELECT id_envio
                                FROM envios
                                WHERE id_pedido = %s
                                """,
                                (id_pedido_pagado,)
                            )

                            if cursor.fetchone() is not None:
                                raise ValueError(
                                    "Este pedido ya tiene un envío registrado"
                                )

                            cursor.execute(
                                """
                                INSERT INTO envios
                                    (id_pedido, sede, direccion, estado)
                                VALUES
                                    (%s, %s, %s, %s)
                                RETURNING id_envio
                                """,
                                (
                                    id_pedido_pagado,
                                    sede_envio.strip(),
                                    direccion.strip(),
                                    "Pendiente"
                                )
                            )

                            id_envio = cursor.fetchone()[0]

                            cursor.execute(
                                """
                                UPDATE variantes_producto
                                SET stock = stock - %s
                                WHERE id_variante = %s
                                  AND stock >= %s
                                """,
                                (
                                    cantidad_pedido,
                                    id_variante_pedido,
                                    cantidad_pedido
                                )
                            )

                            if cursor.rowcount != 1:
                                raise ValueError(
                                    "No se pudo descontar el stock"
                                )

                            conexion.commit()
                            venta_finalizada = True

                        except Exception as error:
                            conexion.rollback()
                            st.error(
                                f"No se pudo finalizar la venta: {error}"
                            )

                        finally:
                            cursor.close()

                        if venta_finalizada:
                            st.session_state.pop(
                                "pedido_pagado",
                                None
                            )
                            st.session_state["mensaje_venta"] = (
                                f"Venta finalizada. Envío N.º {id_envio} "
                                "registrado y stock actualizado correctamente"
                            )
                            st.rerun()

