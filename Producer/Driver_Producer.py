from Class import Driver
from Class import Delivery
from pymongo import MongoClient
import json
import time
from datetime import datetime
from boto import kinesis

kinesis = kinesis.connect_to_region('ap-northeast-1')


def database_collection():
    client = MongoClient()
    db = client.delivery_database
    delivery_collection = db.delivery_collection
    print(db.collection_names())
    return delivery_collection

def create_drivers():
    drivers = []
    for i in range(10):
        drivers.append(Driver.Driver("driver" + str(i), "#"))
    return drivers

# Searching delivery from database for driver to pick up one
def searching_a_delivery(driver):
    cursor = delivery_collection.find(
        {"$and":
            [
                {"ship_from_region_x": {"$gte": driver.getX - 3, "$lte": driver.getX + 3}},
                {"ship_from_region_y": {"$gte": driver.getY() - 3, "$lte": driver.getY() + 3}},
            ]
        })
    current_order_options = []
    for order_created in cursor:
        print(order_created)
        # del order_created['_id']
        current_order_options.append(order_created)

    available_orders = sorted(current_order_options, key=lambda order: order['price'], reverse=True)
    if available_orders:
        print('- Available Orders - \n' + str(available_orders))
        preference_order = available_orders[0]
        print('- Preference Order - \n' + str(preference_order))

    return preference_order

# TODO If the status is updated to "ASSIGNED : 1", the driver should look up another possible delivery
def pick_up_delivery(driver):
    preference_order = searching_a_delivery(driver)

    order_assigned = {
        "order_id": preference_order['order_id'],
        "driver": str(driver.get_driver_info()),
        "order_assigned_time": str(datetime.now())
    }

    # Driver will take the order if availabe
    delivery = Delivery.Delivery(
                                      preference_order['order_id'],
                                     (preference_order['ship_from_region_x'], preference_order['ship_from_region_y']),
                                     (preference_order['ship_to_region_x'], preference_order['ship_to_region_y']),
                                      preference_order['pick_up_time'],
                                      preference_order['price'],
                                      preference_order['order_created_time']
                                 )

    delivery.update_driver(driver, order_assigned['order_assigned_time'])
    delivery_collection.update(
        {"order_id": preference_order['order_id']},
        {"$set": {"status": 1,
                  "driver": order_assigned['driver'],
                  "order_assigned_time": order_assigned['order_assigned_time']
                  }
         }
    )

    driver.take_order(delivery)

    return order_assigned

# TODO : Do deliver and generate complete event to stream
def do_deliver(driver):
    pass

if __name__ == "__main__":

    # MongoDB
    delivery_collection = database_collection()

    # Generate Drivers
    drivers = create_drivers()

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

    # Now driver will pick up the order and the delivery will be taken to him
    # Here, Driver class do a role as next Producer of { order_assigned }
    order_assigned = pick_up_delivery(drivers[0])

    kinesis.put_record('DeliveryStream', json.dumps(order_assigned), str(order_assigned['driver']))
