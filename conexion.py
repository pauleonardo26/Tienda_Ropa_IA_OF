import psycopg2

conexion = psycopg2.connect(
    host="127.0.0.1",
    database="tienda_ropa_ia",
    user="postgres",
    password="Postgres123",
    port="5432"
)

print("Conexión exitosa")



