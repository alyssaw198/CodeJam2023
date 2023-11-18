import time
import json
import threading
from paho.mqtt import client as mqtt_client
from pyqtree import Index
import geopy.distance
from truck import Truck
from load import Load

broker = 'fortuitous-welder.cloudmqtt.com'
port = 1883
topic = "CodeJam"
client_id = 'sillygooses01'
username = 'CodeJamUser'
password = '123CodeJam'

#set up the spatial index for trucks and loads
trucks = Index(bbox=[-180, -90, 180, 90]) #Latitude, Longitude
loads = Index(bbox=[-180, -90, 180, 90])
        
def connect_mqtt():
    '''Connect to mqtt network to recieve messages
    '''
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

def update_position(data):
    '''Updates the location of the entity in the space and checks if there is an available trucker-load match
    '''
    if data["type"] == "Truck":
        load_match, profit = check_loads(data['nextTripLengthPreference'], data['equipType'], data['positionLongitude'], data['positionLatitude'])

        if load_match:
            print("Load:", load_match.load_id, "Truck:", data['truckId'], "Earn:", profit)
            #send notification - return BOOL for if accepted or not
            #if accepted, remove load from loads spatial index
            accepted = True
            #need to specify time limit for answer
            if accepted:
                loads.remove(item=load_match, bbox=(load_match.originLat, load_match.originLong, load_match.originLat, load_match.originLong))
        else:
            #truck did not find a match, save to spatial index
            trucks.insert(item=Truck(data['truckId'], data['positionLatitude'], data['positionLongitude'], data['equipType'], data['nextTripLengthPreference']), bbox=(data['positionLatitude'], data['positionLongitude'], data['positionLatitude'], data['positionLongitude']))
    
    else:
        distance = geopy.distance.geodesic((data['originLatitude'], data['originLongitude']), (data['destinationLatitude'], data['destinationLongitude'])).miles
        truck_match, profit = check_trucks(data['price'], distance, type, data['originLongitude'], data['originLatitude'])

        if truck_match:
            print("Truck:", truck_match.truck_id, "Load:", data['loadId'], "Earn:", profit)
            #send notification with TIMESTAMP - return BOOL for if accepted or not
            #if accepted, remove trucker from trucks spatial index
            accepted = True
            if accepted:
                trucks.remove(item=truck_match, bbox=(truck_match.latitude, truck_match.longitude, truck_match.latitude, truck_match.longitude))
        else:
            #load did not find a match, save to the spatial index
            loads.insert(item=Load(data['loadId'], data['originLatitude'], data['originLongitude'], data['destinationLatitude'], data['destinationLongitude'], data['equipmentType'], data['price'], data['mileage']), bbox=(data['originLatitude'], data['originLongitude'], data['originLatitude'], data['originLongitude']))

def check_loads(preference, type, longitude, latitude): #input is truck info
    '''Check any loads nearby if we get a truck update

    Args:
        preference: String representing the trucker's drive preference
        type: String representing the type of load the trucker is able to carry
        longitude: Float representing the longitude location of the truck
        latitude: Float representing the latitude location of the truck

    Returns:
        load_match: Load object that is the optimal load for that trucker
        max_price: Float that represents the profit of the driver
    '''
    search_box = (
        latitude - 100,
        longitude - 100,
        latitude + 100,
        longitude + 100
    )
    load_match = None
    max_price = 0

    for load in loads.intersect(search_box):
        if type == load.type and (load.total_dist >= 200 and preference == "Long") or (load.total_dist < 200 and preference == "Short"):
            pay = load.pay - (1.38 * (load.mileage + geopy.distance.geodesic((load.originLat, load.originLong), (latitude, longitude)).miles))
            if pay > max_price:
                load_match = load
                max_price = pay
    return load_match, max_price

def check_trucks(pay, distance, type, longitude, latitude): #input is load info
    '''Check if there are any trucks nearby if we recieve a load

    Args:
        pay: Float that represents how much the driver can earn from this load
        distance: Float representing the distance the load needs to be brought
        type: String representing the type of load
        longitude: Float representing the longitude location of the load
        latitude: Float representing the latitude location of the load

    Returns:
        truck_match: Truck object that is the optimal load for that trucker
        max_price: Float that represents the profit of the driver
    '''
    search_box = (
        latitude - 100,
        longitude - 100,
        latitude + 100,
        longitude + 100
    )
    truck_match = None
    max_price = 0

    for truck in trucks.intersect(search_box):
        if type == truck.equip_type and (distance >= 200 and truck.trip_pref == "Long") or (distance < 200 and truck.trip_pref == "Short"):
            pay = pay - (1.38 * (distance + geopy.distance.geodesic((truck.latitude, truck.longitude), (latitude, longitude)).miles))
            if pay > max_price:
                truck_match = truck
                max_price = pay
    return truck_match, max_price

def on_message(client, userdata, message): 
    '''Run when an update is recieved
    '''
    try:
        data = json.loads(message.payload.decode())
        update_position(data)
                        
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
    
if __name__ == '__main__':
    run()