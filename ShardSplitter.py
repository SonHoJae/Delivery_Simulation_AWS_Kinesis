from boto import kinesis

kinesis = kinesis.connect_to_region('ap-northeast-1')
sinfo = kinesis.describe_stream('DeliveryStream')
hkey = int(sinfo['StreamDescription']['Shards'][4]['HashKeyRange']
           ['EndingHashKey'])
print(str(int(hkey)))
shard_id = 'shardId-000000000002'
kinesis.split_shard('DeliveryStream', shard_id, '340282366920938463463374607431768211450')