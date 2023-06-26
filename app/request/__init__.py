from app import app

#controllers 
from app.controllers import *

#rutas con controladores 

###FIX###
app.add_url_rule('/api/iniciar_fix/new', view_func=FixController.iniciar_fix_new, methods=['POST'] )
app.add_url_rule('/api/detener_fix/new', view_func=FixController.detener_fix_new, methods=['POST'] )
app.add_url_rule('/api/get_securitys', view_func=FixController.get_securitys, methods=['POST'] )

app.add_url_rule('/api/get_all_orders', view_func=FixController.get_all_orders, methods=['POST'] )


app.add_url_rule('/api/new_order_manual', view_func=FixController.newOrderTest, methods=['POST'] )
app.add_url_rule('/api/suscribir_mercado', view_func=FixController.suscribir_mercado, methods=['POST'] )
app.add_url_rule('/api/get_positions', view_func=FixController.get_positions, methods=['POST'] )
app.add_url_rule('/api/new_order', view_func=FixController.new_order, methods=['POST'] )
app.add_url_rule('/api/cancel_order', view_func=FixController.cancel_order, methods=['POST'] )
app.add_url_rule('/api/modify_order', view_func=FixController.modify_order, methods=['POST'] )
app.add_url_rule('/api/unsuscribir_mercado', view_func=FixController.unsuscribir_mercado, methods=['POST'] )
app.add_url_rule('/api/get_historico_visor', view_func=FixController.historico_visor, methods=['POST'] )



app.add_url_rule('/api/initC', view_func=FixController.initC, methods=['POST'] )
app.add_url_rule('/api/stopC', view_func=FixController.stopC, methods=['POST'] ) 

####CUENTAS FIX####
app.add_url_rule('/api/cuentas_fix', view_func=CuentasFixController.index)
app.add_url_rule('/api/cuenta_fix', view_func=CuentasFixController.insert,   methods=['POST'])
app.add_url_rule('/api/cuentas_fix/<string:id>', view_func=CuentasFixController.delete, methods=['DELETE'])
app.add_url_rule('/api/cuentas_fix', view_func=CuentasFixController.update,  methods=['PUT'])
app.add_url_rule('/api/cuenta_fix/select', view_func=CuentasFixController.select_cuenta,   methods=['POST'])
app.add_url_rule('/api/user_fix/select', view_func=CuentasFixController.userFix_select,   methods=['POST'])

###user####
app.add_url_rule('/api/checkToken', view_func=UserController.checkToken,   methods=['POST'])
app.add_url_rule('/api/logout', view_func=UserController.logout,   methods=['POST'])
app.add_url_rule('/api/login', view_func=UserController.login,   methods=['POST'])

###BONOS####
#app.add_url_rule('/api/get_data_bonos', view_func=BonosController.get_bonos,   methods=['GET'])

###FIX MANUAL####
app.add_url_rule('/api/manual/<string:id>', view_func=FixManualController.get_fix_manual_data,   methods=['GET'])
app.add_url_rule('/api/manual/new_order', view_func=FixManualController.new_order_manual,   methods=['POST'])
app.add_url_rule('/api/manual/edit_order', view_func=FixManualController.manual_edit_order,   methods=['POST'])
app.add_url_rule('/api/manual/cancel_orden', view_func=FixManualController.manual_cancel_orden,   methods=['POST'])
app.add_url_rule('/api/manual/mass_cancel', view_func=FixManualController.manua_mass_cancel,   methods=['POST'])
app.add_url_rule('/api/manual/get_posiciones/<string:id>', view_func=FixManualController.manua_get_posiciones,   methods=['GET'])
app.add_url_rule('/api/manual/get_balance/<string:id>', view_func=FixManualController.manua_get_balance,   methods=['GET'])
app.add_url_rule('/api/manual/mass_status/<string:id>', view_func=FixManualController.manua_mass_status,   methods=['GET'])
app.add_url_rule('/api/manual/get_trades', view_func=FixManualController.manual_get_trades,   methods=['POST'])