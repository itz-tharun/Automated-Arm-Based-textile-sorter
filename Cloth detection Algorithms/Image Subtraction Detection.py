# This script compares a reference image of an empty tray with a new image
# to detect the presence and location of a cloth.

import cv2
import numpy as np

def compare_images(reference_image_path, live_image_path, output_image_path, threshold_value=25):
    """
    Compares two images to find and highlight differences.

    Args:
        reference_image_path (str): The file path to the reference image of an empty tray.
        live_image_path (str): The file path to the live image with a potential object.
        output_image_path (str): The file path to save the output difference image.
        threshold_value (int): The sensitivity threshold for difference detection (0-255).
                               Lower values are more sensitive.
    """
    try:
        # Load the two images
        ref_image = cv2.imread(reference_image_path)
        live_image = cv2.imread(live_image_path)
        
        if ref_image is None:
            print(f"Error: Could not load the reference image at {reference_image_path}")
            return
        if live_image is None:
            print(f"Error: Could not load the live image at {live_image_path}")
            return

        # Ensure images are the same size
        if ref_image.shape != live_image.shape:
            print("Error: The images must be the same size for comparison.")
            return

        # Convert images to grayscale for simpler comparison
        ref_gray = cv2.cvtColor(ref_image, cv2.COLOR_BGR2GRAY)
        live_gray = cv2.cvtColor(live_image, cv2.COLOR_BGR2GRAY)

        # Calculate the absolute difference between the two grayscale images
        diff = cv2.absdiff(ref_gray, live_gray)

        # Apply a binary threshold to the difference image.
        # Pixels with a difference above the threshold are set to 255 (white).
        _, thresholded_diff = cv2.threshold(diff, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Count the number of white pixels to determine the percentage of change
        total_pixels = thresholded_diff.size
        changed_pixels = np.count_nonzero(thresholded_diff)
        percentage_change = (changed_pixels / total_pixels) * 100

        print(f"Percentage of change detected: {percentage_change:.2f}%")

        # Find contours of the changed areas
        contours, _ = cv2.findContours(thresholded_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw rectangles around the detected differences on the live image
        output_image = live_image.copy()
        for contour in contours:
            # Filter out small areas of noise
            if cv2.contourArea(contour) > 100:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Save the resulting image with the highlighted differences
        cv2.imwrite(output_image_path, output_image)
        print(f"Difference image saved to {output_image_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Main Program Execution ---
if __name__ == "__main__":
    # Define your image file paths here
    REFERENCE_IMAGE = 'empty_tray.jpg'  # Change this to your reference image file
    LIVE_IMAGE = 'tray_with_cloth.jpg'  # Change this to your live image file
    OUTPUT_IMAGE = 'difference_detected.jpg' # The name for the output file

    # Run the comparison
    compare_images(REFERENCE_IMAGE, LIVE_IMAGE, OUTPUT_IMAGE)
