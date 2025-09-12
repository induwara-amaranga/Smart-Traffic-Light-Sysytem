#include <Servo.h>

// Pin definitions
#define NORTH_RED 2
#define NORTH_YELLOW 3
#define NORTH_GREEN 4
#define EAST_RED 5
#define EAST_YELLOW 6
#define EAST_GREEN 7
#define SOUTH_RED 8
#define SOUTH_YELLOW 9
#define SOUTH_GREEN 10
#define WEST_RED 13
#define WEST_YELLOW 12
#define WEST_GREEN 11

// Sensor pins
#define NORTH_SENSOR A0
#define EAST_SENSOR A1
#define SOUTH_SENSOR A2
#define WEST_SENSOR A3

// Emergency vehicle detection
#define SOUND_SENSOR A4
#define SERVO_PIN A5

Servo emergencyServo;

// Traffic light states
enum TrafficState {
  NORTH_GO,
  NORTH_TO_EAST,
  EAST_GO,
  EAST_TO_SOUTH,
  SOUTH_GO,
  SOUTH_TO_WEST,
  WEST_GO,
  WEST_TO_NORTH,
  EMERGENCY_MODE
};

TrafficState currentState = NORTH_GO;
unsigned long stateTimer = 0;
unsigned long greenTime = 15000; // 15 seconds default
unsigned long yellowTime = 3000; // 3 seconds
unsigned long emergencyTimeout = 30000; // 30 seconds

// Vehicle counts
int vehicleCount[4] = {0, 0, 0, 0}; // North, East, South, West
bool emergencyMode = false;
String serialData = "";

void setup() {
  Serial.begin(115200);
  
  // Initialize servo
  emergencyServo.attach(SERVO_PIN);
  emergencyServo.write(0);
  
  // Initialize all LED pins
  for (int i = 2; i <= 13; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
  
  // Initialize sensor pins
  pinMode(NORTH_SENSOR, INPUT);
  pinMode(EAST_SENSOR, INPUT);
  pinMode(SOUTH_SENSOR, INPUT);
  pinMode(WEST_SENSOR, INPUT);
  pinMode(SOUND_SENSOR, INPUT);
  
  // Initial state
  updateTrafficLights();
  stateTimer = millis();
}

void loop() {
  // Read serial commands from Python
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      processCommand(serialData);
      serialData = "";
    } else {
      serialData += c;
    }
  }
  
  // Read sensors
  readVehicleSensors();
  checkEmergencyVehicle();
  
  // Send data to Python
  sendDataToPython();
  
  // Traffic light state machine
  if (!emergencyMode) {
    normalTrafficFlow();
  } else {
    handleEmergencyMode();
  }
}

void readVehicleSensors() {
  vehicleCount[0] = analogRead(NORTH_SENSOR) > 500 ? vehicleCount[0] + 1 : vehicleCount[0];
  vehicleCount[1] = analogRead(EAST_SENSOR) > 500 ? vehicleCount[1] + 1 : vehicleCount[1];
  vehicleCount[2] = analogRead(SOUTH_SENSOR) > 500 ? vehicleCount[2] + 1 : vehicleCount[2];
  vehicleCount[3] = analogRead(WEST_SENSOR) > 500 ? vehicleCount[3] + 1 : vehicleCount[3];
  
  for (int i = 0; i < 4; i++) {
    if (vehicleCount[i] > 10) vehicleCount[i] = 10;
  }
}

void checkEmergencyVehicle() {
  int soundLevel = analogRead(SOUND_SENSOR);
  if (soundLevel > 700 && !emergencyMode) { 
    emergencyMode = true;
    emergencyServo.write(90); // Open emergency lane
  }
}

void normalTrafficFlow() {
  unsigned long currentTime = millis();
  
  int maxVehicles = max(max(vehicleCount[0], vehicleCount[1]), max(vehicleCount[2], vehicleCount[3]));
  greenTime = map(maxVehicles, 0, 10, 10000, 30000); // Dynamic green light
  
  switch (currentState) {
    case NORTH_GO:
      if (currentTime - stateTimer >= greenTime) {
        currentState = NORTH_TO_EAST;
        stateTimer = currentTime;
        updateTrafficLights();
      }
      break;
    case NORTH_TO_EAST:
      if (currentTime - stateTimer >= yellowTime) {
        currentState = EAST_GO;
        stateTimer = currentTime;
        vehicleCount[0] = max(0, vehicleCount[0] - 3);
        updateTrafficLights();
      }
      break;
    case EAST_GO:
      if (currentTime - stateTimer >= greenTime) {
        currentState = EAST_TO_SOUTH;
        stateTimer = currentTime;
        updateTrafficLights();
      }
      break;
    case EAST_TO_SOUTH:
      if (currentTime - stateTimer >= yellowTime) {
        currentState = SOUTH_GO;
        stateTimer = currentTime;
        vehicleCount[1] = max(0, vehicleCount[1] - 3);
        updateTrafficLights();
      }
      break;
    case SOUTH_GO:
      if (currentTime - stateTimer >= greenTime) {
        currentState = SOUTH_TO_WEST;
        stateTimer = currentTime;
        updateTrafficLights();
      }
      break;
    case SOUTH_TO_WEST:
      if (currentTime - stateTimer >= yellowTime) {
        currentState = WEST_GO;
        stateTimer = currentTime;
        vehicleCount[2] = max(0, vehicleCount[2] - 3);
        updateTrafficLights();
      }
      break;
    case WEST_GO:
      if (currentTime - stateTimer >= greenTime) {
        currentState = WEST_TO_NORTH;
        stateTimer = currentTime;
        updateTrafficLights();
      }
      break;
    case WEST_TO_NORTH:
      if (currentTime - stateTimer >= yellowTime) {
        currentState = NORTH_GO;
        stateTimer = currentTime;
        vehicleCount[3] = max(0, vehicleCount[3] - 3);
        updateTrafficLights();
      }
      break;
  }
}

void handleEmergencyMode() {
  setAllRed();
  digitalWrite(NORTH_GREEN, HIGH); // Emergency route example
  
  if (millis() - stateTimer >= emergencyTimeout) {
    emergencyMode = false;
    emergencyServo.write(0);
    stateTimer = millis();
    updateTrafficLights();
  }
}

void updateTrafficLights() {
  setAllRed();
  
  switch (currentState) {
    case NORTH_GO:
      digitalWrite(NORTH_GREEN, HIGH);
      digitalWrite(NORTH_RED, LOW);
      break;
    case NORTH_TO_EAST:
      digitalWrite(NORTH_YELLOW, HIGH);
      digitalWrite(NORTH_GREEN, LOW);
      break;
    case EAST_GO:
      digitalWrite(EAST_GREEN, HIGH);
      digitalWrite(EAST_RED, LOW);
      break;
    case EAST_TO_SOUTH:
      digitalWrite(EAST_YELLOW, HIGH);
      digitalWrite(EAST_GREEN, LOW);
      break;
    case SOUTH_GO:
      digitalWrite(SOUTH_GREEN, HIGH);
      digitalWrite(SOUTH_RED, LOW);
      break;
    case SOUTH_TO_WEST:
      digitalWrite(SOUTH_YELLOW, HIGH);
      digitalWrite(SOUTH_GREEN, LOW);
      break;
    case WEST_GO:
      digitalWrite(WEST_GREEN, HIGH);
      digitalWrite(WEST_RED, LOW);
      break;
    case WEST_TO_NORTH:
      digitalWrite(WEST_YELLOW, HIGH);
      digitalWrite(WEST_GREEN, LOW);
      break;
  }
}

void setAllRed() {
  digitalWrite(NORTH_RED, HIGH);
  digitalWrite(NORTH_YELLOW, LOW);
  digitalWrite(NORTH_GREEN, LOW);
  digitalWrite(EAST_RED, HIGH);
  digitalWrite(EAST_YELLOW, LOW);
  digitalWrite(EAST_GREEN, LOW);
  digitalWrite(SOUTH_RED, HIGH);
  digitalWrite(SOUTH_YELLOW, LOW);
  digitalWrite(SOUTH_GREEN, LOW);
  digitalWrite(WEST_RED, HIGH);
  digitalWrite(WEST_YELLOW, LOW);
  digitalWrite(WEST_GREEN, LOW);
}

void sendDataToPython() {
  Serial.print("{\"state\":\"");
  Serial.print(currentState);
  Serial.print("\",\"vehicles\":[");
  Serial.print(vehicleCount[0]);
  Serial.print(",");
  Serial.print(vehicleCount[1]);
  Serial.print(",");
  Serial.print(vehicleCount[2]);
  Serial.print(",");
  Serial.print(vehicleCount[3]);
  Serial.print("],\"emergency\":");
  Serial.print(emergencyMode ? "true" : "false");
  Serial.println("}");
}

void processCommand(String cmd) {
  if (cmd.startsWith("EMERGENCY")) {
    emergencyMode = true;
    stateTimer = millis();
  } else if (cmd.startsWith("NORMAL")) {
    emergencyMode = false;
  } else if (cmd.startsWith("VEHICLE:")) {
    int dir = cmd.substring(8, 9).toInt();
    int count = cmd.substring(10).toInt();
    if (dir >= 0 && dir < 4) {
      vehicleCount[dir] = count;
    }
  }
}
