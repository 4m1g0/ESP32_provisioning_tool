# ESP32 Provisioning tool

This is a script in python designed to flash multiple ESP32 in a consecutive sequence with the same firmware and also provision the necesary keys into the flash.

## Usage
python3 and esptools are needed to execute this script. It is recommended to run in a python virtual environment.

``` bash
pip install -r requirements
```

```
provision.py [-h] [--csv_file CSV_FILE] [--firmware FIRMWARE]

Flash and provision ESP32 devices in sequence

options:
  -h, --help           show this help message and exit
  --csv_file CSV_FILE  CSV file containing the keys (default: keys.csv)
  --firmware FIRMWARE  Firmware .bin file (default: firmware.bin)
```

Along with the firmware.bin this script provides the partition.bin and bootloader.bin used by default by platformio. In most cases theese files do not need to be modified.

When executing the script it will automatically detect connected ESP32 boards. If no board is connected it will wait until a new board is detected and start the flishing and provisioning process automátically.

When the provision is finished and verified the script waits until the device is disconnected from the computer and, if a new device es conected afterwards the process starts over automatcally.

The provisioning keys must be provided in a CSV file with this format:

``` csv
uuid_device1,ntwKey_device1,appKey_device1
uuid_device2,ntwKey_device2,appKey_device2
uuid_device3,ntwKey_device3,appKey_device3
...
```

Once a key is provisioned into a device it is marked on the csv file as "provisioned" to make sure the same key is never used twice. Moreover if the process fails at any time it can be restarted safely and no keys will be lost or reused.

## Provisioning firmware
The provided firmware must have a funcion at the start of the program that handles the provisioning process and waits for the keys listening to the serial port. 

An example if such a code is provided bellow, and also on the exampleFirmware folder a full example can be found.

``` c++
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
```
