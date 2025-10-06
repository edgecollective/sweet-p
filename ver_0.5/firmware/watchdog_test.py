import time
import board
import digitalio
from watchdog import WatchDogMode
from microcontroller import watchdog as w

# Set up the onboard LED for visual feedback
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Configure the watchdog timer
# Timeout in seconds (between 1.0 and 16.383 seconds on nRF52840)
w.timeout = 5.0  # Reset after 5 seconds if not fed

# Set the watchdog mode
# WatchDogMode.RESET will reset the board when timeout occurs
# WatchDogMode.RAISE will raise a WatchDogTimeout exception instead
w.mode = WatchDogMode.RESET

# Enable the watchdog
w.feed()  # Feed it once to start
print(f"Watchdog enabled with {w.timeout} second timeout")

# Main loop
counter = 0
while True:
    # Blink the LED to show we're running
    led.value = not led.value
    
    # Feed the watchdog to prevent reset
    w.feed()
    print(f"Fed watchdog - count: {counter}")
    
    # Normal operation - feed every second
    time.sleep(1.0)
    counter += 1
    
    # Simulate a problem after 10 iterations
    # Comment out this section for normal continuous operation
    if counter >= 10:
        print("Simulating a hang - watchdog should reset the board...")
        while True:  # Infinite loop without feeding watchdog
            led.value = True
            time.sleep(0.1)
            led.value = False
            time.sleep(0.1)
