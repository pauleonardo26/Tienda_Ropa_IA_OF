from pedidos import crear_pedido_completo

productos = [
    {
        "id_variante": 2,
        "cantidad": 1,
        "precio": 6.00
    },
    {
        "id_variante": None,
        "cantidad": 1,
        "precio": 6.00
    }
]

resultado = crear_pedido_completo(
    productos=productos,
    total=12.00
)

print(resultado)