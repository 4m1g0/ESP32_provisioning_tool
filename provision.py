import csv
import time
import serial
import subprocess
import signal
import sys
from pathlib import Path
import serial.tools.list_ports

def wait_for_disconnect(port_name):
    while True:
        ports = [
            port for port in serial.tools.list_ports.comports()
            if any(keyword in port.description.lower() for keyword in ["usb", "uart", "cp210"])
        ]
        
        if not any(port.device == port_name for port in ports):
            print(f"Port {port_name} was disconnected.")
            break
        time.sleep(0.5)
    

def list_serial_ports():
    """Lists available serial ports that are likely ESP32 devices and allows user selection."""
    ports = [
        port for port in serial.tools.list_ports.comports()
        if any(keyword in port.description.lower() for keyword in ["usb", "uart", "cp210"])
    ]

    if not ports:
        return None
    
    if len(ports) == 1:
        return ports[0].device
    
    print("Available ESP32 serial ports:")
    for i, port in enumerate(ports):
        print(f"[{i}] {port.device} - {port.description}")
    
    while True:
        try:
            choice = int(input("Select a port by index: "))
            if 0 <= choice < len(ports):
                return ports[choice].device
        except ValueError:
            pass
        print("Invalid selection. Try again.")

    
    while True:
        try:
            choice = int(input("Select a port by index: "))
            if 0 <= choice < len(ports):
                return ports[choice].device
        except ValueError:
            pass
        print("Invalid selection. Try again.")

def flash_firmware(port, firmware):
    """Flashes the firmware to the ESP32 using esptool, with debug output and retry delay."""
    cmd = [
        "esptool.py", "--chip", "esp32", "--port", port, "--baud", "460800",
        "--before", "default_reset", "--after", "hard_reset", "write_flash", "-z",
        "--flash_mode", "dio", "--flash_freq", "40m", "--flash_size", "detect",
        "0x1000", "bootloader.bin",
        "0x8000", "partitions.bin",
        "0x10000", "firmware.bin"
    ]
    print("Executing command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Flashing output:")
    print(result.stdout)
    if result.returncode != 0:
        print("Flashing error:", result.stderr)
        time.sleep(5)  # Add delay before retrying
        return False
    return True

def wait_for_provisioning(ser, timeout=60):
    """Waits for the ESP32 to request provisioning."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = ser.readline().decode(errors='ignore').strip()
        print("Serial Output:", line)  # Debug output
        if "Provisioning" in line:
            return True
    return False

def send_keys(ser, keys):
    """Sends the encryption keys to the ESP32 via Serial."""
    keys_str = ",".join(keys) + "\r\n"  # Ensure proper line ending
    print("Sending keys:", keys_str.strip())
    
    ser.reset_input_buffer()  # Clear input buffer before sending
    time.sleep(0.5)  # Ensure ESP32 is ready to receive
    ser.write(keys_str.encode())
    ser.flush()
    ser.readline() # Remove trailing bytes from the buffer
    
    start_time = time.time()
    while time.time() - start_time < 30:  # Waits up to 30s
        line = ser.readline().decode(errors='ignore').strip()
        if len(line) > 0:
            print("Serial Output:", line)  # Debug output
        if "Provisioned" in line:
            return True
    return False

def update_csv(csv_file, row_index):
    """Marks a device as provisioned in the CSV file."""
    rows = []
    with open(csv_file, newline='') as f:
        reader = list(csv.reader(f))
        rows = reader
        rows[row_index].append("Provisioned")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def signal_handler(sig, frame):
    """Handles Ctrl+C gracefully."""
    print("\nProcess interrupted. Exiting gracefully...")
    sys.exit(0)

def main(csv_file, firmware):
    """Main process for flashing and provisioning multiple devices."""
    
    with open(csv_file, newline='') as f:
        reader = list(csv.reader(f))
    
    for i, row in enumerate(reader):
        if len(row) >= 4 and row[3] == "Provisioned":
            continue  # Already provisioned
        
        clave1, clave2, clave3 = row[:3]
        while True:
            port = list_serial_ports()
            if port == None:
                print("No port found, waiting for device...")
                while port == None:
                    port = list_serial_ports()
                    time.sleep(0.3) 
                    continue
            
            print(f"Flashing firmware on {port}...")
            if not flash_firmware(port, firmware):
                print("Retrying flashing...")
                continue
            
            print("Opening serial port...")
            try:
                with serial.Serial(port, 115200, timeout=10) as ser:
                    print("Waiting for provisioning...")
                    if not wait_for_provisioning(ser):
                        print("Provisioning request not detected. Retrying...")
                        continue
                    
                    print("Sending keys...")
                    if send_keys(ser, [clave1, clave2, clave3]):
                        print("Successfully provisioned.")
                        update_csv(csv_file, i)
                        print("Please disconnect disconnect the current device...")
                        wait_for_disconnect(port)
                        break
                    else:
                        print("Provisioning failed. Retrying...")
                        time.sleep(5)  # Delay before retrying
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                time.sleep(5)  # Delay before retrying

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Flash and provision ESP32 devices in sequence")
    parser.add_argument("--csv_file", default="keys.csv", help="CSV file containing the keys (default: keys.csv)")
    parser.add_argument("--firmware", default="firmware.bin", help="Firmware .bin file (default: firmware.bin)")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    
    main(args.csv_file, args.firmware)

