import streamlit as st
import psycopg2
import pandas as pd

st.title("🛒 Consulta de Productos - Tienda")

conexion = psycopg2.connect(
    host="127.0.0.1",
    database="tienda_ropa_ia",
    user="postgres",
    password="Postgres123",
    port="5432"
)

consulta = "SELECT * FROM productos;"

df = pd.read_sql(consulta, conexion)

busqueda = st.text_input("Buscar producto")

if busqueda:
    resultado = df[df.astype(str).apply(
        lambda x: x.str.contains(busqueda, case=False)
    ).any(axis=1)]

    if resultado.empty:
        st.warning("No se encontró ningún producto")
    else:
        st.dataframe(resultado)
else:
    st.dataframe(df)


