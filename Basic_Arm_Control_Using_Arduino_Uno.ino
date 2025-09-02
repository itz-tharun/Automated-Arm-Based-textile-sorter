// Motor and Solenoid Pins
const int motorPins[3][2] = {
  {2, 3},  // Motor 1 (X-axis): D2=forward, D3=reverse
  {4, 5},  // Motor 2 (Y-axis): D4=forward, D5=reverse
  {6, 7}   // Motor 3 (Z-axis): D6=UP, D7=DOWN (but logic will be inverted)
};
const int clawPin = 9;          // Solenoid claw
const int switchDelay = 200;    // Safety delay between direction changes (ms)
bool clawState = false;         // Track claw state (false=open, true=closed)

// Function declarations
void runMotor(int motorIndex, char direction, float seconds);
void runZAxis(char direction, float seconds);
void openClaw();
void closeClaw();

void setup() {
  Serial.begin(9600);
  
  // Initialize all motor control pins
  for (int i = 0; i < 3; i++) {
    pinMode(motorPins[i][0], OUTPUT);
    pinMode(motorPins[i][1], OUTPUT);
    digitalWrite(motorPins[i][0], LOW);
    digitalWrite(motorPins[i][1], LOW);
  }
  
  // Initialize claw (start open)
  pinMode(clawPin, OUTPUT);
  digitalWrite(clawPin, LOW); // LOW = open (inverted logic)
  clawState = false;
  
  Serial.println("Robotic Arm Control Ready");
  Serial.println("Command format: [Motor] [Direction] [Duration]");
  Serial.println("Motors:");
  Serial.println("  X/Y: F=forward, R=reverse");
  Serial.println("  Z: U=up, D=down (INVERTED LOGIC)");
  Serial.println("  C: O=open, C=close (INVERTED LOGIC: HIGH=closed)");
  Serial.println("Examples:");
  Serial.println("  X F 2.5  - X forward 2.5s");
  Serial.println("  Z U 1.0  - Z up 1.0s");
  Serial.println("  C C      - Close claw (HIGH)");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    char motor = toupper(input.charAt(0));
    char dir = toupper(input.charAt(2));
    float duration = input.substring(4).toFloat();
    
    if (motor == 'C' && duration <= 0) duration = 0.1;

    switch(motor) {
      case 'X': case 'Y':
        if (dir == 'F' || dir == 'R') {
          runMotor(motor - 'X', dir, duration);
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

// Motor control functions
void runMotor(int motorIndex, char direction, float seconds) {
  unsigned long duration_ms = seconds * 1000;
  int fwdPin = motorPins[motorIndex][0];
  int revPin = motorPins[motorIndex][1];
  
  Serial.print("Motor ");
  Serial.print(char('X' + motorIndex));
  Serial.print(direction == 'F' ? " FORWARD" : " REVERSE");
  Serial.print(" for ");
  Serial.print(seconds, 1);
  Serial.println(" seconds");

  digitalWrite(fwdPin, LOW);
  digitalWrite(revPin, LOW);
  delay(switchDelay);
  
  if (direction == 'F') digitalWrite(fwdPin, HIGH);
  else digitalWrite(revPin, HIGH);
  
  delay(duration_ms);
  
  digitalWrite(fwdPin, LOW);
  digitalWrite(revPin, LOW);
  Serial.println("Done");
}

// INVERTED Z-axis
void runZAxis(char direction, float seconds) {
  unsigned long duration_ms = seconds * 1000;
  
  Serial.print("Z-axis ");
  Serial.print(direction == 'U' ? "UP (inverted)" : "DOWN (inverted)");
  Serial.print(" for ");
  Serial.print(seconds, 1);
  Serial.println(" seconds");

  digitalWrite(motorPins[2][0], LOW);
  digitalWrite(motorPins[2][1], LOW);
  delay(switchDelay);
  
  // INVERTED mapping: U -> motorPins[2][1], D -> motorPins[2][0]
  if (direction == 'U') digitalWrite(motorPins[2][1], HIGH); 
  else digitalWrite(motorPins[2][0], HIGH); 
  
  delay(duration_ms);
  
  digitalWrite(motorPins[2][0], LOW);
  digitalWrite(motorPins[2][1], LOW);
  Serial.println("Done");
}

// INVERTED CLAW FUNCTIONS
void openClaw() {
  digitalWrite(clawPin, LOW);  // LOW = open (inverted)
  clawState = false;
  Serial.println("Claw OPENED (LOW)");
}

void closeClaw() {
  digitalWrite(clawPin, HIGH); // HIGH = closed (inverted)
  clawState = true;
  Serial.println("Claw CLOSED (HIGH)");
}
