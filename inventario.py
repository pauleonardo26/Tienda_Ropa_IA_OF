import streamlit as st
import pandas as pd


def mostrar_inventario(conexion):

    st.title("🛍️ Inventario")

    consulta = """
    SELECT
        p.id_producto,
        p.nombre,
        p.categoria,
        p.precio,
        v.talla,
        v.color,
        v.stock
    FROM productos p
    LEFT JOIN variantes_producto v
        ON p.id_producto = v.id_producto
    ORDER BY p.id_producto;
    """

    df = pd.read_sql(consulta, conexion)

    busqueda = st.text_input("Buscar producto")

    if busqueda:
        resultado = df[df.astype(str).apply(
            lambda x: x.str.contains(busqueda, case=False)
        ).any(axis=1)]

        if resultado.empty:
            st.warning("No se encontró ningún producto")
        else:
            st.write(df.columns.tolist())
    else:
        st.dataframe(df, use_container_width=True)