import requests

influxdb_start_payload = {
    "influx_url": "http://influxdb:8086",
    "influx_token": "********",
    "influx_org": "my-org",
    "influx_bucket": "sensors_data",
}
influxdb_start_response = requests.post("http://localhost:5000/start_pipeline", json=influxdb_start_payload)
print("InfluxDB Start:", influxdb_start_response.json())

influxdb_stop_response = requests.post("http://localhost:5000/stop_pipeline")
print("InfluxDB Stop:", influxdb_stop_response.json())
