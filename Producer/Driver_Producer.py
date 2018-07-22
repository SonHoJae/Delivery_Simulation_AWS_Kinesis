from Class import Driver
from Class import Delivery
from pymongo import MongoClient
import json
import time
from datetime import datetime
from boto import kinesis
from threading import Thread
import threading
import traceback
from itertools import cycle

kinesis = kinesis.connect_to_region('ap-northeast-1')

shard_hash_key = []
for shard in kinesis.describe_stream('DeliveryStream')['StreamDescription']['Shards']:
    shard_hash_key.append(shard['HashKeyRange']['StartingHashKey'])
#print("starting hashkey"+str(shard_hash_key))
print(shard_hash_key[10:])
print(len(shard_hash_key[10:]))
cycle_partition_key = cycle(shard_hash_key[13:])

def database_collection():
    client = MongoClient()
    db = client.delivery_database
    delivery_collection = db.delivery_collection
    print(db.collection_names())
    return delivery_collection

def create_drivers(number_of_driver):
    drivers = []
    for i in range(number_of_driver):
        drivers.append(Driver.Driver("driver" + str(i)))
    return drivers

# Searching delivery from database for driver to pick up one
def searching_a_delivery(driver):
    cursor = delivery_collection.find(
        {"$and":
            [
                {"ship_from_region_x": {"$gte": driver.getX() - 3, "$lte": driver.getX() + 3}},
                {"ship_from_region_y": {"$gte": driver.getY() - 3, "$lte": driver.getY() + 3}},
                {"status" :0}
            ],
        })


    current_order_options = []
    for order_created in cursor:
        current_order_options.append(order_created)

    available_orders = sorted(current_order_options, key=lambda order: order['price'], reverse=True)
    if available_orders:
        #print('- Available Orders - \n' + str(available_orders))
        preference_order = available_orders[0]
        #print('- Preference Order - \n' + str(preference_order))
    else:
        preference_order = None
    return preference_order

# TODO If the status is updated to "ASSIGNED : 1", the driver should look up another possible delivery
def pick_up_delivery(driver):

    preference_order = searching_a_delivery(driver)
    if preference_order != None:
        order_assigned = {
            "order_id": preference_order['order_id'],
            "driver": str(driver.get_driver_info()),
            "order_assigned_time": str(datetime.now())
        }

        # Driver will take the order if availabe
        delivery = Delivery.Delivery(
                                          preference_order['order_id'],
                                         [preference_order['ship_from_region_x'], preference_order['ship_from_region_y']],
                                         [preference_order['ship_to_region_x'], preference_order['ship_to_region_y']],
                                          preference_order['pick_up_time'],
                                          preference_order['price'],
                                          preference_order['order_created_time']
                                     )

        delivery.assign_driver(driver, order_assigned['order_assigned_time'])
        delivery_collection.update(
            {"order_id": preference_order['order_id']},
            {"$set": {"status": 1,
                      "driver": order_assigned['driver'],
                      "order_assigned_time": order_assigned['order_assigned_time']
                      }
             }
        )

        driver.pick_order(delivery)
        # Release !

        if order_assigned != None:
            print(order_assigned['driver']+'order assgined')

            # Lock query and update

            kinesis.put_record('DeliveryStream', json.dumps(order_assigned), str(order_assigned['order_id']),explicit_hash_key=next(cycle_partition_key))

            do_deliver(driver)
        time.sleep(0.1)
    else:
        order_assigned = None

    return driver, order_assigned

# TODO : Do deliver and generate complete event to stream
def do_deliver(driver):
    print(driver.get_driver_info()+' delivery started')
    delivery = driver.get_delivery().get_delivery_info()
    distance = abs(delivery['ship_from_region'][0] - delivery['ship_to_region'][0])\
               + abs(delivery['ship_from_region'][1] + delivery['ship_to_region'][1])
    print('distance ' + str(distance))
    # after arriving at ship_to_region it will occur complete event
    time.sleep(distance)
    print(str(delivery['order_id'])+' deliver finished')

    order_completed = {
        'order_id' : delivery['order_id']
    }

    delivery_collection.update(
        {"order_id": delivery['order_id']},
        {"$set": {"status": 2,
                  "driver": driver.get_driver_info(),
                  "order_assigned_time": datetime.now()
                  }
         }
    )

    kinesis.put_record('DeliveryStream', json.dumps(order_completed), str(order_completed['order_id']),explicit_hash_key=next(cycle_partition_key))

if __name__ == "__main__":

    # MongoDB
    delivery_collection = database_collection()

    # Generate Drivers
    drivers = create_drivers(5)

    # TODO -> ASSUMING A SITUATION THAT DRIVER PIKCS A ORDER
    # **************  HYPOTHESIS  ***************
    # based on current region, the driver will take an order
    # I put the metric as distance & price
    # however there are potentially something more corresponding to
    # driver's preference (schedule, type of item etc)

    # Allowed regions within 3 x 3
    # ㅁ ㅁ ㅁ ㅁ ㅁ
    # ㅁ ㅁ ㅁ ㅁ ㅁ
    # ㅁ ㅁ () ㅁ ㅁ
    # ㅁ ㅁ ㅁ ㅁ ㅁ
    # ㅁ ㅁ ㅁ ㅁ ㅁ
# getting starting hash key for explicitly transmitting data

    # Now driver will pick up the order and the delivery will be taken to him
    # Here, Driver class do a role as next Producer of { order_assigned }
    for idx, _driver in enumerate(drivers):
        try:
            print(idx)
            pick_up_delivery(_driver)
            #Thread(target=pick_up_delivery, args=(_driver, )).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()

#
# order_completed = {
#     'order_id': 1
# }
#     # print(1)
#     # time.sleep(1)
# kinesis.put_record('DeliveryStream', json.dumps(order_completed), "d", explicit_hash_key="0")
