import numpy as np
from picamera2 import Picamera2
from libcamera import controls 
from PIL import Image
import csv
import sys
import os
import time # Added for initialization delay

# --- Configuration ---
IMAGE_SIZE = (100, 100) # Width, Height for the main output
OUTPUT_FILENAME = 'image_raster_data.csv'

def setup_camera():
    """
    Initializes and configures the Picamera2 instance.
    
    Returns:
        Picamera2: The initialized camera object, or None if setup fails.
    """
    try:
        print("Initializing Raspberry Pi Camera (Picamera2)...")
        # ----------------------------------------------------------------------
        # NOTE: If this part fails with "list index out of range", it means the 
        # RPi OS did not detect a camera. Check the cable connection and run:
        # libcamera-still -t 1  (in a terminal) to verify detection.
        # ----------------------------------------------------------------------
        picam2 = Picamera2()
        
        # Create a configuration for a raw RGB image capture at 100x100 resolution
        config = picam2.create_still_configuration(
            main={"size": IMAGE_SIZE, "format": "RGB888"} # 100x100 in RGB
        )
        picam2.configure(config)
        
        # Removed picam2.set_controls for maximum compatibility, as the focus setting
        # can sometimes cause issues on modules that don't strictly support it.
        
        # Start the camera stream
        picam2.start()
        
        # Add a short delay to allow the sensor to warm up/stabilize
        time.sleep(0.5)
        
        print(f"-> Camera started. Resolution set to {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]}.")
        return picam2
    except Exception as e:
        print(f"ERROR: Failed to initialize Picamera2: {e}")
        print("Please ensure the camera module is connected and the picamera2 library is installed.")
        return None

def capture_image(picam2):
    """
    Captures a 100x100 RGB image array from the running camera stream.
    
    Args:
        picam2 (Picamera2): The initialized and running camera object.

    Returns:
        numpy.ndarray: The captured 3D NumPy array (height, width, 3), or None on error.
    """
    try:
        # picamera2.capture_array returns a NumPy array with the configured format
        image_array = picam2.capture_array("main")
        
        # Check shape to confirm it's 100x100x3
        if image_array.shape != (IMAGE_SIZE[1], IMAGE_SIZE[0], 3):
            print(f"Warning: Captured array shape {image_array.shape} does not match expected (100, 100, 3).")
            # Attempt to resize the array for safety if necessary, but this shouldn't happen
            # with the correct configuration.
        
        print(f"-> Image captured. Array shape: {image_array.shape}")
        
        # Optionally save a temporary PNG to verify the captured image
        temp_img = Image.fromarray(image_array)
        temp_img.save("last_capture_preview.png")
        print("-> Saved 'last_capture_preview.png' for verification.")
        
        return image_array
    
    except Exception as e:
        print(f"ERROR during image capture: {e}")
        return None

def array_to_csv(image_array, filename):
    """
    Converts a 3D NumPy array (H, W, 3) into a CSV file containing 
    Row, Col, R, G, B values for every pixel.
    
    Args:
        image_array (numpy.ndarray): The captured image data.
        filename (str): The name of the CSV file to write to.
    """
    if image_array is None or image_array.size == 0:
        print("Error: No image array provided or array is empty.")
        return

    height, width, channels = image_array.shape
    if channels != 3:
        print(f"Error: Expected 3 color channels (RGB), found {channels}. Cannot proceed with CSV generation.")
        return

    print(f"\n--- Starting CSV conversion ({height*width} pixels) ---")

    try:
        # 'w' mode for writing, 'newline'='' to prevent extra blank rows in Windows
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write the header row
            header = ['Index', 'Row', 'Col', 'R', 'G', 'B']
            csv_writer.writerow(header)
            
            pixel_index = 0
            # Iterate through each pixel in the array
            for r in range(height):
                for c in range(width):
                    # Get the RGB values for the current pixel
                    # Indexing is [row, column, channel]
                    R, G, B = image_array[r, c] 
                    
                    # Write the data row: Index, Row, Col, R, G, B
                    # Convert values to standard Python integers for CSV writing
                    row_data = [pixel_index, r, c, int(R), int(G), int(B)]
                    csv_writer.writerow(row_data)
                    
                    pixel_index += 1
        
        # Confirmation message
        print(f"--- Successfully wrote {pixel_index} pixels to '{os.path.abspath(filename)}' ---")
        
    except Exception as e:
        print(f"An error occurred during file writing: {e}")

def main():
    """
    Main loop to handle camera setup, user input, capture, and cleanup.
    """
    print("=" * 45)
    print(f"Raspberry Pi Camera Raster Data Logger (100x100)")
    print("=" * 45)
    
    # 1. Setup Camera
    picam2 = setup_camera()
    if picam2 is None:
        return # Exit if camera setup failed

    print("\n--- Awaiting Input ---")
    print("Type 'y' and press Enter to capture the image and save data.")
    print("Type 'q' and press Enter to quit and stop the camera.")
    print("-" * 45)

    try:
        # 2. Main Capture Loop
        while True:
            user_input = input("Waiting for capture input (y/q): ").strip().lower()
            
            if user_input == 'q':
                break
            
            elif user_input == 'y':
                print("\n[CAPTURE INITIATED]")
                
                # Capture the Image
                image_data = capture_image(picam2)
                
                # Convert and Store to CSV
                if image_data is not None:
                    array_to_csv(image_data, OUTPUT_FILENAME)
                
                print("\n[Capture and Save Complete. Waiting for next input.]")
                print("-" * 45)
            
            else:
                print("Invalid input. Please type 'y' to capture or 'q' to quit.")
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    
    finally:
        # 3. Cleanup
        print("\nStopping camera stream and exiting.")
        if picam2:
            picam2.stop()

if __name__ == '__main__':
    main()
