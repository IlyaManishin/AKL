import json
import paho.mqtt.client as mqtt
from typing import Any

BROKER = "localhost"  
PORT = 1883
TOPIC = "sensors/data"

def on_connect(client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:
    print("Подключено к брокеру с кодом:", rc)
    client.subscribe(TOPIC)

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        payload_str: str = msg.payload.decode()
        data = json.loads(payload_str)    
         
    except Exception as e:
        print("Ошибка обработки:", e)

def mqtt_run() -> None:
    client: mqtt.Client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

