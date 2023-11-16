import redis

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

def eliminar_orden_por_clave(clave_orden):
    # Eliminar la orden utilizando la clave
    redis_cliente.delete(clave_orden)

# Supongamos que tienes una clave de orden específica
clave_orden_especifica = "orden:20231110105112365594"  # Reemplaza con la clave real de tu orden

# Eliminar la orden por su clave
eliminar_orden_por_clave(clave_orden_especifica)

# Verificar si la orden ha sido eliminada
orden_eliminada = redis_cliente.exists(clave_orden_especifica)

if not orden_eliminada:
    print(f"La orden con clave {clave_orden_especifica} ha sido eliminada.")
else:
    print(f"No se pudo eliminar la orden con clave {clave_orden_especifica}.")
