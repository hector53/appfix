from app.fix_application.application import Application
from app.clases.class_web_socket_server import WebSocketServer
import logging
class socketMessages():
    def __init__(self, application:Application):
        self.clOrdIdEsperar = {}
        self.application = application
        self.server:WebSocketServer = None
        self.log = logging.getLogger("soccketMessage")

    def setServer(self, server:WebSocketServer):
        self.server = server

    async def process_message(self, message):
        #aqui espero que me llegue un mensaje como este
        """ {
            "type": 4,#modify order
            "user_fix": self.user, 
            "cuenta": cuenta, 
            "orderId": orderId, 
            "clOrdId": clOrdId, 
            "origClOrdId": origClOrdId, 
            "symbol": symbol, 
            "side": side, 
            "price": price,
            "quantity": quantity, 
            "orderType": orderType,
            "id_bot": id_bot
        }"""
        #entonces voy primero a verificar que el campo id_bot exista en el message
        if "id_bot" in message:
            self.log.info("si existe id_bot en el mensaje por ende es un mensaje de algun bot")

            #ahora si identifico el mensaje segun su type 
            if message["type"]==3:
                self.clOrdIdEsperar[message["clOrdId"]] = message
                self.log.info(f"es new order ")
                #new order 
                cuenta = message["cuenta"]
                clOrdId = message["clOrdId"]
                symbol = message["symbol"]
                side = message["side"]
                quantity = message["quantity"]
                price = message["price"]
                orderType = message["orderType"]
                order = await self.application.newOrderSingle(clOrdId, symbol, side, quantity, 
                price, orderType,cuenta=cuenta )
                self.log.info(f"order in socket message {order}")
                self.server.send_message(message["id_bot"], str(order))

            if message["type"]==4:
                self.log.info(f"es modify order ")
                #new order 
                cuenta = message["cuenta"]
                clOrdId = message["clOrdId"]
                orderId = message["orderId"]
                origClOrdId = message["origClOrdId"]
                symbol = message["symbol"]
                side = message["side"]
                quantity = message["quantity"]
                price = message["price"]
                orderType = message["orderType"]
                order = await self.application.orderCancelReplaceRequest(clOrdId, orderId, origClOrdId, side,  orderType, symbol,
                                                                    quantity=quantity, price=price, cuenta=cuenta )
                self.server.send_message(message["id_bot"], str(order))
        
            if message["type"]==5:
                self.log.info(f"es cancel order ")
                #new order 
                cuenta = message["cuenta"]
                clOrdId = message["clOrdId"]
                origClOrdId = message["origClOrdId"]
                symbol = message["symbol"]
                side = message["side"]
                quantity = message["quantity"]
                order = await self.application.orderCancelRequest(clOrdId, origClOrdId, side, quantity, symbol, cuenta)
                self.server.send_message(message["id_bot"], str(order))
        
           # if message["type"]=="bb":
            #    self. application.server_md.broadcast(str(message))

         #   if message["type"]=="puntas":
              #  self.application.server_md.broadcast(str(message))
        pass

