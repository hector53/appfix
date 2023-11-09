import asyncio
import websocket
from threading import Thread
import logging
from socketServer import socketServer
import json
import ssl
import string
import requests
import random
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException

class TVSocket(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.changing_pairs = False
        self.pairs = []
        self.log = logging.getLogger("SockerSidebar")
        self.server = socketServer(host, port, self)
        self.server.start()
        

    # Método para cerrar la conexión WebSocket de manera segura
    async def close_client_socket(self):
        # Comprueba si la conexión WebSocket está abierta antes de intentar cerrarla
        if self.ws and not self.ws.closed:
            self.ws.close()

    def generateSession(self):
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string
    
    def search(self, exchange, symbol):
        #print(f"Searching for: {symbol} on exchange: {exchange}")  # #print the search query
        res = requests.get(
            f"https://symbol-search.tradingview.com/symbol_search/?text={symbol}&exchange={exchange}"
        )
        if res.status_code == 200:
            res = res.json()
            #print(f"Response: {res}")  # #print the response
            assert len(res) != 0, "Nothing Found."
            return res[0]
        else:
            #print("Network Error!")
            exit(1)
    
    def getSymbolId(self, data):
        # Here data is the whole response from search()
        symbols = []
        # Check if the 'contracts' key exists and has elements
        if 'contracts' in data and len(data['contracts']) > 0:
            # If it does, get all the contracts and append them to the symbols list
            for contract in data['contracts']:
                symbols.append(f"{data['exchange'].upper()}:{contract['symbol'].upper()}")
        else:
            # If there are no contracts, just get the 'symbol' key
            symbols.append(f"{data['exchange'].upper()}:{data['symbol'].upper()}")
                
        #print(f"Symbols: {symbols}")  # #print the symbols
        return symbols
     
    def suscribir_data(self,ws, pairs):
        print("suscribir_data", pairs)
        session = self.generateSession()
        self.sendMessage(ws, "quote_create_session", [session])
        self.sendMessage(ws, "quote_set_fields", [session, 'base-currency-logoid', 'ch', 'chp', 'currency-logoid', 'currency_code', 'current_session', 'description', 'exchange', 'format', 'fractional', 'is_tradable', 'language', 'local_description', 'logoid', 'lp', 'lp_time', 'minmov', 'minmove2', 'original_name', 'pricescale', 'pro_name', 'short_name', 'type', 'update_mode', 'volume', 'ask', 'bid', 'fundamentals', 'high_price', 'low_price', 'open_price', 'prev_close_price', 'rch', 'rchp', 'rtc', 'rtc_time', 'status', 'industry', 'basic_eps_net_income', 'beta_1_year', 'market_cap_basic', 'earnings_per_share_basic_ttm', 'price_earnings_ttm', 'sector', 'dividends_yield', 'timezone', 'country_code', 'provider_id']) 
        # For each pair, get all the symbols (including contracts) and add them to the session
        for i, pair in enumerate(pairs):
            print("pair", pair)
            # Split the pair into exchange and symbol
            exchange, symbol = pair.split(':')
            # Search for the symbol in the specified market category
            data = self.search(exchange, symbol)
            # Get all the symbol IDs from the response
            symbol_ids = self.getSymbolId(data)
            # Add all the symbols to the session
            for symbol_id in symbol_ids:
                print("symbol_id", symbol_id)
                self.sendMessage(ws, "quote_add_symbols", [session, symbol_id])
        print("saliendo de suscribir data")

    def create_websocket_connection(self):
        # create tunnel
        tradingViewSocket = "wss://prodata.tradingview.com/socket.io/websocket" #'wss://data.tradingview.com/socket.io/websocket?from=chart/DZ1tUo5u/&date=XXXX_XX_XX-XX_XX'
        headers = json.dumps({"Origin": "https://www.tradingview.com", "Accept-Encoding": "gzip, deflate, br", 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

        # Add these two lines to create a context that doesn't check the SSL certificate
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        ws = create_connection(tradingViewSocket, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
        return ws
    
    def prependHeader(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def constructMessage(self, func, paramList):
        return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))

    def createMessage(self, func, paramList):
        return self.prependHeader(self.constructMessage(func, paramList))

    def sendMessage(self, ws, func, args):
        ws.send(self.createMessage(func, args))

    def process_message(self, msg, prices):
        try:
            jsonRes = json.loads(msg)
        #    print("jsonRes", jsonRes)
            if jsonRes["m"] == "qsd":
                try:
                    symbol = jsonRes["p"][1]["n"]
                    keys = ["lp", "bid", "ask", "ch", "chp", "volume"]
                    if symbol not in prices:
                        prices[symbol] = {}
                    for key in keys:
                        value = jsonRes["p"][1]["v"].get(key)
                        if value is not None:
                            prices[symbol][key] = value
                  #  print("precios",json.dumps(prices))
                    self.server.broadcast(json.dumps(prices))
                except KeyError:
                    print("Could not find key in message:")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON message.")
        except KeyError:
            print(f"Key 'm' not found in price message.")
    
    # Método para hacer un update de pairs desde el cliente
    def update_pairs(self, message):
        # Intenta decodificar el mensaje. Si falla, regresa inmediatamente.
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError:
            return

        # Si el mensaje no contiene la clave 'pairs', regresa inmediatamente.
        if 'pairs' not in message_data:
            return

        # El mensaje es relevante, procede como de costumbre.
        self.changing_pairs = True
        self.pairs = message_data["pairs"]
        print("Cambiando pairs")

    async def run_client_socket(self):
        print("entrando al run client socket")
        prices = {}  
        while True:
            try:
                # Crear una conexión WebSocket segura utilizando la función create_connection
                if self.changing_pairs==True:
                    self.changing_pairs=False
                ws = self.create_websocket_connection()
                self.suscribir_data(ws,self.pairs)
                # Recibir mensajes del servidor
                try:
                    while self.changing_pairs==False:
                     #   print("escuchando")
                        result = ws.recv()
                     #   print("result", result)
                        messages = result.split("~m~")
                        messages = [msg for msg in messages if msg]
                        for msg in messages:
                           # print("msg", msg)
                            if msg.startswith("{"):
                               # print("msg", msg)
                                #start_time = time.time()
                                self.process_message(msg, prices)
                    print("saliendo del ciclo infinito q escucha")
                    ws.close()
                    prices = {}
                except Exception as e:
                    ws.close()
                    print("error en el ciclo infinito q escucha")

            except Exception as e:
                print("Error: " + str(e))
                print("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

async def main():
    client = TVSocket("127.0.0.1", 5353)
    pairs = ["CBOT:ZS","CBOT:ZC","CBOT:ZW", "MATBAROFEX:SOJ.ROS","MATBAROFEX:MAI.ROS","MATBAROFEX:TRI.ROS", "BINANCE:BTCUSDT", "SP:SPX", "NASDAQ:NDX", "BINANCE:ETHUSDT", "NYMEX:CL1!", "COMEX:GC1!"]
    client.pairs = pairs
    print("pairs", client.pairs)
    try:
        await client.run_client_socket()
    except KeyboardInterrupt:
        client.server.close()
    print("terminado todo")


if __name__ == "__main__":
    asyncio.run(main())