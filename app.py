import streamlit as st
import psycopg2
import pandas as pd
import importlib
import inventario
import ingreso
import clientes
import ventas
import envios
importlib.reload(ingreso)
importlib.reload(clientes)
importlib.reload(ventas)
importlib.reload(envios)
importlib.reload(inventario)


menu = st.sidebar.radio(
    "Menú",
    [
        "🏠 Inicio",
        "📦 Ingreso de mercadería",
        "🛍️ Inventario",
        "💰 Ventas",
        "👥 Clientes",
        "🚚 Envíos",
        "📊 Reportes",
        "⚙️ Configuración"
    ],
    key="menu_principal"

)

conexion = psycopg2.connect(
    host="127.0.0.1",
    database="tienda_ropa_ia",
    user="postgres",
    password="Postgres123",
    port="5432"
)
if menu == "🏠 Inicio":
    st.title("🏠 Sistema Tienda de Ropa")
    st.write("Selecciona una opción del menú lateral.")


if menu == "🛍️ Inventario":
    inventario.mostrar_inventario(conexion)


if menu == "📦 Ingreso de mercadería":
    ingreso.mostrar_ingreso(conexion)


if menu == "👥 Clientes":
    clientes.mostrar_clientes(conexion)


if menu == "💰 Ventas":
    ventas.mostrar_ventas(conexion)


if menu == "🚚 Envíos":
    envios.mostrar_envios(conexion)