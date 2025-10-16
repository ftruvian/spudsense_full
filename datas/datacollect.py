import serial
import csv
import time

SERIAL_PORT = '/dev/ttyACM0'  
BAUD_RATE = 9600
CSV_FILE = 'sensor_data.csv'

def setup_serial():
    try:
        return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException:
        return None

def initialize_csv():
    try:
        with open(CSV_FILE, mode='x', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ambient_temp_C', 'object_temp_C', 'soil_moisture_percent'])
    except FileExistsError:
        pass

def log_data(data):
    try:
        values = data.strip().split(',')
        if len(values) == 3:
            ambient_temp = float(values[0])
            object_temp = float(values[1])
            moisture_percent = float(values[2])
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([ambient_temp, object_temp, moisture_percent])
    except (ValueError, IndexError):
        pass

if __name__ == '__main__':
    initialize_csv()
    ser = setup_serial()
    if ser:
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line and ',' in line:
                    log_data(line)
            except KeyboardInterrupt:
                break
            except Exception:
                pass
    if ser and ser.is_open:
        ser.close()

