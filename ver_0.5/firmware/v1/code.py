# code.py - Main application
import time
import board
import digitalio
import microcontroller
from microcontroller import watchdog as w
from watchdog import WatchDogMode

use_watchdog=True

# Set up the onboard LED for visual feedback
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Check if a pin is grounded (connect to GND to disable watchdog)
safe_pin = digitalio.DigitalInOut(board.P0_06)  # Pick any pin
safe_pin.pull = digitalio.Pull.UP

if not safe_pin.value:  # Pin is grounded
    #disable watchdog
    w.deinit()
    use_watchdog=False
    

# Check and display the reset reason
print("\n=== Boot Information ===")
print(f"Reset reason: {microcontroller.cpu.reset_reason}")

# Check if we came from a watchdog reset via boot.py
was_watchdog_reset = False
if microcontroller.nvm and microcontroller.nvm[0] == 0xFF:
    was_watchdog_reset = True
    # Clear the flag
    microcontroller.nvm[0] = 0

# Check and display the reset reason
print("\n=== Boot Information ===")
print(f"Reset reason: {microcontroller.cpu.reset_reason}")

if was_watchdog_reset:
    print("*** This was a WATCHDOG RESET (recovered via boot.py) ***")
    # Increment persistent watchdog counter
    if microcontroller.nvm:
        watchdog_count = microcontroller.nvm[1]  # Use NVM[1] for counter
        microcontroller.nvm[1] = (watchdog_count + 1) % 256
        print(f"Total watchdog resets: {microcontroller.nvm[1]}")
    # Flash LED rapidly 5 times to indicate watchdog reset
    for _ in range(5):
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.1)
elif microcontroller.cpu.reset_reason == microcontroller.ResetReason.WATCHDOG:
    print("*** Direct watchdog reset detected ***")
    # Check NVM for a flag if you want to be more certain
else:
    print("Normal boot (power-on or reset button)")
    # Reset watchdog counter on normal boot
    if microcontroller.nvm:
        microcontroller.nvm[1] = 0  # Clear counter on normal boot
    # Single long flash for normal boot
    led.value = True
    time.sleep(1)
    led.value = False

print("========================\n")

if use_watchdog==True:
    # Configure the watchdog timer
    w.timeout = 5.0  # Reset after 5 seconds if not fed
    w.mode = WatchDogMode.RESET

    # Enable the watchdog
    w.feed()  # Feed it once to start
    print(f"Watchdog enabled with {w.timeout} second timeout")

# Main loop
counter = 0
while True:
    # Blink the LED to show we're running
    led.value = not led.value
    
    if use_watchdog==True:
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
