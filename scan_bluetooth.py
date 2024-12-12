import asyncio
import json
from bleak import BleakScanner, BleakClient
import time

# Define the device name and MAC address you are looking for
TARGET_DEVICE_NAME = "ESP32_S3_Bluetooth"  # Replace with the target device's name
TARGET_MAC_ADDRESS = "f0:9e:9e:22:7b:01"  # Replace with the target device's MAC address

# Define the characteristic UUID for receiving data from the device
# You need to replace this with the actual characteristic UUID
TARGET_CHARACTERISTIC_UUID = "87654321-4321-4321-4321-210987654321"

async def scan():
    """ Scan for BLE devices and try to connect to the target device. """
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10)  # Scan for 10 seconds

    # Check if the target device is found
    for device in devices:
        if device.name == TARGET_DEVICE_NAME or device.address == TARGET_MAC_ADDRESS:
            print(f"Device found: {device.name} - {device.address}")
            # Attempt to pair with the device
            try:
                async with BleakClient(device.address) as client:
                    print("Device found successfully and connected.")
                    await receive_data(client)  # Start receiving data once connected
            except Exception as e:
                print(f"Error pairing with device: {e}")
            return

    print("Device not found within 10 seconds")
    await reconnect()

async def receive_data(client):
    """ Continuously receive and process data from the device. """
    while True:
        try:
            # Read the data from the device's characteristic
            data = await client.read_gatt_char(TARGET_CHARACTERISTIC_UUID)

            # Convert the data to a string and parse it as JSON
            json_data = data.decode("utf-8")
            parsed_data = json.loads(json_data)

            # Print the received data
            print("Received data:", parsed_data)

            #await asyncio.sleep(1)  # Delay to avoid overloading with continuous requests

        except Exception as e:
            print(f"Error receiving data: {e}")
            print("Attempting to reconnect...")
            await reconnect()

async def reconnect():
    """ Reconnect the device if disconnected. """
    while True:
        print("Reconnecting to the device...")
        await scan()  # Restart the scan and attempt to reconnect

# Run the scan asynchronously
asyncio.run(scan())
