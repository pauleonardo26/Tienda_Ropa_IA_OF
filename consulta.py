import psycopg2
import pandas as pd

conexion = psycopg2.connect(
    host="127.0.0.1",
    database="tienda_ropa_ia",
    user="postgres",
    password="Postgres123",
    port="5432"
)

consulta = "SELECT * FROM productos LIMIT 10;"

df = pd.read_sql(consulta, conexion)

print(df.to_string())

conexion.close()