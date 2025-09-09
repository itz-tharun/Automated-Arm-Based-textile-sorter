import cv2
import numpy as np

# Open the camera
cap = cv2.VideoCapture(0)  # 0 = USB camera index

if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Capture one frame
ret, frame = cap.read()
if not ret:
    print("Failed to capture image")
    cap.release()
    exit()

# Convert to grayscale
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Blur slightly to remove noise
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Detect edges
edges = cv2.Canny(blurred, 50, 150)  # thresholds can be tuned

# Find contours from edges
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

output = frame.copy()
found = False

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 500:  # ignore very small edges
        found = True
        cv2.drawContours(output, [cnt], -1, (0, 255, 0), 2)  # green outline

        # Get centroid
        M = cv2.moments(cnt)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            cv2.circle(output, (cx, cy), 5, (0, 0, 255), -1)
            print(f"Cloth edge centroid at: ({cx},{cy})")

if not found:
    print("No cloth detected")

# Save output
cv2.imwrite("cloth_edge_detection.jpg", output)
print("Result saved as cloth_edge_detection.jpg")

cap.release()
