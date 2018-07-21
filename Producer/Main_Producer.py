import json
import random
import time
import datetime

from Class import Delivery
from boto import kinesis

kinesis = kinesis.connect_to_region('ap-northeast-1')

# create orders
i = 1
while True:
    ship_from_region = [random.randint(0,5),random.randint(0,5)]
    ship_to_region =[random.randint(0,5),random.randint(0,5)]
    while ship_from_region == ship_to_region:
        ship_to_region =[random.randint(0,5),random.randint(0,5)]
    order_created = {
        "order_id" : i,
        "ship_from_region_x" : ship_from_region[0],
        "ship_from_region_y": ship_from_region[1],
        "ship_to_region_x": ship_to_region[0],
        "ship_to_region_y": ship_to_region[1],
        "pick_up_time" : str(datetime.datetime.now()),
        "price" : (abs(ship_from_region[0] - ship_to_region[0]) + abs(ship_from_region[1] - ship_to_region[1])) * 1000,
        "status" : 0
    }

    # Delivery(i,"here","there","15:30",datetime.datetime.now())
    kinesis.put_record('DeliveryStream', json.dumps(order_created), str(order_created['price']))

    #More than 10 orders per second
    time.sleep(0.09)
    i+=1