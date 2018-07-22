import random
from Class import Delivery

class Driver:
    def __init__(self, name):
        self.name = name
        self.current_region = [random.randint(0,15),random.randint(0,15)]
        self.delivery = None

    def get_driver_info(self):
        return self.name

    def getX(self):
        return self.current_region[0]

    def getY(self):
        return self.current_region[1]

    def get_delivery(self):
        return self.delivery

    def pick_order(self, delivery : Delivery):
        self.delivery = delivery
