# Introduction and Background
This project details the development of a constrained, autonomous robotic arm prototype created during an internship at the National Taiwan Normal University (NTNU), specifically within the Electro-Optical Department. The department’s goal was to research and validate computer vision algorithms suitable for the preliminary sorting stage required by Pade Technology, a textile recycling startup.

The core challenge was dictated by a strict industrial mandate: maximum cost reduction. This meant that while the main production arm's hardware design was scheduled for a later stage, the immediate task was to formulate the control code and vision algorithms that would drive the final system. To test this code, I set up a simpler, low-cost hardware rig utilizing basic DC motors and simplified control systems (relays/H-bridges) instead of expensive industrial components like encoders. Consequently, the prototype arm had no memory of its position (open-loop control).

This necessitated a shift in the engineering focus: instead of relying on hardware precision, the solution became entirely software-centric.

<br>

# Goal and Aim of the Project

The project’s objective was to use the prototype as a research platform to select and validate the optimal computer vision strategy under severe cost constraints, ultimately delivering a tested, robust code base for future hardware implementation.

## Core Goal

To formulate and test the core code logic (vision, calibration, and actuation) for a fully autonomous pick-and-place system that could accurately detect and sort materials, using a low-cost testing rig to validate the code's functionality and robustness before the final arm design phase.

## Research Mandate (Constraints)

### 1.Constraint-Driven Precision:
Establish a system for open-loop positional control where camera pixel coordinates are converted into precise motor run times (seconds) using an empirically derived Linear Regression Calibration model.

### 2.Anomaly Detection: 
The core task was defined as finding the anomaly (the cloth piece) on a known tray, rather than classifying it from a variety of mixed materials. This constraint meant that AI models were unnecessary and were rejected in favor of a simpler, more computationally efficient method.

### 3.Vision Strategy:
Explore and test various vision algorithms to identify the most dynamic and efficient approach suitable for the specified anomaly detection task and the limited computational resources. The Image Subtraction Detection algorithm was ultimately chosen as the perfect fit for these specific constraints.

<br>

# Hardware Explanation and System Architecture

The testing rig operates on a two-layer control architecture: a high-level Intelligence Layer (Python on a Host PC) for computation and a low-level Execution Layer (Arduino Uno) for real-time actuation.

## 1.Actuators and Gripping

### A. DC Motors:
Three DC motors provide motion for the X (base), Y (extension), and Z (vertical) axes.

### B. Claw:
A Solenoid Actuator provides the binary (open/close) gripping mechanism.

### C. Control Evolution:
The drivers evolved from simple relays to BTS7960 H-bridges to utilize Pulse Width Modulation (PWM) for fine-tuning speed and reducing Noice from Back Electromotive Force.

## 2.Electrical Challenges and Solutions

### Problem: 
The 24V DC motors generated severe Back Electromotive Force (Back EMF) and electrical noise, causing the sensitive Arduino USB connection to disconnect.

### Interim Fix:
Flyback diodes were used, which mitigated noise but introduced voltage drop issues.

### Industrial Recommendation:
The definitive solution required implementing Optocouplers (opto-isolators) to achieve complete galvanic isolation, ensuring long-term stability.

## 3.Camera Positioning Experiments
Four different mounting configurations were systematically tested to determine the most practical and accurate placement that balanced visibility, obstruction, and required calibration complexity:

| Configuration | Advantages | Disadvantages |
| :-------: | :------: | :-------: |
| Direct Overhead (Top-Down))  | Provided full, undistorted tray visibility.  | Suffered heavily from arm obstruction and difficulty maintaining a consistent focus across the large area.  |
| Underneath (Upward-Facing)  | Enabled advanced shadow-based detection.  | Required transparent trays, which was mechanically and practically unfeasible for the prototype.  |
| Side View  | Simple to mount and kept the arm mostly clear.  | Caused heavy parallax error and distortion, making pixel-to-physical calibration extremely difficult.  |
| Elevated Side View (Chosen Method) | Offered a slanted top-down perspective with fewer obstructions. | Parallax error was manageable via Perspective Transform software correction. |

### Final decision:
The Elevated Side View was adopted as the optimal balance between visibility, accuracy, and practicality, requiring a robust software transformation layer to compensate for its inherent distortion.

<br>

# Hardware Code Explanation: Arduino Arm Control

The Arduino firmware manages the low-level execution based on serial commands from the Python host. All commands follow a consistent format (e.g., X F 2.0) and are terminated by a newline.

| File Name | Driver Type | Key Functionality | Notes |
| :-------: | :------: | :-------: | :--------: |
| [Basic_Control.ino](./Arduino%20arm%20control/Basic_Control.ino) | Relay-based | Initial implementation of time-based directional control. | Established core serial communication and individual motor commands. |
| [Updated_Control.ino](./Arduino%20arm%20control/Updated_Control.ino) | Relay-based | Introduced simultaneous X and Y motor control. | Optimized movement speed by allowing diagonal traversal. Still limited by relay lack of PWM. |
| [BTS7960_Based_control.ino](./Arduino%20arm%20control/BTS7960_Based_control.ino) | BTS7960 (PWM) | Final, optimized code. Utilizes PWM for speed control (X-axis reduced speed). | Integrates robust, high-current drivers and includes simultaneous XY movement commands for the shortest possible cycle time.|

<br> 

# Algorithms Explored: Computer Vision Pipeline

The algorithmic exploration was crucial to fulfill the research mandate, focusing on efficiency and suitability for anomaly detection.

## 1.Final Chosen Method

### [Image Subtraction Detection.py](./Cloth%20detection%20Algorithms/Image%20Subtraction%20Detection.py)

<br>
<div align="center">
    <img width="398" height="440" src="https://github.com/user-attachments/assets/21ee4bc3-192f-460f-8163-00905f93c330">
</div>
<br>

#### Method:
Relies on the Subtraction Principle. It captures a static reference image of the empty tray, then calculates the absolute difference cv2.absdiff between the live frame and the reference image. The resulting pixels represent only the newly introduced cloth piece (the anomaly).

#### Advantages: 
Highest computational efficiency and perfect dynamic fit for the "find the anomaly" application.


## 2.Explored and Discarded Methods

### [Color based detection.py](./Cloth%20detection%20Algorithms/White%20background%20detection.py)
<br>
<div align="center">
    <img width="408" height="427" src="https://github.com/user-attachments/assets/9c76266c-4d9d-4f4e-8688-f01fdf5680c3">
</div>
<br>

#### Method: 
Used color thresholding to distinguish the cloth from a white tray background.

#### Disadvantages: 
Prone to error with white colored cloths.

### [Canny edge detection.py](./Cloth%20detection%20Algorithms/canny%20edge%20detection.py)

<br>
<div align="center">
    <img width="408" height="427" src="https://github.com/user-attachments/assets/7317130d-3176-4710-91ad-6b4f544cff67">
</div>
<br>

#### Method:
Detects abrupt changes in image intensity to find object boundaries.

#### Disadvantages:
Highly sensitive to external factors like shadows and lighting inconsistencies, making it unstable.

### [Green backdrop detection.py](./Cloth%20detection%20Algorithms/Green%20backdrop%20detection.py)

<br>
<div align="center">
    <img width="381" height="309" alt="Image" src="https://github.com/user-attachments/assets/43a96a8c-907e-4d88-9e32-a399f8184fe1" />
</div>
<br>

#### Method:
Utilizes Chroma Keying principles to isolate the object from a green background (intended for an underneath camera setup).

#### Disadvantages:
Impractical due to the mechanical difficulty of setting up the prototype rig.

<br>


# Calibration and Utility Programs

## Perspective Transformation and Region of Interest (ROI) Flattening

Due to the adoption of the Elevated Side View for the camera, the image suffered from significant parallax and geometric distortion. This necessitated a critical software step to correct the image before calibration could be accurate.

### Region of Interest (ROI) Definition:
The utility program Coordinate detector for [ROI Definition & Perspective Flattening.py](./Calibration%20and%20Testing/ROI%20Definition%20&%20Perspective%20Flattening.py) was used to manually select the four physical corners of the tray in the distorted image. This ROI definition ensures:

1. All detection algorithms only run within the tray area, eliminating false positives from the surrounding environment.

2. The detection system remains robust even if the camera is bumped slightly, as the tray corners can be dynamically re-identified.

<div align="center">
    <img src="https://github.com/user-attachments/assets/d372c2ef-df13-4270-bb17-70fe11f041e4">
</div>
    <div align="center""> 
      WITHOUT ROI DEFINITION(RUNNING COLOR BASED DETECTION)
    </div>
<br>

<div align="center">
    <img src="https://github.com/user-attachments/assets/ea8c9844-2a80-49ed-b3c3-e0fe80bff728">
</div>
    <div align="center""> 
      WITH ROI DEFINITION(RUNNING COLOR BASED DETECTION)
    </div>

### Perspective Transformation:
OpenCV's perspective transform functions (cv2.getPerspectiveTransform and cv2.warpPerspective) were applied. This process maps the four distorted tray corner coordinates to a new, fixed set of four rectangular corner coordinates.

Result: This transformation effectively "flattens" the tilted image into an orthogonal, top-down view. This normalized image plane provides consistent and true X/Y coordinates for the Linear Regression Calibration model to rely upon, dramatically improving positional accuracy.

<div align="center">
    <img width="398" height="440" src="https://github.com/user-attachments/assets/12ed94a9-e496-4215-9b65-39453fdc6ffc">
</div>
    <div align="center""> 
      AFTER PERSPECTIVE TRANSFORMATION
    </div>

## Utility Files Description

This section details the critical utility programs used for image processing setup, hardware verification, and the camera-to-arm transformation essential for open-loop control.

| File Name | Purpose | Key Functionality |
| :-------: | :------: | :-------: |
| [Linear Regression Calibration Program.py](./Calibration%20and%20Testing/Linear%20Regression%20Calibration%20Program.py) | Calibration Core | Performs a linear calibration that maps pixel coordinates from the camera’s view to motor movement time values. It fits simple linear models for X and Y axes, translating image coordinates to open-loop actuation commands. |
| [ROI Definition & Perspective Flattening.py](./Calibration%20and%20Testing/ROI%20Definition%20&%20Perspective%20Flattening.py) | ROI/Perspective Utility | Defines a Region of Interest (ROI) and applies a perspective transform to flatten the slanted camera view into an orthogonal (top-down) rectangular view for accurate measurement. This also helped secure stable reference points for the Linear Regression Calibration. |
| [Camera_capture_test.py](./Calibration%20and%20Testing/camera_capture_test.py) | Hardware Verification | A utility script used to test the USB camera connection, verify camera setup, and capture a single frame for quality check, serving as a foundation for integration. |



# Final Integrated System

This section outlines the structure of the final, autonomous system, detailing the core files that combine the vision, calibration, and actuation components to perform the end-to-end cloth sorting task. The system was finalized in a folder named Final_Cloth_Sorting_Arm.

| File Name | Language | Role in System |
| :-------: | :------: | :-------: |
| [Main Python Program.py](./Final_Cloth_Sorting_Arm/Main%20Python%20Program.py) | Python | **THE FINAL PROGRAM:** Integrates the vision algorithm ( [Image Subtraction Detection](./Cloth%20detection%20Algorithms/Image%20Subtraction%20Detection.py) ), the serial communication library, the ROI flattening logic, and the Linear Regression Calibration model to execute the complete autonomous loop (Detect $\rightarrow$ Calculate Movement Time $\rightarrow$ Send Serial Command $\rightarrow$ Pick $\rightarrow$ Drop). |
| [BTS7960_Based_control.ino](./Final_Cloth_Sorting_Arm/BTS7960_Based_control.ino) | Arduino C++ | **Arduino Controller Program:** Manages the low-level motor actuation using BTS7960 H-bridges and PWM for optimized speed, receiving serial commands from the [Main Python Program.py](./Final_Cloth_Sorting_Arm/Main%20Python%20Program.py) |
| [Coordinate detector for ROI definition and Calibration.py](./Final_Cloth_Sorting_Arm/Coordinate%20detector%20for%20ROI%20definition%20and%20Calibration.py) | Python | Used for generating the calibration parameters that are referenced by the main program. |

<br>

# Conclusion

The primary goal of devising an anomaly detection algorithm suitable for the given application was realized, and a proof-of-concept prototype was successfully designed and implemented using low-cost hardware. While the arm is only industrially viable when transitioned to a closed-loop system utilizing encoders and stepper motors, the primary objective was realized: to create a functional prototype and code base robust enough to validate the core software strategy and pool in enough funding to kick-start the industrial scaling phase of the project.
