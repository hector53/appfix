import redis
import json
from datetime import datetime

# Crear una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

def guardar_orden(orden):
    # Generar una clave única para la orden (puedes usar algún identificador único)
    clave_orden = f"orden:{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Almacenar la orden como un hash en Redis
    redis_cliente.hset(clave_orden, mapping=orden)

    # Agregar la clave de la orden al conjunto de índices
    redis_cliente.sadd("ordenes:indice", clave_orden)

# Ejemplo de una orden
orden_ejemplo = {
  "targetCompId": "ROFX",
  "clOrdId": "qhaxppdh",
  "execId": "1699524014544462",
  "symbol": "TRI.ROS/DIC23",
  "side": "Buy",
  "securityExchange": "ROFX",
  "transactTime": "20231110-12:47:46.750",
  "ordStatus": "NEW",
  "ordType": "Limit",
  "price": 248.9,
  "avgPx": 0,
  "lastPx": 0,
  "orderQty": 1,
  "leavesQty": 1,
  "cumQty": 0,
  "lastQty": 0,
  "text": "ME_ACCEPTED",
  "orderId": "1699620466750552",
  "typeFilled": 0,
  "reject": "false",
  "ordenBot": 0,
  "id_bot": "654d66878b26b58cf6bb1664",
  "cuenta": "REM7654",
  "active": "false"
}

# Guardar la orden en Redis
guardar_orden(orden_ejemplo)

# Filtrar las órdenes por alguna condición (por ejemplo, todas las órdenes con precio mayor a 90.0)
indice_ordenes = redis_cliente.smembers("ordenes:indice")

for clave_orden in indice_ordenes:
    orden = redis_cliente.hgetall(clave_orden)
    print(f"Orden {clave_orden}: {orden}")