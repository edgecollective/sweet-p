"""
DFRobot Gravity: Analog Current to Voltage Converter(For 4~20mA Application)
SKU:SEN0262

GNU Lesser General Public License.
See <http://www.gnu.org/licenses/> for details.
All above must be included in any redistribution
"""

import time
import board
import analogio

# Configuration constants
ANALOG_PIN = board.A2
RANGE = 5000  # Depth measuring range 5000mm (for water)
VREF = 3.3  # ADC's reference voltage, typical for CircuitPython boards: 3.3V
CURRENT_INIT = 4.00  # Current @ 0mm (unit: mA)
DENSITY_WATER = 1  # Pure water density normalized to 1
DENSITY_GASOLINE = 0.74  # Gasoline density
PRINT_INTERVAL = 1.0  # 1 second interval

# Initialize analog input
analog_in = analogio.AnalogIn(ANALOG_PIN)

# Variables
timepoint_measure = time.monotonic()

def get_voltage(pin):
    """Convert analog reading to voltage in mV"""
    return (pin.value * VREF * 1000) / 65536

def main():
    global timepoint_measure
    
    print("Depth probe sensor starting...")
    
    while True:
        current_time = time.monotonic()
        
        if current_time - timepoint_measure > PRINT_INTERVAL:
            timepoint_measure = current_time
            
            # Read voltage from analog pin
            data_voltage = get_voltage(analog_in)
            
            # Convert voltage to current (Sense Resistor: 120ohm)
            data_current = data_voltage / 120.0
            
            # Calculate depth from current readings
            depth = (data_current - CURRENT_INIT) * (RANGE / DENSITY_WATER / 16.0)
            
            if depth < 0:
                depth = 0.0
            
            # Print results
            print(f"depth:{depth:.2f}mm")

if __name__ == "__main__":
    main()