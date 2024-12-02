import requests

# Define payload for starting the MongoDB pipeline
mongodb_start_payload = {
    "mongodb_url": "mongodb://admin:admin12345@localhost:27017",  # URL for the MongoDB instance, including authentication
    "mongo_db": "sensor_data",                                      # The name of the MongoDB database to store the data
    "mongo_collection": "sensor_data",                               # The collection within the database where the data will be stored
}

# Send a POST request to start the MongoDB pipeline with the defined payload
mongodb_start_response = requests.post("http://localhost:5001/start_pipeline", json=mongodb_start_payload)

# Print the response from the start request, which should confirm the pipeline start status
print("MongoDB Start:", mongodb_start_response.json())

# Send a POST request to stop the MongoDB pipeline
mongodb_stop_response = requests.post("http://localhost:5001/stop_pipeline")

# Print the response from the stop request, which should confirm the pipeline stop status
print("MongoDB Stop:", mongodb_stop_response.json())
