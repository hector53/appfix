import redis
import json
from datetime import datetime

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

# Filtrar las órdenes por alguna condición (por ejemplo, todas las órdenes con precio mayor a 90.0)
indice_ordenes = redis_cliente.smembers("ordenes:indice")

for clave_orden in indice_ordenes:
    orden = redis_cliente.hgetall(clave_orden)
    if float(orden.get(b"precio", 0.0)) > 90.0:
        print(f"Orden {clave_orden}: {orden}")