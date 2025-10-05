import serial
import csv
import time

# Configuration
# IMPORTANT: Change 'COM3' to the correct serial port for your Arduino.
# On Windows, it's typically 'COMx' (e.g., 'COM3').
# On macOS/Linux, it's typically '/dev/tty.usbmodemXXXX' or '/dev/ttyACM0'.
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600
CSV_FILE = 'arduino_data2.csv'

def setup_serial_connection():
    """Initializes and returns a serial connection to the Arduino."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # Give the connection a moment to establish
        time.sleep(2)
        print(f"Connected to Arduino on {SERIAL_PORT} at {BAUD_RATE} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. Please check the connection.")
        print(f"Details: {e}")
        return None

def write_to_csv(data, filename):
    """Appends a new row of data to the CSV file."""
    try:
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    except IOError as e:
        print(f"Error: Could not write to file {filename}.")
        print(f"Details: {e}")

def main():
    """Main function to read data and log it."""
    ser = setup_serial_connection()
    if not ser:
        return

    print(f"Logging data to '{CSV_FILE}'. Press Ctrl+C to stop.")

    try:
        while True:
            # Read a line of data from the serial port.
            # The .readline() method will wait until a newline character is received.
            line = ser.readline().decode('utf-8').strip()

            # Check if the line is not empty
            if line:
                # Split the line into individual values, assuming they are comma-separated.
                # Example: "95,25.4,80.1" -> ['95', '25.4', '80.1']
                data_values = line.split(',')

                # Write the list of values to the CSV file.
                write_to_csv(data_values, CSV_FILE)

                # Optional: Print the data to the console for real-time monitoring.
                print(f"Recorded: {line}")

    except KeyboardInterrupt:
        print("\nStopping data logger.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
