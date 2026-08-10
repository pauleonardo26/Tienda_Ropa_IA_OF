import streamlit as st
import pandas as pd


def mostrar_clientes(conexion):

    st.title("👥 Clientes")

    consulta = """
    SELECT
        id_clientes,
        nombre,
        telefono,
        dni,
        direccion,
        distrito
    FROM clientes
    ORDER BY id_clientes DESC;
    """

    df = pd.read_sql(consulta, conexion)

    busqueda = st.text_input("Buscar cliente")

    if busqueda:
        resultado = df[df.astype(str).apply(
            lambda columna: columna.str.contains(
                busqueda,
                case=False,
                na=False
            )
        ).any(axis=1)]

        if resultado.empty:
            st.warning("No se encontró ningún cliente")
        else:
            st.dataframe(resultado, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)