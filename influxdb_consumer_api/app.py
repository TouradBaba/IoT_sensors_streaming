import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from confluent_kafka import Consumer, KafkaException, KafkaError
from influxdb_client import InfluxDBClient, Point
import json
import sys

# Initialize Flask application and SocketIO server
app = Flask(__name__)
socketio = SocketIO(app)

# Kafka configurations
KAFKA_BROKER = 'kafka:9092'  # Kafka broker URL
KAFKA_TOPIC = 'sensor-data-influxdb'  # Kafka topic to consume sensor data from
KAFKA_GROUP_ID = 'sensor-group'  # Kafka consumer group ID

# Global variable to track the producer process
producer_process = None


# Function to start the producer
def run_producer():
    """
    Starts the producer process using subprocess.
    This function checks if the producer is already running, and if so, it prevents multiple instances.
    It sends a log message to the frontend through SocketIO indicating whether the producer was started successfully or failed.
    """
    global producer_process
    try:
        if producer_process and producer_process.poll() is None:
            socketio.emit('log_message', {'log': "Producer is already running."})
            return

        # Run the producer script as a subprocess
        producer_process = subprocess.Popen([sys.executable, 'producer.py'])
        socketio.emit('log_message', {'log': "Producer started successfully."})
    except Exception as e:
        socketio.emit('log_message', {'log': f"Error running producer: {str(e)}"})


# Function to stop the producer
def stop_producer():
    """
    Stops the producer process if it is running.
    It terminates the process and waits for it to finish, then sends a log message to the frontend.
    """
    global producer_process
    if producer_process and producer_process.poll() is None:
        producer_process.terminate()
        producer_process.wait()
        socketio.emit('log_message', {'log': "Producer stopped successfully."})
    else:
        socketio.emit('log_message', {'log': "Producer is not running."})


# Kafka-InfluxDB Consumer function
def run_consumer(influx_url, influx_token, influx_org, influx_bucket):
    """
    This function connects to Kafka as a consumer, subscribes to the sensor data topic,
    processes messages received from Kafka, and writes them to InfluxDB.
    It runs in the background and continues consuming and processing messages until stopped.

    Parameters:
    influx_url (str): URL of the InfluxDB instance
    influx_token (str): InfluxDB authentication token
    influx_org (str): InfluxDB organization name
    influx_bucket (str): InfluxDB bucket to write the data into
    """
    # Initialize Kafka Consumer
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([KAFKA_TOPIC])

    # Initialize InfluxDB Client
    client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
    write_api = client.write_api()

    def process_kafka_message(msg):
        """
        Processes the Kafka message by extracting sensor data, checking for its validity,
        and writing it to InfluxDB. Sends logs for every important event.

        Parameters:
        msg (Kafka message): The message consumed from Kafka
        """
        try:
            data = json.loads(msg.value().decode('utf-8'))
            socketio.emit('log_message', {'log': f"Received message: {data}"})
            sensor_type = data.get('sensor_type')
            x, y, z = data.get('x'), data.get('y'), data.get('z')

            # Check if required data is missing
            if None in [sensor_type, x, y, z]:
                socketio.emit('log_message', {'log': "Invalid message structure. Skipping..."})
                return

            # Create InfluxDB point and write data
            point = Point("sensor_data").tag("sensor_type", sensor_type).field("x", x).field("y", y).field("z", z)
            write_api.write(bucket=influx_bucket, org=influx_org, record=point)
            socketio.emit('log_message', {'log': "Data written to InfluxDB."})
        except Exception as e:
            socketio.emit('log_message', {'log': f"Error processing message: {e}"})

    try:
        socketio.emit('log_message', {'log': "Starting Kafka consumer..."})
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    socketio.emit('log_message', {'log': "End of partition reached."})
                else:
                    raise KafkaException(msg.error())
            else:
                process_kafka_message(msg)
    finally:
        consumer.close()
        client.close()
        socketio.emit('log_message', {'log': "Consumer stopped and InfluxDB connection closed."})


# Render the home page
@app.route('/')
def index():
    """
    Renders the home page (index.html) of the application.
    """
    return render_template('index.html')


# Endpoint to start the pipeline
@app.route('/start_pipeline', methods=['POST'])
def start_pipeline():
    """
    Starts the entire pipeline by first running the producer and then starting the Kafka consumer in the background.
    The function expects the InfluxDB connection details in the request body.

    Expected JSON request body:
    {
        "influx_token": "influxdb_token",
        "influx_org": "influxdb_org",
        "influx_bucket": "influxdb_bucket"
    }

    Returns:
    - JSON response indicating the pipeline start status.
    """
    data = request.json
    influx_url = 'http://influxdb:8086'
    influx_token = data.get('influx_token')
    influx_org = data.get('influx_org')
    influx_bucket = data.get('influx_bucket')

    # Validate request data
    if not all([influx_url, influx_token, influx_org, influx_bucket]):
        return jsonify({'error': 'All fields are required'}), 400

    # Start the producer and consumer
    run_producer()
    socketio.start_background_task(run_consumer, influx_url, influx_token, influx_org, influx_bucket)
    return jsonify({'status': 'Pipeline started'}), 200


# Endpoint to stop the pipeline
@app.route('/stop_pipeline', methods=['POST'])
def stop_pipeline():
    """
    Stops the entire pipeline by stopping the producer process and sending a log message.

    Returns:
    - JSON response indicating the pipeline stop status.
    """
    stop_producer()
    socketio.emit('log_message', {'log': "Pipeline stopped."})
    return jsonify({'status': 'Pipeline stopped'}), 200


# Start the Flask app and SocketIO server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
