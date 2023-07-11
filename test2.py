import json
import random
import re
import string
import ssl
import time
import csv

import requests
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException

def search(query, type):
    res = requests.get(
        f"https://symbol-search.tradingview.com/symbol_search/?text={query}&type={type}"
    )
    if res.status_code == 200:
        res = res.json()
        assert len(res) != 0, "Nothing Found."
        return res[0]
    else:
        print("Network Error!")
        exit(1)

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

def get_auth_token():
    sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    username = ''
    password = ''
    data = {"username": username, "password": password, "remember": "on"}
    headers = {'Referer': 'https://www.tradingview.com'}
    response = requests.post(url=sign_in_url, data=data, headers=headers)
    auth_token = response.json()['user']['auth_token']    
    return auth_token

def constructMessage(func, paramList):
    return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))

def prependHeader(st):
    return "~m~" + str(len(st)) + "~m~" + st

def createMessage(func, paramList):
    return prependHeader(constructMessage(func, paramList))

def sendMessage(ws, func, args):
    ws.send(createMessage(func, args))



def format_historical_data(historical_data):
    formatted_data = []
    for data in historical_data:
        record = {
                        "Timestamp": data['v'][0],
                        "Open": data['v'][1],
                        "High": data['v'][2],
                        "Low": data['v'][3],
                        "Close": data['v'][4],
                        "Volume": data['v'][5]
                    }
        formatted_data.append(record)
    
    return formatted_data


def process_history_message(msg,pair):
    try:
        json_res = json.loads(msg)
        if json_res["m"] == "timescale_update":
            print("Received historical data:")
            if "sds_1" in json_res["p"][1]:  # If the 'sds_1' key exists in the message. Hay que hacer un bucle pidiendo el nombre de cada simbolo. 
                historical_data = json_res["p"][1]["sds_1"]["s"]
                formatted_data = format_historical_data(historical_data)

                # Save formatted data into CSV file
                with open(f'{pair}_historical_data.csv', 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=formatted_data[0].keys())
                    writer.writeheader()
                    for data in formatted_data:
                        writer.writerow(data)

                print("Historical data saved into CSV file.")
                return True
    except json.JSONDecodeError:
        print(f"Failed to decode JSON message: {msg}")
    except KeyError:
        print(f"Key 'm' not found in history message: {json_res}")
    return False


def getSymbolId(pair, market):
    data = search(pair, market)

    # Try to access the 'contracts' list and get the 'symbol' from the first contract
    try:
        contract = data["contracts"][0]  # Gets the first contract
        symbol_name = contract["symbol"]
    except (KeyError, IndexError):
        # If there are no contracts, fall back to the 'symbol' key
        symbol_name = data["symbol"]

    # As before, get the broker name
    try:
        broker = data["prefix"]
    except KeyError:
        broker = data["exchange"]

    symbol_id = f"{broker.upper()}:{symbol_name.upper()}"
    print(symbol_id, end="\n\n")
    return symbol_id

def socketJob(ws):
    prices = {}  
    buffer = ""  
    last_ping_time = time.time()  # Registra el tiempo del último ping enviado
    result = None

    while True:
        try:

            result = ws.recv()
            #print(f"Recibido: {result}")  # Añade este print
            messages = result.split("~m~")
            messages = [msg for msg in messages if msg]

            for msg in messages:
                if msg.startswith("{"):
                    process_history_message(msg,pair)
                    
                elif len(msg) > 0:
                    buffer += msg

            if buffer.startswith("{"):
                process_history_message(buffer,pair)
                buffer = ""

        except KeyboardInterrupt:
            #print("\nGoodbye!")
            exit(0)
        except WebSocketConnectionClosedException:
            print("La conexión con el WebSocket se ha cerrado. Reintentando en 5 segundos...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            ws = create_websocket_connection()  # Re-create the connection
            continue
        except Exception as e:
            print(f"ERROR: {e}\nTradingView message: {result}")
            continue

def sendCreateSeriesMessage(ws, session, params):
    func = "create_series"
    args = [session] + params  # Aquí estamos asumiendo que `params` es una lista con los parámetros requeridos
    sendMessage(ws, func, args)

def create_websocket_connection():
    # create tunnel
    tradingViewSocket = "wss://prodata.tradingview.com/socket.io/websocket?from=chart/DZ1tUo5u/" #'wss://data.tradingview.com/socket.io/websocket?from=chart/DZ1tUo5u/&date=XXXX_XX_XX-XX_XX'
    headers = json.dumps({"Origin": "https://www.tradingview.com", "Accept-Encoding": "gzip, deflate, br", 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

    # Add these two lines to create a context that doesn't check the SSL certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    ws = create_connection(tradingViewSocket, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
    return ws

def main(pairs):
    ws = create_websocket_connection()

    try:
        session = generateSession()
        print("session: ",session)
        #auth_token = get_auth_token() 
        #print("auth: ",auth_token)

        # Send messages
        #sendMessage(ws, "set_auth_token", [auth_token]) 
        #print("Sent set_auth_token")
        sendMessage(ws, "quote_create_session", [session])
        print("Sent quote_create_session")

        for i, pair in enumerate(pairs):
            # Generate a unique symbol name for this pair
            symbol_name = f"sds_sym_{i+1}"

            # No need to search pair from specified market category, using pair as symbol_id directly
            symbol_id = pair.upper()
            sendMessage(ws, "quote_add_symbols", [session, symbol_id])
            print(f"Sent quote_add_symbols with {symbol_id}")

            # generate new chart session for each pair
            chart = chartSession()
            print("chart ",chart)

            # create new chart session for each pair
            sendMessage(ws, "chart_create_session", [chart, ""])  
            print("Sent chart_create_session")

            sendMessage(ws, "resolve_symbol", [chart, symbol_name, symbol_id])
            print(f"Sent resolve_symbol with {symbol_id}")

            sendMessage(ws, "create_series", [chart, f"sds_{i+1}", f"s{i+1}", symbol_name, "1D", 5000, ""])
            print("Sent historical")

        # Start receiving historical data
        while True:
            result = ws.recv()
            messages = result.split("~m~")
            messages = [msg for msg in messages if msg]

            for msg in messages:
                if msg.startswith("{"):
                    if process_history_message(msg, pair):
                        ws.close()
                        print("WebSocket connection closed.")
                        return

    except Exception as e:
        print(f"ERROR: {e}")
        time.sleep(5)  # Wait for 5 seconds before retrying
        ws = create_websocket_connection()  # Re-create the connection


if __name__ == "__main__":
    pairs = ["CBOT_DL:ZSN2022"]  # add or remove pairs as needed
    main(pairs)
