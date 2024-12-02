import requests

# Define payload for starting the InfluxDB pipeline
influxdb_start_payload = {
    "influx_url": "http://influxdb:8086",  # URL for the InfluxDB instance
    "influx_token": "********",            # The authentication token for InfluxDB
    "influx_org": "my-org",                # The organization name in InfluxDB
    "influx_bucket": "sensors_data",       # The InfluxDB bucket to store the data
}

# Send a POST request to start the InfluxDB pipeline with the defined payload
influxdb_start_response = requests.post("http://localhost:5000/start_pipeline", json=influxdb_start_payload)

# Print the response from the start request, which should confirm the pipeline start status
print("InfluxDB Start:", influxdb_start_response.json())

# Send a POST request to stop the InfluxDB pipeline
influxdb_stop_response = requests.post("http://localhost:5000/stop_pipeline")

# Print the response from the stop request, which should confirm the pipeline stop status
print("InfluxDB Stop:", influxdb_stop_response.json())
