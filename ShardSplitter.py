from boto import kinesis

kinesis = kinesis.connect_to_region('ap-northeast-1')
sinfo = kinesis.describe_stream('DeliveryStream')
hkey = int(sinfo['StreamDescription']['Shards'][0]['HashKeyRange']
           ['EndingHashKey'])
print(str(int(hkey/2)))
shard_id = 'shardId-000000000000'
kinesis.split_shard('DeliveryStream', shard_id, str(int(hkey/2)))