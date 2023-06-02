import json

def py_to_json_bool(py_bool):
    json_bool = bool(py_bool)
    json_bool =  str(json_bool).lower()  
    return json_bool

py_bool = False
json_bool = py_to_json_bool(py_bool)
print(json.loads(json_bool))
# "false"