import pymongo
from datetime import datetime
import time
start = time.time()
# Conecta a la base de datos de MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Selecciona la base de datos y la colección
db = client["rofex"]
collection = db["ordenes"]

buscarPendientes = collection.find({
            "active": True,
            "$or": [
            {"ordStatus": "NEW"}, 
            {"ordStatus": "PARTIALLY FILLED"}
            ]
})
pendientes = list(buscarPendientes)
print("pendientes", len(pendientes) )
ordenes_ejecutadas = collection.aggregate([
    {"$match": {"$or": [
        {"ordStatus": "FILLED"},
        {"$and": [
            {"ordStatus": "PARTIALLY FILLED"},
            {"active": True}
        ]}
    ]}},
    {"$group": {
        "_id": "$symbol",
        "ordenes": {"$push": "$$ROOT"}
    }}
])

ejecutadas = list(ordenes_ejecutadas)
print("ejecutadas: ", ejecutadas)
print("ejecutadas", len(ejecutadas) )
print(f'Tiempo transcurrido {time.time() - start }')

