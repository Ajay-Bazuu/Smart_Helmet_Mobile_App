# File: main.py
import asyncio
import json
from bleak import BleakScanner, BleakClient
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from threading import Thread

# Set the window size
Window.size = (400, 600)

# Define the device name and MAC address you are looking for
TARGET_DEVICE_NAME = "ESP32_S3_Bluetooth"  # Replace with the target device's name
TARGET_MAC_ADDRESS = "f0:9e:9e:22:7b:01"  # Replace with the target device's MAC address

# Define the characteristic UUID for receiving data from the device
TARGET_CHARACTERISTIC_UUID = "87654321-4321-4321-4321-210987654321"

class BLEApp(App):
    """ Main Kivy Application """

    def build(self):
        """ Set up the UI layout. """
        self.layout = FloatLayout()  # Use FloatLayout for free positioning
        
        # Initialize log messages storage and max size
        self.log_messages = []
        self.max_messages = 3
        
        # Create a label for logging system messages
        self.log_label = Label(
            text="Starting BLE scan...",
            font_size=24,
            halign="center",
            valign="middle"
        )
        self.log_label.bind(size=self.log_label.setter('text_size'))  # Ensures text wraps inside the Label
        self.layout.add_widget(self.log_label)
        
        # Create a button to start the scanning process
        self.start_button = Button(
            text="Start Scan",
            font_size=24,
            size_hint=(None, None),  # Explicit size hint
            size=(350, 60),  # Fixed width and height for the button
            pos_hint={"center_x": 0.5, "center_y": 0.1}  # Position the button below the label
        )
        
        self.start_button.bind(on_press=self.start_ble_scan)  # Bind the button press to start scanning
        
        # Add the widgets to the layout
        self.layout.add_widget(self.start_button)
        
        return self.layout

    def log_message(self, message):
        """ Log and manage a limited number of messages. """
        # Append the new message
        self.log_messages.append(message)

        # Trim the list to the maximum allowed messages
        if len(self.log_messages) > self.max_messages:
            self.log_messages.pop(0)

        # Combine messages and update the log label
        combined_messages = "\n".join(self.log_messages)
        self.update_log_label(combined_messages)

    def update_log_label(self, combined_messages):
        """ Update the log label with the combined messages. """
        self.log_label.text = combined_messages

    def update_data_label(self, data):
        """ Update the data label to display the latest received data. """
        Clock.schedule_once(lambda dt: self.data_label_update(data), 0)

    def data_label_update(self, data):
        """ Replace the current data label with the new data. """
        self.data_label.text = f"Received data: {data}"

    def start_ble_scan(self, instance):
        """ Start the BLE scanning process when the button is pressed. """
        # Remove the start button
        self.layout.remove_widget(self.start_button)
        
        # Create a "Stop" button to reset the app
        self.stop_button = Button(
            text="Stop",
            font_size=24,
            size_hint=(None, None),  # Explicit size hint
            size=(350, 60),  # Fixed width and height for the button
            pos_hint={"center_x": 0.5, "center_y": 0.1}  # Position the button below the label
        )
        self.stop_button.bind(on_press=self.reset_app)  # Bind to reset_app method
        self.layout.add_widget(self.stop_button)
        
        # Create a label to show the latest data received (dynamic content)
        self.data_label = Label(
            text="Received data: None",
            font_size=20,
            halign="left",
            valign="top"
        )
        self.data_label.bind(size=self.data_label.setter('text_size'))  # Ensures text wraps inside the Label
        self.layout.add_widget(self.data_label)
        
        # Start BLE scanning in a background thread
        thread = Thread(target=lambda: asyncio.run(self.scan()))
        thread.daemon = True  # Daemon thread will stop when the app exits
        thread.start()

    def reset_app(self, instance):
        """ Reset the app to its initial state. """
        # Clear the layout
        self.layout.clear_widgets()
        
        # Reinitialize log messages
        self.log_messages = []
        
        # Add the initial log label
        self.log_label = Label(
            text="Starting BLE scan...",
            font_size=24,
            halign="center",
            valign="middle"
        )
        self.log_label.bind(size=self.log_label.setter('text_size'))  # Ensures text wraps inside the Label
        self.layout.add_widget(self.log_label)
        
        # Add the "Start Scan" button back
        self.start_button = Button(
            text="Start Scan",
            font_size=24,
            size_hint=(None, None),  # Explicit size hint
            size=(350, 60),  # Fixed width and height for the button
            pos_hint={"center_x": 0.5, "center_y": 0.1}  # Position the button below the label
        )
        self.start_button.bind(on_press=self.start_ble_scan)  # Bind the button press to start scanning
        self.layout.add_widget(self.start_button)

    async def scan(self):
        """ Scan for BLE devices and try to connect to the target device. """
        self.log_message("Scanning for BLE devices...")
        devices = await BleakScanner.discover(timeout=10)  # Scan for 10 seconds

        for device in devices:
            if device.name == TARGET_DEVICE_NAME or device.address == TARGET_MAC_ADDRESS:
                self.log_message(f"Device found: {device.name} - {device.address}")
                
                try:
                    async with BleakClient(device.address) as client:
                        self.log_message("Device found successfully and connected.")
                        await self.receive_data(client)  # Start receiving data once connected
                except Exception as e:
                    self.log_message(f"Error pairing with device: {e}")
                return

        self.log_message("Device not found Retrying...")
        await self.reconnect()

    async def receive_data(self, client):
        """ Continuously receive and process data from the device. """
        while True:
            try:
                # Read the data from the device's characteristic
                data = await client.read_gatt_char(TARGET_CHARACTERISTIC_UUID)
                
                # Convert the data to a string and parse it as JSON
                json_data = data.decode("utf-8")
                parsed_data = json.loads(json_data)

                # Display the received data (overwrites the previous data)
                self.update_data_label(parsed_data)

            except Exception as e:
                self.log_message(f"Error receiving data: {e}")
                self.log_message("Attempting to reconnect...")
                await self.reconnect()

    async def reconnect(self):
        """ Reconnect the device if disconnected. """
        while True:
            self.log_message("Reconnecting to the device...")
            await self.scan()

# Run the Kivy app
if __name__ == "__main__":
    BLEApp().run()
