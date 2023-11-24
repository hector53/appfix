import socket
import os

# Especifica el nombre del archivo para el socket
socket_file = "/tmp/my_socket"

# Elimina el archivo del socket si ya existe
try:
    os.unlink(socket_file)
except OSError:
    pass

# Crea un socket de dominio
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Enlaza el socket al archivo
server_socket.bind(socket_file)

# Escucha por conexiones entrantes
server_socket.listen()

print(f"Servidor esperando conexiones en {socket_file}")

while True:
    # Acepta la conexión
    client_socket, _ = server_socket.accept()
    
    # Lee datos del cliente
    data = client_socket.recv(1024).decode('utf-8')
    
    # Realiza alguna acción con los datos recibidos
    print(f"Datos recibidos: {data}")
    
    # Cierra la conexión con el cliente
    client_socket.close()
