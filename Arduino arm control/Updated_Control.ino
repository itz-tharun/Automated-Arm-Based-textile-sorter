// Arduino sketch for controlling a 3-axis robot arm with DC motors and a solenoid-based clamp.

// Motor and Solenoid Pins
const int motorPins[3][2] = {
    {2, 3},  // Motor 1 (X-axis): D2=forward, D3=reverse
    {4, 5},  // Motor 2 (Y-axis): D4=forward, D5=reverse
    {6, 7}   // Motor 3 (Z-axis): D6=UP, D7=DOWN (but logic will be inverted)
};
const int clawPin = 9;       // Solenoid claw
const int switchDelay = 200;    // Safety delay between direction changes (ms)
bool clawState = false;      // Track claw state (false=open, true=closed)

// Function declarations
void runMotor(int motorIndex, char direction, float seconds);
void runZAxis(char direction, float seconds);
void openClaw();
void closeClaw();
void runXYMotors(char direction, float x_seconds, float y_seconds);

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
    Serial.println("   X/Y: F=forward, R=reverse");
    Serial.println("   Z: U=up, D=down (INVERTED LOGIC)");
    Serial.println("   C: O=open, C=close (INVERTED LOGIC: HIGH=closed)");
    Serial.println("New command for simultaneous X/Y movement: XY <direction> <x_duration> <y_duration>");
    Serial.println("Examples:");
    Serial.println("   X F 2.5   - X forward 2.5s");
    Serial.println("   Z U 1.0   - Z up 1.0s");
    Serial.println("   C C       - Close claw (HIGH)");
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
    
    int x_fwdPin = motorPins[0][0];
    int x_revPin = motorPins[0][1];
    int y_fwdPin = motorPins[1][0];
    int y_revPin = motorPins[1][1];

    // Turn on both motors
    if (direction == 'F') {
        digitalWrite(x_fwdPin, HIGH);
        digitalWrite(y_fwdPin, HIGH);
    } else {
        digitalWrite(x_revPin, HIGH);
        digitalWrite(y_revPin, HIGH);
    }

    // Use a non-blocking loop to run motors for their specified durations
    while (x_motor_running || y_motor_running) {
        if (x_motor_running && millis() >= x_end_time) {
            digitalWrite(x_fwdPin, LOW);
            digitalWrite(x_revPin, LOW);
            x_motor_running = false;
        }
        if (y_motor_running && millis() >= y_end_time) {
            digitalWrite(y_fwdPin, LOW);
            digitalWrite(y_revPin, LOW);
            y_motor_running = false;
        }
    }
    Serial.println("Simultaneous XY move complete.");
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
