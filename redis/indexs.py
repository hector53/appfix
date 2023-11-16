import redis

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Assuming you've installed the RedisJSON module
# https://oss.redislabs.com/redisjson/

redis_client.execute_command('JSON.SET', 'orders:123', '.', '{"symbol":"AAPL","quantity":10,"price":150.0}')

# Retrieving JSON document
order_details = redis_client.execute_command('JSON.GET', 'orders:123')
print(order_details)
