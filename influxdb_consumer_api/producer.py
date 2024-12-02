from confluent_kafka import Producer
import websocket
import json
import threading

# Kafka Producer setup
producer = Producer({'bootstrap.servers': 'kafka:9092'})


# Callback for message delivery status
def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: %s' % err)
    else:
        print('Message delivered to %s [%d]' % (msg.topic(), msg.partition()))


# Callback function when message is received
def on_message(ws, message):
    data = json.loads(message)
    values = data['values']

    if len(values) == 3:
        x = values[0]
        y = values[1]
        z = values[2]
        sensor_type = ws.url.split('=')[1]
        message = {
            'sensor_type': sensor_type,
            'x': x,
            'y': y,
            'z': z
        }
        producer.produce('sensor-data-influxdb', key=sensor_type, value=json.dumps(message), callback=delivery_report)
        producer.flush()
    else:
        print(f"Unexpected data format from sensor {ws.url}")


def on_error(ws, error):
    print(f"Error occurred with {ws.url}: {error}")


def on_close(ws, reason):
    print(f"Connection closed for {ws.url}: {reason}")


def on_open(ws):
    print(f"Connected to WebSocket server for {ws.url}")


# Function to connect to a WebSocket server for given sensors
def connect_to_sensor_server(sensor_url):
    ws = websocket.WebSocketApp(sensor_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

sensor_urls = [
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.accelerometer",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.gyroscope",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.magnetic_field",
    "ws://192.168.100.3:8080/sensor/connect?type=android.sensor.gravity"
]

threads = []
for sensor_url in sensor_urls:
    thread = threading.Thread(target=connect_to_sensor_server, args=(sensor_url,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
