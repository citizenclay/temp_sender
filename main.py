from machine import Pin, Timer, I2C, reset
from ssd1306 import SSD1306_I2C
from utime import sleep, time
from network import WLAN, STA_IF
from dht import DHT22
from umqtt_simple import MQTTClient
from gc import enable, collect
import wifi_cred

# soil sensor enable on pin 13,
# soil read on pin 33, relay out on pin 12, no longer used

# display pins
sda = Pin(21)
scl = Pin(22)
# led for hearbeat
hbt = Pin(2, Pin.OUT)
# DHT22 pins
dht_enable = Pin(27, Pin.OUT)
dht = DHT22(Pin(14))
# enable pins for LED and DHT22
hbt.value(1)
dht_enable.value(1)
# start the display
i2c = I2C(sda = sda, scl = scl)
oled = SSD1306_I2C(128, 64, i2c)
# global variables
temp_raw = 0
hum_raw = 0
# WiFi init
STATION = WLAN(STA_IF)
# Message broker variables
CLIENT_ID = wifi_cred.ID
SERVER = wifi_cred.MSGBROKER
# MQTT client set-up
client = MQTTClient(CLIENT_ID, SERVER)
client.user = wifi_cred.MQTTUSER
client.pswd = wifi_cred.MQTTPSWD
mqtt_topics = (b'temp', b'humidity')
# timer assignments for HW timers
main_timer = Timer(0)
dht_timer = Timer(2)
# start the GC
enable()

def do_connect():
    '''method to connect to WiFi ap and MQTT broker'''
    if STATION.isconnected():
        STATION.disconnect()
        STATION.active(False)
        sleep(1)
    STATION.active(True)
    STATION.connect(wifi_cred.SSID, wifi_cred.WPA2PSK)
    # connect to broker
    client.connect()

def alive():
    '''blinks connected LED when called'''
    t = time()
    hbt.value(0)
    while t+.5 >= time():
        sleep(0)
    hbt.value(1)


def read_temphum():
    '''DHT22 manager that takes readings and resets the sensor'''
    def dht_cb(timer):
        '''main callback that takes readings from sensor and stores in global variable'''
        global temp_raw
        global hum_raw
        temp_raw = dht.temperature()
        hum_raw = dht.humidity()
        timer.deinit()
    def dht_error(timer):
        ''' callback that resets DHT22 by turning off its +3.3v pin and turning it back on'''
        dht_enable.value(1)
        timer.deinit()
    try:
        dht.measure()
        dht_timer.init(period=1000, mode=dht_timer.ONE_SHOT, callback=dht_cb)
    except OSError: #DHT22 raises this error if it fails to read
        dht_enable.value(0)
        dht_timer.init(period=500, mode=dht_timer.ONE_SHOT, callback=dht_error)

def publish_readings():
    '''publish readings stored in global variables'''
    temp_msg = (b'{0:3.1f}'.format(temp_raw))
    hum_msg = (b'{0:3.1f}'.format(hum_raw))
    readings = (temp_msg, hum_msg)
    try:
        for topic, reading in zip(mqtt_topics, readings):
            client.publish(topic, reading)
    except AttributeError: # raises if MQTT client isn't connected
        do_connect()
    except OSError: # raises if WiFi isn't connected (this only works the first time for some reason)
        client.connect()

def display_readings():
    '''display readings stored in global variables'''
    oled.fill(0)
    oled.text('Temp: ' + str(temp_raw), 10, 10)
    oled.text('Hum: ' + str(hum_raw), 10, 20)
    oled.show()

def main_cb(timer):
    '''main loop to be called periodically (slowly)'''
    read_temphum()
    alive()
    publish_readings()
    display_readings()
    collect()
# start the main timer
main_timer.init(period=10000, mode=main_timer.PERIODIC, callback=main_cb)