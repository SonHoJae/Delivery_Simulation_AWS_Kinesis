from Class import Driver
from enum import Enum


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

    def update_status(self, status: DeliveryStatus) -> DeliveryStatus:
        self.status = status
        return status

    def update_driver(self, _driver: Driver, assigned_time):
        self.driver = _driver
        self.assigned_time = assigned_time
        self.update_status(DeliveryStatus.ORDER_ASSIGNED)
