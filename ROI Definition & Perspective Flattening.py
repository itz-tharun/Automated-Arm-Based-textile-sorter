import cv2
import numpy as np

# Step 0: Capture image from camera
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("❌ Error: Could not open camera.")
    exit()
ret, image = camera.read()
if not ret:
    print("❌ Error: Could not read frame from camera.")
    exit()
camera.release()
orig = image.copy()

# Step 1: Use fixed, hardcoded coordinates for the tray
# Your points are inserted here
fixed_tray_contour = np.array([(155, 109), (208, 476), (545, 393), (436, 88)], dtype="float32").reshape(4, 1, 2)

# Step 2: Perspective transform
def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left
    rect[2] = pts[np.argmax(s)]   # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect

rect = order_points(fixed_tray_contour)
(tl, tr, br, bl) = rect

# compute new width and height
widthA = np.linalg.norm(br - bl)
widthB = np.linalg.norm(tr - tl)
maxWidth = max(int(widthA), int(widthB))

heightA = np.linalg.norm(tr - br)
heightB = np.linalg.norm(tl - bl)
maxHeight = max(int(heightA), int(heightB))

dst = np.array([
    [0, 0],
    [maxWidth - 1, 0],
    [maxWidth - 1, maxHeight - 1],
    [0, maxHeight - 1]], dtype="float32")

M = cv2.getPerspectiveTransform(rect, dst)
warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

cv2.imwrite("tray_scanned.png", warped)
print("✅ Perspective transform completed using fixed coordinates: tray_scanned.png")

