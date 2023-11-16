import redis

# Crea una conexión a Redis
redis_cliente = redis.StrictRedis(host='localhost', port=6379, db=0)

# Puedes probar la conexión utilizando el método ping
respuesta_ping = redis_cliente.ping()
print("Respuesta del servidor Redis:", respuesta_ping)

# Almacenar un valor con una clave
redis_cliente.set('mi_clave', 'mi_valor')

# Recuperar un valor
valor_recuperado = redis_cliente.get('mi_clave')
print("Valor recuperado:", valor_recuperado.decode('utf-8'))