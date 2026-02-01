#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// name Arduino board pins used by the circuit
#define SENSOR_PIN A0

int rawValue = 0;
float voltage = 0.0;
float ldrResistance = 0;

const float VCC = 3.28;
const float R_FIXED = 9450.0; // 10k ohm resistor

void setup() {
    Serial.begin(9600);

    if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
        Serial.println(F("SSD1306 allocation failed"));
        for (;;); // Don't proceed, loop forever
    }

    display.clearDisplay();
    display.setTextColor(WHITE);

    pinMode(SENSOR_PIN, INPUT);
}

void loop() {
    rawValue = analogRead(SENSOR_PIN);
    voltage = rawValue * (VCC / 4095.0);
    if (voltage > 0) {
        ldrResistance = R_FIXED * ((VCC / voltage) - 1.0);
    }

    displayInfo();

    delay(500); // 500ms delay for readability
}

void displayInfo() {
    Serial.print("DATA,");
    Serial.print(millis());
    Serial.print(",");
    Serial.print(rawValue);
    Serial.print(",");
    Serial.print(voltage, 3);
    Serial.print(",");
    Serial.println(ldrResistance);

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 0);
    display.println("Sensor");
    display.println("Characterization");
    display.print("Time: ");
    display.print(millis() / 1000.0, 1);
    display.println(" s");
    display.print("Raw ADC: ");
    display.println(rawValue);
    display.print("Voltage: ");
    display.print(voltage, 3);
    display.println(" V");
    display.print("LDR R: ");
    display.print(ldrResistance, 1);
    display.println(" Ohm");
    display.display();
}
