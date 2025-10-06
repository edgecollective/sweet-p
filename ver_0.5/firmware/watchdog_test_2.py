import time
import board
import digitalio
import microcontroller
import supervisor
from watchdog import WatchDogMode

# Check if we're in safe mode due to watchdog reset
if supervisor.runtime.safe_mode_reason:
    print(f"Safe mode detected! Reason: {supervisor.runtime.safe_mode_reason}")
    
    # Check specifically for watchdog timeout
    if supervisor.runtime.safe_mode_reason == supervisor.SafeModeReason.WATCHDOG:
        print("Watchdog timer caused reset - automatically restarting...")
        
        # Optional: Store watchdog reset info in NVM if you want persistence
        # import nvm_helper  # You'd need to create this module
        # nvm_helper.increment_watchdog_count()
        
        # Reload to exit safe mode and run normal code
        #supervisor.reload()
        microcontroller.reset()

# Import watchdog after safe mode check
from microcontroller import watchdog as w

# Set up the onboard LED for visual feedback
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Check and display the reset reason
print("\n=== Boot Information ===")
print(f"Reset reason: {microcontroller.cpu.reset_reason}")

# Determine if this was a watchdog reset
if microcontroller.cpu.reset_reason == microcontroller.ResetReason.WATCHDOG:
    print("*** This was a WATCHDOG RESET ***")
    # Flash LED rapidly 5 times to indicate watchdog reset
    for _ in range(5):
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.1)
else:
    print("Normal boot (power-on, reset button, or reload)")
    # Single long flash for normal boot
    led.value = True
    time.sleep(1)
    led.value = False

print("========================\n")

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
