import redis

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

def actualizar_orden(clave_orden, nuevos_datos):
    # Actualizar los campos de la orden utilizando hmset
    redis_cliente.hmset(clave_orden, nuevos_datos)

# Supongamos que tienes una clave de orden específica
clave_orden_especifica = "orden:20231110105112365594"  # Reemplaza con la clave real de tu orden

# Nuevos datos que deseas actualizar en la orden
nuevos_datos = {
    "precio": 120.0,
    # Agrega más campos según sea necesario
}

# Actualizar la orden por su clave
actualizar_orden(clave_orden_especifica, nuevos_datos)

# Mostrar los detalles actualizados de la orden
orden_actualizada = redis_cliente.hgetall(clave_orden_especifica)
orden_actualizada_decodificada = {campo.decode('utf-8'): valor.decode('utf-8') for campo, valor in orden_actualizada.items()}

print(f"Detalles actualizados de la orden {clave_orden_especifica}:")
for campo, valor in orden_actualizada_decodificada.items():
    print(f"{campo}: {valor}")