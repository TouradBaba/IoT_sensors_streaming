from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import websocket
import json
import threading

# Shared data for X axis of each sensor
x_data_accel = []
x_data_gyro = []
x_data_magnetic = []
x_data_gravity = []

# Time data for each sensor
time_data_accel = []
time_data_gyro = []
time_data_magnetic = []
time_data_gravity = []

# Colors for each axis (for graph visualization)
x_data_color_accel = "#d32f2f"  # Red for Accelerometer
x_data_color_gyro = "#7cb342"   # Green for Gyroscope
x_data_color_magnetic = "#0288d1"  # Blue for Magnetic Field
x_data_color_gravity = "#f57c00"  # Orange for Gravity

# Background color for plots
background_color = "#fafafa"  # Light grey background


class Sensor:
    """
    A class representing a sensor that connects to a WebSocket server and receives data.
    Handles connection, message reception, and storing sensor data.
    """

    def __init__(self, address, sensor_type, x_data_storage, time_data_storage):
        """
        Initializes the Sensor object with required connection details and data storage.

        Parameters:
            address (str): The WebSocket server address to connect to.
            sensor_type (str): The type of sensor.
            x_data_storage (list): A list to store the x-axis data for the sensor.
            time_data_storage (list): A list to store the time data for the sensor.
        """
        self.address = address
        self.sensor_type = sensor_type
        self.x_data_storage = x_data_storage
        self.time_data_storage = time_data_storage

    def on_message(self, ws, message):
        """
        Called each time a new message is received from the WebSocket server.
        This method extracts sensor values and timestamps and appends them to the respective data storage.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection object.
            message (str): The message received from the WebSocket, typically in JSON format.
        """
        values = json.loads(message)['values']
        timestamp = json.loads(message)['timestamp']

        # Only append x-axis data
        self.x_data_storage.append(values[0])
        # Append to time_data only after updating x_data_storage
        self.time_data_storage.append(float(timestamp / 1000000))

    @staticmethod
    def on_error(ws, error):
        """
        Handles errors during WebSocket connection.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection object.
            error (str): The error message.
        """
        print("Error occurred")
        print(error)

    @staticmethod
    def on_close(ws, close_code, reason):
        """
        Handles the WebSocket closure.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection object.
            close_code (int): The WebSocket close code.
            reason (str): The reason for the closure.
        """
        print("Connection closed")
        print("Close code:", close_code)
        print("Reason:", reason)

    def on_open(self, ws):
        """
        Called when a WebSocket connection is successfully established.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection object.
        """
        print(f"Connected to: {self.address}")

    def make_websocket_connection(self):
        """
        Establishes the WebSocket connection and starts receiving data.
        This method is called in a separate thread to avoid blocking the main thread.
        """
        ws = websocket.WebSocketApp(f"ws://{self.address}/sensor/connect?type={self.sensor_type}",
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        # Blocking call to listen for messages
        ws.run_forever()

    def connect(self):
        """
        Starts a separate thread to connect to the WebSocket server and receive data.
        This allows for asynchronous communication without blocking the UI.
        """
        thread = threading.Thread(target=self.make_websocket_connection)
        thread.start()


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window of the application, which contains the UI and plots for visualizing sensor data.
    This class is responsible for managing the layout and updating the sensor plots.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the main window, sets up the UI, and starts the timer for updating plots.

        Parameters:
            *args, **kwargs: Arguments passed to the parent class (QtWidgets.QMainWindow).
        """
        super(MainWindow, self).__init__(*args, **kwargs)

        # Set up the plot widgets
        self.graphWidget1 = pg.PlotWidget()
        self.graphWidget2 = pg.PlotWidget()
        self.graphWidget3 = pg.PlotWidget()
        self.graphWidget4 = pg.PlotWidget()

        # Layout setup to display plots in a grid format
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.graphWidget1, 0, 0)
        layout.addWidget(self.graphWidget2, 0, 1)
        layout.addWidget(self.graphWidget3, 1, 0)
        layout.addWidget(self.graphWidget4, 1, 1)

        # Central widget setup
        central_widget = QtWidgets.QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set background color for each graph widget
        self.graphWidget1.setBackground(background_color)
        self.graphWidget2.setBackground(background_color)
        self.graphWidget3.setBackground(background_color)
        self.graphWidget4.setBackground(background_color)

        # Set titles for each graph
        self.graphWidget1.setTitle("Accelerometer X", color="#8d6e63", size="20pt")
        self.graphWidget2.setTitle("Gyroscope X", color="#8d6e63", size="20pt")
        self.graphWidget3.setTitle("Magnetic Field X", color="#8d6e63", size="20pt")
        self.graphWidget4.setTitle("Gravity X", color="#8d6e63", size="20pt")

        # Add labels to axes for each plot
        styles = {"color": "#f00", "font-size": "15px"}
        self.graphWidget1.setLabel("left", "m/s^2", **styles)
        self.graphWidget1.setLabel("bottom", "Time (milliseconds)", **styles)

        self.graphWidget2.setLabel("left", "m/s^2", **styles)
        self.graphWidget2.setLabel("bottom", "Time (milliseconds)", **styles)

        self.graphWidget3.setLabel("left", "m/s^2", **styles)
        self.graphWidget3.setLabel("bottom", "Time (milliseconds)", **styles)

        self.graphWidget4.setLabel("left", "m/s^2", **styles)
        self.graphWidget4.setLabel("bottom", "Time (milliseconds)", **styles)

        # Initialize the plots with empty data
        self.x_data_line_accel = self.graphWidget1.plot([], [], name="Accelerometer X", pen=pg.mkPen(color=x_data_color_accel))
        self.x_data_line_gyro = self.graphWidget2.plot([], [], name="Gyroscope X", pen=pg.mkPen(color=x_data_color_gyro))
        self.x_data_line_magnetic = self.graphWidget3.plot([], [], name="Magnetic X", pen=pg.mkPen(color=x_data_color_magnetic))
        self.x_data_line_gravity = self.graphWidget4.plot([], [], name="Gravity X", pen=pg.mkPen(color=x_data_color_gravity))

        # Set up a timer to update the plot every 50 milliseconds
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        """
        Updates the sensor plots with the latest data. Limits the data to the most recent 1000 values.

        This method ensures that the plot updates by only displaying a fixed number of data points.
        """
        limit = -1000  # Limit data to the latest 1000 points

        data_sources = [
            (time_data_accel, x_data_accel, self.x_data_line_accel),
            (time_data_gyro, x_data_gyro, self.x_data_line_gyro),
            (time_data_magnetic, x_data_magnetic, self.x_data_line_magnetic),
            (time_data_gravity, x_data_gravity, self.x_data_line_gravity)
        ]

        for time_data, x_data, line in data_sources:
            if len(time_data) > 0 and len(x_data) > 0:
                # Update the data for each sensor plot
                line.setData(time_data[limit:], x_data[limit:])


# Create and connect sensors
accelerometer_sensor = Sensor(address="192.168.100.3:8080", sensor_type="android.sensor.accelerometer", x_data_storage=x_data_accel, time_data_storage=time_data_accel)
gyroscope_sensor = Sensor(address="192.168.100.3:8080", sensor_type="android.sensor.gyroscope", x_data_storage=x_data_gyro, time_data_storage=time_data_gyro)
magnetic_field_sensor = Sensor(address="192.168.100.3:8080", sensor_type="android.sensor.magnetic_field", x_data_storage=x_data_magnetic, time_data_storage=time_data_magnetic)
gravity_sensor = Sensor(address="192.168.100.3:8080", sensor_type="android.sensor.gravity", x_data_storage=x_data_gravity, time_data_storage=time_data_gravity)

# Connect sensors asynchronously
accelerometer_sensor.connect()
gyroscope_sensor.connect()
magnetic_field_sensor.connect()
gravity_sensor.connect()

# Initialize the PyQt5 application
app = QtWidgets.QApplication(sys.argv)

# Initialize and show the main window
window = MainWindow()
window.show()

# Run the application's event loop
sys.exit(app.exec_())
