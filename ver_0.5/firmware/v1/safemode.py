# safemode.py - This ONLY runs when in safe mode
import supervisor
import microcontroller
import time

print("[safemode.py] Safe mode handler activated")
print(f"[safemode.py] Reason: {supervisor.runtime.safe_mode_reason}")

# Check if safe mode was caused by watchdog
if supervisor.runtime.safe_mode_reason == supervisor.SafeModeReason.WATCHDOG:
    print("[safemode.py] Watchdog timeout detected - will reset to exit safe mode")
    
    # Set a flag in NVM to track this was a watchdog reset
    # This helps your main code know what happened
    if microcontroller.nvm:
        # Use NVM[0] as a watchdog flag: 0xFF = watchdog reset
        microcontroller.nvm[0] = 0xFF
        print("[safemode.py] Watchdog flag set in NVM")
    
    # Brief delay so you can see the message if monitoring serial
    time.sleep(0.5)
    
    # Hard reset to exit safe mode and run normally
    microcontroller.reset()

# If we get here, safe mode was caused by something else
# Let it proceed to safe mode as normal for debugging
print("[safemode.py] Non-watchdog safe mode - entering safe mode for debugging")
