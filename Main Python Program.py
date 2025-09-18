import cv2
import numpy as np

# --- Camera Capture and Perspective Transform (from previous solution) ---

# Step 0: Capture image from camera
camera = cv2.VideoCapture(1) # Use camera index 0 as a default. If camera 1 was specifically requested, use 1.
if not camera.isOpened():
    print("❌ Error: Could not open camera.")
    exit()
ret, image = camera.read()
if not ret:
    print("❌ Error: Could not read frame from camera.")
    exit()
camera.release()
orig_full_frame = image.copy() # Store the original full frame for context if needed later

# Step 1: Use fixed, hardcoded coordinates for the tray
# These are the points you provided: (19, 63), (110, 433), (441, 306), (289, 1)
# The order_points function will sort them into top-left, top-right, bottom-right, bottom-left.
fixed_tray_contour = np.array([(168, 92), (232, 454), (571, 362), (451, 57)], dtype="float32").reshape(4, 1, 2)

# Step 2: Perspective transform
def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum the coordinates to find top-left (smallest sum) and bottom-right (largest sum)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left
    rect[2] = pts[np.argmax(s)]   # bottom-right
    
    # Compute the difference between the coordinates to find top-right (smallest difference)
    # and bottom-left (largest difference)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    
    return rect

rect = order_points(fixed_tray_contour)
(tl, tr, br, bl) = rect

# Compute new width and height based on the maximum dimensions of the transformed rectangle
widthA = np.linalg.norm(br - bl)
widthB = np.linalg.norm(tr - tl)
maxWidth = max(int(widthA), int(widthB))

heightA = np.linalg.norm(tr - br)
heightB = np.linalg.norm(tl - bl)
maxHeight = max(int(heightA), int(heightB))

# Define the destination points for the perspective transform (a perfect rectangle)
dst = np.array([
    [0, 0],
    [maxWidth - 1, 0],
    [maxWidth - 1, maxHeight - 1],
    [0, maxHeight - 1]], dtype="float32")

# Get the perspective transform matrix
M = cv2.getPerspectiveTransform(rect, dst)
# Apply the perspective transform to the original full frame
warped_tray = cv2.warpPerspective(orig_full_frame, M, (maxWidth, maxHeight))

# --- Cloth Detection (applied to the warped_tray) ---

# Convert the warped tray image to HSV color space
hsv = cv2.cvtColor(warped_tray, cv2.COLOR_BGR2HSV)

# Define the color range for cloth detection (these are example values, adjust as needed)
# The provided lower/upper bounds (0, 50, 50) and (179, 255, 255) cover a very broad range,
# essentially detecting most saturated colors. You might want to narrow this for specific cloth colors.
lower_cloth_color = np.array([0, 50, 50])
upper_cloth_color = np.array([179, 255, 255])

# Create a mask to isolate pixels within the defined color range
mask = cv2.inRange(hsv, lower_cloth_color, upper_cloth_color)


# Morphological operations to reduce noise and close gaps
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # Removes small objects (noise)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # Closes small holes inside larger objects

# Find contours in the masked image
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Prepare an output image, which will be the warped tray with detections drawn on it
output_tray_detection = warped_tray.copy()
found_cloth = False

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 500:  # Filter out small contours which are likely noise
        found_cloth = True
        
        # Calculate the centroid (center of mass) of the contour
        M = cv2.moments(cnt)
        if M["m00"] != 0: # Avoid division by zero
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            print(f"Cloth found at centroid (on warped tray): ({cx},{cy})")

            # Draw the contour outline on the output image
            cv2.drawContours(output_tray_detection, [cnt], -1, (0, 255, 0), 2) # Green outline
            
            # Draw a circle at the centroid
            cv2.circle(output_tray_detection, (cx, cy), 5, (0, 0, 255), -1) # Red circle
        else:
            print("Warning: Moment m00 is zero, cannot calculate centroid for a contour.")


if not found_cloth:
    print("No cloth detected within the defined tray area.")

# Save the output image with cloth detections
cv2.imwrite('tray_cloth_detection_output.jpg', output_tray_detection)
print("Detection output on warped tray saved as tray_cloth_detection_output.jpg")
