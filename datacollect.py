import serial
import csv
from datetime import datetime

# Set these values appropriately
SERIAL_PORT = '/dev/ttyUSB0'  # or '/dev/ttyUSB0' on Linux/Mac
BAUD_RATE = 9600
CSV_FILE = 'sensor_data.csv'

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(['SampleNumber', 'SensorNumber', 'AmbientTemp(C)', 'ObjectTemp(C)', 'SoilMoisture(%)'])

            while True:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        ambient, object_temp, moisture = map(float, line.split(','))
                        timestamp = datetime.now().isoformat()
                        writer.writerow([timestamp, ambient, object_temp, int(moisture)])
                        print(f"{timestamp} | Ambient: {ambient} C | Object: {object_temp} C | Moisture: {moisture}")
                    except ValueError:
                        print(f"Invalid line: {line}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Logging stopped by user.")

if __name__ == '__main__':
    main()

