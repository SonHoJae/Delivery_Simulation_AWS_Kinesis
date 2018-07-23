from pymongo import MongoClient

client = MongoClient()
db = client.delivery_database
delivery_collection = db.delivery_collection
cursor = delivery_collection.find()
for row in cursor:
    print(row)
# delivery_collection.drop()