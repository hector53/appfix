import redis

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

def obtener_orden_por_clave(clave_orden):
    # Obtener todos los campos y valores de la orden utilizando hgetall
    orden = redis_cliente.hgetall(clave_orden)

    # Convertir bytes a strings (si es necesario)
    orden_decodificada = {campo.decode('utf-8'): valor.decode('utf-8') for campo, valor in orden.items()}

    return orden_decodificada

# Supongamos que tienes una clave de orden específica
clave_orden_especifica = "orden:20231110154157843394"  # Reemplaza con la clave real de tu orden

# Obtener la orden por su clave
orden = obtener_orden_por_clave(clave_orden_especifica)

# Mostrar los detalles de la orden
print(f"Detalles de la orden {clave_orden_especifica}:")
for campo, valor in orden.items():
    print(f"{campo}: {valor}")