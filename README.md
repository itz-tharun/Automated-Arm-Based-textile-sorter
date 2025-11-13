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

# Hardware Code Explanation: Arduino Arm Control

The Arduino firmware manages the low-level execution based on serial commands from the Python host. All commands follow a consistent format (e.g., X F 2.0) and are terminated by a newline.

| File Name | Driver Type | Key Functionality | Notes |
| :-------: | :------: | :-------: | :--------: |
| [Basic_Control.ino](./Automated-Arm-Based-textile-sorter/Arduino%20arm%20control/Basic_Control.ino) | Relay-based | Initial implementation of time-based directional control. | Established core serial communication and individual motor commands. |
| [Updated_Control.ino](./Automated-Arm-Based-textile-sorter/Arduino%20arm%20control/Updated_Control.ino) | Relay-based | Introduced simultaneous X and Y motor control. | Optimized movement speed by allowing diagonal traversal. Still limited by relay lack of PWM. |
| [BTS7960_Based_control.ino](./Automated-Arm-Based-textile-sorter/Arduino%20arm%20control/BTS7960_Based_control.ino) | BTS7960 (PWM) | Final, optimized code. Utilizes PWM for speed control (X-axis reduced speed). | Integrates robust, high-current drivers and includes simultaneous XY movement commands for the shortest possible cycle time.|

# Algorithms Explored: Computer Vision Pipeline

The algorithmic exploration was crucial to fulfill the research mandate, focusing on efficiency and suitability for anomaly detection.

## 1.Final Chosen Method

### [Image Subtraction Detection.py](./Automated-Arm-Based-textile-sorter/Cloth%20detection%20Algorithms/Image%20Subtraction%20Detection.py)

### Method:
Relies on the Subtraction Principle. It captures a static reference image of the empty tray, then calculates the absolute difference ($\text{cv2.absdiff}$) between the live frame and the reference image. The resulting pixels represent only the newly introduced cloth piece (the anomaly).

### Advantages: 
Highest computational efficiency and perfect dynamic fit for the "find the anomaly" application.

5.2 Explored and Discarded Methods

White background detection.py

Method: Used color thresholding to distinguish the cloth from a white tray background.

Disadvantages: Prone to error with varied cloth colors or inconsistent lighting.

canny edge detection.py

Method: Detects abrupt changes in image intensity to find object boundaries.

Disadvantages: Highly sensitive to external factors like shadows and lighting inconsistencies, making it unstable.

Green backdrop detection.py

Method: Utilizes Chroma Keying principles to isolate the object from a green background (intended for an underneath camera setup).

Disadvantages: Impractical due to the mechanical difficulty of setting up the prototype rig.
