class Truck:
    def __init__(self, truck_id, latitude, longitude, equip_type, trip_pref):
        self.truck_id = truck_id
        self.latitude = latitude
        self.longitude = longitude
        self.equip_type = equip_type
        self.trip_pref = trip_pref
        #another property that says the last timestamp this truck recieved a notification, make sure we don't spam a trucker
        self.last_noti = None

    def update(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f"Truck ID: {self.truck_id}, Position: ({self.latitude}, {self.longitude}), Equipment Type: {self.equip_type}, Trip Preference: {self.trip_pref}"