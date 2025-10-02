import serial
import time
import numpy as np
import cv2
import sys

# --- Part 1: Your Calibration Data ---
# These data points map a pixel coordinate to a motor movement time.
x_calibration_data = [
    (367, 0),
    (230, 1.2),
    (260, 1.2),
    (415, 0)
]

y_calibration_data = [
    (106, 0.4),
    (121, 0.4),
    (416, 4.2),
    (377, 4.2)
]

# --- Part 2: Automatic Calibration ---
x_pixels = np.array([p[0] for p in x_calibration_data])
x_times = np.array([p[1] for p in x_calibration_data])
x_slope, x_intercept = np.polyfit(x_pixels, x_times, 1)

y_pixels = np.array([p[0] for p in y_calibration_data])
y_times = np.array([p[1] for p in y_calibration_data])
y_slope, y_intercept = np.polyfit(y_pixels, y_times, 1)

print("✅ Calibration complete. Your linear model is:")
print(f"X_time = {x_slope:.4f} * x_pixel + {x_intercept:.4f}")
print(f"Y_time = {y_slope:.4f} * y_pixel + {y_intercept:.4f}")
print("-" * 40)

# --- Part 3: Serial Communication Setup ---
PORT = 'COM7'
BAUD_RATE = 9600
ARDUINO_RESET_DELAY = 2

def send_command(ser, command):
    """Sends a command to the Arduino and waits for a brief period."""
    print(f"Sending command: {command}")
    ser.write(f"{command}\n".encode())
    time.sleep(0.5)

# --- Part 4: Automated Image Subtraction Logic ---
# These constants and the tray contour are from the second script you provided.
THRESHOLD_VALUE = 50
MIN_CONTOUR_AREA = 225
DILATION_ITERATIONS = 5

# Define the 4 points of the tray on the camera image
fixed_tray_contour = np.array([
    (374, 122), (238, 133), (267, 428), (426, 394)
], dtype="int32")

def apply_tray_mask(image, contour):
    """Mask out everything except the tray region."""
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.fillPoly(mask, [contour], 255)
    return cv2.bitwise_and(image, image, mask=mask)

def perform_pick_and_place(ser, camera, reference_image):
    """Performs a single pick-and-place cycle using image subtraction."""
    print("\n--- Starting new detection cycle ---")
    
    ret, live_image = camera.read()
    if not ret:
        print("❌ Error: Could not read frame.")
        return False
    
    # Apply tray mask and convert to grayscale for comparison
    ref_gray = cv2.cvtColor(apply_tray_mask(reference_image, fixed_tray_contour), cv2.COLOR_BGR2GRAY)
    live_gray = cv2.cvtColor(apply_tray_mask(live_image, fixed_tray_contour), cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference
    diff = cv2.absdiff(ref_gray, live_gray)
    _, thresh = cv2.threshold(diff, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=DILATION_ITERATIONS)

    # Find contours of changes
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found_object = False
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > MIN_CONTOUR_AREA:
            found_object = True
            M_contour = cv2.moments(largest_contour)
            if M_contour["m00"] != 0:
                cx = int(M_contour['m10'] / M_contour['m00'])
                cy = int(M_contour['m01'] / M_contour['m00'])
                
                print(f"✅ Object detected at centroid: ({cx}, {cy})")
                
                # Draw the detected object and centroid for visualization
                display_frame = live_image.copy()
                cv2.polylines(display_frame, [fixed_tray_contour], True, (255, 0, 0), 2)
                cv2.drawContours(display_frame, [largest_contour], -1, (0, 255, 0), 2)
                cv2.circle(display_frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.imshow("Detection Result", display_frame)
                cv2.waitKey(1)
            else:
                found_object = False

    if not found_object:
        print("⚠️ No object detected.")
        return False

    # Calculate and Execute Movements
    x_to_object_time = (x_slope * cx) + x_intercept
    y_to_object_time = (y_slope * cy) + y_intercept
    x_to_object_time = max(0, x_to_object_time)
    y_to_object_time = max(0, y_to_object_time)

    print("\nStarting pick-and-place cycle.")
    
    # === STEP A: MOVE TO OBJECT ===
    print("--- Step 1: Moving to object location ---")
    send_command(ser, f"XY F {x_to_object_time:.2f} {y_to_object_time:.2f}")
    
    # === STEP B: PICK UP OBJECT ===
    print("--- Step 2: Picking up the object ---")
    send_command(ser, "Z D 2.3")
    send_command(ser, "C C")
    send_command(ser, "Z U 3.1")
    
    # === STEP C: MOVE TO BIN ===
    print("--- Step 3: Moving to drop-off bin (home position) ---")
    send_command(ser, f"XY R {x_to_object_time:.2f} {y_to_object_time:.2f}")

    # === STEP D: DROP OFF OBJECT ===
    print("--- Step 4: Dropping off the object ---")
    send_command(ser, "C O")
    
    print("\n✅ Cycle complete!")
    return True

def run_manual_mode(ser):
    """Allows manual control of the robot arm via the console."""
    print("Manual control mode activated. Enter commands (e.g., 'X F 1.0').")
    print("Type 'q' to return to the main menu.")
    while True:
        command = input("Enter command: ").strip()
        if command.lower() == 'q':
            print("Returning to main menu.")
            break
        if command:
            try:
                send_command(ser, command)
            except serial.SerialException as e:
                print(f"❌ Serial communication error: {e}. Check the connection.")
                break

def run_one_time_mode(ser, camera, reference_image):
    """Runs a single automatic pick-and-place cycle."""
    perform_pick_and_place(ser, camera, reference_image)
    print("One-time cycle complete. Returning to main menu.")

def run_continuous_mode(ser, camera, reference_image):
    """Runs automatic pick-and-place cycles continuously."""
    print("Continuous automatic mode activated.")
    print("Press 'q' at any time to quit the program.")
    while True:
        try:
            if perform_pick_and_place(ser, camera, reference_image):
                print("Cycle complete. Waiting 10 seconds before next scan...")
                time.sleep(10)
            else:
                print("No object found. Scanning again in 10 seconds...")
                time.sleep(10)

        except serial.SerialException as e:
            print(f"❌ Serial communication error: {e}. Attempting to reconnect...")
            if ser.is_open:
                ser.close()
            time.sleep(2)
            try:
                ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
                time.sleep(ARDUINO_RESET_DELAY)
                print("✅ Reconnected to Arduino.")
            except serial.SerialException:
                print("❌ Failed to reconnect. Check the physical connection and try again.")
                return # Exit this mode
        
        # Check for 'q' key press to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting program as requested...")
            sys.exit()

# Main program loop
try:
    print(f"Connecting to Arduino on port {PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(ARDUINO_RESET_DELAY)
    print("Connection established. Please wait for camera initialization...")
    
    camera = cv2.VideoCapture(1)
    if not camera.isOpened():
        print("❌ Error: Could not open camera.")
        raise Exception("Camera not found")
    print("Camera initialized.")
    
    # --- NEW: Capture the reference image of the empty tray ---
    print("\n--- Initial Setup ---")
    print("Please ensure the tray is EMPTY and clear of any objects.")
    input("Press Enter to capture the reference image...")
    
    ret, reference_image = camera.read()
    if not ret:
        print("❌ Error: Failed to capture reference image.")
        raise Exception("Reference image capture failed")
    cv2.imshow("Reference Image Captured", reference_image)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()
    print("✅ Reference image of the empty tray captured successfully!")
    
    while True:
        print("\n--- Main Menu ---")
        print("1. Manual Control")
        print("2. Automatic One-Time Cycle")
        print("3. Automatic Continuous Cycle")
        print("Q. Quit")
        
        choice = input("Enter your choice: ").strip().lower()
        
        if choice == '1':
            run_manual_mode(ser)
        elif choice == '2':
            run_one_time_mode(ser, camera, reference_image)
        elif choice == '3':
            run_continuous_mode(ser, camera, reference_image)
        elif choice == 'q':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or Q.")

except serial.SerialException as e:
    print(f"❌ Could not open serial port '{PORT}'. Check the connection and port name.")
    print(f"Error: {e}")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
    if 'camera' in locals() and camera.isOpened():
        camera.release()
        print("Camera released.")
    cv2.destroyAllWindows()
