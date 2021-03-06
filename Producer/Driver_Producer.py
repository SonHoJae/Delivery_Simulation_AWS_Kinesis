from Class import Driver
from Class import Delivery
from pymongo import MongoClient
import json
import time
import datetime
from boto import kinesis
from threading import Thread
import traceback
from itertools import cycle
import random
kinesis = kinesis.connect_to_region('ap-northeast-1')

shard_hash_key = []
for shard in kinesis.describe_stream('DeliveryStream')['StreamDescription']['Shards']:
    shard_hash_key.append(shard['HashKeyRange']['StartingHashKey'])

print(shard_hash_key)
cycle_partition_key = cycle(shard_hash_key)

def database_collection():
    client = MongoClient()
    db = client.delivery_database
    delivery_collection = db.delivery_collection
    print(db.collection_names())
    return delivery_collection

def create_drivers(number_of_driver):
    drivers = []
    for i in range(number_of_driver):
        drivers.append(Driver.Driver("driver_" + str(i)))
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

    # If there is an order, driver take some rest and check out the time again.
    documents = list(cursor)
    i = 0
    while len(documents) == 0:
        print('Hey, '+driver.get_driver_info()+ ' in ( '+str(driver.getX())+','+str(driver.getY())
              + ' ) faild to find a good order.. Driver is taking some rest and searching it again')
        time.sleep(5)
        cursor = delivery_collection.find(
            {"$and":
                [
                    {"ship_from_region_x": {"$gte": driver.getX() - 3, "$lte": driver.getX() + 3}},
                    {"ship_from_region_y": {"$gte": driver.getY() - 3, "$lte": driver.getY() + 3}},
                    {"status": 0}
                ],
            })

        documents = list(cursor)
    current_order_options = []

    # # filter pickup time - distance < 0
    # pickup - datetime.datetime.now() -
    for order_created in documents:
        current_order_options.append(order_created)
    available_orders_after_location = sorted(current_order_options, key=lambda order: order['price'], reverse=True)

    def filter_unreachable_region(order):
        current_to_source = abs(driver.getX() - order['ship_from_region_x']) \
                            + abs(driver.getY() - order['ship_from_region_y'])
        delivery_distance = abs(order['ship_from_region_x'] - order['ship_to_region_x']) \
                            + abs(order['ship_from_region_y'] + order['ship_to_region_y'])
        estimate_time = datetime.datetime.strptime(order['pick_up_time'], "%Y-%m-%d %H:%M:%S.%f")  \
                        - datetime.datetime.now() + datetime.timedelta(0,3) # 3 is spare time
        delivery_time = current_to_source + delivery_distance
        estimate_time = estimate_time.total_seconds()
        if delivery_time < estimate_time:
            return True
        return False

    available_orders_after_distance = list(filter(filter_unreachable_region, available_orders_after_location))

    if len(available_orders_after_location)-len(available_orders_after_distance) > 0:
        print('\n\n'+str(len(available_orders_after_location)-len(available_orders_after_distance))
              +' regions filtered due to unreachable locations within pick-up time')

    if available_orders_after_distance:
        #print('- Available Orders - \n' + str(available_orders))
        preference_order = available_orders_after_distance[0]
        #print('- Preference Order - \n' + str(preference_order))
        print(driver.get_driver_info() + " location ->" + str(driver.getX()) + ',' + str(driver.getY()),end=' *** ')
        print(driver.get_driver_info() + " source location ->" +
              str(preference_order['ship_from_region_x']) + ',' + str(preference_order['ship_from_region_y']))
    else:
        preference_order = None

    return preference_order

# TODO If the status is updated to "ASSIGNED : 1" or "2", the driver should look up another possible delivery
def pick_up_delivery(driver):
    preference_order = searching_a_delivery(driver)
    if preference_order != None:
        order_assigned = {
            "order_id": preference_order['order_id'],
            "driver": str(driver.get_driver_info())
        }

        # If the status is updated to "ASSIGNED : 1", or "2" the driver should look up another possible delivery
        # Driver will take the order if availabe
        delivery = Delivery.Delivery(
                                          preference_order['order_id'],
                                         [preference_order['ship_from_region_x'], preference_order['ship_from_region_y']],
                                         [preference_order['ship_to_region_x'], preference_order['ship_to_region_y']],
                                          preference_order['pick_up_time'],
                                          preference_order['price'],
                                          preference_order['order_created_time']
                                     )

        delivery.assign_driver(driver)
        delivery_collection.update(
            {"order_id": preference_order['order_id']},
            {"$set": {"status": 1,
                      "driver": order_assigned['driver'],
                      "order_assigned_time": str(datetime.datetime.now())
                      }
             }
        )
        print('assigned '+ driver.get_driver_info()+' '+str(datetime.datetime.now()))

        driver.pick_order(delivery)

        if order_assigned != None:
            print(order_assigned['driver']+' order assgined')

            # Lock query and update
            kinesis.put_record('DeliveryStream', json.dumps(order_assigned), str(order_assigned['order_id']),explicit_hash_key=next(cycle_partition_key))

            do_deliver(driver)
    else:
        order_assigned = None

    return driver, order_assigned

# TODO : Do deliver and generate complete event to stream
def do_deliver(driver):
    delivery = driver.get_delivery().get_delivery_info()

    current_to_source = abs(driver.getX() - delivery['ship_from_region'][0]) \
                        + abs(driver.getY() - delivery['ship_from_region'][1])
    delivery_distance = abs(delivery['ship_from_region'][0] - delivery['ship_to_region'][0])\
               + abs(delivery['ship_from_region'][1] + delivery['ship_to_region'][1])
    print(driver.get_driver_info()+' delivery started with order_id : '+ str(delivery['order_id']) + ' and distance ' + str(delivery_distance)+'\n\n')

    # after arriving at ship_to_region it will occur complete event
    time.sleep(int(current_to_source + delivery_distance))
    time.sleep(3)
    print(driver.get_driver_info() + ' delivery finished with order_id : ' + str(delivery['order_id']))

    order_completed = {
        'order_id' : delivery['order_id']
    }

    print('completion '+ driver.get_driver_info()+' '+str(datetime.datetime.now()))
    delivery_collection.update(
        {"order_id": delivery['order_id']},
        {"$set":
             {      "status": 2,
                   "order_completed_time": str(datetime.datetime.now())
             }
         }
    )
    kinesis.put_record('DeliveryStream', json.dumps(order_completed), str(order_completed['order_id']),explicit_hash_key=next(cycle_partition_key))

    driver.earn_credit(delivery_distance) # he earn credit corresponding to running distance
    driver.update_location(delivery['ship_to_region'][0],delivery['ship_to_region'][1])
    print('Now this thread('+ driver.get_driver_info()+ ') will take some rest and work again.')
    time.sleep(10)

    pick_up_delivery(driver)

if __name__ == "__main__":

    # MongoDB
    delivery_collection = database_collection()

    # Generate Drivers
    drivers = create_drivers(10)

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
            Thread(target=pick_up_delivery, args=(_driver, )).start()
            time.sleep(random.randint(1,9))
        except:
            print("Thread did not start.")
            traceback.print_exc()
