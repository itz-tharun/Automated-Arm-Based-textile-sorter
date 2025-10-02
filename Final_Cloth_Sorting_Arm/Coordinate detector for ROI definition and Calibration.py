import cv2
import numpy as np

# A list to store the clicked points.
points = []

# Mouse callback function
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point added: ({x}, {y})")
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow("Camera Feed", frame)

# Set up video capture and window
cap = cv2.VideoCapture(1)
cv2.namedWindow("Camera Feed")
cv2.setMouseCallback("Camera Feed", click_event)

print("Click on the four corners of the tray in this order: top-left, top-right, bottom-right, bottom-left.")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Display the frame and points
    for point in points:
        cv2.circle(frame, point, 5, (0, 255, 0), -1)
        
    cv2.imshow("Camera Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()

# Print the final list of points
if len(points) == 4:
    print("\nFinal points for hardcoding:")
    print(points)
else:
    print("\nDid not capture exactly 4 points. Please try again.")
