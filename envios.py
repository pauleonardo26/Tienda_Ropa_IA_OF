import streamlit as st
import pandas as pd


def mostrar_envios(conexion):

    st.title("🚚 Envíos")

    consulta = """
    SELECT
        e.id_envio,
        e.id_pedido,
        c.nombre AS cliente,
        c.telefono,
        e.sede,
        e.direccion,
        e.estado
    FROM envios e
    JOIN pedidos p
        ON e.id_pedido = p.id_pedido
    JOIN clientes c
        ON p.id_clientes = c.id_clientes
    ORDER BY e.id_envio DESC;
    """

    df_envios = pd.read_sql(consulta, conexion)

    if df_envios.empty:
        st.info("Todavía no hay envíos registrados.")
    else:
        st.dataframe(
            df_envios,
            use_container_width=True
        )