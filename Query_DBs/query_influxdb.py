import influxdb_client

# InfluxDB configuration
bucket = "sensors_data"  # Name of the InfluxDB bucket where sensor data is stored
org = "my-org"  # Organization name in InfluxDB
token = ""  # The authentication token for InfluxDB
url = "http://localhost:8086"  # URL of the InfluxDB instance

# Initialize the InfluxDB client
client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

# Query script
query_api = client.query_api()  # Get the InfluxDB query API to execute queries
query = '''
from(bucket: "sensors_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => exists r["sensor_type"])
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''

# Execute the query and parse results
result = query_api.query(org=org, query=query)  # Execute the query
results = []  # Initialize a list to store the parsed results
for table in result:  # Iterate over tables in the query result
    for record in table.records:  # Iterate over records in each table
        # Append the relevant data to the results list
        results.append({
            "time": record.get_time(),
            "sensor_type": record.values.get("sensor_type", "unknown"),
            "field": record.get_field(),
            "value": record.get_value()
        })

# Print the results
print("Queried Results:")
for entry in results:  # Iterate over each entry in the results list
    print(f"Time: {entry['time']}, Sensor Type: {entry['sensor_type']}, Field: {entry['field']}, Value: {entry['value']}")
