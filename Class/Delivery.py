from Class import Driver
from enum import Enum
import numpy as np

class DeliveryStatus(Enum):
    ORDER_CREATED = 0
    ORDER_ASSIGNED = 1
    ORDER_COMPLETED = 2


class Delivery:
    def __init__(self, order_id, ship_from_region, ship_to_region, pick_up_time, price, created_time):
        self.order_id = order_id
        self.ship_from_region = ship_from_region
        self.ship_to_region = ship_to_region
        self.pick_up_time = pick_up_time
        self.price = price
        self.created_time = created_time
        self.assigned_time = None
        self.completed_time = None
        self.driver = None
        self.status = DeliveryStatus.ORDER_CREATED

    def get_delivery_info(self):
        return {"order_id" : self.order_id,
                 "ship_from_region" : self.ship_from_region,
                 "ship_to_region" : self.ship_to_region,
                 "pick_up_time" : self.pick_up_time,
                 "price" : self.price,
                 "created_time" : self.created_time,
                 "assigned_time" : self.assigned_time,
                 "completed_time" : self.completed_time,
                 "driver" : self.driver.get_driver_info(),
                 "status" : self.status }

    def update_status(self, status: DeliveryStatus) -> DeliveryStatus:
        self.status = status
        return status

    def assign_driver(self, _driver: Driver):
        self.driver = _driver
        self.update_status(DeliveryStatus.ORDER_ASSIGNED)