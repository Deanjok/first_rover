import socket
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
        IP = wlan.ifconfig()[0]
        break
    
    else:
        print("connection failed")
    attempts += 1
    print(wlan.status())
    if attempts == 15:
        break
    

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(("0.0.0.0", 5005))
print("Listening...")

while True:
    data, addr = sock.recvfrom(64)
    text = data.decode()
    print(text)
