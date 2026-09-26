# =========================================================
# sesion.py
# Control de sesión de pedidos y expiración por inactividad
# =========================================================

import time

from botones import invalidar_botones


# =========================================================
# CONFIGURACIÓN
# =========================================================

# Tiempo máximo de inactividad de una sesión de pedido:
# 5 minutos = 300 segundos
TIEMPO_EXPIRACION_SEGUNDOS = 300


# =========================================================
# MEMORIA DE SESIONES
# =========================================================

# Guarda la última actividad de cada cliente.
ULTIMA_ACTIVIDAD_CLIENTES = {}


# Clientes cuya sesión ya venció y deben escribir CATÁLOGO
# antes de poder comenzar nuevamente.
ESPERANDO_CATALOGO_CLIENTES = set()


# =========================================================
# INICIAR SESIÓN
# =========================================================

def iniciar_sesion(numero_cliente):
    """
    Inicia o reinicia el contador de actividad del cliente.
    """

    if not numero_cliente:
        return

    ULTIMA_ACTIVIDAD_CLIENTES[numero_cliente] = time.time()

    # Si vuelve a iniciar una sesión válida,
    # deja de estar bloqueado esperando CATÁLOGO.
    ESPERANDO_CATALOGO_CLIENTES.discard(numero_cliente)


# =========================================================
# REGISTRAR ACTIVIDAD
# =========================================================

def registrar_actividad(numero_cliente):
    """
    Actualiza la última actividad del cliente.

    Debe llamarse cuando el cliente realiza una acción
    válida dentro del flujo del pedido.
    """

    if not numero_cliente:
        return

    ULTIMA_ACTIVIDAD_CLIENTES[numero_cliente] = time.time()

    ESPERANDO_CATALOGO_CLIENTES.discard(numero_cliente)


# =========================================================
# SABER SI LA SESIÓN EXPIRÓ
# =========================================================

def sesion_expirada(numero_cliente):
    """
    Devuelve True si la sesión superó los 5 minutos
    de inactividad.
    """

    if not numero_cliente:
        return False

    ultima_actividad = ULTIMA_ACTIVIDAD_CLIENTES.get(numero_cliente)

    # Si no existe sesión registrada,
    # no podemos considerarla expirada.
    if ultima_actividad is None:
        return False

    tiempo_transcurrido = time.time() - ultima_actividad

    return tiempo_transcurrido >= TIEMPO_EXPIRACION_SEGUNDOS


# =========================================================
# LIMPIAR SESIÓN
# =========================================================

def limpiar_sesion(
    numero_cliente,
    estado_clientes,
    cotizaciones_clientes,
    producto_seleccionado_clientes=None
):
    """
    Elimina toda la información temporal del pedido
    del cliente.

    NO toca la base de datos.

    NO elimina productos de PostgreSQL.

    NO descuenta stock.

    Solo limpia la sesión temporal del cliente.
    """

    if not numero_cliente:
        return

    # -----------------------------------------------------
    # Estado actual del cliente
    # -----------------------------------------------------

    if estado_clientes is not None:
        estado_clientes.pop(numero_cliente, None)

    # -----------------------------------------------------
    # Cotización temporal
    # -----------------------------------------------------

    if cotizaciones_clientes is not None:
        cotizaciones_clientes.pop(numero_cliente, None)

    # -----------------------------------------------------
    # Producto seleccionado desde una tarjeta
    # -----------------------------------------------------

    if producto_seleccionado_clientes is not None:
        producto_seleccionado_clientes.pop(numero_cliente, None)

    # -----------------------------------------------------
    # Última actividad
    # -----------------------------------------------------

    ULTIMA_ACTIVIDAD_CLIENTES.pop(numero_cliente, None)

    # -----------------------------------------------------
    # Todos los botones anteriores quedan inválidos
    # -----------------------------------------------------

    invalidar_botones(numero_cliente)


# =========================================================
# VERIFICAR Y EXPIRAR
# =========================================================

def verificar_y_expirar(
    numero_cliente,
    estado_clientes,
    cotizaciones_clientes,
    producto_seleccionado_clientes=None
):
    """
    Comprueba si la sesión expiró.

    Si expiró:

    1. Borra estado temporal.
    2. Borra cotización temporal.
    3. Borra producto seleccionado.
    4. Invalida botones anteriores.
    5. Obliga al cliente a escribir CATÁLOGO.

    Devuelve:

        True  -> la sesión acaba de expirar.
        False -> la sesión sigue vigente.
    """

    if not numero_cliente:
        return False

    if not sesion_expirada(numero_cliente):
        return False

    # -----------------------------------------------------
    # Limpiar absolutamente toda la sesión temporal
    # -----------------------------------------------------

    limpiar_sesion(
        numero_cliente,
        estado_clientes,
        cotizaciones_clientes,
        producto_seleccionado_clientes
    )

    # -----------------------------------------------------
    # El cliente deberá escribir CATÁLOGO
    # para comenzar nuevamente.
    # -----------------------------------------------------

    ESPERANDO_CATALOGO_CLIENTES.add(numero_cliente)

    return True


# =========================================================
# ESTADO: ESPERANDO CATÁLOGO
# =========================================================

def esta_esperando_catalogo(numero_cliente):
    """
    Indica si el cliente tiene una sesión vencida
    y debe escribir CATÁLOGO.
    """

    if not numero_cliente:
        return False

    return numero_cliente in ESPERANDO_CATALOGO_CLIENTES


# =========================================================
# PERMITIR NUEVO CATÁLOGO
# =========================================================

def permitir_catalogo(numero_cliente):
    """
    Permite que el cliente vuelva a comenzar después
    de escribir CATÁLOGO.
    """

    if not numero_cliente:
        return

    ESPERANDO_CATALOGO_CLIENTES.discard(numero_cliente)

    # Inicia una nueva sesión desde este momento.
    iniciar_sesion(numero_cliente)


# =========================================================
# REINICIAR SESIÓN COMPLETAMENTE
# =========================================================

def reiniciar_sesion(
    numero_cliente,
    estado_clientes,
    cotizaciones_clientes,
    producto_seleccionado_clientes=None
):
    """
    Limpia completamente una sesión anterior
    y comienza una nueva.
    """

    limpiar_sesion(
        numero_cliente,
        estado_clientes,
        cotizaciones_clientes,
        producto_seleccionado_clientes
    )

    iniciar_sesion(numero_cliente)


# =========================================================
# FIN
# =========================================================
