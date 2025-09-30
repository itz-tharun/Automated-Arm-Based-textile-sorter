import serial
import time
import numpy as np
import cv2

# --- Part 1: Your Calibration Data ---
# These data points map a pixel coordinate to a motor movement time.
# They should be obtained by measuring the arm's travel time to specific points
# in the camera's FULL FIELD OF VIEW.
x_calibration_data = [
    (454, 0),
    (239, 1),
    (330, 1),
    (542, 0)
]

y_calibration_data = [
    (105, 0.7),
    (136, 0.7),
    (435, 4),
    (367, 4)
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

try:
    # Establish serial and camera connection
    print(f"Connecting to Arduino on port {PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(ARDUINO_RESET_DELAY)
    print("Connection established. Starting continuous operation loop...")
    print("Press 'q' at any time to quit the program.")
    
    camera = cv2.VideoCapture(1)
    if not camera.isOpened():
        print("❌ Error: Could not open camera.")
        raise Exception("Camera not found")

    # --- Part 4: Automated White Object Detection and Control Loop ---
    # Define the 4 points of the tray on the camera image
    fixed_tray_contour = np.array([
        (456, 106), (240, 137), (331, 436), (543, 368)
    ], dtype="float32")
    
    def order_points(pts):
        pts = pts.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    while True:
        try:
            print("\n--- Starting new detection cycle ---")
            
            ret, frame = camera.read()
            if not ret:
                print("❌ Error: Could not read frame. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Get the perspective transform matrix and warp the image
            rect = order_points(fixed_tray_contour)
            (tl, tr, br, bl) = rect
            widthA = np.linalg.norm(br - bl)
            widthB = np.linalg.norm(tr - tl)
            maxWidth = max(int(widthA), int(widthB))
            heightA = np.linalg.norm(tr - br)
            heightB = np.linalg.norm(tl - bl)
            maxHeight = max(int(heightA), int(heightB))
            dst = np.array([
                [0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]
            ], dtype="float32")
            M = cv2.getPerspectiveTransform(rect, dst)
            warped_tray = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))

            # Convert to HSV to better detect white colors
            hsv = cv2.cvtColor(warped_tray, cv2.COLOR_BGR2HSV)

            # Define a broad range for cloth color
            lower_cloth_color = np.array([0, 50, 50])
            upper_cloth_color = np.array([179, 255, 255])

            # Create a mask and apply morphological operations
            mask = cv2.inRange(hsv, lower_cloth_color, upper_cloth_color)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find the largest contour within the warped ROI
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            found_white_object = False
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 500:
                    found_white_object = True
                    M_contour = cv2.moments(largest_contour)
                    if M_contour["m00"] != 0:
                        # Centroid is relative to the warped image
                        cx_warped = int(M_contour['m10'] / M_contour['m00'])
                        cy_warped = int(M_contour['m01'] / M_contour['m00'])
                        
                        # Invert the perspective transform to get the centroid's original FOV coordinates
                        Minv = cv2.getPerspectiveTransform(dst, rect)
                        centroid_warped = np.array([[cx_warped, cy_warped]], dtype='float32')
                        centroid_fov = cv2.perspectiveTransform(centroid_warped.reshape(-1, 1, 2), Minv)
                        cx_fov = int(centroid_fov[0][0][0])
                        cy_fov = int(centroid_fov[0][0][1])

                        # Draw the outline on the original frame using the transformed contour
                        largest_contour_fov = cv2.perspectiveTransform(largest_contour.astype(np.float32), Minv)
                        cv2.drawContours(frame, [np.int32(largest_contour_fov)], -1, (0, 255, 0), 2)
                        cv2.circle(frame, (cx_fov, cy_fov), 5, (0, 0, 255), -1)
                        
                        print(f"✅ White object detected at centroid (in full FOV): ({cx_fov}, {cy_fov})")
                    else:
                        found_white_object = False
            
            if not found_white_object:
                print("⚠️ No white object detected. Scanning again in 10 seconds...")
                time.sleep(10)
                continue

            # --- Part 5: Calculate and Execute Movements ---
            x_to_object_time = (x_slope * cx_fov) + x_intercept
            y_to_object_time = (y_slope * cy_fov) + y_intercept
            x_to_object_time = max(0, x_to_object_time)
            y_to_object_time = max(0, y_to_object_time)

            print("\nStarting pick-and-place cycle.")
            
            # === STEP A: MOVE TO WHITE OBJECT ===
            print("--- Step 1: Moving to object location ---")
            send_command(ser, f"X F {x_to_object_time:.2f}")
            send_command(ser, f"Y F {y_to_object_time:.2f}")
            
            # === STEP B: PICK UP OBJECT ===
            print("--- Step 2: Picking up the object ---")
            send_command(ser, "Z D 3.0")
            send_command(ser, "C C")
            send_command(ser, "Z U 4.3")
            
            # === STEP C: MOVE TO BIN ===
            print("--- Step 3: Moving to drop-off bin (home position) ---")
            send_command(ser, f"X R {x_to_object_time:.2f}")
            send_command(ser, f"Y R {y_to_object_time:.2f}")

            # === STEP D: DROP OFF OBJECT ===
            print("--- Step 4: Dropping off the object ---")
            send_command(ser, "C O")
            
            print("\n✅ Cycle complete! Ready for next object...")
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
                # If reconnection fails, we let the loop continue and try again on the next iteration.
        
        # Check for 'q' key press to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting program as requested...")
            break

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
