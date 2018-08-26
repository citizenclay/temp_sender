# temp_sender
Micropython ESP32 temp sensor based on DHT22 sensor

This script requires the ssd1306 and umqtt.simple libraries to be frozen in the Micropython build or you will run out of memory. I renamed the simple.py script because it needed to be in the modules directory to compile.

Modify the wifi_cred_example.py to your settings and transfer it to the esp32 also. If your broker doesn't require a user/pswd, just remove the relevant lines from the script.