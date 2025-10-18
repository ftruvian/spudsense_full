import serial
import csv
import time
import os
from datetime import datetime
from typing import List, Optional, Tuple

# --- Machine Learning and Image Processing Imports ---
# NumPy is essential for both image analysis and ML prediction arrays.
import numpy as np
# joblib is required for loading the pre-trained models
import joblib 

# --- Picamera2 Imports (Optional/Hardware Specific) ---
try:
    from picamera2 import Picamera2
except ImportError:
    print("WARNING: Picamera2 not found. RGB functions will return (0, 0, 0).")
    print("On RPi, ensure you run: pip install picamera2 numpy joblib")
    
# --- System Monitoring Import ---
try:
    import psutil
except ImportError:
    print("WARNING: psutil not found. Resource monitoring disabled. Run: pip install psutil")

# --- Configuration ---
# NOTE: VERIFY THESE PORTS ARE CORRECT FOR YOUR THREE ARDUINO BOARDS
MOISTURE_PORT = '/dev/ttyUSB1'  # Port for the Arduino with soil sensors
IR_PORT = '/dev/ttyUSB0'        # Port for the Arduino with IR sensor
PUMP_PORT = '/dev/ttyUSB2'      # Port for the Arduino with pumps/relays
MOTOR_PORT = '/dev/ttyUSB3'     # Port for the Arduino with motor controller
BAUD_RATE = 9600

VALID_COMMANDS = ['A', 'B', 'C', 'D', 'E'] 

CSV_FILENAME = 'dual_sensor_readings.csv'
TIMEOUT_SECONDS = 5
RESET_DELAY = 2 # Time to wait after opening serial port for Arduino reset

# --- ML Model Configuration ---
# Set the desired model. Options: 'SVR_RBF', 'LINEAR_REGRESSION', 'RIDGE_REGRESSION'
MODEL_CHOICE = 'RIDGE_REGRESSION' 
# The CWSI value (0.0 to 1.0) above which watering is triggered.
CWSI_WATERING_THRESHOLD = 0.4

# Define all model file paths
SVR_SCALER_PATH = 'svr_rbf_scaler.joblib'
SVR_MODEL_PATH = 'svr_rbf_model.joblib'
LINEAR_SCALER_PATH = 'linear_regression_s/caler.joblib'
LINEAR_MODEL_PATH = 'linear_regression_model.joblib'
RIDGE_SCALER_PATH = 'ridge_linear_regression_scaler.joblib'
RIDGE_MODEL_PATH = 'ridge_linear_regression_model.joblib'


# --- Global Model and Scaler Variables ---
# These will be loaded once at the start of the script.
ML_SCALER = None
ML_MODEL = None


def load_ml_models():
    """Loads the pre-trained ML scaler and model based on MODEL_CHOICE."""
    global ML_SCALER, ML_MODEL
    
    if MODEL_CHOICE == 'SVR_RBF':
        scaler_path = SVR_SCALER_PATH
        model_path = SVR_MODEL_PATH
    elif MODEL_CHOICE == 'LINEAR_REGRESSION':
        scaler_path = LINEAR_SCALER_PATH
        model_path = LINEAR_MODEL_PATH
    elif MODEL_CHOICE == 'RIDGE_REGRESSION':
        scaler_path = RIDGE_SCALER_PATH
        model_path = RIDGE_MODEL_PATH
    else:
        print(f"FATAL ERROR: Invalid MODEL_CHOICE: {MODEL_CHOICE}. Must be 'SVR_RBF', 'LINEAR_REGRESSION', or 'RIDGE_REGRESSION'.")
        return

    try:
        print(f"--- Loading {MODEL_CHOICE} Model Set ---")
        print(f"Loading Scaler from: {scaler_path}")
        ML_SCALER = joblib.load(scaler_path)
        print(f"Loading Model from: {model_path}")
        ML_MODEL = joblib.load(model_path)
        print(f"{MODEL_CHOICE} models loaded successfully.")
    except Exception as e:
        print(f"FATAL ERROR: Could not load {MODEL_CHOICE} models or scaler. Ensure files exist. Error: {e}")
        # Setting them to None so the prediction function knows they failed to load
        ML_SCALER = None
        ML_MODEL = None

def predict_cwsi(moisture: float, ambient_temp: float, object_temp: float, r_value: int, g_value: int, b_value: int) -> float:
    """
    Predicts the CWSI using the loaded ML model after scaling the input features.
    The required features for the model are assumed to be: 
    [R_value, G_value, B_value, Ambient_Temp, Object_Temp].
    """
    # The 'np' used here is the globally imported numpy.
    if ML_SCALER is None or ML_MODEL is None:
        print("[ML PREDICTION ERROR] Model or Scaler not loaded. Returning CWSI 9.99.")
        return 9.99

    try:
        # The model is trained on 5 features in this order: 
        # [R, G, B, Ambient_Temp, Object_Temp]
        feature_data = np.array([[r_value, g_value, b_value, ambient_temp, object_temp]])

        # 1. Scale the input data
        scaled_data = ML_SCALER.transform(feature_data)
        
        # 2. Predict the CWSI
        predicted_cwsi_array = ML_MODEL.predict(scaled_data)
        predicted_cwsi = predicted_cwsi_array[0]
        
        # Ensure CWSI is clamped between 0 and 1, then round
        if predicted_cwsi < 0.0:
            predicted_cwsi = 0.0
        elif predicted_cwsi > 1.0:
            predicted_cwsi = 1.0
            
        return round(predicted_cwsi, 3)

    except Exception as e:
        print(f"[ML PREDICTION ERROR] Failed during scaling or prediction: {e}")
        return 9.99

def capture_and_analyze_rgb() -> Tuple[int, int, int]:
    """
    Captures a small image using Picamera2 and returns the average R, G, B values.
    Returns (0, 0, 0) on failure or if libraries are missing.
    """
    try:
        # Check if the necessary library is available
        if 'Picamera2' not in globals():
            return 0, 0, 0
            
        picam2 = Picamera2()
        
        # Configure for a fast, low-resolution capture (e.g., 32x32)
        config = picam2.create_still_configuration(main={"size": (32, 32)})
        picam2.configure(config)
        picam2.start()
        
        # Give sensor time to settle (adjust as needed)
        time.sleep(1) 
        
        # Capture image data as a NumPy array (RGB format)
        # np.mean is available here because numpy is imported globally
        array = picam2.capture_array()
        picam2.stop()
        
        # Calculate the average RGB value across the whole small image
        avg_r = int(np.mean(array[..., 0]))
        avg_g = int(np.mean(array[..., 1]))
        avg_b = int(np.mean(array[..., 2]))
        
        print(f"   [CAMERA] Captured Avg RGB: ({avg_r}, {avg_g}, {avg_b})")
        return (avg_r, avg_g, avg_b)
        
    except NameError:
        # This occurs if Picamera2 is not imported
        return (0, 0, 0)
    except Exception as e:
        print(f"[CAMERA ERROR] Could not capture image or process data: {e}")
        return (0, 0, 0) # Return black on error

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
                    'Predicted CWSI', # New/Reintroduced column
                    'Red Value',
                    'Green Value',
                    'Blue Value'
                ])
            print(f"Created new CSV file: {CSV_FILENAME} with CWSI prediction headers.")
        except IOError as e:
            print(f"Error creating CSV file: {e}")

def read_serial_data(port: str, baud: int, command: str, expected_parts: int) -> Optional[List[float]]:
    """
    Handles connection, command sending, data reading, parsing, and closing 
    for a single serial device.
    """
    ser = None
    data_str = "N/A"
    
    try:
        ser = serial.Serial(port, baud, timeout=TIMEOUT_SECONDS)
        time.sleep(RESET_DELAY) 
        
        command_bytes = (command + '\n').encode('utf-8')
        ser.write(command_bytes)
        
        if expected_parts > 0:
            line = ser.readline()
            
            if not line:
                print(f"Error: No data received from {port} for command '{command}' within {TIMEOUT_SECONDS}s.")
                return None

            data_str = line.decode('utf-8').strip()
            data_parts = data_str.split(',')

            if len(data_parts) != expected_parts:
                 print(f"Error: {port} returned {len(data_parts)} part(s) ('{data_str}'), expected {expected_parts}.")
                 return None

            float_values = [float(p) for p in data_parts]
            return float_values
        
        return []

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
        
        command_bytes = (pump_command + '\n').encode('utf-8') 
        ser.write(command_bytes)
        
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
    motor_command = 'M'
    print(f"   Sending motor command: {motor_command}")
    
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=TIMEOUT_SECONDS)
        time.sleep(RESET_DELAY) 
        
        command_bytes = (motor_command + '\n').encode('utf-8')
        ser.write(command_bytes)
        
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
    Automates the full data acquisition, CWSI prediction, 
    logging, and control cycle for all five sensors (A-E) in alphabetical order.
    """
    
    commands_to_run = VALID_COMMANDS
    
    for command in commands_to_run:
        print(f"\n=======================================================")
        print(f"--- Initiating Read and Analysis for Sensor {command} ---")
        print(f"=======================================================")
        
        # --- 1. Read Moisture Data (Expected: 1 value) ---
        print(f"\n--- 1. Reading Soil Moisture Board ({MOISTURE_PORT}) ---")
        moisture_data = read_serial_data(
            port=MOISTURE_PORT, 
            baud=BAUD_RATE, 
            command=command, 
            expected_parts=1
        )
        if moisture_data is None:
            continue

        moisture_value = moisture_data[0]
        print(f"Successfully received Moisture: {moisture_value}%")


        # --- 2. Read IR Temperature Data (Expected: 2 values) ---
        print(f"\n--- 2. Reading IR Temperature Board ({IR_PORT}) ---")
        temp_data = read_serial_data(
            port=IR_PORT, 
            baud=BAUD_RATE, 
            command='T', 
            expected_parts=2
        )
        if temp_data is None:
            continue
            
        ambient_temp, object_temp = temp_data
        print(f"Successfully received Ambient Temp: {ambient_temp}°C, Object Temp: {object_temp}°C")
        
        
        # --- 3. Capture and Analyze RGB Data ---
        print(f"\n--- 3. Capturing Visual Data (Picamera2) ---")
        r_value, g_value, b_value = capture_and_analyze_rgb()

        
        # --- 4. Predict CWSI and Decide ---
        predicted_cwsi = predict_cwsi(moisture_value, ambient_temp, object_temp, r_value, g_value, b_value)
        print(f"\n--- 4. Predicting Stress (ML Model: {MODEL_CHOICE}) ---")
        
        if predicted_cwsi >= 0.0 and predicted_cwsi <= 1.0:
            print(f"   Predicted CWSI: {predicted_cwsi}")
        else:
            # This handles the case where the ML model fails to load or predict
            print(f"   [WARNING] ML Prediction Failed (Code: {predicted_cwsi}). Skipping watering decision.")
            
            # --- 6. Send Motor Command (Still move motor even if prediction fails) ---
            print(f"\n--- 6. Signaling Motor Controller ({MOTOR_PORT}) ---")
            send_motor_command(MOTOR_PORT, BAUD_RATE)
            time.sleep(1)
            continue


        # --- 5. Conditional Pump Command (CWSI-BASED DECISION) ---
        print(f"\n--- 5. Checking Watering Need ({PUMP_PORT}) ---")

        if predicted_cwsi >= CWSI_WATERING_THRESHOLD:
            print(f"   WATERING REQUIRED! Predicted CWSI ({predicted_cwsi}) >= {CWSI_WATERING_THRESHOLD}")
            send_pump_command(PUMP_PORT, BAUD_RATE, command)
        else:
            print(f"   Plant Healthy. Predicted CWSI ({predicted_cwsi}) < {CWSI_WATERING_THRESHOLD}")
            print("   No command sent to pump board.")


        # --- 6. Log Data ---
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n--- 6. Logging Results ---")

        # Order: Timestamp, Command, Moisture, Ambient Temp, Object Temp, Predicted CWSI, R, G, B
        log_row = [
            current_time, 
            command, 
            moisture_value, 
            ambient_temp, 
            object_temp, 
            predicted_cwsi,
            r_value,
            g_value,
            b_value
        ]
        
        try:
            with open(CSV_FILENAME, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(log_row)
            
            print(f"Successfully logged all data points to {CSV_FILENAME}.")
        except Exception as e:
            print(f"An unexpected error occurred during CSV writing: {e}")
            
        # --- 7. Send Motor Command ---
        # The motor is signaled after all data and decisions have been made for the CURRENT sensor.
        print(f"\n--- 7. Signaling Motor Controller ({MOTOR_PORT}) ---")
        send_motor_command(MOTOR_PORT, BAUD_RATE)
        
        # Add a short delay between sensor checks
        time.sleep(1) 

def report_system_resources(start_time: float, end_time: float, process):
    """Calculates and prints the average system resource consumption for the current script using psutil."""
    # Check if psutil was successfully imported (globally)
    if 'psutil' not in globals() or not process:
        print("\nSystem resource report skipped (psutil not available or process not initialized).")
        return

    try:
        # CPU usage percentage specific to this process since the last call
        avg_cpu = process.cpu_percent(interval=None)

        # Memory usage specific to this process
        mem = process.memory_info()
        total_time = round(end_time - start_time, 2)
        
        # Convert bytes to MB for process memory report
        # RSS (Resident Set Size) is the physical memory used by the process
        mem_used_mb = mem.rss / (1024**2) 

        print("\n=======================================================")
        print("--- SCRIPT RESOURCE REPORT ---")
        print(f"Total Execution Time: {total_time} seconds")
        print(f"Average CPU Usage (Script only): {avg_cpu:.1f}%")
        print("--- Memory Usage (Script only, at end) ---")
        print(f"Physical Memory Used (RSS): {mem_used_mb:.2f} MB")
        print("=======================================================")

    except Exception as e:
        print(f"\n[RESOURCE REPORT ERROR] Failed to generate script-only report: {e}")

if __name__ == "__main__":
    # Load models before starting communication loop
    load_ml_models()
    initialize_csv()
    
    # --- Resource Monitoring Setup ---
    start_time = time.time()
    cpu_monitor_ready = False
    process = None # Variable to hold the process object
    
    # Check if psutil is available before attempting to use it
    if 'psutil' in globals():
        try:
            # Get the current process object for script-specific metrics
            process = psutil.Process(os.getpid())
            # Call once to zero out the counter for the subsequent call
            process.cpu_percent(interval=None)
            cpu_monitor_ready = True 
        except Exception as e:
            print(f"Error initializing psutil Process: {e}")
            cpu_monitor_ready = False

    # --- Main Execution ---
    if ML_MODEL is not None and ML_SCALER is not None:
        communicate_with_devices()
    else:
        print("\nScript terminated because ML models failed to load.")

    # --- Resource Monitoring Report ---
    end_time = time.time()
    if cpu_monitor_ready and process:
        report_system_resources(start_time, end_time, process)
    else:
        print("\nSystem resource report skipped (psutil not available or setup failed).")

