from websocket_server import WebsocketServer
from threading import Thread
import logging
import json
import asyncio
import pymongo
from datetime import timedelta, datetime
logging.basicConfig(filename=f'reportsSidebar.log', level=logging.INFO,
                    format='%(asctime)s %(name)s  %(levelname)s  %(message)s  %(lineno)d ')
   
class socketServer(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.log = logging.getLogger("SockerSidebar")
        self.server = WebsocketServer(self.host, self.port, logging.INFO) 
        self.clients = []
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["rofex"]

    def get_ordenes(self, limit):
        collection = self.db["ordenes"]
        fecha_actual=datetime.today()
        # Agregar 4 horas a la fecha actual
        fecha_actual_mas_4h=fecha_actual + timedelta(hours=4)
        # Convertir la fecha a un formato legible
        fecha_actual_mas_4h_str=fecha_actual_mas_4h.strftime(
        "%Y%m%d")
        fechaBuscar = fecha_actual_mas_4h_str
        ordenesPendientes = collection.aggregate([
        {"$match": {"$or": [
      { "ordStatus": "NEW" },
      { "ordStatus": "PARTIALLY FILLED" },
    ], "active": True, "transactTime": {"$regex": f"^{fechaBuscar}"}}
    },
        {"$sort": {"transactTime": -1}},
        {"$group": {
        "_id": "$symbol",
        "ordenes": {"$push": {
            "symbol": "$symbol",
        "side": "$side",
        "transactTime": "$transactTime", 
        "ordType": "$ordType", 
        "price":"$price", 
        "leavesQty": "$leavesQty",
        "id_bot": "$id_bot"
        }},
        "count": {"$sum": 1}
        }},
        {"$project": {
        "symbol": "$_id",
        "ordenes": {"$slice": ["$ordenes", limit]},
        "_id": 0
        }},
        ])


        ordenesEjecutadas=collection.aggregate([
        {"$match": {"$or": [
        {"ordStatus": "FILLED"},
        {"ordStatus": "PARTIALLY FILLED"},
        
        ], "transactTime": {"$regex": f"^{fechaBuscar}"}}},
        {"$sort": {"transactTime": -1}},
        {"$group": {
        "_id": "$symbol",
        "ordenes": {"$push": {
             "symbol": "$symbol",
            "side": "$side",
            "transactTime": "$transactTime", 
            "ordType": "$ordType", 
            "price":"$price", 
            "lastQty": "$lastQty",
            "id_bot": "$id_bot"
        }},
        "count": {"$sum": 1}
        }},
        {"$project": {
        "symbol": "$_id",
        "ordenes": {"$slice": ["$ordenes", limit]},
        "_id": 0
        }},
        ])
        pendientes = list(ordenesPendientes)
        ejecutadas = list(ordenesEjecutadas)
        return {"pendientes": pendientes, "ejecutadas": ejecutadas}

    def close(self):
        self.server.shutdown_abruptly()
        
    async def run(self):
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
       # self.log.info(f"procesando mensaje de cliente .....: {task}")
        if task["type"]==1: 
            ordenes = self.get_ordenes(task["limit"])
            self.broadcast(str(ordenes))

        
    def handleMessage(self, client, server, message):
        print("cliente envio mensaje: ", message)
        encode_json = json.loads(str(message).replace("'", '"'))
        self.process_message(encode_json)
       # self.message_queue.put_nowait(encode_json)
        pass
    
    def handleClose(self, client, server):
        self.clients.remove(client)


async def main():
    sock = socketServer('127.0.0.1', 5250)
    try:
        await sock.run()
    except KeyboardInterrupt:
        sock.close()
        print("saliendo del socket")
    finally: 
        print("saliendo de todo")


if __name__ == '__main__':
    asyncio.run(main())