# Controls 2 motors for a PCA9685 motor board.
# Reads speeds from -100 to 100, one per line, and drives the motor.
# Positive = forward, negative = backward, 0 = brake.
# Stops the motor safely on Ctrl+C or when input ends.

from motorboard import MotorDriver  # library for the motor board
from time import sleep, sleep_us, ticks_ms, ticks_diff        # used for ramping speed
import sys                          # for sys.stdin.readline()
from machine import Pin
from machine import time_pulse_us
import select
import socket
import network
from secrets import SSID, PASSWORD

WINDOW = 3
STOP_DISTANCE = 40.0
MAX_MISSES = 5

trig_pin = Pin(14,Pin.OUT)
echo_pin = Pin(15,Pin.IN)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID,PASSWORD)
attempts = 0
while True:
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
        if attempts == 10:
            sys.exit()
        

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(("0.0.0.0", 5005))
print("Listening...")

print("Starting the motor...")  # confirms the program has started
# wifi goes first then all the motor codes
# motor.pwm is how we talk to the PCA9685 chip
motor = MotorDriver()

# Board channels (numbered output wires from the chip, 0-15).
# We use six:
# Motor A
#   Channel 0 = speed (PWM)
#   Channel 1 = direction input A (on/off)
#   Channel 2 = direction input B (on/off)
# Motor B
#   Channel 3 = speed (PWM)
#   Channel 4 = direction input C (on/off)
#   Channel 5 = direction input D (on/off)


def move(speed):
    """Drive the motor. speed: -100 to 100 (sign = direction)."""

    # Pick the direction pair. 1 = on, 0 = off.
    # The motor driver reads channels 1, 2, 4 and 5 TOGETHER:
    #   pin_a  pin_b pin_c pin_d result
    #     0      1     1     0   forward
    #     1      0     0     1   backward
    #     1      1     1     1   brake (stop hard)
    # (all 0s, 0 0 0 0, would coast instead; brake was chosen on purpose)
    if speed > 0:
        pin_a = 0
        pin_b = 1
        pin_c = 1
        pin_d = 0
        pin_e = 1
        pin_f = 0
        pin_g = 1
        pin_h = 0

    elif speed < 0:
        pin_a = 1
        pin_b = 0
        pin_c = 0
        pin_d = 1
        pin_e = 0
        pin_f = 1
        pin_g = 0
        pin_h = 1
    else:
        pin_a = 1
        pin_b = 1
        pin_c = 1
        pin_d = 1
        pin_e = 1
        pin_f = 1
        pin_g = 1
        pin_h = 1

    # Duty = % of time the power is on (0-100).
    # Direction is already handled by the pins, so duty only needs
    # the size of the speed, not its sign: abs(-50) -> 50.
    duty = abs(speed)

    # Can't be on more than 100% of the time, so cap it.
    if duty > 100:
        duty = 100

    # Speed: channel 0 and 3 flickers on and off (PWM). The motor feels the
    # average, so 50 = on half the time = half power.
    # Despite the name, this library's setServoPulse takes a percentage
    # and converts it to the chip's 0-4095 range: duty * (4095 / 100).
    motor.pwm.setServoPulse(0, duty) # Motor A
    motor.pwm.setServoPulse(3, duty) # Motor B
    motor.pwm.setServoPulse(6, duty)
    motor.pwm.setServoPulse(9, duty)

    # Direction: send the pair chosen above. Both lines always run;
    # channel 1 always gets pin_a and channel 2 always gets pin_b.
    motor.pwm.setLevel(1, pin_a)
    motor.pwm.setLevel(2, pin_b)
    # channel 4 always gets pin_c and channel 5 always gets pin_d
    motor.pwm.setLevel(4, pin_c)
    motor.pwm.setLevel(5, pin_d)
    
    motor.pwm.setLevel(7, pin_e)
    motor.pwm.setLevel(8, pin_f)
    
    motor.pwm.setLevel(10, pin_g)
    motor.pwm.setLevel(11, pin_h)
    
def get_distance():
    trig_pin.value(0)
    sleep_us(2)
    trig_pin.value(1)
    sleep_us(10)
    trig_pin.value(0)
    duration = time_pulse_us(echo_pin, 1, 30000)
    if duration < 0:
        return 0.0
    else:
        return duration * 0.0343 / 2
    
def add_reading(history, distance):
    history.append(distance)
    if len(history) > 3:
        history.pop(0)
    return history

def average(history):
    if len(history) == 0:
        return None
    return sum(history) / len(history)
# in a while loop read through the list, only read real numbers that are not 0.0

# Googling how to read through a lsit
# LOG: TypeError: '<' not supported between instances of 'NoneType' and 'float'
# FIX: add_reading was never called so the list was always empty therefore average return None
        # Looked up how to get list index and item at the same time
        
current_speed = 0
new_speed = 0
RAMP_DELAY = 0.05
RAMP_STEP = 10
poller = select.poll()
poller.register(sock, select.POLLIN)
TIMEOUT_MS = 2000
last_message = ticks_ms()
history = []
MISS_COUNTER = 0
avg = 0

while True:
    try:
        distance = get_distance()
        sleep(0.08)
        #print(f"Distance {distance}")
        elapsed = ticks_diff(ticks_ms(), last_message)
        #print(elapsed)
        #This will only trigger if a new input is sent
        if poller.poll(0): # readline() returns one line of text, including the "\n" at the end.
            last_message = ticks_ms()  
            data, addr = sock.recvfrom(64)
            text = data.decode()
            #print(text)

            #Read it from the inside out:

            #line.strip() turns "50.5\n" into "50.5" (text)
            #float(...) turns it into 50.5 (a float)
            #int(...) turns it into 50 (an int, so range() is happy)
            new_speed = int(float(text.strip()))
            if distance > 0.0:
                add_reading(history, distance)
                # LOG: this lines keeps giving NameError: name 'reading' isn't defined

                avg = average(history)
                
                if avg <= STOP_DISTANCE:
                    print(f"Current Speed 1: {current_speed}")
                    current_speed = 0

                    # ramp down, stop and start reversing, then we need to check if the avg is above 40 and stop
                    while 0.0 < avg < 50.0:
                        sleep(0.06)
                        distance = get_distance()
                        add_reading(history, distance)
                        avg = average(history)
                        print(f"Avg: {avg}")
                        print(f"History: {history}")
                        print(f"Distance: {distance}")
                        

                        for magnitude in range(current_speed, -101, -RAMP_STEP):
                            move(magnitude)
                            sleep(RAMP_DELAY)
                        current_speed = -100
                        
                    for magnitude in range(current_speed,1,RAMP_STEP):
                        move(magnitude)
                        sleep(RAMP_DELAY)
                    current_speed = 0
                    new_speed = 0
            # if there is no input we need to look at out sensor
                #if 0.0 < avg <= STOP_DISTANCE:
                    #for magnitude in range(current_speed,-1,-RAMP_STEP):
                     #   move(magnitude)
                      #  sleep(RAMP_DELAY)
                   # current_speed = 0
                    
                else:
                        # if the input is higher than the current value it will ramp up slowly
                        # from current_speed (50) to value(100) with a step of RAMP_STEP and a
                        # delay of RAMP_DELAY. Function move() has magnitude inside it because
                        # we want that smooth ramp up to the speed we want
                    if new_speed > current_speed:
                        for magnitude in range(current_speed,new_speed+1,RAMP_STEP):
                            move(magnitude)
                            sleep(RAMP_DELAY)
                        # The same as above but for value < current_speed and with a negative RAMP_STEP
                    elif new_speed < current_speed:
                        for magnitude in range(current_speed,new_speed-1,-RAMP_STEP):
                            move(magnitude)
                            sleep(RAMP_DELAY)
                    else:
                        move(current_speed)

                        #Setting move(value) so that if we are increasing by lets say 2 and the input is
                        # 51 it may stop a little and then set itself to 51, so we still get the smooth acceleration/
                        # deceleration but it will set to the correct value
                    move(new_speed)
                        # Setting the value to current_speed so that the program knows what is the current_speed
                        # at the top of it and it can be reused.
                    current_speed = new_speed
                MISS_COUNTER = 0
            else:
                #print("issue")
                MISS_COUNTER += 1
                #if avg is None:
                  #  current_speed = 0
                  #  new_speed = 0
                if avg >= STOP_DISTANCE:
                    if MISS_COUNTER >= MAX_MISSES:
                        current_speed = 0
                        new_speed = 0
                    else:
                        current_speed = new_speed
                else:
                    current_speed = 0
                    new_speed = 0
                    
        #LOG; This lines give syntax error
        # Fix: it looked like this         else: elapsed > TIMEOUT_MS:
        if elapsed > TIMEOUT_MS:
            print("hello")
            move(0)
            current_speed = 0
            new_speed = 0
            #print(new_speed)
            #print(current_speed
                
                
            #print(f"Current speed: {current_speed}")
        # Input that isn't a number (e.g. "hello" or a blank line): ignore it.
    except ValueError:
        pass

        # Ctrl+C: stop the motor before exiting, so it doesn't keep running.
    except KeyboardInterrupt:
        move(0)
        print("You pressed Ctrl+C\nExiting program...")
        break


