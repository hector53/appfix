import redis
import json
from datetime import datetime

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

def guardar_orden(orden):
    # Generar una clave única para la orden (puedes usar algún identificador único)
    clave_orden = f"orden:{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Almacenar la orden como un hash en Redis
    redis_cliente.hmset(clave_orden, orden)

    # Agregar la clave de la orden al conjunto de índices
    redis_cliente.sadd("ordenes:indice", clave_orden)

# Ejemplo de una orden
orden_ejemplo = {
    "fecha": "2023-11-10",
    "precio": 100.0,
    "otro_dato": "valor",
    # Agrega más campos según sea necesario
}

# Guardar la orden en Redis
guardar_orden(orden_ejemplo)

# Filtrar las órdenes por alguna condición (por ejemplo, todas las órdenes con precio mayor a 90.0)
indice_ordenes = redis_cliente.smembers("ordenes:indice")

for clave_orden in indice_ordenes:
    orden = redis_cliente.hgetall(clave_orden)
    if float(orden.get(b"precio", 0.0)) > 90.0:
        print(f"Orden {clave_orden}: {orden}")