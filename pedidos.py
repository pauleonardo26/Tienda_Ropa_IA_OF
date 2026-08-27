# =========================================================
# 01 - IMPORTACIONES
# =========================================================

from conexion import conexion

# =========================================================
# 02 - CREAR PEDIDO PENDIENTE
# =========================================================

def crear_pedido_pendiente(total, id_clientes=None):

    cursor = conexion.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO pedidos
                (id_clientes, fecha, estado, total)
            VALUES
                (%s, CURRENT_TIMESTAMP, 'Pendiente', %s)
            RETURNING id_pedido
            """,
            (
                id_clientes,
                total
            )
        )

        id_pedido = cursor.fetchone()[0]

        conexion.commit()

        return {
            "ok": True,
            "id_pedido": id_pedido,
            "mensaje": "Pedido pendiente creado correctamente."
        }

    except Exception as error:

        conexion.rollback()

        return {
            "ok": False,
            "mensaje": f"No se pudo crear el pedido: {error}"
        }

    finally:

        cursor.close()

# =========================================================
# 03 - GUARDAR DETALLES DEL PEDIDO
# =========================================================

def guardar_detalles_pedido(id_pedido, productos):

    cursor = conexion.cursor()

    try:

        if not productos:
            return {
                "ok": False,
                "mensaje": "El pedido no tiene productos."
            }

        for producto in productos:

            id_variante = producto.get("id_variante")
            cantidad = int(producto.get("cantidad", 0) or 0)
            precio = float(producto.get("precio", 0) or 0)

            if not id_variante:
                raise ValueError(
                    "Hay un producto sin id_variante."
                )

            if cantidad <= 0:
                raise ValueError(
                    f"La variante {id_variante} tiene cantidad inválida."
                )

            if precio < 0:
                raise ValueError(
                    f"La variante {id_variante} tiene precio inválido."
                )

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
                    precio
                )
            )

        conexion.commit()

        return {
            "ok": True,
            "mensaje": "Detalles del pedido guardados correctamente."
        }

    except Exception as error:

        conexion.rollback()

        return {
            "ok": False,
            "mensaje": f"No se pudieron guardar los detalles: {error}"
        }

    finally:

        cursor.close()

# =========================================================
# 04 - CREAR PEDIDO COMPLETO
# =========================================================

def crear_pedido_completo(productos, total, id_clientes=None):

    cursor = conexion.cursor()

    try:

        if not productos:
            raise ValueError(
                "El pedido no tiene productos."
            )

        cursor.execute(
            """
            INSERT INTO pedidos
                (id_clientes, fecha, estado, total)
            VALUES
                (%s, CURRENT_TIMESTAMP, 'Pendiente', %s)
            RETURNING id_pedido
            """,
            (
                id_clientes,
                total
            )
        )

        id_pedido = cursor.fetchone()[0]

        for producto in productos:

            id_variante = producto.get("id_variante")
            cantidad = int(
                producto.get("cantidad", 0) or 0
            )
            precio = float(
                producto.get("precio", 0) or 0
            )

            if not id_variante:
                raise ValueError(
                    "Hay un producto sin id_variante."
                )

            if cantidad <= 0:
                raise ValueError(
                    f"La variante {id_variante} "
                    "tiene una cantidad inválida."
                )

            if precio < 0:
                raise ValueError(
                    f"La variante {id_variante} "
                    "tiene un precio inválido."
                )

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
                    precio
                )
            )

        conexion.commit()

        return {
            "ok": True,
            "id_pedido": id_pedido,
            "mensaje": (
                "Pedido completo creado correctamente."
            )
        }

    except Exception as error:

        conexion.rollback()

        return {
            "ok": False,
            "mensaje": (
                f"No se pudo crear el pedido completo: {error}"
            )
        }

    finally:

        cursor.close()