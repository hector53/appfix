from app import jsonify, request, abort, make_response
from app import  jwt_required,get_jwt_identity
from app import  ObjectId, mongo, logging, sesionesFix, time
from app import config_fix_settings
from app.models import DbUtils
from app.controllers.utils import UtilsController
from datetime import date, datetime, timedelta
from app.clases.class_main import MainTask
import asyncio
from threading import Thread
from app import thread, urlAppbots
from app.clases.class_rest_primary import RofexAPI
from app import urlAppbots
import requests
import json
log = logging.getLogger(__name__)

class FixController:

    @staticmethod
    async def newOrderTest():
        from app import fixM
      #  async def newOrderSingle(self, clOrdId, symbol, side, quantity, price, orderType, 
           #                      idTriangulo=0, cuenta=""):
        req_obj = request.get_json()
        print("req", req_obj)
        dataOrder = req_obj["dataOrder"]
        userFix = req_obj["userFix"]
        fixTask = await fixM.get_fixTask_by_id_user(userFix)
        if fixTask: 
            print("si tenemos la sesion iniciada para ese user")
            order = await fixTask.application.newOrderSingle(dataOrder["clOrdId"], dataOrder["symbol"],
                                                       dataOrder["side"], dataOrder["quantity"], 
                                                       dataOrder["price"], dataOrder["orderType"],
                                                       cuenta=dataOrder["cuenta"]
                                                        )
            return jsonify(order)
        else:
            print("no tenemos la sesion iniciada")
            abort(make_response(jsonify(message="sesion no iniciada"), 400))
        
    async def modify_order(): 
        from app import fixM
        print("modify_order: ")
        req_obj = request.get_json()
        print("req_obj", req_obj)
        print("fixM.main_tasks", fixM.main_tasks)
        user_fix = req_obj["user_fix"]
        cuenta = req_obj["cuenta"]
        orderId = req_obj["orderId"]
        origClOrdId = req_obj["origClOrdId"]
        clOrdId = req_obj["clOrdId"]
        symbol = req_obj["symbol"]
        side = req_obj["side"]
        price = req_obj["price"]
        orderType = req_obj["orderType"]
        quantity = req_obj["quantity"]
        order = {"llegoRespuesta": False}
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            order = await fixM.main_tasks[user_fix].application.orderCancelReplaceRequest(clOrdId, orderId, origClOrdId, side,  orderType, symbol, quantity, price, cuenta)
        return order

    async def cancel_order(): 
        from app import fixM
        print("cancel_order: ")
        req_obj = request.get_json()
        print("req_obj", req_obj)
        print("fixM.main_tasks", fixM.main_tasks)
        user_fix = req_obj["user_fix"]
        cuenta = req_obj["cuenta"]
        origClOrdId = req_obj["origClOrdId"]
        clOrdId = req_obj["clOrdId"]
        symbol = req_obj["symbol"]
        side = req_obj["side"]
        quantity = req_obj["quantity"]
        order = {"llegoRespuesta": False}
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            order = await fixM.main_tasks[user_fix].application.orderCancelRequest(clOrdId, origClOrdId, side, quantity, symbol,  cuenta)
        return order

    async def new_order(): 
        from app import fixM
        print("new_order: ")
        req_obj = request.get_json()
        print("req_obj", req_obj)
        print("fixM.main_tasks", fixM.main_tasks)
        user_fix = req_obj["user_fix"]
        cuenta = req_obj["cuenta"]
        clOrdId = req_obj["clOrdId"]
        symbol = req_obj["symbol"]
        side = req_obj["side"]
        quantity = req_obj["quantity"]
        price = req_obj["price"]
        orderType = req_obj["orderType"]
        order = {"llegoRespuesta": False}
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            order = await fixM.main_tasks[user_fix].application.newOrderSingle(clOrdId, symbol, side, quantity, 
                                                  price, orderType,cuenta=cuenta )
        return order

    async def get_positions():
        from app import fixM
        print("get_positions: ")
        req_obj = request.get_json()
        user_fix = req_obj["user_fix"]
        cuenta = req_obj["cuenta"]
        posiciones = []
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            getP = fixM.main_tasks[user_fix].application.rest.get_positions(cuenta)
            log.info(f"getP :{getP}")
            posiciones = getP
        log.info(f"return posiciones : {posiciones}")
        return jsonify(posiciones)
    
    async def unsuscribir_mercado():
        from app import fixM
        print("suscribir mercado: ")
        req_obj = request.get_json()
        print("req", req_obj)

        symbols = req_obj["symbols"]
        user_fix = req_obj["user_fix"]
        status = {"status": False}
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            #ahora si hago la solicitud a fix para suscribir a mercado en estos simbolos 
            # necesito un codigo unico para identificar cuando llegue la notificacion de esto
            status = await fixM.main_tasks[user_fix].application.marketDataRequest(entries=[0, 1], symbols=symbols, subscription=2,
                    depth=5, updateType=0)
        return jsonify(status)
    
    async def historico_visor():
        from app.clases.cla_historicotv import HistoricoTV
        req_obj = request.get_json()
        symbol = req_obj["symbol"]
        limit = req_obj["limit"]
        pairs = []
        pairs.append(symbol)
        his = HistoricoTV()
        result = await asyncio.create_task(his.get_data_for_symbol(pairs, limit))
        return jsonify(result)

    async def suscribir_mercado():
        from app import fixM
        print("suscribir mercado: ")
        req_obj = request.get_json()
        print("req", req_obj)
        
        symbols = req_obj["symbols"]
        user_fix = req_obj["user_fix"]
        status = {"status": False}
        if user_fix in fixM.main_tasks: 
            log.info(f"si existe la sesion de fix")
            #ahora si hago la solicitud a fix para suscribir a mercado en estos simbolos 
            # necesito un codigo unico para identificar cuando llegue la notificacion de esto
            status = await fixM.main_tasks[user_fix].application.marketDataRequest(entries=[0, 1], symbols=symbols, subscription=1,
                    depth=5, updateType=0)
        return jsonify(status)
        

    def ciclo_infinito(id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(FixController.ciclo_infinito_coro(id))
        finally:
            loop.close()

    # Función que ejecuta el ciclo infinito utilizando asyncio
    async def ciclo_infinito_coro(id):
        try: 
            while True:
                # Aquí puedes poner el código que quieras ejecutar en el ciclo infinito
                log.info(f"estoy en el ciclo infinito con asyncio: {id}")
                await asyncio.sleep(1)
        finally:
            log.info("saliendo del ciclo")



    def initC():
        global thread
        id = len(thread)
        thread[id] = Thread(target=FixController.ciclo_infinito, args=(id,))
        thread[id].start()
        # Creamos un nuevo hilo y lo iniciamos
        return 'Ciclo infinito iniciado'
    

        
      
    def stopC():
        global thread
        if thread is not None:
            # Detenemos el hilo
            thread.stop()
            thread = None
            return 'Ciclo infinito detenido'
        else:
            return 'El ciclo infinito no está en ejecución'

    async def iniciar_socket_bot(url, user, account, accountFixId, puertows ):
        import traceback
        payload = {
            "user": user, 
            "account": account, 
            "accountFixId": accountFixId,
            "puertows": puertows
        }
        print("entrando a iniciar socket bot", payload)
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{url}/api/iniciar_fix/new", data=json.dumps(payload), headers=headers)
            response.raise_for_status()  # Lanza una excepción si la respuesta es un código de error HTTP
            if response.status_code == 200:
                return True
            else:
                return False
        except requests.exceptions.HTTPError as err:
            print("Error HTTP: ", err)
            print(traceback.format_exc())
            return False
        except Exception as err:
            print("Ocurrió un error: ", err)
            print(traceback.format_exc())
            return False

    async def iniciar_fix_new():
        from app import fixM
        req_obj = request.get_json()
        print("req iniciar fix", req_obj)
        id_fix = req_obj["user"]["user"]
        accountFixId = req_obj["user"]["id"]
        BeginString = "FIXT.1.1"
        target = "ROFX"
        settings = config_fix_settings(req_obj["user"]["puerto"], BeginString, id_fix, target, id_fix)
        print("pase settings")
        response = {"status": True, "id_fix": id_fix}
        log.info("voy a iniciar otro ciclo infinito antes")
        print("iniciando mainFix")
        iniciarSocketBot = await FixController.iniciar_socket_bot(urlAppbots, id_fix, req_obj["cuenta"], accountFixId, req_obj["user"]["puertows"] )
        if iniciarSocketBot==False: 
            return {"status": False}
        mainFix = MainTask(settings, target, id_fix, req_obj["user"]["password"], req_obj["cuenta"], target, accountFixId, req_obj["user"]["puertows"])
        #iniciar en la otra app el mismo socket pero cliente
        url_rest = "https://api.remarkets.primary.com.ar/"
        if int(req_obj["user"]["live"])==1: 
            url_rest = req_obj["user"]["url_rest"]
        print("iniciando balance")
        mainFix.application.rest = RofexAPI(user=id_fix, password=req_obj["user"]["password"], base_url=url_rest)
        log.info(f"fixM: {fixM}")
        print("agregando task a fixM")
        await fixM.add_task(mainFix)
        login = await mainFix.check_logged_on()
        log.info("saliendo de checkLogOn en flask ")
        log.info(f"fixM: {fixM.tasks}")
        if login==True:
            log.info("login = true")
            await DbUtils.update_fix_session_mongo(req_obj["user"]["id"], 1)
            log.info("dbultil = true")
            return jsonify(response)
        else:
            return {"status": False}
    


    @staticmethod
    async def iniciar_fix_m():
        req_obj = request.get_json()
        print("req", req_obj)
        
        id_fix = req_obj["user"]["user"]
        user_id = req_obj["user"]["id"]
        BeginString = "FIXT.1.1"
        target = "ROFX"
        settings = config_fix_settings(req_obj["user"]["puerto"], BeginString, id_fix, target, id_fix)
        response = {"status": True, "id_fix": id_fix}
        login = False
        try:
            sesionesFix[id_fix] = main(settings, target, id_fix, req_obj["user"]["password"], req_obj["cuenta"])
            sesionesFix[id_fix].daemon = True
            sesionesFix[id_fix].start()
            time.sleep(4)
            #ahora iniciar rest
            url_rest = "https://api.remarkets.primary.com.ar/"
            if int(req_obj["user"]["live"])==1: 
                url_rest = req_obj["user"]["url_rest"]
            sesionesFix[id_fix].application.rest = RofexAPI(user=id_fix, password=req_obj["user"]["password"], base_url=url_rest)

            while True: 
                if sesionesFix[id_fix].application.sessions[target]['connected']!=None:
                    print("la variable cambio de None ")
                    if sesionesFix[id_fix].application.sessions[target]['connected']==True:
                        print("la variable cambio a True")
                        sesionesFix[id_fix].application.server_md = server_md
                        log.info("sesion fix creada")
                        login = True
                        sesionesFix[id_fix].application.triangulos[0] = fixManual(sesionesFix[id_fix].application,id_fix, 0,req_obj["cuenta"], user_id)
                        sesionesFix[id_fix].application.triangulos[0].daemon = True
                        sesionesFix[id_fix].application.triangulos[0].start()
                        time.sleep(1)
                        break
                    else:
                        response = {"status": False, "id_fix": id_fix, "mgs": "datos incorrectos"}
                        sesionesFix[id_fix].application.logout()
                        sesionesFix[id_fix].initiator.stop()
                        del sesionesFix[id_fix]
                        break

        except Exception() as e: 
            log.warning(f"error al crear sesion fix: {e}")
            response = {"status": False, "id_fix": id_fix, "msg": e}
        if login==True:
            #actualizar el status de la sesion en la tabla fix_sessions
            #ahora vamos a iniciar el bot manual en la sesion de fix 
            await DbUtils.update_fix_session_mongo(req_obj["user"]["id"], 1)
            return jsonify(response)
        else:
            abort(make_response(jsonify(message="Datos de sesion incorrectos"), 401))

    async def detener_fix_new():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['user']["user"]
        id_user = req_obj['user']["id"]
        log.info(f"fixM: {fixM.tasks}")

        getFixTask = await fixM.get_fixTask_by_id_user(id_fix)
        if getFixTask:
            print("si existe a session")
            print("detener los bots abiertos ")
            bots = mongo.db.bots_ejecutandose.find({
                "user_fix": id_fix, "status": {"$gt": 0}
            })
            if bots: 
                print("si hay bots activos para este usuario")
                for bot in bots: 
                    await DbUtils.update_status_bot_ejecuntadose(str(bot["_id"]), 0)
                    #ahora cancelar las ordenes abiertas 
                    fix = {
                        "user": id_fix, 
                        "account": bot["cuenta"]
                    }
               #     response =  await UtilsController.detener_bot_by_id(fix, bot["_id"])
            await getFixTask.stopColaFix()
            getFixTask.application.logout()
            getFixTask.initiator.stop()
            
            getFixTask.threadFix.join()
            getFixTask.threadBalance.join()
            getFixTask.server_md.close()
            log.info(f"fixM: {fixM.tasks}")
            log.info(f"fixM: {fixM.main_tasks}")
            await fixM.stop_task_by_id(id_fix)
            await DbUtils.update_fix_session_mongo(id_user, 0)
            log.info(f"fixM: {fixM.tasks}")
            log.info(f"fixM: {fixM.main_tasks}")
            return {"status": True}
        else:
            print("noexiste pero actualizadmos en db")
            await DbUtils.update_fix_session_mongo(id_user, 0)
            return {"status": False}
        
    def get_all_orders():
        print("hola get_all_orders")
        fecha_actual=datetime.today()
        # Agregar 4 horas a la fecha actual
        fecha_actual_mas_4h=fecha_actual + timedelta(hours=4)
        # Convertir la fecha a un formato legible
        fecha_actual_mas_4h_str=fecha_actual_mas_4h.strftime(
        "%Y%m%d")
        """ordenesToda=mongo.db.ordenes.find({
         "ordStatus": { "$nin": ["CANCELLED", "REJECTED"] }
        }, {"_id": 0})
        
        """
        ordenesEjecutadas=mongo.db.ordenes.aggregate([
        {"$match": {"$or": [
        {"ordStatus": "FILLED"},
        {"$and": [
        {"ordStatus": "PARTIALLY FILLED"},
        {"active": True}
        ]}
        ]}},
        {"$sort": {"transactTime": -1}},
        {"$group": {
        "_id": "$symbol",
        "ordenes": {"$push": {
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
        "ordenes": {"$slice": ["$ordenes", 10]},
        "_id": 0
        }},
        ])
        ejecutadas = list(ordenesEjecutadas)

        
       # log.info(list(ordenesToda))
        return jsonify(list(ejecutadas))
    
    def get_securitys():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        inicio = time.time()
        id_fix = req_obj['id_fix']
        if id_fix in fixM.main_tasks:
            #ahora necesito saber el tipo de cuenta si es demo o no 
            cuentaFix = mongo.db.cuentas_fix.find_one({"user": id_fix }, {"_id": 0})
            account_type = "demo"
            if cuentaFix["live"]==1: 
                account_type="live"
            today = date.today()
            securitys = mongo.db.securitys.find_one({"date": str(today), "account_type": account_type})
            if securitys:
                UtilsController.guardar_security_in_fix(securitys["data"], id_fix)
                response = {"securitys": str(securitys["data"]).replace("'", '"'), "date": str(datetime.now()), "status": True}
                log.info(f"response: {response}")
                return jsonify(response)
            fixM.main_tasks[id_fix].application.securityListRequest(symbol="")
            response = {"status": True}
            while True: 
                time.sleep(0.1)
            #   log.info(f"esperando seguridad {sesionesFix[id_fix].application.securitySegments}")
            #"MERV" in fixM.main_tasks[id_fix].application.securitySegments
                if "DDA" in fixM.main_tasks[id_fix].application.securitySegments and "DDF" in fixM.main_tasks[id_fix].application.securitySegments  and "DUAL" in fixM.main_tasks[id_fix].application.securitySegments:
                    break
            print("saliendo de ciclo securitys, enviando a guardar en db")
            time.sleep(1)
            securitys_data = UtilsController.fetch_securitys_data(id_fix)
            log.info(f"ahora a guardar los securitys")
            UtilsController.guardar_security_in_fix(securitys_data, id_fix)
            log.info(f"ahora guardar en db")
            document = {
            "date": str(today),
            "account_type": account_type,
            "data": securitys_data
            }
            mongo.db.securitys.insert_one(document)
            response = {"securitys": str(securitys_data).replace("'", '"'), "date": str(datetime.now()), "status": True}

        else:
            response = {"status": False}
        log.info(f"response: {response}")
        return jsonify(response)