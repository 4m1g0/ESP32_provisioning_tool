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
    bool provisioned = preferences.getBool("done", false);

    while (!provisioned) {
        Serial.println("Provisioning");
        delay(500); // Print "Provisioning" every 500ms

        if (!Serial.available()) 
            continue;
        
        String input = Serial.readStringUntil('\n');
        input.trim();

        // Array to store comma positions
        int commaPositions[4];

        // Manually find the positions of the commas
        commaPositions[0] = input.indexOf(',');
        commaPositions[1] = input.indexOf(',', commaPositions[0] + 1);
        commaPositions[2] = input.indexOf(',', commaPositions[1] + 1);
        commaPositions[3] = input.indexOf(',', commaPositions[2] + 1);

        // Check if we found all 4 commas
        if (commaPositions[3] != -1) {
            String devAddr = input.substring(0, commaPositions[0]);
            String fNwkSIntKey = input.substring(commaPositions[0] + 1, commaPositions[1]);
            String sNwkSIntKey = input.substring(commaPositions[1] + 1, commaPositions[2]);
            String nwkSEncKey = input.substring(commaPositions[2] + 1, commaPositions[3]);
            String appSKey = input.substring(commaPositions[3] + 1);

            // Store the keys in preferences
            preferences.putString("devAddr", devAddr);
            preferences.putString("fNwkSIntKey", fNwkSIntKey);
            preferences.putString("sNwkSIntKey", sNwkSIntKey);
            preferences.putString("nwkSEncKey", nwkSEncKey);
            preferences.putString("appSKey", appSKey);
            preferences.putBool("done", true);

            Serial.println("Provisioned");
            ESP.restart();
        }
    }

    if (provisioned) {
        delay(500); // Needed to allow time to open the serial port after flashing

        Serial.println("Provisioned");
        Serial.print("devAddr: "); Serial.println(preferences.getString("devAddr", ""));
        Serial.print("fNwkSIntKey: "); Serial.println(preferences.getString("fNwkSIntKey", ""));
        Serial.print("sNwkSIntKey: "); Serial.println(preferences.getString("sNwkSIntKey", ""));
        Serial.print("nwkSEncKey: "); Serial.println(preferences.getString("nwkSEncKey", ""));
        Serial.print("appSKey: "); Serial.println(preferences.getString("appSKey", ""));
    }
}
