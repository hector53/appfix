import redis
import datetime
def recibir_mensaje(pubsub):
    mensaje = pubsub.get_message()
    if mensaje and mensaje['type'] == 'message':
        return mensaje['data'].decode('utf-8')
    return None

if __name__ == "__main__":
    cliente_redis = redis.StrictRedis(host='localhost', port=6379, db=0)
    pubsub = cliente_redis.pubsub()
    pubsub.subscribe('canal_compartido')

    while True:
        # Esperar mensaje de B
        mensaje_de_b = recibir_mensaje(pubsub)
        if mensaje_de_b:
            print(f"App A recibió de B: {mensaje_de_b}")
            #imprimir fecha actual con milisegundos, que el formato salgan los milisegundos
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))


