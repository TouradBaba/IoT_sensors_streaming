import requests

mongodb_start_payload = {
    "mongodb_url": "mongodb://admin:admin12345@localhost:27017",
    "mongo_db": "sensor_data",
    "mongo_collection": "sensor_data",
}
mongodb_start_response = requests.post("http://localhost:5001/start_pipeline", json=mongodb_start_payload)
print("MongoDB Start:", mongodb_start_response.json())

mongodb_stop_response = requests.post("http://localhost:5001/stop_pipeline")
print("MongoDB Stop:", mongodb_stop_response.json())
