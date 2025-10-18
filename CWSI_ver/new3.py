import serial
import csv
import time
import os
from datetime import datetime
from typing import List, Optional

# --- NEW IMPORTS FOR RESOURCE MONITORING ---
try:
    import resource
    import sys
    # Flag to check if the resource module is available
    RESOURCE_AVAILABLE = True
except ImportError:
    # On Windows, resource module is typically not available
    RESOURCE_AVAILABLE = False
# ----------------------------------------


# --- Configuration ---
# NOTE: VERIFY THESE PORTS ARE CORRECT FOR YOUR THREE ARDUINO BOARDS
start = time.time()

MOISTURE_PORT = '/dev/ttyUSB1'  # Port for the Arduino with soil sensors
IR_PORT = '/dev/ttyUSB0'        # Port for the Arduino with IR sensor
PUMP_PORT = '/dev/ttyUSB2'      # Port for the Arduino with pumps/relays
MOTOR_PORT = '/dev/ttyUSB3'     # Port for the Arduino with motor controller
BAUD_RATE = 9600

VALID_COMMANDS = ['A', 'B', 'C', 'D', 'E'] 

CSV_FILENAME = 'dual_sensor_readings.csv'
RESOURCE_LOG_FILENAME = 'script_resource_log.txt' # New log file for resources
TIMEOUT_SECONDS = 5
RESET_DELAY = 2 # Time to wait after opening serial port for Arduino reset

# --- CWSI Configuration (CALIBRATED VALUES) ---
# dT_LL: Non-Water Stressed Baseline (Well-Watered)
CWSI_DT_LL = -2.06
# dT_UL: Upper Limit for Water Stress (Drought)
CWSI_DT_UL = -1.33
# Stress Threshold for Watering (CWSI >= 0.4 means water)
CWSI_WATERING_THRESHOLD = 0.4


def calculate_cwsi(ambient_temp: float, object_temp: float) -> float:
    """
    Computes the Crop Water Stress Index (CWSI) based on the temperature difference.
    CWSI = [(Tc - Ta) - dT_LL] / [dT_UL - dT_LL]
    """
    # Calculate the current temperature differential (dT)
    current_dt = object_temp - ambient_temp
    
    # Calculate the difference in the baselines (denominator)
    baseline_diff = CWSI_DT_UL - CWSI_DT_LL
    
    if baseline_diff <= 0:
        print("CWSI Error: Upper limit (dT_UL) must be greater than lower limit (dT_LL).")
        return -9.99 # Return error code
    
    # Calculate the CWSI value
    cwsi_raw = (current_dt - CWSI_DT_LL) / baseline_diff
    
    # CWSI is typically clamped between 0 and 1
    if cwsi_raw < 0.0:
        return 0.0
    elif cwsi_raw > 1.0:
        return 1.0
    else:
        # Round the result for clean logging
        return round(cwsi_raw, 3) 

def initialize_csv():
    """Checks if the CSV file exists and creates it with updated headers if not."""
    if not os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Timestamp', 
                    'Sensor Command', 
                    'Moisture Reading %', 
                    'Ambient Temperature C', 
                    'Object Temperature C',
                    'CWSI'
                ])
            print(f"Created new CSV file: {CSV_FILENAME} with dual-sensor headers (including CWSI).")
        except IOError as e:
            print(f"Error creating CSV file: {e}")

# ----------------------------------------------------------------------
# --- NEW FUNCTION FOR RESOURCE MONITORING ---
# ----------------------------------------------------------------------
def log_resource_usage(start_time: float):
    """
    Measures and logs the script's CPU time (user/system) and peak memory usage.
    Logs the information to a separate file and prints to console.
    """
    if not RESOURCE_AVAILABLE:
        print("\n--- Resource Monitoring Skipped ---")
        print("   The 'resource' module is not available on this system (e.g., Windows).")
        return

    print("\n=======================================================")
    print("--- Measuring and Logging Resource Consumption ---")
    print("=======================================================")
    
    # 1. Get process usage statistics
    usage = resource.getrusage(resource.RUSAGE_SELF)
    
    # 2. Calculate times
    # user_cpu_time: seconds the process has spent in user mode
    user_cpu_time = usage.ru_utime
    # system_cpu_time: seconds the process has spent in kernel mode
    system_cpu_time = usage.ru_stime
    # total_cpu_time: sum of user and system time
    total_cpu_time = user_cpu_time + system_cpu_time
    # wall_clock_time: total time elapsed since script start (calculated outside this function)
    wall_clock_time = time.time() - start_time
    
    # 3. Get peak memory usage (Maximum Resident Set Size)
    # The unit is system-dependent (usually kilobytes or bytes). 
    # resource.getpagesize() can be used for more robust calculation, 
    # but ru_maxrss is typically in KB on Linux, and B on macOS/BSD. 
    # We'll assume KB for a standard Linux-based environment (common for Arduino projects).
    # Check the platform for better memory unit reporting
    
    # On Linux, ru_maxrss is in KiB (1024 bytes)
    if sys.platform.startswith('linux'):
        peak_memory_kb = usage.ru_maxrss
        peak_memory_mb = peak_memory_kb / 1024.0
    # On macOS/BSD, ru_maxrss is in Bytes
    elif sys.platform == 'darwin' or sys.platform.startswith('freebsd'):
        peak_memory_bytes = usage.ru_maxrss
        peak_memory_mb = peak_memory_bytes / (1024.0 * 1024.0)
    else:
        # Fallback for other Unix-like systems, assuming a reasonable unit
        peak_memory_mb = usage.ru_maxrss / 1024.0 # Default to KB assumption / 1024
        
    # 4. Format the output
    report_lines = [
        f"--- Script Resource Log ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---",
        f"Wall Clock Time:    {wall_clock_time:.3f} seconds",
        f"Total CPU Time:     {total_cpu_time:.3f} seconds",
        f"  (User CPU Time):  {user_cpu_time:.3f} seconds",
        f"  (System CPU Time):{system_cpu_time:.3f} seconds",
        f"Peak Memory Usage:  {peak_memory_mb:.2f} MB",
        "-------------------------------------------------------",
    ]
    
    report = "\n".join(report_lines)
    
    # 5. Print to console
    print(report)
    
    # 6. Log to file
    try:
        with open(RESOURCE_LOG_FILENAME, 'a') as f:
            f.write(report + "\n\n")
        print(f"   Resource usage successfully logged to {RESOURCE_LOG_FILENAME}.")
    except Exception as e:
        print(f"   Error writing resource log file: {e}")
        
# ----------------------------------------------------------------------
# --- END OF NEW FUNCTION ---
# ----------------------------------------------------------------------

def read_serial_data(port: str, baud: int, command: str, expected_parts: int) -> Optional[List[float]]:
    """
    Handles connection, command sending, data reading, parsing, and closing 
    for a single serial device.
    """
    ser = None
    data_str = "N/A"
    
    try:
        # Open serial connection
        ser = serial.Serial(port, baud, timeout=TIMEOUT_SECONDS)
        
        # Give Arduino time to reset
        time.sleep(RESET_DELAY) 
        
        # Send command
        command_bytes = (command + '\n').encode('utf-8')
        ser.write(command_bytes)
        
        # Read response line (only applicable for data boards)
        if expected_parts > 0:
            line = ser.readline()
            
            if not line:
                print(f"Error: No data received from {port} for command '{command}' within {TIMEOUT_SECONDS}s.")
                return None

            # Decode and split the response string
            data_str = line.decode('utf-8').strip()
            data_parts = data_str.split(',')

            if len(data_parts) != expected_parts:
                 print(f"Error: {port} returned {len(data_parts)} part(s) ('{data_str}'), expected {expected_parts}.")
                 return None

            # Convert parts to floats
            float_values = [float(p) for p in data_parts]
            return float_values
        
        return [] # Return empty list if no parts expected (like for pump board)

    except serial.SerialException as e:
        print(f"Serial Port Error on {port} (Check connection/permissions): {e}")
        return None
    except ValueError:
        print(f"Error: Received data from {port} ('{data_str}') is not correctly formatted float(s).")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during serial communication with {port}: {e}")
        return None
    finally:
        # Ensure the serial port is always closed
        if ser and ser.is_open:
            ser.close()

def send_pump_command(port: str, baud: int, command_id: str) -> bool:
    """
    Sends ONLY the command ID (e.g., 'A') to the pump control Arduino 
    to trigger the watering sequence.
    """
    
    pump_command = command_id
    print(f"   Sending pump activation command: {pump_command}")
    
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=TIMEOUT_SECONDS)
        time.sleep(RESET_DELAY) 
        
        # Send the single character command followed by a newline
        command_bytes = (pump_command + '\n').encode('utf-8') 
        ser.write(command_bytes)
        
        # We don't expect a formal response, but we ensure the write completed
        return True
        
    except serial.SerialException as e:
        print(f"Serial Port Error on {port} (Pump board connection/permissions): {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while sending pump command: {e}")
        return False
    finally:
        if ser and ser.is_open:
            ser.close()

def send_motor_command(port: str, baud: int) -> bool:
    """
    Sends the 'M' command to the motor control Arduino to trigger movement.
    """
    #motor_command = 'M' # This variable was implicitly used in the original code's print
    print(f"   Sending motor command: M")
    
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=TIMEOUT_SECONDS)
        time.sleep(RESET_DELAY) 
        
        # Send the 'M' command followed by a newline
        command_bytes = ('M\n').encode('utf-8')
        ser.write(command_bytes)
        
        # Read back confirmation from motor board (optional but helpful for debug)
        line = ser.readline()
        if line:
             print(f"   Motor board response: {line.decode('utf-8').strip()}")

        return True
        
    except serial.SerialException as e:
        print(f"Serial Port Error on {port} (Motor board connection/permissions): {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while sending motor command: {e}")
        return False
    finally:
        if ser and ser.is_open:
            ser.close()


def communicate_with_devices():
    """
    Coordinates reading data from all three Arduinos, calculates CWSI, 
    sends pump trigger command only if stress condition is met, and sends 
    the motor movement command after processing each sensor in alphabetical order (A-E).
    """
    
    # 1. Define the commands to cycle through
    # Cycle through A, B, C, D, E in alphabetical order
    commands_to_run = VALID_COMMANDS
    
    for command in commands_to_run:
        print(f"\n=======================================================")
        print(f"--- Initiating Read and Analysis for Sensor {command} ---")
        print(f"=======================================================")
        
        # --- 2. Read Moisture Data (Expected: 1 value) ---
        print(f"\n--- 1. Reading Soil Moisture Board ({MOISTURE_PORT}) ---")
        moisture_data = read_serial_data(
            port=MOISTURE_PORT, 
            baud=BAUD_RATE, 
            command=command, 
            expected_parts=1
        )
        if moisture_data is None:
            continue # Skip to next command if moisture reading failed

        moisture_value = moisture_data[0]
        print(f"Successfully received Moisture: {moisture_value}%")


        # --- 3. Read IR Temperature Data (Expected: 2 values) ---
        print(f"\n--- 2. Reading IR Temperature Board ({IR_PORT}) ---")
        # Send a dummy command 'T' (for Temperature) to trigger the IR sensor.
        temp_data = read_serial_data(
            port=IR_PORT, 
            baud=BAUD_RATE, 
            command='T', 
            expected_parts=2
        )
        if temp_data is None:
            continue # Skip to next command if temp reading failed
            
        ambient_temp, object_temp = temp_data
        print(f"Successfully received Ambient Temp: {ambient_temp}°C, Object Temp: {object_temp}°C")

        # --- 4. Calculate CWSI and Decide ---
        cwsi_value = calculate_cwsi(ambient_temp, object_temp)
        print(f"\n--- 3. Calculating Stress ---")
        print(f"   Calculated CWSI: {cwsi_value}")


        # --- 5. Conditional Pump Command ---
        print(f"\n--- 4. Checking Watering Need ({PUMP_PORT}) ---")

        if cwsi_value >= CWSI_WATERING_THRESHOLD:
            print(f"   WATERING REQUIRED! CWSI ({cwsi_value}) >= {CWSI_WATERING_THRESHOLD}")
            # Send ONLY the command ID to trigger the timed pump run on Arduino
            send_pump_command(PUMP_PORT, BAUD_RATE, command)
        else:
            print(f"   Plant Healthy. CWSI ({cwsi_value}) < {CWSI_WATERING_THRESHOLD}")
            print("   No command sent to pump board.")


        # --- 6. Log Data ---
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("\n--- 5. Logging Results ---")

        # Order: Timestamp, Command, Moisture, Ambient Temp, Object Temp, CWSI
        log_row = [
            current_time, 
            command, 
            moisture_value, 
            ambient_temp, 
            object_temp, 
            cwsi_value
        ]
        
        try:
            with open(CSV_FILENAME, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(log_row)
            
            print(f"Successfully logged reading and CWSI to {CSV_FILENAME}.")
        except Exception as e:
            print(f"An unexpected error occurred during CSV writing: {e}")
            
        # --- 7. Send Motor Command ---
        # The motor is signaled after all data and decisions have been made for the CURRENT sensor.
        print(f"\n--- 6. Signaling Motor Controller ({MOTOR_PORT}) ---")
        send_motor_command(MOTOR_PORT, BAUD_RATE)
        
        # Add a short delay between sensor checks
        time.sleep(1) # Wait 1 second before moving to the next sensor.

if __name__ == "__main__":
    initialize_csv()
    communicate_with_devices()

# --- CALL THE NEW RESOURCE LOGGING FUNCTION ---
log_resource_usage(start)
# ----------------------------------------------

print("--- %s seconds -----" % (time.time() - start))
