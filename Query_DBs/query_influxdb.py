import influxdb_client

# InfluxDB configuration
bucket = "sensors_data"
org = "my-org"
token = ""
url = "http://localhost:8086"

# Initialize the InfluxDB client
client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

# Query script
query_api = client.query_api()
query = '''
from(bucket: "sensors_data")
  |> range(start: -1h)  // Query the last 1 hour
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => exists r["sensor_type"])  // Include only records with sensor_type
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''

# Execute the query and parse results
result = query_api.query(org=org, query=query)
results = []
for table in result:
    for record in table.records:
        results.append({
            "time": record.get_time(),
            "sensor_type": record.values.get("sensor_type", "unknown"),
            "field": record.get_field(),
            "value": record.get_value()
        })

# Print the results
print("Queried Results:")
for entry in results:
    print(f"Time: {entry['time']}, Sensor Type: {entry['sensor_type']}, Field: {entry['field']}, Value: {entry['value']}")
