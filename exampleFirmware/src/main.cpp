#include <Arduino.h>
#include <Preferences.h>

Preferences preferences;
void provisioning();

void setup() {
    provisioning();
}

void loop() {
}


void provisioning() {
    Serial.begin(115200);
    
    preferences.begin("provision", false);
    bool provisioned = false;
    provisioned = preferences.getBool("done", false);

    while (!provisioned) {
        Serial.println("Provisioning");
        delay(500); // Print "Provisioning" every 30 seconds

        if (!Serial.available()) 
            continue;
        
        String input = Serial.readStringUntil('\n');
        input.trim();
        
        int firstComma = input.indexOf(',');
        int secondComma = input.lastIndexOf(',');

        if (firstComma > 0 && secondComma > 0) {
            String key1 = input.substring(0, firstComma);
            String key2 = input.substring(firstComma + 1, secondComma);
            String key3 = input.substring(secondComma + 1);

            preferences.putString("key1", key1);
            preferences.putString("key2", key2);
            preferences.putString("key3", key3);
            preferences.putBool("done", true);

            Serial.println("Provisioned");
            ESP.restart();
        }
        
    }
    if (provisioned) {
        Serial.println("Provisioned");
        Serial.print("Key1: "); Serial.println(preferences.getString("key1", ""));
        Serial.print("Key2: "); Serial.println(preferences.getString("key2", ""));
        Serial.print("Key3: "); Serial.println(preferences.getString("key3", ""));
    }
}