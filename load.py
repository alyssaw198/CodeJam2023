import geopy.distance

class Load: 
    def __init__(self, load_id, originLat, originLong, destLat, destLong, type_equip, pay, mileage):
        self.load_id = load_id
        self.originLat = originLat
        self.originLong = originLong
        self.destLat = destLat
        self.destLong = destLong
        self.type = type_equip
        self.pay = pay
        self.mileage = mileage
        self.total_dist = geopy.distance.geodesic((originLat, originLong), (destLat, destLong)).miles
    
    def __str__(self):
        return f"Load ID: {self.load_id}, Origin: ({self.originLat}, {self.originLong}), Destination: ({self.destLat}, {self.destLong}), Equipment Type: {self.type}, Pay: {self.pay}, Mileage: {self.mileage}"
        
