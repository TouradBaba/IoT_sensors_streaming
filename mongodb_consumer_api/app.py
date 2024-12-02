import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from confluent_kafka import Consumer, KafkaException, KafkaError
from pymongo import MongoClient
import json
import sys

# Initialize Flask app and SocketIO server
app = Flask(__name__)
socketio = SocketIO(app)

# Kafka configurations
KAFKA_BROKER = 'kafka:9092'  # Address of the Kafka broker
KAFKA_TOPIC = 'sensor-data-mongodb'  # Kafka topic name
KAFKA_GROUP_ID = 'sensor-group'  # Kafka consumer group ID

# Global variable to track the producer process
producer_process = None


# Function to start the Kafka producer
def run_producer():
    """
    Starts the Kafka producer process if it is not already running.

    If the producer is already running, it sends a log message indicating so.
    If there is an error while starting the producer, it sends an error log.
    """
    global producer_process
    try:
        # Check if the producer is already running
        if producer_process and producer_process.poll() is None:
            socketio.emit('log_message', {'log': "Producer is already running."})
            return

        # Run the producer using subprocess
        producer_process = subprocess.Popen([sys.executable, 'producer.py'])
        socketio.emit('log_message', {'log': "Producer started successfully."})
    except Exception as e:
        socketio.emit('log_message', {'log': f"Error running producer: {str(e)}"})


# Function to stop the Kafka producer
def stop_producer():
    """
    Stops the Kafka producer process if it is running.

    If the producer is not running, it sends a log message indicating so.
    """
    global producer_process
    if producer_process and producer_process.poll() is None:
        producer_process.terminate()  # Terminate the producer process
        producer_process.wait()  # Wait for the process to terminate
        socketio.emit('log_message', {'log': "Producer stopped successfully."})
    else:
        socketio.emit('log_message', {'log': "Producer is not running."})


# Kafka-MongoDB Consumer
def run_consumer(mongo_url, mongo_db_name, mongo_collection_name):
    """
    Kafka consumer that reads messages from a Kafka topic and writes the data to MongoDB.

    Parameters:
    - mongo_url (str): MongoDB connection URL.
    - mongo_db_name (str): Name of the MongoDB database.
    - mongo_collection_name (str): Name of the MongoDB collection.
    """
    # Create a Kafka consumer instance
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,  # Kafka broker address
        'group.id': KAFKA_GROUP_ID,  # Consumer group ID
        'auto.offset.reset': 'earliest'  # Start reading from the earliest message
    })
    consumer.subscribe([KAFKA_TOPIC])  # Subscribe to the Kafka topic

    try:
        # Connect to MongoDB
        client = MongoClient(mongo_url)
        db = client[mongo_db_name]
        collection = db[mongo_collection_name]
    except Exception as e:
        socketio.emit('log_message', {'log': f"MongoDB connection failed: {str(e)}"})
        return

    def process_kafka_message(msg):
        """
        Process and insert the Kafka message into MongoDB.

        Parameters:
        - msg (Message): The Kafka message received.
        """
        try:
            data = json.loads(msg.value().decode('utf-8'))  # Decode and parse the message
            socketio.emit('log_message', {'log': f"Received message: {data}"})

            # Validate that the data is a dictionary
            if not isinstance(data, dict):
                socketio.emit('log_message', {'log': "Invalid message structure. Skipping..."})
                return

            try:
                # Insert the data into the MongoDB collection
                collection.insert_one(data)
                socketio.emit('log_message', {'log': "Data written to MongoDB."})
            except Exception as e:
                socketio.emit('log_message', {'log': f"MongoDB insert failed: {str(e)}"})

        except Exception as e:
            socketio.emit('log_message', {'log': f"Error processing message: {e}"})

    socketio.emit('log_message', {'log': "Starting Kafka consumer..."})
    while True:
        msg = consumer.poll(1.0)  # Poll for new Kafka messages
        if msg is None:
            continue  # No message, continue polling

        if msg.error():  # Handle Kafka errors
            if msg.error().code() == KafkaError._PARTITION_EOF:
                socketio.emit('log_message', {'log': "End of partition reached."})
            else:
                raise KafkaException(msg.error())  # Raise exception for other errors
        else:
            process_kafka_message(msg)  # Process valid Kafka message

    consumer.close()  # Close the Kafka consumer
    client.close()  # Close the MongoDB client
    socketio.emit('log_message', {'log': "Consumer stopped and MongoDB connection closed."})


# Render the home page
@app.route('/')
def index():
    """
    Render the home page.
    """
    return render_template('index.html')


# Endpoint to start the pipeline
@app.route('/start_pipeline', methods=['POST'])
def start_pipeline():
    """
    Starts the data pipeline, including running the Kafka producer and starting the Kafka consumer.

    Receives MongoDB connection details in the request body and starts the consumer in the background.
    """
    data = request.json
    mongo_url = 'mongodb://admin:admin12345@mongodb:27017/'  # MongoDB URL
    mongo_db_name = data.get('mongo_db_name')  # MongoDB database name
    mongo_collection_name = data.get('mongo_collection_name')  # MongoDB collection name

    # Start the Kafka producer
    run_producer()

    # Start the Kafka consumer in the background
    socketio.start_background_task(run_consumer, mongo_url, mongo_db_name, mongo_collection_name)
    return jsonify({'status': 'Pipeline started'}), 200


# Endpoint to stop the pipeline
@app.route('/stop_pipeline', methods=['POST'])
def stop_pipeline():
    """
    Stops the data pipeline by terminating the Kafka producer and consumer.
    """
    stop_producer()  # Stop the producer
    socketio.emit('log_message', {'log': "Pipeline stopped."})
    return jsonify({'status': 'Pipeline stopped'}), 200


# Start the Flask app and SocketIO server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
