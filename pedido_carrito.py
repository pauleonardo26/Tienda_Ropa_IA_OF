# =========================================================
# pedido_carrito.py
# Lógica de carrito y cotización acumulativa
# =========================================================

MAX_PRODUCTOS_PEDIDO = 5


def contar_productos(cotizacion):
    """Cuenta líneas de producto/variantes dentro de la cotización."""
    if not cotizacion:
        return 0

    return len(cotizacion.get("productos", []))


def agregar_productos_a_cotizacion(
    cotizacion_actual,
    nuevos_productos,
    total_nuevo
):
    """
    Agrega los productos nuevos a la cotización existente.

    No descuenta stock.
    No crea pedidos SQL.
    No crea pagos.
    """
    productos_actuales = []

    if cotizacion_actual:
        productos_actuales = list(
            cotizacion_actual.get("productos", [])
        )

    cantidad_actual = len(productos_actuales)
    cantidad_nueva = len(nuevos_productos)

    if cantidad_actual + cantidad_nueva > MAX_PRODUCTOS_PEDIDO:
        disponibles = MAX_PRODUCTOS_PEDIDO - cantidad_actual

        return {
            "ok": False,
            "error": (
                f"⚠️ Puedes agregar como máximo "
                f"{MAX_PRODUCTOS_PEDIDO} productos diferentes "
                f"en un pedido.\n\n"
                f"Ya tienes {cantidad_actual} "
                f"y estás intentando agregar {cantidad_nueva}.\n\n"
                f"Te quedan {max(disponibles, 0)} "
                f"espacio(s) disponible(s)."
            )
        }

    productos_finales = productos_actuales + list(nuevos_productos)

    total_actual = 0

    if cotizacion_actual:
        total_actual = float(
            cotizacion_actual.get("total", 0) or 0
        )

    total_final = round(
        total_actual + float(total_nuevo or 0),
        2
    )

    return {
        "ok": True,
        "cotizacion": {
            "productos": productos_finales,
            "total": total_final,
            "cantidad_productos": len(productos_finales),
            "confirmado": False,
            "finalizada": False
        }
    }


def construir_mensaje_cotizacion(
    productos,
    total,
    titulo="🧾 *COTIZACIÓN DE TU PEDIDO*"
):
    """
    Construye la cotización mostrando cada variante con su
    precio unitario y subtotal.
    """

    mensaje = f"{titulo}\n\n"

    productos_agrupados = {}

    for item in productos:

        nombre = item.get(
            "producto",
            "Producto"
        )

        if nombre not in productos_agrupados:
            productos_agrupados[nombre] = []

        productos_agrupados[nombre].append(item)

    for nombre_producto, items in productos_agrupados.items():

        mensaje += f"*{nombre_producto}*\n"

        for item in items:

            talla = item.get("talla", "")
            color = item.get("color", "")
            cantidad = int(
                item.get("cantidad", 0) or 0
            )
            precio = float(
                item.get("precio", 0) or 0
            )
            subtotal = float(
                item.get("subtotal", 0) or 0
            )

            mensaje += (
                f"• T{talla} · {color} · "
                f"{cantidad} und.\n"
                f"  {cantidad} und. × S/ {precio:.2f} "
                f"= *S/ {subtotal:.2f}*\n"
            )

        mensaje += "\n"

    mensaje += (
        "────────────────\n"
        f"💰 *TOTAL: S/ {float(total):.2f}*\n"
        "────────────────"
    )

    return mensaje

