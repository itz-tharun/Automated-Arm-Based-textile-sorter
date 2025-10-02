// Each motor driver controls one motor and requires 3 Arduino pins:
// ENA (Enable), RPWM (Forward), and LPWM (Reverse).
// All RPWM and LPWM pins MUST be PWM-capable pins (3, 5, 6, 9, 10, 11 on Uno).

// X-AXIS MOTOR DRIVER (Motor 1)
const int ENA_X = 2;
const int RPWM_X = 3;  // PWM Pin
const int LPWM_X = 5;  // PWM Pin

// Y-AXIS MOTOR DRIVER (Motor 2)
const int ENA_Y = 4;
const int RPWM_Y = 6;  // PWM Pin
const int LPWM_Y = 9;  // PWM Pin

// Z-AXIS MOTOR DRIVER (Motor 3)
const int ENA_Z = 7;
const int RPWM_Z = 10; // PWM Pin
const int LPWM_Z = 11; // PWM Pin

// Solenoid claw pin
const int clawPin = 8;
const int motorSpeed = 255;         // Speed (0-255). This is now set to maximum.
const int switchDelay = 200;        // Safety delay between direction changes (ms)

// Function declarations
void runMotor(int motorIndex, char direction, float seconds);
void runZAxis(char direction, float seconds);
void openClaw();
void closeClaw();
void runXYMotors(char direction, float x_seconds, float y_seconds);

void setup() {
  Serial.begin(9600);
  
  // Set all motor driver control pins as outputs
  pinMode(ENA_X, OUTPUT);
  pinMode(RPWM_X, OUTPUT);
  pinMode(LPWM_X, OUTPUT);
  pinMode(ENA_Y, OUTPUT);
  pinMode(RPWM_Y, OUTPUT);
  pinMode(LPWM_Y, OUTPUT);
  pinMode(ENA_Z, OUTPUT);
  pinMode(RPWM_Z, OUTPUT);
  pinMode(LPWM_Z, OUTPUT);
  
  // Initialize all enable pins to HIGH to activate the drivers
  digitalWrite(ENA_X, HIGH);
  digitalWrite(ENA_Y, HIGH);
  digitalWrite(ENA_Z, HIGH);

  // Initialize all PWM pins to 0 to ensure motors are stopped
  analogWrite(RPWM_X, 0);
  analogWrite(LPWM_X, 0);
  analogWrite(RPWM_Y, 0);
  analogWrite(LPWM_Y, 0);
  analogWrite(RPWM_Z, 0);
  analogWrite(LPWM_Z, 0);
  
  // Initialize claw (start open)
  pinMode(clawPin, OUTPUT);
  digitalWrite(clawPin, LOW); // LOW = open
  
  Serial.println("Robotic Arm Control Ready (BTS7960 Drivers)");
  Serial.println("Command format: [Motor] [Direction] [Duration]");
  Serial.println("Motors:");
  Serial.println("   X/Y: F=forward, R=reverse");
  Serial.println("   Z: U=up, D=down");
  Serial.println("   C: O=open, C=close");
  Serial.println("New command for simultaneous X/Y movement: XY <direction> <x_duration> <y_duration>");
  Serial.println("Examples:");
  Serial.println("   X F 2.5    - X forward 2.5s");
  Serial.println("   Z U 1.0    - Z up 1.0s");
  Serial.println("   C C        - Close claw");
  Serial.println("   XY F 2.5 1.5 - X/Y forward for 2.5s/1.5s (simultaneously)");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    // Handle new XY command
    if (input.startsWith("XY")) {
      char dir = toupper(input.charAt(3));
      int first_space = input.indexOf(' ', 4);
      int second_space = input.indexOf(' ', first_space + 1);
      float x_duration = input.substring(first_space + 1, second_space).toFloat();
      float y_duration = input.substring(second_space + 1).toFloat();
      
      runXYMotors(dir, x_duration, y_duration);
    } else {
      // Original single-motor commands
      char motor = toupper(input.charAt(0));
      char dir = toupper(input.charAt(2));
      float duration = input.substring(4).toFloat();
      
      if (motor == 'C' && duration <= 0) duration = 0.1;

      switch(motor) {
        case 'X': case 'Y':
          if (dir == 'F' || dir == 'R') {
            runMotor(motor == 'X' ? 0 : 1, dir, duration);
          } else {
            Serial.println("Error: Use F/R for X/Y axes");
          }
          break;
          
        case 'Z':
          if (dir == 'U' || dir == 'D') {
            runZAxis(dir, duration);
          } else {
            Serial.println("Error: Use U=up, D=down for Z-axis");
          }
          break;
          
        case 'C':
          if (dir == 'O') {
            openClaw();
          } else if (dir == 'C') {
            closeClaw();
          } else {
            Serial.println("Error: Use O to open or C to close claw");
          }
          break;
          
        default:
          Serial.println("Error: Invalid motor (use X/Y/Z/C)");
      }
    }
  }
}

// Motor control functions (updated for BTS7960)
void runMotor(int motorIndex, char direction, float seconds) {
  unsigned long duration_ms = seconds * 1000;
  
  int pwmPinForward;
  int pwmPinReverse;

  if (motorIndex == 0) { // X-Axis
    pwmPinForward = RPWM_X;
    pwmPinReverse = LPWM_X;
  } else { // Y-Axis
    pwmPinForward = RPWM_Y;
    pwmPinReverse = LPWM_Y;
  }

  Serial.print("Motor ");
  Serial.print(motorIndex == 0 ? 'X' : 'Y');
  Serial.print(direction == 'F' ? " FORWARD" : " REVERSE");
  Serial.print(" for ");
  Serial.print(seconds, 1);
  Serial.println(" seconds");

  // Stop motors for a moment to prevent short-circuiting
  analogWrite(pwmPinForward, 0);
  analogWrite(pwmPinReverse, 0);
  delay(switchDelay);
  
  if (direction == 'F') {
    analogWrite(pwmPinForward, motorSpeed);
  } else {
    analogWrite(pwmPinReverse, motorSpeed);
  }
  
  delay(duration_ms);
  
  // Stop the motor
  analogWrite(pwmPinForward, 0);
  analogWrite(pwmPinReverse, 0);
  Serial.println("Done");
}

// New function for simultaneous X and Y motor control
void runXYMotors(char direction, float x_seconds, float y_seconds) {
  Serial.print("Simultaneous XY move for X:");
  Serial.print(x_seconds, 1);
  Serial.print("s and Y:");
  Serial.print(y_seconds, 1);
  Serial.println("s");

  unsigned long start_time = millis();
  unsigned long x_end_time = start_time + (unsigned long)(x_seconds * 1000);
  unsigned long y_end_time = start_time + (unsigned long)(y_seconds * 1000);
  bool x_motor_running = true;
  bool y_motor_running = true;
  
  // Turn on both motors
  if (direction == 'F') {
    analogWrite(RPWM_X, motorSpeed);
    analogWrite(RPWM_Y, motorSpeed);
  } else {
    analogWrite(LPWM_X, motorSpeed);
    analogWrite(LPWM_Y, motorSpeed);
  }

  // Use a non-blocking loop to run motors for their specified durations
  while (x_motor_running || y_motor_running) {
    if (x_motor_running && millis() >= x_end_time) {
      analogWrite(RPWM_X, 0);
      analogWrite(LPWM_X, 0);
      x_motor_running = false;
    }
    if (y_motor_running && millis() >= y_end_time) {
      analogWrite(RPWM_Y, 0);
      analogWrite(LPWM_Y, 0);
      y_motor_running = false;
    }
  }
  Serial.println("Simultaneous XY move complete.");
}

// Z-axis control (updated for BTS7960)
void runZAxis(char direction, float seconds) {
  unsigned long duration_ms = seconds * 1000;
  
  Serial.print("Z-axis ");
  Serial.print(direction == 'U' ? "UP" : "DOWN");
  Serial.print(" for ");
  Serial.print(seconds, 1);
  Serial.println(" seconds");

  // Stop motor for a moment
  analogWrite(RPWM_Z, 0);
  analogWrite(LPWM_Z, 0);
  delay(switchDelay);
  
  // The BTS7960 logic is simple: U -> RPWM, D -> LPWM
  if (direction == 'U') {
    analogWrite(RPWM_Z, motorSpeed);
  } else {
    analogWrite(LPWM_Z, motorSpeed);
  }
  
  delay(duration_ms);
  
  // Stop the motor
  analogWrite(RPWM_Z, 0);
  analogWrite(LPWM_Z, 0);
  Serial.println("Done");
}

// Claw control functions (unchanged)
void openClaw() {
  digitalWrite(clawPin, LOW);   // LOW = open
  Serial.println("Claw OPENED (LOW)");
}

void closeClaw() {
  digitalWrite(clawPin, HIGH);  // HIGH = closed
  Serial.println("Claw CLOSED (HIGH)");
}
