#include <Arduino.h>
#include <Preferences.h>

uint32_t devAddr  =   0x0000000000000000;
uint8_t fNwkSIntKey[16]; 
uint8_t sNwkSIntKey[16]; 
uint8_t nwkSEncKey[16]; 
uint8_t appSKey[16]; 

Preferences preferences;
void provisioning();

void setup() {
    provisioning();
}

void loop() {
    
    Serial.print("fNwkSIntKey en bytes: ");
    for (size_t i = 0; i < 16; i++) {
        Serial.print("0x");
        if (fNwkSIntKey[i] < 0x10) Serial.print("0");  // Asegurar formato 0x0X
        Serial.print(fNwkSIntKey[i], HEX);
        Serial.print(" ");
    }
    Serial.println();

    Serial.print("sNwkSIntKey en bytes: ");
    for (size_t i = 0; i < 16; i++) {
        Serial.print("0x");
        if (sNwkSIntKey[i] < 0x10) Serial.print("0");  // Asegurar formato 0x0X
        Serial.print(sNwkSIntKey[i], HEX);
        Serial.print(" ");
    }
    Serial.println();

    Serial.print("nwkSEncKey en bytes: ");
    for (size_t i = 0; i < 16; i++) {
        Serial.print("0x");
        if (nwkSEncKey[i] < 0x10) Serial.print("0");  // Asegurar formato 0x0X
        Serial.print(nwkSEncKey[i], HEX);
        Serial.print(" ");
    }
    Serial.println();

    Serial.print("appSKey en bytes: ");
    for (size_t i = 0; i < 16; i++) {
        Serial.print("0x");
        if (appSKey[i] < 0x10) Serial.print("0");  // Asegurar formato 0x0X
        Serial.print(appSKey[i], HEX);
        Serial.print(" ");
    }
    Serial.println();


    Serial.print("devAddr en bytes: ");
    Serial.println(devAddr, HEX);

    delay(3000);
}








void hexStringToByteArray(String hexString, uint8_t *byteArray, size_t byteArraySize) {
    for (size_t i = 0; i < byteArraySize; i++) {
        byteArray[i] = strtoul(hexString.substring(i * 2, i * 2 + 2).c_str(), nullptr, 16);
    }
}

uint32_t hexStringToUint32(String hexString) {
    uint32_t value = 0;
    for (size_t i = 0; i < 4; i++) {  // 4 bytes en un uint32_t
        value <<= 8;  // Desplazar 8 bits a la izquierda
        value |= strtoul(hexString.substring(i * 2, i * 2 + 2).c_str(), nullptr, 16);
    }
    return value;
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

        hexStringToByteArray(preferences.getString("fNwkSIntKey", ""), fNwkSIntKey, 16);
        hexStringToByteArray(preferences.getString("sNwkSIntKey", ""), sNwkSIntKey, 16);
        hexStringToByteArray(preferences.getString("nwkSEncKey", ""), nwkSEncKey, 16);
        hexStringToByteArray(preferences.getString("appSKey", ""), appSKey, 16);
        devAddr = hexStringToUint32(preferences.getString("devAddr", ""));
    }
}
