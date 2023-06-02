from websocket_server import WebsocketServer
from threading import Thread
import logging
import json
import asyncio
from asyncio import Queue
from app.fix_application.application import Application
class socketServer(Thread):
    def __init__(self, host, port, application:Application):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.log = logging.getLogger("SockerFix")
        self.application = application
        self.server = WebsocketServer(self.host, self.port, logging.INFO) 
        self.clients = []

    def close(self):
        self.server.shutdown_abruptly()
        
    def run(self):
        self.server.set_fn_new_client(self.handleConnected)
        self.server.set_fn_client_left(self.handleClose)   
        self.server.set_fn_message_received(self.handleMessage)   
        self.server.run_forever()
        
    def broadcast(self, message):
        for client in self.clients:
            self.send(client, message)
                
    def send(self, client, message):
        self.server.send_message(client, message)
        
    def handleConnected(self, client, server):  
        self.clients.append(client) 

    def process_message(self, task):
        self.log.info(f"procesando mensaje de cliente .....: {task}")
        if "type" in task:
            self.log.info(f"si hay type")
            if task["type"]==3:
                self.log.info(f"es new order ")
                #new order 
                cuenta = task["cuenta"]
                clOrdId = task["clOrdId"]
                symbol = task["symbol"]
                side = task["side"]
                quantity = task["quantity"]
                price = task["price"]
                orderType = task["orderType"]
                order = self.application.newOrderSingle(clOrdId, symbol, side, quantity, 
                price, orderType,cuenta=cuenta )

            if task["type"]==4:
                self.log.info(f"es modify order ")
                #new order 
                cuenta = task["cuenta"]
                clOrdId = task["clOrdId"]
                orderId = task["orderId"]
                origClOrdId = task["origClOrdId"]
                symbol = task["symbol"]
                side = task["side"]
                quantity = task["quantity"]
                price = task["price"]
                orderType = task["orderType"]
                order = self.application.orderCancelReplaceRequest(clOrdId, orderId, origClOrdId, side,  orderType, symbol,
                                                                    quantity=quantity, price=price, cuenta=cuenta )
        
            if task["type"]==5:
                self.log.info(f"es cancel order ")
                #new order 
                cuenta = task["cuenta"]
                clOrdId = task["clOrdId"]
                origClOrdId = task["origClOrdId"]
                symbol = task["symbol"]
                side = task["side"]
                quantity = task["quantity"]
                order = self.application.orderCancelRequest(clOrdId, origClOrdId, side, quantity, symbol, cuenta)
        
            if task["type"]=="bb":
                self.application.server_md.broadcast(str(task))

            if task["type"]=="puntas":
                self.application.server_md.broadcast(str(task))
        
    def handleMessage(self, client, server, message):
        #print("cliente envio mensaje: ", message)
        encode_json = json.loads(str(message).replace("'", '"'))
        self.process_message(encode_json)
       # self.message_queue.put_nowait(encode_json)
        pass
    
    def handleClose(self, client, server):
        self.clients.remove(client)