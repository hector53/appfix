import multiprocessing
import time

def recibir_mensaje(memoria_compartida):
    with memoria_compartida.get_lock():
        return memoria_compartida.value.decode('utf-8')

if __name__ == "__main__":
    memoria_ab = multiprocessing.Array('c', b' ' * 1024, lock=True)

    while True:
        # Esperar mensaje de B
        print("dando vuelta")
        mensaje_de_b = recibir_mensaje(memoria_ab)
        print("mensaje de b: ",mensaje_de_b)
        if mensaje_de_b.strip():
            print(f"App A recibió de B: {mensaje_de_b}")

        time.sleep(1)  # Evitar el uso intensivo de la CPU
