WINDOW = 3
history = []
STOP_DISTANCE = 30.0
MAX_MISSES = 3
readings = [0.0, 45.2, 44.8, 0.0, 43.9, 12.0, 42.5, 41.0, 0.0, 0.0, 0.0,
            29.5, 28.0, 27.1, 26.4, 31.0, 33.5, 45.0]
stops = 0
MISS_COUNTER = 0
avg = 0
positions = []

def add_reading(history, readings):
    history.append(readings)
    if len(history) > WINDOW:
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
for i, reading in enumerate(readings, start = 0):
    if reading != 0.0:
        add_reading(history, reading)
        avg = average(history)
        if avg < STOP_DISTANCE:
            print(f"{i}: {reading} | avg: {avg:.1f} | STOP")
            stops += 1
            positions.append(i)
            
        else:
            print(f"{i}: {reading} | avg: {avg:.1f} | GO")
        MISS_COUNTER = 0
        # LOG: prints no echo | misses 3 | GO & no echo | misses 3 | STOP (sensor lost)
        # FIX: put if MISS_COUNTER == MAX_MISSES inside the if reading == 0.0
        # and put and if statement if MISS_COUNTER == MAX_MISSES...
    if reading == 0.0:
        MISS_COUNTER += 1
        if avg == None:
            print(f"{i}: no echo | misses {MISS_COUNTER} | STOP (sensor lost)")
            stops += 1
            positions.append(i)
        elif avg >= STOP_DISTANCE:
            if MISS_COUNTER >= MAX_MISSES:
                print(f"{i}: no echo | misses {MISS_COUNTER} | STOP (sensor lost)")
                stops += 1
                positions.append(i)

            else:
                print(f"{i}: no echo | misses {MISS_COUNTER} | GO")
        else:
            stops += 1
            positions.append(i)
            print(f"{i}: no echo | misses {MISS_COUNTER} | STOP (too close)")
        
        # add it to history
        # LOG: Had an issue where it printed misses 4
        # Fix:  set MISS_COUNTER = 0 when it read something besides 0.0
# Looking on google how to delete oldest element in a li
print(f"STOPs: {stops}")
print(f"Positions: {positions}")

# LOG: getting a TypeError: list.append() takes exactly one argument (0 given) even though I gave an argument
# Fix: i put list.append(history) instead of history.append(reading)

# if the list holds more than WINDOW remove the oldest and reset miss counter to 0
    
# if 0.0 shows up dont add to history but add 1 to MISSES
# Had to google how to replace oldest entry of a list with a new one FIFO
# How to avg a list
# if the MISSES = 3, STOP
# if if average of distance is below 30.0 STOP
# otherwise keep going