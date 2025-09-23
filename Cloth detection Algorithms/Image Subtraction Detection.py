import cv2
import numpy as np

# Open camera
cap = cv2.VideoCapture(1)

# Read the first frame as reference
ret, reference = cap.read()
if not ret:
    print("Failed to capture reference frame.")
    cap.release()
    exit()

reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
reference_gray = cv2.GaussianBlur(reference_gray, (21, 21), 0)

print("Reference frame captured. Starting detection...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Compute absolute difference with reference
    diff = cv2.absdiff(reference_gray, gray)
    _, thresh = cv2.threshold(diff, 30, 200, cv2.THRESH_BINARY)  # higher threshold for noise reduction
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find contours of changes
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Pick the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)

        if area > 500:  # filter out small changes/noise
            # Draw contour outline
            cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)

            # Find centroid
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
                print(f"Centroid: ({cX}, {cY})")

    cv2.imshow("Change Detection", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
