from confluent_kafka import Producer
import websocket
import json
import threading

# Kafka Producer setup
producer = Producer({'bootstrap.servers': 'kafka:9092'})


# Callback for message delivery status
def delivery_report(err, msg):
    """
    Callback function to handle the delivery report of the message sent to Kafka.

    This function is triggered when a message is delivered successfully or fails.

    Parameters:
    err (KafkaError): Error object if message delivery failed.
    msg (Message): The Kafka message being delivered.
    """
    if err is not None:
        print('Message delivery failed: %s' % err)
    else:
        print('Message delivered to %s [%d]' % (msg.topic(), msg.partition()))


# Callback function when message is received from WebSocket
def on_message(ws, message):
    """
    Callback function that is triggered when a message is received from the WebSocket.

    This function processes the received data, formats it, and sends it to Kafka.

    Parameters:
    ws (WebSocketApp): The WebSocket object that received the message.
    message (str): The message received from the WebSocket server.
    """
    data = json.loads(message)  # Parse the message into a JSON object
    values = data['values']  # Extract the sensor data values

    if len(values) == 3:
        # 3 values expected: x, y, z
        x = values[0]
        y = values[1]
        z = values[2]
        sensor_type = ws.url.split('=')[1]  # Extract the sensor type from the URL

        # Create the message to send to Kafka
        message = {
            'sensor_type': sensor_type,
            'x': x,
            'y': y,
            'z': z
        }

        # Produce the message to Kafka
        producer.produce('sensor-data-mongodb', key=sensor_type, value=json.dumps(message), callback=delivery_report)
        producer.flush()  # Ensure the message is sent immediately
    else:
        # If the data format is incorrect, print a warning message
        print(f"Unexpected data format from sensor {ws.url}")


def on_error(ws, error):
    """
    Callback function to handle errors with the WebSocket connection.

    Parameters:
    ws (WebSocketApp): The WebSocket object that encountered the error.
    error (str): The error message encountered during the WebSocket operation.
    """
    print(f"Error occurred with {ws.url}: {error}")


def on_close(ws, reason):
    """
    Callback function to handle the closure of a WebSocket connection.

    Parameters:
    ws (WebSocketApp): The WebSocket object that was closed.
    reason (str): The reason for the WebSocket connection closure.
    """
    print(f"Connection closed for {ws.url}: {reason}")


def on_open(ws):
    """
    Callback function to handle the successful opening of a WebSocket connection.

    Parameters:
    ws (WebSocketApp): The WebSocket object that was opened.
    """
    print(f"Connected to WebSocket server for {ws.url}")


# Function to connect to a WebSocket server for given sensors
def connect_to_sensor_server(sensor_url):
    """
    Establishes a WebSocket connection to a sensor server and processes incoming messages.

    Parameters:
    sensor_url (str): The WebSocket URL for the sensor data server.
    """
    ws = websocket.WebSocketApp(sensor_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()  # Run the WebSocket connection indefinitely


# List of sensor WebSocket URLs to connect to
sensor_urls = [
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.accelerometer",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.gyroscope",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.magnetic_field",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.gravity"
]

# List to hold threads for each WebSocket connection
threads = []
for sensor_url in sensor_urls:
    # Create and start a new thread for each sensor connection
    thread = threading.Thread(target=connect_to_sensor_server, args=(sensor_url,))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()
