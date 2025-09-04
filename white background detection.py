import cv2
import numpy as np

cap = cv2.VideoCapture(1)  # Your USB camera index

if not cap.isOpened():
    print("Cannot open camera 0")
    exit()

ret, frame = cap.read()
if not ret:
    print("Failed to capture image")
    cap.release()
    exit()

# Convert to HSV
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Threshold for cloth detection (adjust based on your cloth color)
lower = np.array([0, 50, 50])
upper = np.array([179, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

# Morphological operations to reduce noise
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

# Find contours
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

output = frame.copy()
found = False

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 500:  # filter small noise
        found = True
        M = cv2.moments(cnt)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        print(f"Cloth found at centroid: ({cx},{cy})")

        # Draw contour outline (thickness=2)
        cv2.drawContours(output, [cnt], -1, (0, 255, 0), 2)

        # Draw centroid circle
        cv2.circle(output, (cx, cy), 5, (0, 0, 255), -1)

if not found:
    print("No cloth detected")

cv2.imwrite('detection_output_contour.jpg', output) # The Output of the detection is stored as a photo with the name detection_output_contour.jpg
print("Detection output saved as detection_output_contour.jpg")

cap.release()

