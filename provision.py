import csv
import time
import serial
import subprocess
import signal
import sys
from pathlib import Path
import serial.tools.list_ports

def erase_flash(port):
    cmd = [
        "esptool.py", "--chip", "esp32", "--port", port, "erase_flash"
    ]
    print("Executing command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Output:")
    print(result.stdout)

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

def flash_firmware(port, firmware, chip):
    cmd = [
        "esptool.py", "--chip", chip, "--port", port, "--baud", "460800",
        "--before", "default_reset", "--after", "hard_reset", "write_flash", "-z",
        "--flash_mode", "dio", "--flash_freq", "40m", "--flash_size", "detect",
        "0x1000", "bootloader.bin",
        "0x8000", "partitions.bin",
        "0x10000", firmware
    ]
    print("Executing command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Flashing output:")
    print(result.stdout)
    if result.returncode != 0:
        print("Flashing error:", result.stderr)
        time.sleep(5)
        return False
    return True

def wait_for_provisioning(ser, port):
    start_time = time.time()
    while time.time() - start_time < 60:
        line = ser.readline().decode(errors='ignore').strip()
        print("Serial Output:", line)
        if "Provisioning" in line:
            return True
        if "Provisioned" in line:
            choice = input("Device already provisioned. Erase flash and restart? (y/n): ")
            if choice.lower() == 'y':
                erase_flash(port)
                return False
    return False

def send_keys(ser, keys):
    keys_str = ",".join(keys) + "\r\n"
    print("Sending keys:", keys_str.strip())
    
    ser.reset_input_buffer()
    time.sleep(0.5)
    ser.write(keys_str.encode())
    ser.flush()
    ser.readline()
    
    start_time = time.time()
    while time.time() - start_time < 30:
        line = ser.readline().decode(errors='ignore').strip()
        if len(line) > 0:
            print("Serial Output:", line)
        if "Provisioned" in line:
            return True
    return False

def update_csv(csv_file, row_index):
    rows = []
    with open(csv_file, newline='') as f:
        reader = list(csv.reader(f))
        rows = reader
        rows[row_index].append("Provisioned")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def signal_handler(sig, frame):
    print("\nProcess interrupted. Exiting gracefully...")
    sys.exit(0)

def main(csv_file, firmware, chip):
    with open(csv_file, newline='') as f:
        reader = list(csv.reader(f))
    
    for i, row in enumerate(reader):
        if row[-1] == "Provisioned":
            continue
        
        claves = row if "Provisioned" not in row else row[:-1]
        
        while True:
            port = list_serial_ports()
            if port is None:
                print("No port found, waiting for device...")
                while port is None:
                    port = list_serial_ports()
                    time.sleep(0.3)
                    continue
            
            print(f"Flashing firmware on {port}...")
            if not flash_firmware(port, firmware, chip):
                print("Retrying flashing...")
                continue
            
            print("Opening serial port...")
            try:
                with serial.Serial(port, 115200, timeout=10) as ser:
                    print("Waiting for provisioning...")
                    if not wait_for_provisioning(ser, port):
                        print("Restarting process...")
                        continue
                    
                    print("Sending keys...")
                    if send_keys(ser, claves):
                        print("Successfully provisioned.")
                        update_csv(csv_file, i)
                        print("Please disconnect the current device...")
                        wait_for_disconnect(port)
                        break
                    else:
                        print("Provisioning failed. Retrying...")
                        time.sleep(5)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Flash and provision ESP32 devices in sequence")
    parser.add_argument("--csv_file", default="keys.csv", help="CSV file containing the keys (default: keys.csv)")
    parser.add_argument("--firmware", default="firmware.bin", help="Firmware .bin file (default: firmware.bin)")
    parser.add_argument("--chip", default="esp32s3", help="type of esp32 chip (default: esp32s3) Options: esp32, esp32s3")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    main(args.csv_file, args.firmware, args.chip)

