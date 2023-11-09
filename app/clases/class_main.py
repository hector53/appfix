from app.fix_application.application import Application
import quickfix as fix
from threading import Thread
import asyncio
import logging
from threading import Thread
from app.WebSocket.broadcastWebSocket import socketServer
#class main para quickfix 
class MainTask():
    def __init__(self, config_file, market, user, passwd, account, target, accountFixId, puertows):
        self.target = target
        self.market = market
        self.user = user
        self.passwd = passwd
        self.account = account
        self.accountFixId = accountFixId
        self.settings = config_file
        self.threadFix = None
        self.message_queue = asyncio.Queue()
        #server Broadcaster
        self.log = logging.getLogger("MainFix")
        self.storefactory = fix.FileStoreFactory(config_file)
        self.logfactory = fix.FileLogFactory(config_file)
        self.application = Application(self.market, self.user, self.passwd, self.account)
        self.server_md = socketServer('127.0.0.1', int(puertows), self.application)
        self.server_md.start()
        self.application.server_md = self.server_md
        self.initiator = fix.SocketInitiator(self.application, self.storefactory, self.settings, self.logfactory)
        self.threadCola = None
        self.stopCola = asyncio.Event()
        self.taskToCancel = None
        self.threadBalance = None
    
    async def checkLoggedOn(self):
        #logfix.info(f"entrando a checklogon in hilo")
        while self.application.sessions[self.target]['connected']==None:
            await asyncio.sleep(0.1)
        #logfix.info(f"saliendo a checklogon")
        return self.application.sessions[self.target]['connected']

    async def check_logged_on(self):
        task = asyncio.create_task(self.checkLoggedOn())
        # Esperar a que la tarea asincrónica termine y devuelva su resultado
        response = await task
        return response
    
    async def run(self):
        try:
            #logfix.info(f"entrando a run de main class")
            self.threadFix = Thread(target=self.initiator.start)
            #logfix.info(f"threfix: { self.threadFix} ")
            self.threadFix.start()
            #logfix.info(f"ya envie el iniciador de fix")
           # self.threadCola = Thread(target=self.startCola)
          #  self.threadCola.start()
            #logfix.info(f"user: {self.user}")
            if self.user != "FIX_BZ_ESCODA":
                #logfix.info(f"nmo es un usuario balanc")
                self.threadBalance = Thread(target=self.startLoopBalance)
                self.threadBalance.start()
            
        finally:
            self.log.error("se cerro el run d ela tarea main task")
        
    def startLoopBalance(self):
        loop = asyncio.new_event_loop()# creo un nuevo evento para asyncio y asi ejecutar todo de aqui en adelante con async await 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_forever_balance())#ejecuto la funcion q quiero
        loop.close()
    
    def startCola(self):
        loop3 = asyncio.new_event_loop()# creo un nuevo evento para asyncio y asi ejecutar todo de aqui en adelante con async await 
        asyncio.set_event_loop(loop3)
        loop3.run_until_complete(self.run_forever())#ejecuto la funcion q quiero
        loop3.close()

    async def run_forever_balance(self):
        #logfix.info(f"estoy en el ciclo run_forever_balance")
        try:
            contador = 0
            while not self.stopCola.is_set():
                contador+=1
                if contador>=300:
                    await self.consultar_balances_en_cuentas()
                    contador=0
                await asyncio.sleep(0.1)
        except Exception as e:
            # Manejar la excepción adecuadamente
            self.log.error(f"Se ha producido una excepción: {e}")
        finally: 
            self.log.error(f"se cerro el ciclo del balance")

    async def consultar_balances_en_cuentas(self):
        from app import mongo
        from bson import ObjectId
        #logfix.info("consultar balances ")
         #primero necesito las cuentas activas 
        try: 
            cuentas = []
            #mejor las traigo de la db 
            cuentasFix = mongo.db.cuentas_fix.find_one({'_id': ObjectId(self.accountFixId)})
            if cuentasFix:
                #logfix.info("si tengo cuentas en este user ")
                cuentas = cuentasFix["cuentas"]
            if len(cuentas)>0:
                #logfix.info(f"si hay cuentas: {cuentas}")
                for cuenta in cuentas:
                    #logfix.info(f"consultando balance en cuenta: {cuenta['cuenta']}  ")
                    await self.update_balance_general(cuenta["cuenta"])
        except Exception as e: 
            self.log.error(f"error al actualizar balance de cuentas: {e}")

    async def update_balance_general(self, cuenta=""):
        if cuenta == "":
            cuenta = self.cuenta
        #logfix.info("primero pedir el balance actual")
        balance = await self.get_balance(cuenta)
        #logfix.info(f"balance {balance}")
        if balance != 0:
            try:
                #logfix.info(f"ahora actualizar la variable ")
                newBalance = balance["detailedAccountReports"][
                        "0"]["currencyBalance"]["detailedCurrencyBalance"]
                self.application.balance[cuenta] =  newBalance
                self.server_md.broadcast(str({"type": 2, "cuenta": cuenta, "balance": newBalance}))
                #logfix.info(                    f"nuevo balance es: {self.application.balance[cuenta]}")
            except Exception as e:
                self.log.error(f"error actualizando balance: {e}")
        else:
            self.log.error("error consultando balance")

    async def run_forever(self):
        #logfix.info(f"estoy en el ciclo start")
        try:
            while not self.stopCola.is_set():
             #   #logfix.info("ciclo infinito")
                if not self.message_queue.empty():
                    task = await self.message_queue.get()
                    asyncio.create_task(self.process_message(task))
                    self.message_queue.task_done()
                await asyncio.sleep(0.01)
        except Exception as e:
            # Manejar la excepción adecuadamente
            self.log.error(f"Se ha producido una excepción: {e}")
        finally: 
            self.log.error(f"se cerro el ciclo de cola en main task")

    async def stopColaFix(self):
        #logfix.info(f"deteniendo cola")
        self.stopCola.set()

    async def update_tickers_bot(self, task):
        id_bot = task["id_bot"]
        #logfix.info(f"""procesando tarea de enviar actualizacion de book al id_bot: {id_bot}, 
       # aqui agregamos tarea a la cola del bot para verificar puntas, pero primero actualizamos tickers en el bot """)
        #task = {"type": 0, "symbolTicker": symbolTicker, "marketData": data["marketData"], 
                    #   "id_bot": self.suscripcionId[MDReqID]["id_bot"] }
        #logfix.info(f"bot data: {self.botManager.main_tasks[id_bot].botData}")
        #logfix.info(f"self.botManager.tasks: {self.botManager.tasks}")
        #logfix.info(f"self.botManager.main_tasks: {self.botManager.main_tasks}")            
        symbolTicker = task["symbolTicker"]
        marketData = task["marketData"]
        if id_bot in self.botManager.main_tasks:
            #logfix.info(f"tickers antes: {self.botManager.main_tasks[id_bot]._tickers[symbolTicker]}")
            self.botManager.main_tasks[id_bot]._tickers[symbolTicker] = marketData
            #logfix.info(f"tickers despues: {self.botManager.main_tasks[id_bot]._tickers[symbolTicker]}")
            #logfix.info(f"ahora si agregamos tarea al bot para verificar puntas")
            if self.botManager.main_tasks[id_bot].botData["botIniciado"]==True:
                await self.botManager.main_tasks[id_bot].add_task(task)
            #logfix.info(f"listo tarea agregada al bot")
            #logfix.info(f"self.botManager.tasks: {self.botManager.tasks}")
            #logfix.info(f"self.botManager.main_tasks: {self.botManager.main_tasks}") 
        else:
            self.log.error("el bot no esta en el botManager quizas ya se detuvo")
       # await asyncio.sleep(0.1)

    def process_message(self, task):
        #logfix.info(f"procesando mensaje de cliente .....: {task}")
        if "type" in task:
            #logfix.info(f"si hay type")
            if task["type"]==3:
                #logfix.info(f"es new order ")
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
                #logfix.info(f"es modify order ")
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
                #logfix.info(f"es cancel order ")
                #new order 
                cuenta = task["cuenta"]
                clOrdId = task["clOrdId"]
                origClOrdId = task["origClOrdId"]
                symbol = task["symbol"]
                side = task["side"]
                quantity = task["quantity"]
                order = self.application.orderCancelRequest(clOrdId, origClOrdId, side, quantity, symbol, cuenta)
        


    async def get_balance(self, account=""):
        try:
            #logfix.info(f"get balance {account} ")
            balance = self.application.rest.get_balance(account)
            #logfix.info(f"balance {balance}")
            return balance["accountData"]
        except Exception as e:
            self.log.error(f"error solicitando balance: {e}")
            return 0