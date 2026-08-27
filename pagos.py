# =========================================================
# 01 - IMPORTACIONES
# =========================================================

from conexion import conexion

# =========================================================
# 02 - OBTENER PEDIDO PENDIENTE
# =========================================================

def obtener_pedido_pendiente(id_pedido):

    cursor = conexion.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id_pedido,
                id_clientes,
                fecha,
                estado,
                total
            FROM pedidos
            WHERE id_pedido = %s
            """,
            (id_pedido,)
        )

        pedido = cursor.fetchone()

        if pedido is None:
            return {
                "ok": False,
                "mensaje": "El pedido no existe."
            }

        estado = str(pedido[3]).strip().lower()

        if estado != "pendiente":
            return {
                "ok": False,
                "mensaje": (
                    f"El pedido no está pendiente. "
                    f"Estado actual: {pedido[3]}"
                )
            }

        return {
            "ok": True,
            "pedido": {
                "id_pedido": pedido[0],
                "id_clientes": pedido[1],
                "fecha": pedido[2],
                "estado": pedido[3],
                "total": float(pedido[4] or 0)
            }
        }

    finally:
        cursor.close()

# =========================================================
# 03 - VALIDAR STOCK DE TODO EL PEDIDO
# =========================================================

def validar_stock_pedido(id_pedido):

    cursor = conexion.cursor()

    try:

        cursor.execute(
            """
            SELECT
                d.id_detalle,
                d.id_variante,
                d.cantidad,
                d.precio,
                v.stock
            FROM detalle_pedido d
            JOIN variantes_producto v
                ON v.id_variante = d.id_variante
            WHERE d.id_pedido = %s
            ORDER BY d.id_detalle
            """,
            (id_pedido,)
        )

        detalles = cursor.fetchall()

        if not detalles:
            return {
                "ok": False,
                "mensaje": "El pedido no tiene productos."
            }

        productos = []
        errores = []

        for detalle in detalles:

            id_detalle = detalle[0]
            id_variante = detalle[1]
            cantidad = int(detalle[2] or 0)
            precio = float(detalle[3] or 0)
            stock_actual = int(detalle[4] or 0)

            if cantidad <= 0:
                errores.append(
                    f"El detalle {id_detalle} tiene una cantidad inválida."
                )
                continue

            if stock_actual < cantidad:
                errores.append(
                    f"La variante {id_variante} no tiene stock suficiente. "
                    f"Solicitado: {cantidad}. Disponible: {stock_actual}."
                )
                continue

            productos.append(
                {
                    "id_detalle": id_detalle,
                    "id_variante": id_variante,
                    "cantidad": cantidad,
                    "precio": precio,
                    "stock_actual": stock_actual
                }
            )

        if errores:
            return {
                "ok": False,
                "errores": errores,
                "productos": productos
            }

        return {
            "ok": True,
            "productos": productos
        }

    finally:
        cursor.close()

# =========================================================
# 04 - REGISTRAR PAGO DEL PEDIDO
# =========================================================

def registrar_pago(id_pedido, metodo, monto):

    cursor = conexion.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO pagos
                (id_pedido, metodo, monto, estado)
            VALUES
                (%s, %s, %s, %s)
            RETURNING id_pago
            """,
            (
                id_pedido,
                metodo,
                monto,
                "Pendiente"
            )
        )

        id_pago = cursor.fetchone()[0]

        conexion.commit()

        return {
            "ok": True,
            "id_pago": id_pago,
            "mensaje": "Pago registrado correctamente."
        }

    except Exception as error:

        conexion.rollback()

        return {
            "ok": False,
            "mensaje": f"No se pudo registrar el pago: {error}"
        }

    finally:
        cursor.close()


# =========================================================
# 05 - CONFIRMAR PAGO Y DESCONTAR STOCK
# =========================================================

def confirmar_pago_y_descontar_stock(id_pago):

    cursor = conexion.cursor()

    try:

        # =========================================================
        # 05.1 - OBTENER PAGO Y BLOQUEAR REGISTRO
        # =========================================================

        cursor.execute(
            """
            SELECT
                id_pago,
                id_pedido,
                metodo,
                monto,
                estado
            FROM pagos
            WHERE id_pago = %s
            FOR UPDATE
            """,
            (id_pago,)
        )

        pago = cursor.fetchone()

        if pago is None:
            raise ValueError("El pago no existe.")

        id_pedido = pago[1]
        estado_pago = str(pago[4]).strip().lower()

        if estado_pago != "pendiente":
            raise ValueError(
                f"El pago ya no está pendiente. "
                f"Estado actual: {pago[4]}"
            )

        # =========================================================
        # 05.2 - OBTENER PEDIDO Y BLOQUEAR REGISTRO
        # =========================================================

        cursor.execute(
            """
            SELECT
                id_pedido,
                estado,
                total
            FROM pedidos
            WHERE id_pedido = %s
            FOR UPDATE
            """,
            (id_pedido,)
        )

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("El pedido asociado no existe.")

        estado_pedido = str(pedido[1]).strip().lower()
        total_pedido = float(pedido[2] or 0)
        monto_pago = float(pago[3] or 0)

        if estado_pedido != "pendiente":
            raise ValueError(
                f"El pedido ya no está pendiente. "
                f"Estado actual: {pedido[1]}"
            )

        if round(monto_pago, 2) != round(total_pedido, 2):
            raise ValueError(
                f"El monto pagado S/ {monto_pago:.2f} "
                f"no coincide con el total del pedido "
                f"S/ {total_pedido:.2f}."
            )

        # =========================================================
        # 05.3 - OBTENER TODAS LAS VARIANTES DEL PEDIDO
        # =========================================================

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
            (id_pedido,)
        )

        detalles = cursor.fetchall()

        if not detalles:
            raise ValueError(
                "El pedido no tiene productos para descontar."
            )

        # =========================================================
        # 05.4 - VALIDAR STOCK DE TODAS LAS VARIANTES
        # =========================================================

        for detalle in detalles:

            id_variante = detalle[0]
            cantidad = int(detalle[1] or 0)
            stock_actual = int(detalle[2] or 0)

            if cantidad <= 0:
                raise ValueError(
                    f"La variante {id_variante} "
                    "tiene una cantidad inválida."
                )

            if stock_actual < cantidad:
                raise ValueError(
                    f"No hay stock suficiente para la variante "
                    f"{id_variante}. "
                    f"Solicitado: {cantidad}. "
                    f"Disponible: {stock_actual}."
                )

        # =========================================================
        # 05.5 - DESCONTAR STOCK DE TODAS LAS VARIANTES
        # =========================================================

        for detalle in detalles:

            id_variante = detalle[0]
            cantidad = int(detalle[1])

            cursor.execute(
                """
                UPDATE variantes_producto
                SET stock = stock - %s
                WHERE id_variante = %s
                  AND stock >= %s
                """,
                (
                    cantidad,
                    id_variante,
                    cantidad
                )
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    f"No se pudo descontar stock "
                    f"de la variante {id_variante}."
                )

        # =========================================================
        # 05.6 - MARCAR PEDIDO COMO PAGADO
        # =========================================================

        cursor.execute(
            """
            UPDATE pedidos
            SET estado = 'Pagado'
            WHERE id_pedido = %s
              AND estado = 'Pendiente'
            """,
            (id_pedido,)
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "No se pudo actualizar el pedido a Pagado."
            )

        # =========================================================
        # 05.7 - MARCAR PAGO COMO CONFIRMADO
        # =========================================================

        cursor.execute(
            """
            UPDATE pagos
            SET estado = 'Confirmado'
            WHERE id_pago = %s
              AND estado = 'Pendiente'
            """,
            (id_pago,)
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "No se pudo confirmar el pago."
            )

        # =========================================================
        # 05.8 - GUARDAR TODO
        # =========================================================

        conexion.commit()

        return {
            "ok": True,
            "id_pago": id_pago,
            "id_pedido": id_pedido,
            "mensaje": (
                "Pago confirmado y stock actualizado correctamente."
            )
        }

    except Exception as error:

        conexion.rollback()

        return {
            "ok": False,
            "mensaje": str(error)
        }

    finally:

        cursor.close()

