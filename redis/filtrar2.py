import redis
import json
from datetime import datetime
# Crear una conexión a Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Función para guardar una orden en Redis
def guardar_orden(orden):
    clave_orden = f"orden:{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    redis_client.hset(clave_orden,  mapping=orden)

    # Crear conjuntos adicionales para índices inversos
    redis_client.sadd(f"symbol:{orden['symbol']}", clave_orden)
    redis_client.sadd(f"id_bot:{orden['id_bot']}", clave_orden)
    redis_client.sadd(f"ordStatus:{orden['ordStatus']}", clave_orden)
    redis_client.sadd(f"leavesQty:{orden['leavesQty']}", clave_orden)
    redis_client.sadd(f"active:{orden['active']}", clave_orden)
    # Puedes agregar más conjuntos de índices según tus necesidades

# Función para buscar órdenes con condiciones adicionales
def buscar_ordenes(symbol, id_bot, size):
    clave_symbol = f"symbol:{symbol}"
    clave_id_bot = f"id_bot:{id_bot}"
    clave_ordStatus_new = f"ordStatus:NEW"
    clave_ordStatus_partially_filled = f"ordStatus:PARTIALLY FILLED"
    clave_leavesQty = f"leavesQty:"
    clave_active = f"active:true"

    # Obtener claves para órdenes que cumplen con las condiciones
    claves_symbol = redis_client.smembers(clave_symbol)
    claves_id_bot = redis_client.smembers(clave_id_bot)
    claves_ordStatus_new = redis_client.smembers(clave_ordStatus_new)
    claves_ordStatus_partially_filled = redis_client.smembers(clave_ordStatus_partially_filled)
    claves_active = redis_client.smembers(clave_active)

    # Calcular la intersección de claves que cumplen con todas las condiciones
    claves_interseccion = (
        claves_active &
        claves_symbol & claves_id_bot & claves_ordStatus_new  |
        (claves_symbol & claves_id_bot & claves_ordStatus_partially_filled & redis_client.smembers(f"{clave_leavesQty}{size}"))
    )

    # Obtener detalles de órdenes a partir de las claves obtenidas
    detalles_ordenes =[]
    for clave in claves_interseccion:
        orden = redis_client.hgetall(clave)
        orden_decodificada = {campo.decode('utf-8'): valor.decode('utf-8') for campo, valor in orden.items()}
        detalles_ordenes.append(orden_decodificada)

    return detalles_ordenes

# Ejemplo de una orden
orden_ejemplo = {
    "targetCompId": "ROFX",
    "clOrdId": "qhaxppdh",
    "execId": "1699524014544462",
    "symbol": "TRI.ROS/DIC23",
    "side": "Buy",
    "ordStatus": "NEW",
    "leavesQty": 1,
    "orderId": "1699620466756553",
    "id_bot": "654d66878b26b58ff6bb1664",
    "active": "true"  # Cambiado a booleano
}

# Guardar la orden en Redis
#guardar_orden(orden_ejemplo)

# Buscar órdenes con condiciones adicionales
ordenes_encontradas = buscar_ordenes("TRI.ROS/DIC23", "654d66878b26b58ff6bb1664", 1)

# Mostrar el resultado
print("Órdenes encontradas:")
for orden in ordenes_encontradas[0]:
    print(orden)
