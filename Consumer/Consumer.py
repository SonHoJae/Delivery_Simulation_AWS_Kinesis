from boto import kinesis
from pymongo import MongoClient
import json
import time
import socket
import sys
from collections import OrderedDict
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
                                      'LATEST')['ShardIterator'] # shard_iterator_type]
print(shard_it)
top_10_region = OrderedDict()
top_10_region_key = []
lowest_rank = -1

def ranking_sort(updated_order):
    global top_10_region
    global top_10_region_key
    global lowest_rank

    new_key, new_value = None, None
    for k,v in updated_order.items():
        new_key, new_value = k, v
    top_10_region[k] = v
    a = sorted(list(top_10_region.items()), key=lambda x: x[1], reverse=True)
    print(a[:10])
    #TODO : IMPORVE SORTING ALGORITHM
    #
    # if len(top_10_region) == 0:
    #     top_10_region[new_key] = new_value
    #     top_10_region_key.append(new_key)
    # else:
    #     if new_key in top_10_region:
    #         top_10_region[new_key] = new_value
    #         top_10_region_key.append(new_key)
    #     else:
    #         for key, value in top_10_region.items():
    #             if value < new_value:

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
count =0
while True:
    out = kinesis.get_records(shard_it)
    # print("shardId : "+kinesis.describe_stream('DeliveryStream')['StreamDescription']['Shards'][shard_id][
    #                                       'ShardId'],end=" ")

    if len(out['Records']) > 0:
        try :
            data = json.loads(out['Records'][0]['Data'])
        except ValueError:
            pass
        #
        print(count)
        count += 1
        # region = str(data['ship_from_region_x']) + ',' + str(data['ship_from_region_y'])
        # # order_created
        # if data['status'] == 0:
        #     if region in order_created:
        #         order_created[region] += 1
        #     else:
        #         order_created[region] = 1
        #     # {region: order_created[region]}
        #     if order_created[region] > lowest_rank or len(top_10_region) < 10:
        #         # TODO MongoDB or Socket? -> Socket : if I use mongodb, the sort algorthm and stuff should be queried
        #         #  every time
        client_socket.sendall(str(data).encode("utf8"))
#        delivery_collection.insert(data)
    shard_it = out['NextShardIterator']
    time.sleep(0.09)
#
# print(db.collection_names())
# cursor = delivery_collection.find({})
# for document in cursor:
#     print(document)