from websocket_server import WebsocketServer
from threading import Thread
import logging
import json
class socketServer(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.log = logging.getLogger("SockerSidebar")
        self.server = WebsocketServer(self.host, self.port, logging.INFO) 
        self.clients = []
        
    def close(self):
        self.server.shutdown_abruptly()
        
    def run(self):
        self.server.set_fn_new_client(self.handleConnected)
        self.server.set_fn_client_left(self.handleClose)   
        self.server.set_fn_message_received(self.handleMessage)   
        self.server.run_forever()
    
    def handleInterrupt(self, signal, frame):
      #  self.log.info("Señal SIGINT recibida. Deteniendo servidor de WebSocket...")
        self.close()
        
    def broadcast(self, message):
        for client in self.clients:
            self.send(client, message)
                
    def send(self, client, message):
        self.server.send_message(client, message)
        
    def handleConnected(self, client, server):  
        print("cliente conectado", client)
        self.clients.append(client) 

    def process_message(self, task):
        self.log.info(f"procesando mensaje de cliente .....: {task}")
#            self.broadcast(str(ordenes))

        
    def handleMessage(self, client, server, message):
        print("cliente envio mensaje: ", message)
        encode_json = json.loads(str(message).replace("'", '"'))
        self.process_message(encode_json)
       # self.message_queue.put_nowait(encode_json)
        pass
    
    def handleClose(self, client, server):
        self.clients.remove(client)