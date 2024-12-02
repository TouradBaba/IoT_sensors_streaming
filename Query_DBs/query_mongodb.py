from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient("mongodb://admin:admin12345@localhost:27017")

# Choose the database and collection
db = client['sensor_data']
collection = db['sensor_data']

# Number of recent documents to retrieve
num_documents = 10

# Query the data (retrieving the last few inserted documents)
documents = collection.find().sort('_id', -1).limit(num_documents)

# Print out the documents
for doc in documents:
    print(doc)

# Close the connection
client.close()
