import asyncio
import websockets
from urllib.parse import urlparse, parse_qs
from threading import Thread

class WebSocketServer(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        """
        Constructor de la clase WebSocketServer.

        Args:
        - host (str): dirección IP o nombre de host donde se alojará el servidor.
        - port (int): número de puerto donde se alojará el servidor.
        """
        self.host = host
        self.port = port
        self.clients = {}

    def run(self):
        """
        Inicia el servidor WebSocket.
        """
        print("start cola")
        loop = asyncio.new_event_loop()# creo un nuevo evento para asyncio y asi ejecutar todo de aqui en adelante con async await 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_forever())#ejecuto la funcion q quiero
        loop.close()#cierro el evento

    async def handle(self, websocket, path):
        """
        Manejador de solicitudes de WebSocket.

        Args:
        - websocket (WebSocketServerProtocol): objeto que representa la conexión WebSocket.
        - path (str): ruta de la solicitud WebSocket.

        Nota:
        - Esta función se ejecuta cada vez que se recibe una solicitud WebSocket.
        """
        # Acceder a los parámetros de la URL de la solicitud de WebSocket
        query = urlparse(path).query
        params = parse_qs(query)
        client_id = params.get('client_id', [None])[0]
        print(f"Nuevo cliente conectado con ID {client_id}")

        # Agregar el cliente a la lista de clientes
        self.clients[client_id] = websocket

        try:
            async for message in websocket:
                print(f"Mensaje recibido de cliente con ID {client_id}: {message}")
                # Responder al cliente con el mismo mensaje recibido
                await websocket.send(message)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Cliente con ID {client_id} desconectado")
            # Eliminar el cliente de la lista de clientes
            del self.clients[client_id]

    async def send_message(self, client_id, message):
        """
        Enviar un mensaje a un cliente específico por medio de su ID.

        Args:
        - client_id (str): ID del cliente al que se le enviará el mensaje.
        - message (str): mensaje que se enviará al cliente.

        Nota:
        - Si el cliente no está conectado, el mensaje no se enviará.
        """
        # Enviar un mensaje a un cliente específico por medio de su ID
        websocket = self.clients.get(client_id)
        if websocket:
            await websocket.send(message)

    async def broadcast_message(self, message):
        """
        Enviar un mensaje a todos los clientes conectados.

        Args:
        - message (str): mensaje que se enviará a todos los clientes.
        """
        # Enviar un mensaje a todos los clientes conectados
        for websocket in self.clients.values():
            await websocket.send(message)


    async def run_forever(self):
        """
        Ejecutar el servidor WebSocket de forma indefinida.
        """
        async with websockets.serve(self.handle, self.host, self.port):
            await asyncio.Future()  # Esperar indefinidamente