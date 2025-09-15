import cv2

# Load your image
image = cv2.imread("Tray_detection_photo.png")

# Mouse callback function
def get_coords(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked coordinates: ({x}, {y})")

cv2.imshow("Click corners", image)
cv2.setMouseCallback("Click corners", get_coords)

cv2.waitKey(0)
cv2.destroyAllWindows()
