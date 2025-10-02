import time
import bluetooth
import network
import machine

from models import BLData
import mqtt

SCAN_MS = 2000
ATOM_SCAN_TIME = 100 

SSID = "OnePlus"       
PASSWORD = "1234abcd"

# Добавляем переменную для управления записью маршрута
is_recording = True

# Настраиваем кнопку на пине 0 (замените на нужный пин)
# Кнопка должна быть подключена с подтяжкой к питанию (PULL_UP)
button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)  
    wlan.active(True)

    if not wlan.isconnected():
        try:
            wlan.connect(SSID, PASSWORD)
            for i in range(20): 
                if wlan.isconnected():
                    break
                time.sleep(1)
        except:
            pass

    if wlan.isconnected():
        print("WIFI: Успешно!")
    else:
        raise Exception("Ошибка подключения WIFI")

def decode_name(adv):
    data = bytes(adv)
    i = 0
    L = len(data)
    while i + 1 < L:
        length = data[i]
        if length == 0:
            break
        ad_type = data[i + 1]
        if ad_type in (0x08, 0x09):
            start = i + 2
            end = start + (length - 1)
            try:
                return data[start:end].decode("utf-8", "ignore")
            except:
                return None
        i += 1 + length
    return None

def scan_once(scan_ms=ATOM_SCAN_TIME):
    devices = {}

    def bt_irq(event, data):
        if event == 5:  
            addr_type, addr, adv_type, rssi, adv_data = data
            mac = ":".join("{:02x}".format(b) for b in addr)
            name = decode_name(adv_data) or ""

            if name.startswith("beacon_"):
                devices[mac] = (rssi, name)

    ble.irq(bt_irq)
    ble.gap_scan(scan_ms)
    time.sleep_ms(scan_ms + 10) 
    return devices

def find_stations():
    res = []
    aggregated = {}  

    iterations = int(SCAN_MS/ATOM_SCAN_TIME)
    for _ in range(iterations):
        found = scan_once()
        for mac, (rssi, name) in found.items():
            if mac not in aggregated:
                aggregated[mac] = [0, 0, name]
            aggregated[mac][0] += rssi
            aggregated[mac][1] += 1

    for mac, (rssi_sum, count, name) in aggregated.items():
        avg_rssi = rssi_sum // count
        res.append(BLData(name, avg_rssi))      
    return res

def check_button():
    """Проверяет состояние кнопки завершения маршрута"""
    global is_recording
    if button.value() == 0:  # Кнопка нажата (низкий уровень)
        time.sleep_ms(50)  # Защита от дребезга
        if button.value() == 0:  # Подтверждаем нажатие
            is_recording = False
            print("Кнопка завершения маршрута нажата!")
            return True
    return False

ble = bluetooth.BLE()
ble.active(True)
connect_wifi()
mqtt.mqtt_connect()

print("Начало записи маршрута...")
print("Для завершения нажмите кнопку")

try:
    while is_recording:
        # Проверяем кнопку перед началом сканирования
        if check_button():
            break
            
        res: list[BLData] = find_stations()
        res.sort(key=lambda i: i.get_index())
        print(res)

        mqtt.mqtt_send_bldata(res)
        
        # Также проверяем кнопку после отправки данных
        if check_button():
            break

finally:
    # Корректно завершаем работу
    ble.active(False)
    print("Запись маршрута завершена")
    print("BLE отключен")