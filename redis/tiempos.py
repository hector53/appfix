import redis
import time
from datetime import datetime

# Conéctate a Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Realiza la consulta y mide el tiempo
start_time = datetime.now()
result = redis_client.get('foo')  # Reemplaza con tu consulta
end_time = datetime.now()

# Calcula y muestra el tiempo de la consulta en microsegundos
elapsed_time = (end_time - start_time).total_seconds() * 1e6
print(f'Tiempo de consulta en Redis: {elapsed_time:.2f} microsegundos')
