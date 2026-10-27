import network
from time import sleep
from secrets import SSID, PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID,PASSWORD)
attempts = 0
while True:
    wlan.isconnected()
    print("connecting...")
    sleep(1)
    if wlan.isconnected():
        print(wlan.ifconfig()[0])
    
    else:
        print("connection failed")
    attempts += 1
    print(wlan.status())
    if attempts == 15:
        break
    