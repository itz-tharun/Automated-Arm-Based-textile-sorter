import cv2
import numpy as np

# Load your image
img = cv2.imread("tray.jpg")

# STEP 1: Manually mark or detect tray corners (clockwise order)
# Example: replace these with the actual (x,y) pixel coordinates of the tray corners in your image
# Order: top-left, top-right, bottom-right, bottom-left
pts_src = np.float32([
    [120, 80],    # top-left
    [480, 60],    # top-right
    [500, 400],   # bottom-right
    [100, 420]    # bottom-left
])

# STEP 2: Define the size of the output rectangle (flattened tray)
width, height = 400, 400  # Change according to your tray dimensions
pts_dst = np.float32([
    [0, 0],
    [width - 1, 0],
    [width - 1, height - 1],
    [0, height - 1]
])

# STEP 3: Get the perspective transform matrix
matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)

# STEP 4: Apply warpPerspective to get the flattened tray
warped = cv2.warpPerspective(img, matrix, (width, height))

# Display results
cv2.imshow("Original", img)
cv2.imshow("Flattened Tray", warped)
cv2.waitKey(0)
cv2.destroyAllWindows()
