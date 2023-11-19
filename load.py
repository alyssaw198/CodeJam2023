import geopy.distance
from datetime import datetime, timedelta

class Load: 
    def __init__(self, timestamp, load_id, originLat, originLong, destLat, destLong, type_equip, pay, mileage):
        self.load_id = load_id
        self.originLat = originLat
        self.originLong = originLong
        self.destLat = destLat
        self.recieved_at = timestamp
        self.destLong = destLong
        self.type = type_equip
        self.pay = pay
        self.mileage = mileage
        self.total_dist = geopy.distance.geodesic((originLat, originLong), (destLat, destLong)).miles
        self.wait_time = 0
    
    def calculate_wait_time(self, current_time):
        self.wait_time = (datetime.strptime(self.recieved_at.split("T")[1], "%H:%M:%S") - datetime.strptime(current_time.split("T")[1], "%H:%M:%S")).total_seconds()
    
    def __str__(self):
        return f"Load ID: {self.load_id}, Origin: ({self.originLat}, {self.originLong}), Destination: ({self.destLat}, {self.destLong}), Equipment Type: {self.type}, Pay: {self.pay}, Mileage: {self.mileage}"
        
