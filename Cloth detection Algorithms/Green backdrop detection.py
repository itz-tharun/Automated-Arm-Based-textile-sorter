import cv2
import numpy as np

# ====== CONFIG ======
CAM_INDEX = 0                 # your USB camera
MIN_CLOTH_AREA = 1500         # pixels; tune for your scale
SAVE_DEBUG = "tray_detection_debug.jpg"

# HSV thresholds for a BRIGHT GREEN backdrop (adjust if your green differs)
# Tip: neon chart paper usually falls in this range.
GREEN_LO = np.array([35,  40,  40])   # H,S,V
GREEN_HI = np.array([85, 255, 255])

# Optional: set camera resolution (comment out if not needed)
# W, H = 1280, 720
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

def largest_contour(mask):
    cts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cts:
        return None
    return max(cts, key=cv2.contourArea)

def mask_from_contour(shape, cnt):
    m = np.zeros(shape[:2], dtype=np.uint8)
    cv2.drawContours(m, [cnt], -1, 255, thickness=cv2.FILLED)
    return m

def main():
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture frame")
        return

    # Convert to HSV for robust color threshold
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 1) Find the tray region by detecting the largest GREEN area
    green_mask = cv2.inRange(hsv, GREEN_LO, GREEN_HI)
    # Clean up green mask a bit
    k = np.ones((5,5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, k)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, k)

    tray_ct = largest_contour(green_mask)
    if tray_ct is None or cv2.contourArea(tray_ct) < 5000:
        print("Tray (green backdrop) not found. Adjust HSV or ensure backdrop is visible.")
        # Save a quick debug image to help tune HSV
        dbg = frame.copy()
        cv2.imwrite(SAVE_DEBUG, dbg)
        print(f"Saved debug as {SAVE_DEBUG}")
        return

    # Make a precise tray mask from the contour
    tray_mask = mask_from_contour(frame, tray_ct)

    # 2) Inside the tray only, detect NON-GREEN = (cloth, arm, anything not green)
    non_green = cv2.bitwise_not(green_mask)
    non_green_in_tray = cv2.bitwise_and(non_green, tray_mask)

    # Optional: suppress tiny specks
    non_green_in_tray = cv2.morphologyEx(non_green_in_tray, cv2.MORPH_OPEN, k)
    non_green_in_tray = cv2.morphologyEx(non_green_in_tray, cv2.MORPH_CLOSE, k)

    # 3) Find cloth regions (largest non-green blob inside tray)
    cloth_ct = largest_contour(non_green_in_tray)
    output = frame.copy()

    # Draw tray outline for reference
    cv2.drawContours(output, [tray_ct], -1, (0, 255, 255), 2)

    if cloth_ct is None or cv2.contourArea(cloth_ct) < MIN_CLOTH_AREA:
        print("No cloth detected (non-green blob too small or absent).")
        cv2.imwrite(SAVE_DEBUG, output)
        print(f"Saved debug as {SAVE_DEBUG}")
        return

    # Centroid for pick point
    M = cv2.moments(cloth_ct)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = -1, -1

    # Draw cloth outline + centroid
    cv2.drawContours(output, [cloth_ct], -1, (0, 255, 0), 2)
    if cx >= 0:
        cv2.circle(output, (cx, cy), 6, (0, 0, 255), -1)

    # Bounding box (optional—helpful for robot gripper)
    x, y, w, h = cv2.boundingRect(cloth_ct)
    cv2.rectangle(output, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # Print results
    print(f"Cloth centroid (pixels): ({cx}, {cy})")
    print(f"Bounding box (x,y,w,h): ({x}, {y}, {w}, {h})")

    # Save debug visualization
    cv2.imwrite(SAVE_DEBUG, output)
    print(f"Saved debug as {SAVE_DEBUG}")

if __name__ == "__main__":
    main()
