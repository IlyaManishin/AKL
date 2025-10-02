from models import BLData, bl_list_to_json
from umqtt.simple import MQTTClient
import ujson


MQTT_BROKER = "5.35.88.189"   # публичный брокер
MQTT_PORT   = 22
CLIENT_ID   = "esp32_micropython"
TOPIC       = b"test/beacons"

def mqtt_send_bldata(data: list[BLData]):
    json_res = bl_list_to_json(data)
    client = connect_mqtt()
    client.publish(TOPIC, json_res)
    print("Отправлено:", json_res)
    client.disconnect()
    
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.connect()
    print("Подключено к MQTT:", MQTT_BROKER)
    return client
