#!/usr/bin/env python3
"""
Live plotting script for tprobe2.py serial output with fixed depth scale
Reads voltage, current, and depth data from serial port and plots in real-time
Depth scale is fixed to 0-1000mm
"""

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import argparse
import sys
import time

class SerialPlotter:
    def __init__(self, port, baudrate=115200, max_points=100):
        self.port = port
        self.baudrate = baudrate
        self.max_points = max_points
        
        # Data storage
        self.times = deque(maxlen=max_points)
        self.voltages = deque(maxlen=max_points)
        self.currents = deque(maxlen=max_points)
        self.depths = deque(maxlen=max_points)
        
        # Serial connection
        self.ser = None
        self.start_time = time.time()
        
        # Plot setup
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(10, 8))
        self.fig.suptitle('Live Sensor Data from tprobe2.py (Fixed Depth Scale)')
        
        # Initialize lines
        self.line1, = self.ax1.plot([], [], 'b-', label='Voltage (mV)')
        self.line2, = self.ax2.plot([], [], 'r-', label='Current (mA)')
        self.line3, = self.ax3.plot([], [], 'g-', label='Depth (mm)')
        
        # Setup axes
        self.ax1.set_ylabel('Voltage (mV)')
        self.ax1.grid(True)
        self.ax1.legend()
        
        self.ax2.set_ylabel('Current (mA)')
        self.ax2.grid(True)
        self.ax2.legend()
        
        self.ax3.set_ylabel('Depth (mm)')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.grid(True)
        self.ax3.legend()
        # Fixed depth scale from 0 to 1000mm
        self.ax3.set_ylim([0, 1000])
        
    def connect_serial(self):
        """Connect to serial port"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            return False
    
    def read_data(self):
        """Read and parse data from serial port"""
        if not self.ser or not self.ser.is_open:
            return None
            
        try:
            line = self.ser.readline().decode('utf-8').strip()
            if line:
                # Parse the space-separated values: voltage current depth
                parts = line.split()
                if len(parts) >= 3:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    depth = float(parts[2])
                    
                    current_time = time.time() - self.start_time
                    
                    return current_time, voltage, current, depth
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error parsing data: {e}")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            
        return None
    
    def update_plot(self, frame):
        """Update plot with new data"""
        data = self.read_data()
        
        if data:
            current_time, voltage, current, depth = data
            
            # Add new data
            self.times.append(current_time)
            self.voltages.append(voltage)
            self.currents.append(current)
            self.depths.append(depth)
            
            # Update lines
            self.line1.set_data(list(self.times), list(self.voltages))
            self.line2.set_data(list(self.times), list(self.currents))
            self.line3.set_data(list(self.times), list(self.depths))
            
            # Auto-scale axes (except depth which is fixed)
            if len(self.times) > 1:
                time_range = [min(self.times), max(self.times)]
                
                self.ax1.set_xlim(time_range)
                self.ax2.set_xlim(time_range)
                self.ax3.set_xlim(time_range)
                
                if self.voltages:
                    voltage_range = [min(self.voltages) * 0.95, max(self.voltages) * 1.05]
                    self.ax1.set_ylim(voltage_range)
                
                if self.currents:
                    current_range = [min(self.currents) * 0.95, max(self.currents) * 1.05]
                    self.ax2.set_ylim(current_range)
                
                # Depth scale remains fixed at 0-1000mm
                # self.ax3.set_ylim([0, 1000])  # Already set in __init__
            
            # Print latest values
            print(f"Time: {current_time:.1f}s, Voltage: {voltage:.2f}mV, Current: {current:.2f}mA, Depth: {depth:.2f}mm")
        
        return self.line1, self.line2, self.line3
    
    def start_plotting(self):
        """Start the live plotting"""
        if not self.connect_serial():
            return
        
        # Start animation
        ani = animation.FuncAnimation(
            self.fig, self.update_plot, interval=100, blit=False, cache_frame_data=False
        )
        
        try:
            plt.tight_layout()
            plt.show()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("Serial connection closed")

def main():
    parser = argparse.ArgumentParser(description='Live plot serial data from tprobe2.py with fixed depth scale')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('-b', '--baudrate', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('-p', '--points', type=int, default=100, help='Maximum points to display (default: 100)')
    
    args = parser.parse_args()
    
    plotter = SerialPlotter(args.port, args.baudrate, args.points)
    plotter.start_plotting()

if __name__ == "__main__":
    main()