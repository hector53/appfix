from app import mongo, sesionesFix, ObjectId, logging, datetime, jsonify, request, asyncio, abort, make_response

log = logging.getLogger(__name__)

class FixManualController:
    @staticmethod

    def get_fix_manual_data(id):
        from app import fixM
        id_fix = id
        response = {
            "status": False,
            "msg": "fix no activo",
            "isFixManualActive": False,
        }
        if id_fix in fixM.main_tasks:
            #ver si bot manual esta activo 
            isFixManualActive = True
            response = {
                "status": True,
                "msg": "fix activo",
                "isFixManualActive": isFixManualActive,
            }
        return jsonify(response)

    async def new_order_manual():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['id_fix']
        order = req_obj['order']
        if id_fix in fixM.main_tasks:
            cuenta = fixM.main_tasks[id_fix].account
            response = await fixM.main_tasks[id_fix].application.nueva_orden_manual(order["symbol"], order["side"], order["size"], order["price"], order["type"], cuenta)
            return response
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))

    async def manual_edit_order():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['id_fix']
        typeRequest = int(req_obj['typeRequest'])
        orden = req_obj['orden']
        if id_fix in fixM.main_tasks:
            sideOrder = 1 if orden["side"] == "Buy" else 2
            cuenta = fixM.main_tasks[id_fix].account
            if typeRequest == 1:
                response = await fixM.main_tasks[id_fix].application.modificar_orden_manual(orderId=orden["orderId"],
                        origClOrdId=orden["clOrdId"], side=sideOrder, orderType=2, symbol=orden["symbol"],
                        quantity=orden["size"], price=orden["price"], sizeViejo=orden["sizeViejo"], cuenta=cuenta)
            elif typeRequest == 2:
                response = await fixM.main_tasks[id_fix].application.modificar_orden_manual_2(orderId=orden["orderId"],
                        origClOrdId=orden["clOrdId"], side=sideOrder, orderType=2, symbol=orden["symbol"],
                        quantity=orden["size"], price=orden["price"], cuenta=cuenta)
            return response
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))

    async def manual_cancel_orden():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['id_fix']
        orden = req_obj['orden']
        if id_fix in fixM.main_tasks:
            cuenta = fixM.main_tasks[id_fix].account
            sideOrder = 1 if orden["side"] == "Buy" else 2
            response = await fixM.main_tasks[id_fix].application.cancelar_orden_manual(orden["orderId"], orden["clOrdId"], sideOrder, orden["orderQty"], orden["symbol"], cuenta)
            return response
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))

    async def manua_mass_cancel():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['id_fix']
        marketSegment = req_obj['marketSegment']
        await fixM.main_tasks[id_fix].application.orderMassCancelRequest(marketSegment=marketSegment)
        return jsonify({"status":True})

    async def manua_get_posiciones(id):
        from app import fixM
        id_fix = id
        cuenta = request.args.get('cuenta', '')
        if id_fix in fixM.main_tasks:
            response = await fixM.main_tasks[id_fix].application.get_posiciones(cuenta)
            return jsonify(response)
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))

    async def manua_get_balance(id):
        from app import fixM
        id_fix = id
        print("request", request)
        cuenta = request.args.get('cuenta', '')
        print("uenta", cuenta)
        if id_fix in fixM.main_tasks:
            balance = await fixM.main_tasks[id_fix].application.get_balance(account=cuenta)
            return jsonify(balance)
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))

    async def manua_mass_status(id):
        print("assadasdasd mass status")
        from app import fixM
        id_fix = id
        cuenta = request.args.get('cuenta', '')
        response = {"status": False}
        if id_fix in fixM.main_tasks:
            response = await fixM.main_tasks[id_fix].application.orderMassStatusRequest("0", 7, cuenta)
        return jsonify(response)

    async def manual_get_trades():
        from app import fixM
        req_obj = request.get_json()
        print(req_obj)
        id_fix = req_obj['id_fix']
        market_id = req_obj['market_id']
        symbol = req_obj['symbol']
        desde = req_obj['desde']
        hasta = req_obj['hasta']
        if id_fix in fixM.main_tasks:
            response = await fixM.main_tasks[id_fix].application.get_trades_manual(market_id, symbol, desde, hasta)
            return jsonify(response)
        else:
            abort(make_response(jsonify(message="manual no activo"), 401))
