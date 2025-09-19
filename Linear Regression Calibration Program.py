import numpy as np

# Calibration data points (pixel coordinate, motor movement time)
x_calibration_data = [
    (454, 0),
    (239, 1),
    (330, 1),
    (542, 0)
]

y_calibration_data = [
    (105, 0.7),
    (136, 0.7),
    (435, 4),
    (367, 4)
]

# Extract data arrays
x_pixels = np.array([p[0] for p in x_calibration_data])
x_times = np.array([p[1] for p in x_calibration_data])
y_pixels = np.array([p[0] for p in y_calibration_data])
y_times = np.array([p[1] for p in y_calibration_data])

# Fit linear models
x_slope, x_intercept = np.polyfit(x_pixels, x_times, 1)
y_slope, y_intercept = np.polyfit(y_pixels, y_times, 1)

print("✅ Calibration complete. Your linear model is:")
print(f"X_time = {x_slope:.4f} * x_pixel + {x_intercept:.4f}")
print(f"Y_time = {y_slope:.4f} * y_pixel + {y_intercept:.4f}")
print("-" * 40)

def predict_motor_time(x_pixel, y_pixel):
    """Predict motor movement time for given camera pixel coordinates."""
    x_time = x_slope * x_pixel + x_intercept
    y_time = y_slope * y_pixel + y_intercept
    # Clamp to non-negative times
    x_time = max(0, x_time)
    y_time = max(0, y_time)
    return x_time, y_time

def main():
    print("Enter camera pixel coordinates to get motor movement times.")
    print("Enter 'q' at any time to quit.")
    while True:
        x_input = input("Enter x pixel coordinate: ")
        if x_input.lower() == 'q':
            print("Exiting.")
            break
        y_input = input("Enter y pixel coordinate: ")
        if y_input.lower() == 'q':
            print("Exiting.")
            break
        try:
            x_pixel = float(x_input)
            y_pixel = float(y_input)
        except ValueError:
            print("Invalid input. Please enter numeric values for pixel coordinates.")
            continue

        x_time, y_time = predict_motor_time(x_pixel, y_pixel)
        print(f"Predicted motor times -> X: {x_time:.2f}, Y: {y_time:.2f}")
        print("-" * 40)

if __name__ == "__main__":
    main()
