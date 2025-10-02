import json
import paho.mqtt.client as mqtt
from typing import Any

import rssi_position
from app_state import GlobalState, AppStates

BROKER = "localhost"
PORT = 1883
TOPIC = "test/beacons"

global_state = GlobalState()


def on_connect(client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:
    print("Подключено к брокеру с кодом:", rc)
    client.subscribe(TOPIC)


def json_data_to_station_rssi(data) -> list[rssi_position.StationRssi]:
    res = []
    for i in data:
        try:
            station_rssi = rssi_position.StationRssi(i["name"], i["rssi"])
            res.append(station_rssi)
        except:
            pass
    return res

def print_station(station: rssi_position.StationRssi):
    print(f"{station.name} = {station.rssi}")

def on_board_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    global_state.save_last_updated()
    # if global_state.get_state() == AppStates.WAITING:
    #     return
    try:
        payload_str: str = msg.payload.decode()
        data = json.loads(payload_str)
        stations = json_data_to_station_rssi(data)
    except Exception as e:
        print("Ошибка обработки:", e)
        return 
    
    for i in stations:
        if int(i.name.split("_")[1]) <= 4:
            print_station(i) 
    if len(stations) < 2:
        return


def mqtt_run() -> None:
    client: mqtt.Client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_board_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
