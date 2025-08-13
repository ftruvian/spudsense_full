import serial
import time
import csv
from datetime import datetime

# Replace with your Arduino's serial port
SERIAL_PORT = '/dev/ttyUSB0'  # Linux
# SERIAL_PORT = 'COM3'        # Windows
BAUD_RATE = 115200
CSV_FILE = 'temperature_log.csv'

try:
    # Open serial connection
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # Wait for Arduino to reset

    # Open CSV file and write header if needed
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write header only if file is empty
        if file.tell() == 0:
            writer.writerow(['Timestamp', 'Ambient Temp (°C)', 'Object Temp (°C)'])

        print("Logging data to", CSV_FILE)
        
        while True:
            line = ser.readline().decode().strip()
            if line:
                try:
                    ambient, object_temp = map(float, line.split(','))
                    timestamp = datetime.now().isoformat()
                    writer.writerow([timestamp, ambient, object_temp])
                    file.flush()  # Ensure it's written immediately

                    print(f"[{timestamp}] Ambient: {ambient:.2f} °C | Object: {object_temp:.2f} °C")
                except ValueError:
                    print(f"Malformed line: {line}")

except serial.SerialException as e:
    print(f"Serial connection error: {e}")

