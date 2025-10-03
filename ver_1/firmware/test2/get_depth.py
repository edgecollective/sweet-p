import time
import board
import analogio

# Constants
ANALOG_PIN = board.A0
RANGE = 5000  # Depth measuring range 5000mm (for water)
VREF = 3.3  # ADC reference voltage for most CircuitPython boards (3.3V)
CURRENT_INIT = 4.00  # Current @ 0mm (unit: mA)
DENSITY_WATER = 1  # Pure water density normalized to 1
DENSITY_GASOLINE = 0.74  # Gasoline density
PRINT_INTERVAL = 1.0  # 1 second interval

# Initialize analog input
analog_in = analogio.AnalogIn(ANALOG_PIN)

# Variables
timepoint_measure = time.monotonic()

def get_voltage(pin):
    """Convert analog reading to voltage"""
    return (pin.value * VREF) / 65536

def main():
    global timepoint_measure
    
    print("Depth sensor starting...")
    
    while True:
        current_time = time.monotonic()
        
        if current_time - timepoint_measure > PRINT_INTERVAL:
            timepoint_measure = current_time
            
            # Read voltage from analog pin
            data_voltage = get_voltage(analog_in) * 1000  # Convert to mV
            
            # Calculate current (assuming 120 ohm sense resistor)
            data_current = data_voltage / 120.0  # Current in mA
            
            # Calculate depth from current readings
            depth = (data_current - CURRENT_INIT) * (RANGE / DENSITY_WATER / 16.0)
            
            # Ensure depth is not negative
            if depth < 0:
                depth = 0.0
            
            # Print results
            print(f"depth: {depth:.2f}mm")
        
        time.sleep(0.1)  # Small delay to prevent excessive CPU usage

if __name__ == "__main__":
    main()
