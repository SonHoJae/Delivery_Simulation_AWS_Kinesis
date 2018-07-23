import json
import random
import time
import datetime
import sys
from Class import Delivery
from boto import kinesis
from pymongo import MongoClient
from itertools import cycle

kinesis = kinesis.connect_to_region('ap-northeast-1')

shard_hash_key = []
for _ in range(20):
    print(kinesis.describe_stream('DeliveryStream'))
print('checking')
for shard in kinesis.describe_stream('DeliveryStream')['StreamDescription']['Shards']:
    shard_hash_key.append(shard['HashKeyRange']['StartingHashKey'])

cycle_partition_key = cycle(shard_hash_key)

def database_collection():
    client = MongoClient()
    db = client.delivery_database
    delivery_collection = db.delivery_collection
    print(db.collection_names())
    return delivery_collection
database_collection = database_collection()
# create orders
i = 1
while True:
    a = datetime.datetime.now()
    ship_from_region = [random.randint(0,20),random.randint(0,20)]
    ship_to_region =[random.randint(0,20),random.randint(0,20)]
    while ship_from_region == ship_to_region:
        ship_to_region =[random.randint(0,20),random.randint(0,20)]
    order_created = {
        "order_id" : i,
        "ship_from_region_x" : ship_from_region[0],
        "ship_from_region_y": ship_from_region[1],
        "ship_to_region_x": ship_to_region[0],
        "ship_to_region_y": ship_to_region[1],
        "pick_up_time" : str(datetime.datetime.now()),
        "price" : (abs(ship_from_region[0] - ship_to_region[0]) + abs(ship_from_region[1] - ship_to_region[1])) * 1000,
        "status" : 0,
        "order_created_time" : str(datetime.datetime.now())
    }
    kinesis.put_record('DeliveryStream', json.dumps(order_created), str(order_created['price']),
                       explicit_hash_key=next(cycle_partition_key))
    database_collection.insert(order_created)

    time.sleep(0.09)
    b = datetime.datetime.now()
    c = b - a
    #print(divmod(c.total_seconds(), 60))
    i+=1