
'''
Controls 4 motors for a PCA9685 motor board.
Reads speeds from -100 to 100, one per line, and drives the motor
Receives data thourgh WiFi (UDP)
Positive = forward, negative = backward, 0 = brake.
Stops the motor safely on Ctrl+C or when input ends.
'''
# Imports

# Importing MotorDriver from motoboard. This will let us move the motors.
from motorboard import MotorDriver
# importing sleep, sleep_us, ticks_ms, ticks_diff.
# Sleep allows us to have pauses in the program so that the sensors and the hardware, can catch up with one another.
# sleep_us. This allows us to pause the program in some places for microseconds. Reason we dont use seconds or milliseconds in some cases
# is because we need a pause but a millisecond is still too long
# ticks_ms the time right now, in ms since the pico powered on. 
# ticks_diff the differnece between ticks_ms() and last_message
from time import sleep, sleep_us, ticks_ms, ticks_diff
# sys is used to exit the program
import sys
# Importing Pin from the pico so that we are able to use the certain pins for the hardware
from machine import Pin
# time_pulse_us, measues how long a pin stays high or low, in microsenconds.
from machine import time_pulse_us
# select, Poll() comes from here, allows you to check whether data has arrived without delay
import select
# socket sends and receives messages over the network.
import socket
#network contrsol the Pico's WiFi chip.
import network
# wifi password and the SSID
from secrets import SSID, PASSWORD

# Storing Universal Variables
WINDOW = 3 # Variable that stores the maximum amount of elements we want in a list
STOP_DISTANCE = 40.0 # The distance from an object at which the rover should stop
MAX_MISSES = 5 # The max amount of miss readings of 0.0 we tolerate otherwise STOP 
current_speed = 0 # Current rover speed
new_speed = 0 # New rover speed. Allows us to assign new speed
RAMP_DELAY = 0.05 # The delay between each RAMP_STEP of the rovers speed
RAMP_STEP = 10 # The step by which the rover is allowed to increase/decrease speed
# select.POLLIN, what to watch it for IN means incoming data. 
TIMEOUT_MS = 2000 # The max amount of time we allows the pico to not receive a signal
last_message = ticks_ms() # Assigns ticks_ms() to last_message
# We are using this to track the time between eah signal/ command that is sent to the rover
history = [] # Our list for storing distance from an object
miss_counter = 0 # Allows us to track how many miss reading of 0.0 we have in a row.
# If 5 then we terminate the program and the rover stops 
avg = 0 # Average distance, calculated from the history list that only holds 3 values at the same time


# Pin varaibles
# This will control the Trig pin from the HC-SRO4
trig_pin = Pin(14,Pin.OUT)
# This will control the Echo pin from the HC-SRO4
echo_pin = Pin(15,Pin.IN)

# Connects the Pico to the WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID,PASSWORD)
# Tracking the amount of attempts that it takes us to connect the two boards
attempts = 0
'''
A while True loop that tries to connec the two boards via WIFI.
If a connection is established it prints the IP address.
And then sets it to the variable IP and breaks from the True loop.
else if a connection is not established it tries again counts the attempts
counter up by 1 each time it fails.
prints the status of the issue. 
If it tries 10 times and the connection is not established it quits the program
'''
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
        
# socket.socket. Using the socket library to build its functon that builds a new socket.
# AF_INET is the IPv4. The familiar IP address style
# socket.SOCK_DGRAM, which kind of message it is this one is UDP
# stores all this is sock
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
poller = select.poll() #Creates a watcher and assigns it to poller.
poller.register(sock, select.POLLIN) # tells the watcher what to watch. sock, the wifi socket

# This means listen on port 5005, in any address the Pico has
sock.bind(("0.0.0.0", 5005))
print("Listening...")

# Confirming that the wifi has been connected and now the motors will start.
print("Starting the motor...")

'''
Connecting to the motorboard file and taking out the MotorDriver class so
that we can now use the board to drive the motors.
motor.pwm is how we talk to the PCA9685 chip
'''
motor = MotorDriver()

# Board channels (numbered output wires from the chip, 0-11).
# We use 12:
# Motor A
#   Channel 0 = speed (PWM)
#   Channel 1 = direction input A (on/off)
#   Channel 2 = direction input B (on/off)
# Motor B
#   Channel 3 = speed (PWM)
#   Channel 4 = direction input C (on/off)
#   Channel 5 = direction input D (on/off)
# Motor C
#   Channel 6 = speed (PWM)
#   Channel 7 = direction input E (on/off)
#   Channel 8 = direction input F (on/off)
# Motor D
#   Channel 9 = speed (PWM)
#   Channel 10 = direction input G (on/off)
#   Channel 11 = direction input H (on/off)
'''
A function that determines how our motors move. Forward, Backward and which will
be moving forwards or backwards
'''
def move(speed):
    """Drive the motor. speed: -100 to 100 (sign = direction)."""

    # Pick the direction pair. 1 = on, 0 = off.
    # The motor driver reads channels 1, 2, 4 and 5 TOGETHER:
    #   pin_a  pin_b pin_c pin_d pin_e pin_f pin_g pin_h     result
    #     0      1     1     0     1     0     1     0       forward
    #     1      0     0     1     0     1     0     1       backward
    #     1      1     1     1     1     1     1     1       brake (stop hard)
    # (all 0s, 0 0 0 0 0 0 0 0, would coast instead; brake was chosen on purpose)
    # Going forward
    if speed > 0:
        pin_a = 0
        pin_b = 1
        pin_c = 1
        pin_d = 0
        pin_e = 1
        pin_f = 0
        pin_g = 1
        pin_h = 0
        
    # Moving backwards
    elif speed < 0:
        pin_a = 1
        pin_b = 0
        pin_c = 0
        pin_d = 1
        pin_e = 0
        pin_f = 1
        pin_g = 0
        pin_h = 1
        
    # Hard Breaking
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

    # Speed: channel 0, 3, 6 and 9 flickers on and off (PWM). The motor feels the
    # average, so 50 = on half the time = half power.
    # Despite the name, this library's setServoPulse takes a percentage
    # and converts it to the chip's 0-4095 range: duty * (4095 / 100).
    motor.pwm.setServoPulse(0, duty) # Motor A
    motor.pwm.setServoPulse(3, duty) # Motor B
    motor.pwm.setServoPulse(6, duty) # Motor C
    motor.pwm.setServoPulse(9, duty) # Motor D
    
    # Direction: send the pair chosen above. Both lines always run;
    # channel 1 always gets pin_a and channel 2 always gets pin_b.
    motor.pwm.setLevel(1, pin_a)
    motor.pwm.setLevel(2, pin_b)
    # channel 4 always gets pin_c and channel 5 always gets pin_d
    motor.pwm.setLevel(4, pin_c)
    motor.pwm.setLevel(5, pin_d)
    # channel 7 always gets pin_e and channel 8 always gets pin_f
    motor.pwm.setLevel(7, pin_e)
    motor.pwm.setLevel(8, pin_f)
    # channel 10 always gets pin_g and channel 11 always gets pin_h  
    motor.pwm.setLevel(10, pin_g)
    motor.pwm.setLevel(11, pin_h)

# This function is using the HC-SRO4 to figure out the distance from the closest
# object in front of the rover
def get_distance():
    trig_pin.value(0) # It turns off
    sleep_us(2) # Pauses for 2 microseconds
    trig_pin.value(1) # Turns on
    sleep_us(10) # Waits 10 microseconds
    trig_pin.value(0) # Turns off again
    '''
    This is done because HC-SR04 starts its measuerement when the Trif pin receives
    a short pulse: low, then high for 10 microseconds, then low again. That means go to the sensor
    echo_pin means which pin to watch.
    1 measure how long it stays high
    30000, give up after 30,000 microseconds (30ms) if nothing happens.
    and then it returns the time in microseconds to duration
    '''
    
    duration = time_pulse_us(echo_pin, 1, 30000)
    # If the duration is below 0 we will set that to 0 because it means that an error has occured
    # -2 Echo never went high
    # -1 Echo went high but didnt comeback low within 30ms
    if duration < 0:
        # This means no echo, no valid reading.
        return 0.0
    # if the number is zero or above we will return the distance that was measured
    else:
        # 0.0343 is the speed of sound in cm per microsecond.
        # duration * 0.0343 = time x speed = distance.
        # / 2 because the sound went there and back, so it will only be half the distance.
        return duration * 0.0343 / 2
    

def add_reading(history, distance):
'''
This is where the history list is adding a distance, checking if the list is above 3
elements and if it is is pops(0) which means it deleted the first entry of the list,
because it is the oldest one. If you think of a list [1.2, 3.2, 5.4] with this function
let's add another number which is 4.8. The function adds it to the list [1.2, 3.2, 5.4, 4.8].
It checks if the list is above WINDOW = 3. if it is it deletes the first entry 1.2 with
history.pop(0). The list then becomes [3.2, 5.4, 4.8]. We then return the list outside of the function
If another number comes in we now delete 3.2 since it is the Oldest entry and we are following
FIFO. First In First Out.
'''
    history.append(distance)
    if len(history) > WINDOW:
        history.pop(0)
    return history

def average(history):
'''
Calculates the average distane in the 3 element history list.
If we have just started the program or there are no elements in the list
which makes the length of the list = 0. We will return None. Why None? I don't know
If the length does not equal = 0 we will take the sum of the list and / it by the length to
get our average number of the list. The while loop will not add 0.0 to the list as that
will drag down the avg by a lot. This means the rover might constantly jitter because of a
miss readings, that are not true.
'''
    if len(history) == 0:
        # Returns None because an empty line has no average. Returning 0 would mean
        # touching somethings so its wrong. It will also drag the avg down.
        return None
    return sum(history) / len(history)

while True:
'''
The overall structure in this loop is we try to see if the loop receives an input, if it does
it reads it, turns it into an int. If the avg distance is above 40 the rover drives forwards if not it stops.
Reverses to 50cm away and then stops, and starts driving forward again. If an input is not
received after 2 seconds it stops the rover to prevent it from crashing into a wall if input does not
arrive because the program was shutdown or a bug occured. And if a exception occurs we try to stop
the program from crashing
'''
    # try to run the while loop
    try:
        # Getting the distance from the sensor.
        distance = get_distance()
        # Because the sensors recommended delay is 0.06 between readings, we set it a little
        # above that. Otherwise the sensor might give a lot of miss readings
        sleep(0.08)
        # Checks the elapsed time since last input.
        '''
        last_message and ticks_ms() are used to calculated the elapsed time since last input.
        it is at the top here because it makes a full loop and just before the program decides
        if the input is quick enough or not it calculates the elapsed time.
        '''
        elapsed = ticks_diff(ticks_ms(), last_message)
        
        '''
        This will only trigger if a new input is sent and received
        It checks if anything has arrived. the (0) means answer whatever has arrived
        immediately with a 0 ms delay. Returns True if something is waiting and False otherwise.
        '''
        if poller.poll(0):
            # Assigns the time the moment the last message arrived.
            # restarts the time and assigns it to last_message
            last_message = ticks_ms()
            data, addr = sock.recvfrom(64)
            # recvfrom(64) means it receives the input from sock as 64 bytes piece.
            # data = the input we gave it.
            # addr = the address it was sent from
            # we need to unpack both because it will always give to pieces of info.
            # Pi:   50  →  "50\n"  →  .encode()  →  b"50\n"  ──WiFi──►  Pico: b"50\n"  →  .decode()  →  "50\n"  →  strip, float, int  →  50
            text = data.decode()


            '''
            The input is text. We strip the white spaces from the start and end
            We turn it into a float, we then turn it into an integer and assign it to
            new speed. Because a new_speed has been received.
            '''
            new_speed = int(float(text.strip()))
            
            '''
            In this loop we check if the distance that has been received is above 0.0
            We add it to the history list. Calculate the average distance. IF average distance
            if below or equal to STOP_DISTANCE = 40. We stop, reverse until avg is 50,
            stop and go forward again. And reset the miss_counter because the
            program got a good reading of above 0.0.
            Else we add 1 to the miss_counter because the reading was off. Check
            the avg distance, if it is above STOP_DISTANCE, it then checks if miss_counter
            is above or equal to MAX_MISSES. if yes then it stop the rover. To prevent a crash
            If miss_counter is below MAX_MISSES sets current speed to new speed.
            If avg_DISTANCE is below the STOP_DISTANCE the rover will stop, to prvent a crash
            '''
            if distance > 0.0:
                add_reading(history, distance)

                avg = average(history)
                '''
                this if statement checks if the avg distance is below or equal to STOP_DISTANCE
                then set current speed to 0. So stop immediately. Then reverse until we are beyond 50cm
                from the object and then stop again.
                '''
                if avg <= STOP_DISTANCE:
                    print(f"Current Speed 1: {current_speed}")
                    move(0)

                    # ramp down, stop and start reversing, then we need to check if the avg is above 40 and stop
                    while 0.0 < avg < 50.0:
                        sleep(0.06)
                        distance = get_distance()
                        add_reading(history, distance)
                        avg = average(history)
                        print(f"avg: {avg}")
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
                '''
                else if the avg distance is above STOP_DISTANCE
                it looks if new_speed is above current if so ramp up to that new speed
                by RAMP_STEP. If new_speed is lower than current ramp down to that speed
                by RAMP_STEP
                if it is the same then keep moving at current speed.
                As we exit the statements we move at a new speed since we always want to be at that speed here
                and then it assigns new speed to current speed. Resets the miss_counter because the reading
                was positive
                '''
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
                miss_counter = 0
                '''
                If distance is below 0.0 we add a miss_counter because we got an error/ missread.
                check if avg distance is above STOP_DISTANCE if it is it then checks if miss_counter is
                above MAX_MISSES and if it is it stops the rover to prevent a crash. If it isn't set new_speed
                to current speed.
                If avg is below STOP_DISTANCE we immediately stop to prevent an accident
                '''
            else:
                miss_counter += 1
                if avg > STOP_DISTANCE:
                    if miss_counter >= MAX_MISSES:
                        current_speed = 0
                        new_speed = 0
                        sys.exit()
                    else:
                        current_speed = new_speed
                else:
                    current_speed = 0
                    new_speed = 0
                    
        #LOG; This lines give syntax error
        # Fix: it looked like this         else: elapsed > TIMEOUT_MS:
        '''
        If a message has not been received within TIMEOUT_MS. Set speed to 0 to not crash into anything
        '''
        if elapsed > TIMEOUT_MS:
            move(0)
            current_speed = 0
            new_speed = 0
                            
    # Input that isn't a number (e.g. "hello" or a blank line): ignore it.
    except ValueError:
        pass

    # Ctrl+C: stop the motor before exiting, so it doesn't keep running.
    except KeyboardInterrupt:
        move(0)
        print("You pressed Ctrl+C\nExiting program...")
        break


