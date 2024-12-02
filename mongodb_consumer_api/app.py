import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from confluent_kafka import Consumer, KafkaException, KafkaError
from pymongo import MongoClient
import json
import sys

app = Flask(__name__)
socketio = SocketIO(app)

# Kafka configurations
KAFKA_BROKER = 'kafka:9092'
KAFKA_TOPIC = 'sensor-data-mongodb'
KAFKA_GROUP_ID = 'sensor-group'

# Global variable to track the producer process
producer_process = None


# Function to start the producer
def run_producer():
    global producer_process
    try:
        if producer_process and producer_process.poll() is None:
            socketio.emit('log_message', {'log': "Producer is already running."})
            return

        # Run the producer using subprocess
        producer_process = subprocess.Popen([sys.executable, 'producer.py'])
        socketio.emit('log_message', {'log': "Producer started successfully."})
    except Exception as e:
        socketio.emit('log_message', {'log': f"Error running producer: {str(e)}"})


# Function to stop the producer
def stop_producer():
    global producer_process
    if producer_process and producer_process.poll() is None:
        producer_process.terminate()
        producer_process.wait()
        socketio.emit('log_message', {'log': "Producer stopped successfully."})
    else:
        socketio.emit('log_message', {'log': "Producer is not running."})


# Kafka-MongoDB Consumer
def run_consumer(mongo_url, mongo_db_name, mongo_collection_name):
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([KAFKA_TOPIC])

    try:
        client = MongoClient(mongo_url)
        db = client[mongo_db_name]
        collection = db[mongo_collection_name]
    except Exception as e:
        socketio.emit('log_message', {'log': f"MongoDB connection failed: {str(e)}"})
        return

    def process_kafka_message(msg):
        try:
            data = json.loads(msg.value().decode('utf-8'))
            socketio.emit('log_message', {'log': f"Received message: {data}"})

            if not isinstance(data, dict):
                socketio.emit('log_message', {'log': "Invalid message structure. Skipping..."})
                return

            try:
                collection.insert_one(data)
                socketio.emit('log_message', {'log': "Data written to MongoDB."})
            except Exception as e:
                socketio.emit('log_message', {'log': f"MongoDB insert failed: {str(e)}"})

        except Exception as e:
            socketio.emit('log_message', {'log': f"Error processing message: {e}"})

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

    consumer.close()
    client.close()
    socketio.emit('log_message', {'log': "Consumer stopped and MongoDB connection closed."})


# Render the home page
@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to start the pipeline
@app.route('/start_pipeline', methods=['POST'])
def start_pipeline():
    data = request.json
    mongo_url = 'mongodb://admin:admin12345@mongodb:27017/'
    mongo_db_name = data.get('mongo_db_name')
    mongo_collection_name = data.get('mongo_collection_name')

    run_producer()
    socketio.start_background_task(run_consumer, mongo_url, mongo_db_name, mongo_collection_name)
    return jsonify({'status': 'Pipeline started'}), 200


# Endpoint to stop the pipeline
@app.route('/stop_pipeline', methods=['POST'])
def stop_pipeline():
    stop_producer()
    socketio.emit('log_message', {'log': "Pipeline stopped."})
    return jsonify({'status': 'Pipeline stopped'}), 200


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
