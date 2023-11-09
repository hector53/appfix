import json
import random
import string
import ssl
import requests
from websocket import create_connection
import logging


class HistoricoTV():
    def __init__(self):
        self.log = logging.getLogger("socketHistorico")

    def search(self, exchange, symbol):
        res = requests.get(
            f"https://symbol-search.tradingview.com/symbol_search/?text={symbol}&exchange={exchange}"
        )
        if res.status_code == 200:
            res = res.json()
            print(f"Response: {res}")  # Print the response
            assert len(res) != 0, "Nothing Found."
            return res[0]
        else:
            print("Network Error!")
            exit(1)

    def get_auth_token(self):
        sign_in_url = 'https://www.tradingview.com/accounts/signin/'
        username = ''
        password = ''
        data = {"username": username, "password": password, "remember": "on"}
        headers = {
            'Referer': 'https://www.tradingview.com'
        }
        response = requests.post(url=sign_in_url, data=data, headers=headers)
        auth_token = response.json()['user']['auth_token']    
        return auth_token
    
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
    
    def generateSession(self):
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string

    def chartSession(self):
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "cs_" + random_string
    
    def prependHeader(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def constructMessage(self, func, paramList):
        return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))
    
    def createMessage(self, func, paramList):
        return self.prependHeader(self.constructMessage(func, paramList))

    def sendMessage(self, ws, func, args):
        #start_time = time.time()  # Registra el tiempo antes de enviar el mensaje
        ws.send(self.createMessage(func, args))

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
                
        print(f"Symbols: {symbols}")  # Print the symbols
        return symbols
    async def get_data_for_symbol(self, pairs, limit):
        ws = self.create_websocket_connection()
        contador = 0
        try:
            session = self.generateSession()
            print("session: ",session)

            self.sendMessage(ws, "quote_create_session", [session])
            print("Sent quote_create_session")

           
            # For each pair, get all the symbols (including contracts) and add them to the session
            for i, pair in enumerate(pairs):
                # Generate a unique symbol name for this pair
                symbol_name = f"sds_sym_{i+1}"

                # No need to search pair from specified market category, using pair as symbol_id directly
                symbol_id = pair.upper()
                self.sendMessage(ws, "quote_add_symbols", [session, symbol_id])
                print(f"Sent quote_add_symbols with {symbol_id}")

                # generate new chart session for each pair
                chart = self.chartSession()
                print("chart ",chart)

                # create new chart session for each pair
                self.sendMessage(ws, "chart_create_session", [chart, ""])  
                print("Sent chart_create_session")

                self.sendMessage(ws, "resolve_symbol", [chart, symbol_name, symbol_id])
                print(f"Sent resolve_symbol with {symbol_id}")

                self.sendMessage(ws, "create_series", [chart, f"sds_{i+1}", f"s{i+1}", symbol_name, "1D", limit, ""])
                print("Sent historical")
                print("se acabaron los simbolos")
            print("se acabaron los pairs")
            response = await self.escuchar_socket(ws, pair)
            # Start receiving historical data
            return response

        except Exception as e:
            print(f"ERROR: {e}")
    async def escuchar_socket(self, ws, pair):
        try:
            response = {}
            r = False
            while True:
                print("ciclo infinito")
                result = ws.recv()
               # self.log.info(f"result: {result}")
                messages = result.split("~m~")
                messages = [msg for msg in messages if msg]

                for msg in messages:
                    if msg.startswith("{"):
                        res, result = self.process_history_message(msg, pair)
                        if res:
                            response = result 
                            r = True
                            print("WebSocket connection closed.")
                            break 
                if r:
                    break
                
            return response
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return None

    def process_history_message(self, msg,pair):
       # log.info(f"llego mensaje de socket pair: {pair} :{msg} ")
        try:
            json_res = json.loads(msg)
            if json_res["m"] == "timescale_update":
                if "sds_1" in json_res["p"][1]:  # If the 'sds_1' key exists in the message. "s" trae la data
                    historical_data = json_res["p"][1]["sds_1"]["s"]
                    formatted_data = self.format_historical_data(historical_data)
                    return True, formatted_data
            return False, {}
        except json.JSONDecodeError:
            print(f"Failed to decode JSON message: {msg}")
            return False, {}
        except KeyError:
            print(f"Key 'm' not found in history message: {json_res}")
            return False, {}
        
    def format_historical_data(self, historical_data):
        formatted_data = []
        for data in historical_data:
            record = {
                "Timestamp": data['v'][0],
                "Open": data['v'][1],
                "High": data['v'][2],
                "Low": data['v'][3],
                "Close": data['v'][4]
            }
            # Check if 'Volume' exists
            if len(data['v']) > 5:
                record["Volume"] = data['v'][5]
            formatted_data.append(record)
        
        return formatted_data