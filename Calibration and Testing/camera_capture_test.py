import cv2

# Initialize the camera. 0 usually refers to the default camera.
camera = cv2.VideoCapture(1)

# Check if the camera opened successfully
if not camera.isOpened():
    print("❌ Error: Could not open camera.")
    exit()

# Read a single frame from the camera
ret, frame = camera.read()

# Check if the frame was successfully read
if ret:
    # Save the captured frame to a file
    cv2.imwrite("captured_photo.png", frame)
    print("✅ Photo saved as 'captured_photo.png'")
else:
    print("⚠️ Error: Failed to capture a photo.")

# Release the camera and close all windows
camera.release()
cv2.destroyAllWindows()
