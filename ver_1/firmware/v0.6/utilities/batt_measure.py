import board
import time
from analogio import AnalogIn

# Configuration
NUM_AVE = 10
TIME_SPACING = 1  # seconds between readings

# Initialize ADC pin
adc_pin = AnalogIn(board.A1)

def get_voltage(pin):
    """Convert raw ADC value to voltage (0-3.3V range)"""
    return (pin.value * 3.3) / 65536

def get_average_voltage():
    """Take NUM_AVE readings, spaced TIME_SPACING seconds apart, and return average"""
    total = 0.0

    print(f"Taking {NUM_AVE} readings, {TIME_SPACING} second(s) apart...")

    for i in range(NUM_AVE):
        voltage = get_voltage(adc_pin)*2.
        total += voltage
        print(f"  Reading {i+1}: {voltage:.3f} V")
        if i < NUM_AVE - 1:  # Don't sleep after last reading
            time.sleep(TIME_SPACING)

    average = total / NUM_AVE
    return average

# Main loop
while True:
    avg_voltage = get_average_voltage()
    print(f"Average voltage: {avg_voltage:.3f} V")
    print("-" * 30)
    time.sleep(1)  # Brief pause before next averaging cycle
