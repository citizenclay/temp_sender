from machine import Pin, Timer, I2C, reset
from ssd1306 import SSD1306_I2C
from utime import sleep, time
from network import WLAN, STA_IF
from dht import DHT22
from umqtt.simple import MQTTClient
from gc import enable, collect
from . import wifi_cred

# soil sensor enable on pin 13,
# soil read on pin 33, relay out on pin 12, no longer used
sda = Pin(21)
scl = Pin(22)
hbt = Pin(2, Pin.OUT)
dht_enable = Pin(27, Pin.OUT)
dht = DHT22(Pin(14))
hbt.value(1)
dht_enable.value(1)
i2c = I2C(sda = sda, scl = scl)
oled = SSD1306_I2C(128, 64, i2c)
temp_raw = 0
hum_raw = 0
STATION = WLAN(STA_IF)
CLIENT_ID = 'Closet'
SERVER = wifi_cred.MSGBROKER
client = MQTTClient(CLIENT_ID, SERVER)
client.user = 'mqtt-test'
client.pswd = 'mqtt-test'
mqtt_topics = (b'temp', b'humidity')
main_timer = Timer(0)
#soil_timer = Timer(1)
dht_timer = Timer(2)
enable()

def do_connect():
    '''method to connect to wifi ap'''
    if STATION.isconnected():
        STATION.disconnect()
        STATION.active(False)
        sleep(1)
    STATION.active(True)
    STATION.connect(wifi_cred.SSID, wifi_cred.WPA2PSK)
    client.connect()

def alive():
    t = time()
    hbt.value(0)
    while t+.5 >= time():
        sleep(0)
    hbt.value(1)


def read_temphum():
    def dht_cb(timer):
        global temp_raw
        global hum_raw
        temp_raw = dht.temperature()
        hum_raw = dht.humidity()
        timer.deinit()
    def dht_error(timer):
        dht_enable.value(1)
        timer.deinit()
    try:
        dht.measure()
        dht_timer.init(period=1000, mode=dht_timer.ONE_SHOT, callback=dht_cb)
    except OSError:
        dht_enable.value(0)
        dht_timer.init(period=500, mode=dht_timer.ONE_SHOT, callback=dht_error)

def publish_readings():
    temp_msg = (b'{0:3.1f}'.format(temp_raw))
    hum_msg = (b'{0:3.1f}'.format(hum_raw))
    readings = (temp_msg, hum_msg)
    try:
        for topic, reading in zip(mqtt_topics, readings):
            client.publish(topic, reading)
    except AttributeError:
        do_connect()
    except OSError:
        client.connect()

def display_readings():
    oled.fill(0)
    oled.text('Temp: ' + str(temp_raw), 10, 10)
    oled.text('Hum: ' + str(hum_raw), 10, 20)
    oled.show()

def main_cb(timer):
    read_temphum()
    alive()
    publish_readings()
    display_readings()
    collect()
main_timer.init(period=10000, mode=main_timer.PERIODIC, callback=main_cb)