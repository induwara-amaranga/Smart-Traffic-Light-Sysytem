// smart_traffic_arduino.ino
#define SOUND_SENSOR_NORTH A0
#define SOUND_SENSOR_EAST A1
#define SOUND_SENSOR_SOUTH A2

// LED pins for North path
#define NORTH_RED 12
#define NORTH_YELLOW 3
#define NORTH_GREEN 4

// LED pins for East path
#define EAST_RED 5
#define EAST_YELLOW 6
#define EAST_GREEN 7

// LED pins for South path
#define SOUTH_RED 8
#define SOUTH_YELLOW 9
#define SOUTH_GREEN 10

// Buzzer and display
#define BUZZER 11
#define LCD_RS 2
#define LCD_ENABLE 13

#include <LiquidCrystal.h>
LiquidCrystal lcd(LCD_RS, LCD_ENABLE, A3, A4, A5, 2);

String currentCommand = "";
bool emergencyMode = false;
unsigned long lastSoundCheck = 0;
int soundThreshold = 400; // Adjust based on testing

void setup() {
    Serial.begin(9600);
    
    // Initialize LCD
    lcd.begin(16, 2);
    lcd.print("Smart Traffic");
    lcd.setCursor(0, 1);
    lcd.print("System Ready");
    
    // Initialize LED pins
    pinMode(NORTH_RED, OUTPUT);
    pinMode(NORTH_YELLOW, OUTPUT);
    pinMode(NORTH_GREEN, OUTPUT);
    pinMode(EAST_RED, OUTPUT);
    pinMode(EAST_YELLOW, OUTPUT);
    pinMode(EAST_GREEN, OUTPUT);
    pinMode(SOUTH_RED, OUTPUT);
    pinMode(SOUTH_YELLOW, OUTPUT);
    pinMode(SOUTH_GREEN, OUTPUT);
    pinMode(BUZZER, OUTPUT);
    
    // Start with all red
    setAllRed();
    
    delay(2000);
    lcd.clear();
}

void loop() {
    checkEmergencyVehicles();
    
    if (Serial.available()) {
        currentCommand = Serial.readStringUntil('\n');
        currentCommand.trim();
        processCommand(currentCommand);
    }
    
    updateDisplay();
    delay(100);
}

void checkEmergencyVehicles() {
    if (millis() - lastSoundCheck > 500) { // Check every 500ms
        int northSound = analogRead(SOUND_SENSOR_NORTH);
        int eastSound = analogRead(SOUND_SENSOR_EAST);
        int southSound = analogRead(SOUND_SENSOR_SOUTH);
        
        if (northSound > soundThreshold) {
            Serial.println("EMERGENCY_NORTH");
            handleEmergency("NORTH");
        } else if (eastSound > soundThreshold) {
            Serial.println("EMERGENCY_EAST");
            handleEmergency("EAST");
        } else if (southSound > soundThreshold) {
            Serial.println("EMERGENCY_SOUTH");
            handleEmergency("SOUTH");
        }
        
        lastSoundCheck = millis();
    }
}

void handleEmergency(String direction) {
    emergencyMode = true;
    digitalWrite(BUZZER, HIGH);
    delay(100);
    digitalWrite(BUZZER, LOW);
    
    lcd.clear();
    lcd.print("EMERGENCY!");
    lcd.setCursor(0, 1);
    lcd.print(direction + " PATH");
    
    // Immediate green for emergency path
    setAllRed();
    delay(1000);
    
    if (direction == "NORTH") {
        digitalWrite(NORTH_GREEN, HIGH);
        digitalWrite(NORTH_RED, LOW);
    } else if (direction == "EAST") {
        digitalWrite(EAST_GREEN, HIGH);
        digitalWrite(EAST_RED, LOW);
    } else if (direction == "SOUTH") {
        digitalWrite(SOUTH_GREEN, HIGH);
        digitalWrite(SOUTH_RED, LOW);
    }
    
    delay(10000); // Emergency green for 10 seconds
    emergencyMode = false;
}

void processCommand(String command) {
    if (emergencyMode) return; // Ignore commands during emergency
    
    if (command == "YELLOW_ALL") {
        setAllYellow();
    } else if (command == "GREEN_NORTH") {
        setGreenPath("NORTH");
    } else if (command == "GREEN_EAST") {
        setGreenPath("EAST");
    } else if (command == "GREEN_SOUTH") {
        setGreenPath("SOUTH");
    } else if (command == "RED_ALL") {
        setAllRed();
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
}

void setAllYellow() {
    digitalWrite(NORTH_RED, LOW);
    digitalWrite(NORTH_YELLOW, HIGH);
    digitalWrite(NORTH_GREEN, LOW);
    digitalWrite(EAST_RED, LOW);
    digitalWrite(EAST_YELLOW, HIGH);
    digitalWrite(EAST_GREEN, LOW);
    digitalWrite(SOUTH_RED, LOW);
    digitalWrite(SOUTH_YELLOW, HIGH);
    digitalWrite(SOUTH_GREEN, LOW);
}

void setGreenPath(String path) {
    setAllRed(); // First set all red
    
    if (path == "NORTH") {
        digitalWrite(NORTH_GREEN, HIGH);
        digitalWrite(NORTH_RED, LOW);
    } else if (path == "EAST") {
        digitalWrite(EAST_GREEN, HIGH);
        digitalWrite(EAST_RED, LOW);
    } else if (path == "SOUTH") {
        digitalWrite(SOUTH_GREEN, HIGH);
        digitalWrite(SOUTH_RED, LOW);
    }
}

void updateDisplay() {
    if (!emergencyMode) {
        lcd.clear();
        lcd.print("Traffic: Active");
        lcd.setCursor(0, 1);
        
        String activeLight = "Unknown";
        if (digitalRead(NORTH_GREEN)) activeLight = "North Green";
        else if (digitalRead(EAST_GREEN)) activeLight = "East Green";
        else if (digitalRead(SOUTH_GREEN)) activeLight = "South Green";
        else if (digitalRead(NORTH_YELLOW)) activeLight = "All Yellow";
        else activeLight = "All Red";
        
        lcd.print(activeLight);
    }
}
