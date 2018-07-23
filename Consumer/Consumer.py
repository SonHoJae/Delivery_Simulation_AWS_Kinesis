from boto import kinesis
from pymongo import MongoClient
import time
import socket
import sys

# Database setup
client = MongoClient()
db = client.delivery_database
delivery_collection = db.delivery_collection


kinesis = kinesis.connect_to_region('ap-northeast-1')
shard_id = sys.argv[1]
print(shard_id)

# stream info
print('shard_number' +str(shard_id))
print(kinesis.describe_stream('DeliveryStream'))
shard_it = kinesis.get_shard_iterator(kinesis.list_streams()['StreamNames'][0], #stream_name
                                      kinesis.describe_stream('DeliveryStream')['StreamDescription']['Shards'][
                                          int(shard_id)][
                                          'ShardId'], # shard_id
                                      'LATEST')['ShardIterator']

client_socket = None
def client():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8888

    try:
        client_socket.connect((host, port))
    except:
        print("Connection error")
        sys.exit()

    print("Enter 'quit' to exit")

client()
order_created = {}
count = 0
while True:
    out = kinesis.get_records(shard_it)

    if len(out['Records']) > 0:
        try :
            data = out['Records'][0]['Data']
            print(count, data)
        except ValueError:
            pass

        count += 1
        #  every time
        client_socket.sendall(str(data).encode("utf8"))

    shard_it = out['NextShardIterator']
    time.sleep(0.09)