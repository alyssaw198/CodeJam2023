import random
import time
import json
import threading
import os
from twilio.rest import Client
import geopy.distance
from paho.mqtt import client as mqtt_client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
broker = 'fortuitous-welder.cloudmqtt.com'
port = 1883
topic = "CodeJam"
client_id = 'sillygooses01'
username = 'CodeJamUser'
password = '123CodeJam'
trucks = {}
loads = {}
mobile_client = Client(account_sid, auth_token)

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

        if data["type"] == "Load":
            load_id = data['loadId']
            loads[load_id] = Load(load_id, data['originLatitude'], data['originLongitude'], data['destinationLatitude'], data['destinationLongitude'], data['equipmentType'], data['price'], data['mileage'])
            load_start = (loads[load_id].originLat, loads[load_id].originLong)
            load_end = (loads[load_id].destLat, loads[load_id].destLong)
            valid_trucks = {}
            for truck_id, truck in trucks.items():
                truck_start = (truck.latitude, truck.longitude)
                if truck.equip_type == loads[load_id].type:
                    truck_distance_to_load = geopy.distance.geodesic(load_start, truck_start).miles
                    if truck_distance_to_load <= 100:
                        load_distance = geopy.distance.geodesic(load_start, load_end).miles
                        if (load_distance >= 200 and truck.trip_pref == "Long") or (load_distance < 200 and truck.trip_pref == "Short"): 
                            valid_trucks[truck_id] = loads[load_id].pay - (1.38 * (loads[load_id].mileage + truck_distance_to_load))
            if valid_trucks:
                max_pay_truck_id = max(valid_trucks, key=valid_trucks.get)
                max_pay = valid_trucks[max_pay_truck_id]
                if max_pay < 0:
                    print("We don't work for nothing or pay to work.")
                else:
                    sms_body = f'A new job has appeared! Truck ID: {max_pay_truck_id}, Load ID: {load_id}, Pay: {max_pay}'
                    mobile_client.messages.create(
                        body=sms_body,
                        from_='+18447681638',  # Replace with your Twilio number
                        to='+19146105558'  # Replace with the desired recipient number
                    )
        if data["type"] == "Truck":
            truck_id = data['truckId']
            valid_loads = {}
            if truck_id in trucks:
                # Update existing truck
                trucks[truck_id].update(data['positionLatitude'], data['positionLongitude'])
            else:
                # Create new truck
                trucks[truck_id] = Truck(truck_id, data['positionLatitude'], data['positionLongitude'], data['equipType'], data['nextTripLengthPreference'])
            for load_id, load in loads.items():
                load_start = (load.originLat, load.originLong)
                load_end = (load.destLat, load.destLong)
                truck_cord = (trucks[truck_id].latitude, trucks[truck_id].longitude)
                if trucks[truck_id].equip_type == load.type:
                    truck_distance_to_load = geopy.distance.geodesic(load_start, truck_cord).miles
                    if truck_distance_to_load <= 100:
                        load_distance = geopy.distance.geodesic(load_start, load_end).miles
                        if (load_distance >= 200 and trucks[truck_id].trip_pref == "Long") or (load_distance < 200 and trucks[truck_id].trip_pref == "Short"): 
                            valid_loads[load.load_id] = load.pay - (1.38 * (load.mileage + truck_distance_to_load))
        
            #print(trucks[truck_id])  # Print the updated truck information
            if valid_loads:
                max_pay_load_id = max(valid_loads, key=valid_loads.get)
                max_pay = valid_loads[max_pay_load_id]
                if max_pay < 0:
                    print("We don't work for nothing or pay to work.")
                else:
                    sms_body = f'A new job has appeared! Truck ID: {truck_id}, Load ID: {max_pay_load_id}, Pay: {max_pay}'
                    mobile_client.messages.create(
                        body=sms_body,
                        from_='+18447681638',  # Replace with your Twilio number
                        to='+19146105558'  # Replace with the desired recipient number
                    )
            #print(loads[load_id])
            
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
    print("\nTotal Trucks:")
    print(len(trucks.items()))
    print("\nTotal Loads:")
    print(len(loads.items()))
    
if __name__ == '__main__':
    run()
