import serial
import csv
import time
import os
from datetime import datetime

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600

VALID_COMMANDS = ['A', 'B', 'C', 'D', 'E'] 

CSV_FILENAME = 'single_sensor_readings.csv'
TIMEOUT_SECONDS = 5
RESET_DELAY = 2 

def initialize_csv():
    """Checks if the CSV file exists and creates it with headers if not."""
    if not os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Log both the command sent and the resulting reading
                writer.writerow(['Timestamp', 'Sensor Command', 'Moisture Reading %'])
            print(f"Created new CSV file: {CSV_FILENAME} with headers.")
        except IOError as e:
            print(f"Error creating CSV file: {e}")

def get_user_command():
    """Prompts the user for a valid sensor command."""
    while True:
        prompt = f"Enter sensor command ({', '.join(VALID_COMMANDS)}): "
        # Read user input, remove whitespace, and convert to uppercase for consistency
        user_input = input(prompt).strip().upper() 
        if user_input in VALID_COMMANDS:
            return user_input
        print(f"Invalid command. Please enter one of: {', '.join(VALID_COMMANDS)}")

def communicate_with_arduino():
    """
    Establishes serial connection, asks the user for a command, 
    sends the command, reads the single response, and logs it.
    """
    # 1. Get the command from the user
    command = get_user_command()
    ser = None
    
    try:
        # 2. Initialize serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT_SECONDS)
        
        # Give Arduino time to reset after opening the serial port
        time.sleep(RESET_DELAY) 
        
        print(f"\nConnected to Arduino on {SERIAL_PORT} at {BAUD_RATE} baud.")
        
        # Map command index to pin number for user feedback (A is index 0 -> Pin 1, B is index 1 -> Pin 2, etc.)
        target_pin = f"A{VALID_COMMANDS.index(command) + 1}"
        
        print(f"-> Requesting data for Command '{command}' (Sensor on Pin {target_pin})...")

        # 3. Send command to Arduino
        # The command must be encoded to bytes before sending, with a newline
        command_bytes = (command + '\n').encode('utf-8')
        ser.write(command_bytes)
        
        # 4. Read the resulting single line of output from the Arduino
        line = ser.readline()
        
        if line:
            # Decode bytes to string and clean up extra whitespace/newlines
            data_str = line.decode('utf-8').strip()
            
            # Attempt to convert to a float
            try:
                moisture_value = float(data_str)
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"<- Received reading for Sensor {command}: {moisture_value}%")
                
                # 5. Put the single collected value into the .csv file
                log_row = [current_time, command, moisture_value]
                with open(CSV_FILENAME, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(log_row)
                
                print(f"\nSuccessfully logged reading to {CSV_FILENAME}.")

            except ValueError:
                print(f"Error: Received data '{data_str}' is not a valid number. Logging skipped.")
            
        else:
            print(f"Error: No data received for command '{command}' within {TIMEOUT_SECONDS} seconds.")

    except serial.SerialException as e:
        print(f"Serial Port Error (Check connection/permissions): {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure the serial port is always closed
        if ser and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    initialize_csv()
    communicate_with_arduino()

