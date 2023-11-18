import random
import time
import json
import threading
from paho.mqtt import client as mqtt_client

broker = 'fortuitous-welder.cloudmqtt.com'
port = 1883
topic = "CodeJam"
client_id = 'sillygooses01'
username = 'CodeJamUser'
password = '123CodeJam'
trucks = {}
loads = {}

class Truck:
    def __init__(self, truck_id, latitude, longitude, equip_type, trip_pref):
        self.truck_id = truck_id
        self.latitude = latitude
        self.longitude = longitude
        self.equip_type = equip_type
        self.trip_pref = trip_pref
        #dict of load objects

    def update(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        #be able to update this truck's distance to EACH of the possible loads
        #if a load is within the truck's radius
        #run another function that checks if delivering this load is within the trucker's preferences AND within the trucker's cost
        #match load with trucker and send notification if found good match
        #if not continue 

    def __str__(self):
        return f"Truck ID: {self.truck_id}, Position: ({self.latitude}, {self.longitude}), Equipment Type: {self.equip_type}, Trip Preference: {self.trip_pref}"

class Load: 
    def __init__(self, load_id, originLat, originLong, destLat, destLong, type, pay, mileage):
        self.load_id = load_id
        self.originLat = originLat
        self.originLong = originLong
        self.destLat = destLat
        self.destLong = destLong
        self.type = type
        self.pay = pay
        self.mileage = mileage
    def __str__(self):
        return f"Load ID: {self.load_id}, Origin: ({self.originLat}, {self.originLong}), Destination: ({self.destLat}, {self.destLong}), Equipment Type: {self.type}, Pay: {self.pay}, Mileage: {self.mileage}"
        
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(topic)  # Subscribe to the topic here
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message  # Set the on_message callback
    client.connect(broker, port)
    return client

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())

        if data["type"] == "Truck":
            truck_id = data['truckId']
            if truck_id in trucks:
                # Update existing truck
                trucks[truck_id].update(data['positionLatitude'], data['positionLongitude'])
            else:
                # Create new truck
                trucks[truck_id] = Truck(truck_id, data['positionLatitude'], data['positionLongitude'], data['equipType'], data['nextTripLengthPreference'])
            
            print(trucks[truck_id])  # Print the updated truck information

        # Handle 'Load' type messages if needed
        if data["type"] == "Load":
            load_id = data['loadId']
            loads[load_id] = Load(load_id, data['originLatitude'], data['originLongitude'], data['destinationLatitude'], data['destinationLongitude'], data['equipmentType'], data['price'], data['mileage'])
            
            print(loads[load_id])
            
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

def run():
    client = connect_mqtt()
    client.loop_start()

    # Set a timer for 30 seconds to stop the loop
    timer = threading.Timer(30.0, client.loop_stop)
    timer.start()

    try:
        while timer.is_alive():
            time.sleep(1)  # Keep the script alive
    except KeyboardInterrupt:
        client.loop_stop()  # Stop the loop on interruption

    # Print the entire trucks dictionary
    print("\nAll Trucks Data:")
    for truck_id, truck in trucks.items():
        print(truck)
    print("\nAll Load Data:")
    for load_id, load in loads.items():
        print(load)
if __name__ == '__main__':
    run()
