import json
import random
import re
import string
import ssl
import time
import threading
import gzip
import base64
import requests
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException


from websocket_server import WebsocketServer

def new_client(client, server):
    print("New client connected")

def client_left(client, server):
    print("Client disconnected")

def message_received(client, server, message):
    print(f"Message from {client['id']}: {message}")
# Create a WebSocket server
server = WebsocketServer(port=5353)  # Listen on port 8080
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server_thread = threading.Thread(target=server.run_forever)


''' 
---Markets in TradingView---

interval = ['1', '5', '15', '30', '60', '120', '240', 1D, '1W', '1M']
'''

def search(exchange, symbol):
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

def get_auth_token():
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

def generateSession():
    stringLength = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for i in range(stringLength))
    return "qs_" + random_string

def chartSession():
    stringLength = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for i in range(stringLength))
    return "cs_" + random_string


def prependHeader(st):
    return "~m~" + str(len(st)) + "~m~" + st


def constructMessage(func, paramList):
    return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))


def createMessage(func, paramList):
    return prependHeader(constructMessage(func, paramList))


def sendMessage(ws, func, args):
    ws.send(createMessage(func, args))


ping_counter = 1  # Define una variable global para contar los pings
def sendPingPacket(ws):
    global ping_counter
    ping_message = f"~h~{ping_counter}"
    ping_packet = f"~m~{len(ping_message)}~m~{ping_message}"
    ws.send(ping_packet)
    ##print(f"Enviado mensaje ping: {ping_packet}")  # Añade este #print
    ping_counter += 1


def process_message(msg, prices):
    try:
        jsonRes = json.loads(msg)
        print("jsonRes", jsonRes)
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
                #print("precios",json.dumps(prices))
                if len(prices)>80:
                    server.send_message_to_all(json.dumps(prices))
            except KeyError:
                print("Could not find key in message:")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON message.")
    except KeyError:
        print(f"Key 'm' not found in price message.")
    # Enviar los precios a todos los clientes del servidor WebSocket
    

def getSymbolId(data):
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


def socketJob(ws):
    #print("entrando a socket job")
    prices = {}  
    buffer = ""  
    last_ping_time = time.time()  # Registra el tiempo del último ping enviado
    result = None

    while True:
        #print("entrando al ciclo de socket job")
        try:
            current_time = time.time()  # Registra el tiempo actual
            # Comprueba si ha pasado un minuto desde el último ping
            if current_time - last_ping_time >= 10:
                sendPingPacket(ws)  # Envia un nuevo ping
                last_ping_time = current_time  # Actualiza el tiempo del último ping enviado

            result = ws.recv()
           # #print(f"Recibido: {result}")  # Añade este #print
            messages = result.split("~m~")
            messages = [msg for msg in messages if msg]

            for msg in messages:
                if msg.startswith("{"):
                    #start_time = time.time()
                    process_message(msg, prices)
                    #end_time = time.time()
                    #elapsed_time = end_time - start_time
                    ##print(f"Tiempo: {elapsed_time * 1000} ms")
                    
              

        except KeyboardInterrupt:
            ##print("\nGoodbye!")
            server.shutdown()
            exit(0)
        except WebSocketConnectionClosedException:
            #print("La conexión con el WebSocket se ha cerrado. Reintentando en 5 segundos...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            ws = create_websocket_connection()  # Re-create the connection
            continue
        except Exception as e:
            print(f"ERROR: {e}\nTradingView message: ")
            continue

def sendCreateSeriesMessage(ws, session, params):
    func = "create_series"
    args = [session] + params  # Aquí estamos asumiendo que `params` es una lista con los parámetros requeridos
    sendMessage(ws, func, args)

def create_websocket_connection():
    # create tunnel
    tradingViewSocket = "wss://prodata.tradingview.com/socket.io/websocket" #'wss://data.tradingview.com/socket.io/websocket?from=chart/DZ1tUo5u/&date=XXXX_XX_XX-XX_XX'
    headers = json.dumps({"Origin": "https://www.tradingview.com", "Accept-Encoding": "gzip, deflate, br", 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

    # Add these two lines to create a context that doesn't check the SSL certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    ws = create_connection(tradingViewSocket, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
    return ws



def main(pairs):
    server_thread.start()
    ws = create_websocket_connection()
    contador = 0
    while True:  # Keep the connection alive
        #print("contador: ", contador)
        try:
            session = generateSession()
            #print("session: ",session)
            sendMessage(ws, "quote_create_session", [session])
            #print("Sent quote_create_session")

            sendMessage(ws, "quote_set_fields", [session, 'base-currency-logoid', 'ch', 'chp', 'currency-logoid', 'currency_code', 'current_session', 'description', 'exchange', 'format', 'fractional', 'is_tradable', 'language', 'local_description', 'logoid', 'lp', 'lp_time', 'minmov', 'minmove2', 'original_name', 'pricescale', 'pro_name', 'short_name', 'type', 'update_mode', 'volume', 'ask', 'bid', 'fundamentals', 'high_price', 'low_price', 'open_price', 'prev_close_price', 'rch', 'rchp', 'rtc', 'rtc_time', 'status', 'industry', 'basic_eps_net_income', 'beta_1_year', 'market_cap_basic', 'earnings_per_share_basic_ttm', 'price_earnings_ttm', 'sector', 'dividends_yield', 'timezone', 'country_code', 'provider_id']) 

            # For each pair, get all the symbols (including contracts) and add them to the session
            for i, pair in enumerate(pairs):
                # Split the pair into exchange and symbol
                exchange, symbol = pair.split(':')
                
                # Generate a unique symbol name for this pair
                symbol_name = f"sds_sym_{i+1}"

                # Search for the symbol in the specified market category
                data = search(exchange, symbol)

                # Get all the symbol IDs from the response
                symbol_ids = getSymbolId(data)

                # Add all the symbols to the session
                for symbol_id in symbol_ids:
                    sendMessage(ws, "quote_add_symbols", [session, symbol_id])
                    #print(f"Sent quote_add_symbols with {symbol_id}")

                    # Generate a new chart session for each symbol
                  #  chart = chartSession()
                    #print("chart ",chart)

                    # Create a new chart session for each symbol
                  #  sendMessage(ws, "chart_create_session", [chart, ""])  
                    #print("Sent chart_create_session")

                 #   sendMessage(ws, "resolve_symbol", [chart, symbol_name, symbol_id])
                    #print(f"Sent resolve_symbol with {symbol_id}")

                   # sendMessage(ws, "create_series", [chart, f"sds_{i+1}", f"s{i+1}", symbol_name, "1D", 10, ""])
                    #print("Sent historical")
                #print("se acabaron los simbolos")
            #print("se acabaron los pairs")


            socketJob(ws)

        except Exception as e:
            #print(f"ERROR: {e}")
            time.sleep(5)
            ws = create_websocket_connection()
            continue

        # Inicia el servidor WebSocket en un nuevo thread
        #server_thread = threading.Thread(target=server.run_forever)
        #server_thread.start()
        contador+=1


if __name__ == "__main__":
    pairs = ["CBOT:ZS","CBOT:ZC","CBOT:ZW", "MATBAROFEX:SOJ.ROS","MATBAROFEX:MAI.ROS","MATBAROFEX:TRI.ROS", "BINANCE:BTCUSDT", "SP:SPX"]
    main(pairs)

'''if __name__ == "__main__":
    ZS = ["CBOT:ZSN2023",'CBOT:ZSQ2023', 'CBOT:ZSU2023', 'CBOT:ZSX2023', 'CBOT:ZSF2024', 'CBOT:ZSH2024', 'CBOT:ZSK2024', 'CBOT:ZSN2024']
    ZC = ["CBOT:ZCN2023",'CBOT:ZCQ2023', 'CBOT:ZCU2023', 'CBOT:ZCX2023', 'CBOT:ZCF2024', 'CBOT:ZCH2024', 'CBOT:ZCK2024', 'CBOT:ZCN2024']
    ZW = ["CBOT:ZWN2023",'CBOT:ZWQ2023', 'CBOT:ZWU2023', 'CBOT:ZWX2023', 'CBOT:ZWF2024', 'CBOT:ZWH2024', 'CBOT:ZWK2024', 'CBOT:ZWN2024']
    SOJROS = ["MATBAROFEX:SOJ.ROSN2023",'MATBAROFEX:SOJ.ROSQ2023', 'MATBAROFEX:SOJ.ROSX2023', 'MATBAROFEX:SOJ.ROSF2024', 'MATBAROFEX:SOJ.ROSH2024', 'MATBAROFEX:SOJ.ROSK2024', 'MATBAROFEX:SOJ.ROSN2024']
    MAIROS = ["MATBAROFEX:MAI.ROSN2023",'MATBAROFEX:MAI.ROSU2023', 'MATBAROFEX:MAI.ROSV2023', 'MATBAROFEX:MAI.ROSZ2023','MATBAROFEX:MAI.ROSF2024', 'MATBAROFEX:MAI.ROSH2024', 'MATBAROFEX:MAI.ROSJ2024', 'MATBAROFEX:MAI.ROSN2024']
    TRIROS = ["MATBAROFEX:TRI.ROSN2023",'MATBAROFEX:TRI.ROSU2023', 'MATBAROFEX:TRI.ROSX2023', 'MATBAROFEX:TRI.ROSZ2023','MATBAROFEX:TRI.ROSF2024', 'MATBAROFEX:TRI.ROSH2024', 'MATBAROFEX:TRI.ROSN2024']
    SOYCME = ["MATBAROFEX:SOY.CMEM2023",'MATBAROFEX:SOY.CMEV2023',  'MATBAROFEX:SOY.CMEJ2024']
    CRNCME = ["MATBAROFEX:CRN.CMEM2023",'MATBAROFEX:CRN.CMEQ2023', 'MATBAROFEX:CRN.CMEX2023', 'MATBAROFEX:CRN.CMEJ2024']
    BTCUSDT = ["BINANCE:BTCUSDT"]
    pairs = ZS + ZC + ZW + SOJROS + MAIROS + TRIROS + SOYCME + CRNCME + BTCUSDT
    main(pairs)'''




# Este lo tengo que hacer con todos los futuros de cbot cme de agro
# Indices de EEUU, DXY, VIX
# Euro y real
# Oro y wti
# Activos argentinos?
# Brasil, IBOV, futuros BMFBOVESPA:SOY1! soja3 sjc1!
# https://stackoverflow.com/questions/65731895/accessing-private-websocket-data-from-tradingview-in-python
# https://github.com/rushic24/tradingview-scraper/tree/master 


