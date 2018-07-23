
# Kinesis - Collect, Process streaming data in real time.
#### SDK(bogo for Python) ** bogo is used for the simulation **
#### KPL(Kinesis Producer Library)-only java KCL(Kinesis Consumer Library)-support with various languages
#### RESTful API

<hr/>

![Kinesis Architecture](https://docs.aws.amazon.com/streams/latest/dev/images/architecture.png "Kinesis Architecture")

#### Producer
> ###### PUT records to stream
#### Streams
> ##### Shards : Indentified sequence of data records(1 Shard upto 5 transactions/sec(Read), 2MB/sec(Read) 1,000 records per second(Write), 1MB/sec(Write))
> ##### Data records
> ##### Sequence number : data record identifier
> ##### Partition key : determine which shard is going to be used

#### Retention Period
> ##### 24 Hours by default upto 168 hours
#### Consumer
> ##### GET records from stream and PROCESS

<hr/>

## Delivery_Simulation
### Kinesis
![Overview](https://i.imgur.com/wiMuZTF.jpg "Overview")

#### 0. Instructions
> 1. Install [bogo](http://boto.cloudhackers.com/en/latest/ref/kinesis.html) & [aws cli](https://aws.amazon.com/ko/cli/)
> 2. cmd > aws configure
> 3. aws kinesis create-stream --stream-name=DeliveryStream --shard-count=[count]
> 4. aws kinesis describe-stream --stream-name=DeliveryStream
#### 1. Hypothesis
> There are [30x30] dimension map and 10 drivers on the map.
> A driver is looking for an order under condition that takes consideration of pick_up_time & distance
> taking time [driver_location to delivey_src] + [delivery_src to delivery_dst] < pick_up_time
> delivery_src should be within [3x3] from the driver
#### 2. Producer
> Event is randomly generated
> Main_Producer.py -> order_created event generated

![Driver_Producer](https://i.imgur.com/o9mrwOc.png "Driver_Producer")

> Driver_Producer.py -> there are 10 threads(drivers) is finding orders. if an order doesn't satisfy driver's
condition, the driver is going to take a rest and search it again. Once the order is assigned to a driver,
order_assigned event will be generated. after completing order, order_completed event is generated and update
driver's location. Now the driver takes some rest(time.sleep), and search for a new order based on new location
(previous destination)
##### For fair data distribution I used count **cycle(shard_hash_key)** which means it shoots data around at each shard
##### This is possible by setting partition_key explicitly

#### 3. Consumer.py / Consumer_Batch.bat
> In my simulation, I created 6 shards on the Stream. The data size that I transfer through pipeline, are 368
bytes(order_created) 240 bytes(order_assigned/order_completed) I transmit data about 10 transactions/sec(from
Main_Producer) and  20 transations/sec(the worst case from Driver_Producer) which means I should handle about 30
transactions.
> There is no concern with writing to shards however for reading,I should make sure within 5 transactions/sec per
shards. so I created 7 shards to accept data without missing them
> total amount of price that are in created orders, and that are in completed orders
> average time completion time (from created to completed), average response time (from created to assigned)

#### 4. Simple_Server.py
> The server receives data from consumer(from each shards) and process it for the purpose
> For better performance, I didn't use database when processing ranking method. I used defaultdict structure with list.
> Before I found defaultdict structure, I was supposed to use insertionRanking which can get sorting result with on-line strategy

#### 5. Controlling shards(Split and Merge)
> CREATE aws kinesis create-stream --stream-name=DeliveryStream --shard-count=4
> DESCRIBE aws kinesis describe-stream --stream-name=DeliveryStream
> DELETE aws kinesis delete-stream --stream-name=DeliveryStream

#### 6. Simulation Video
[![Watch the video](https://i.imgur.com/mRAF72o.jpg)](https://vimeo.com/user87602558/review/281284344/893d615e04)
<hr/>

#### My issues
> 1. I needed to make a decision over storage for the result.
> Since I have to tackle real-time streaming, I should avoid disk operation with database
> With Mongodb I can store and query data on memory there was no issue.
> For top-10 result  'Online Sorting' has better performance.

> 2. Working with Shards, I found there are data missing over the pipeline. this is because data transmitted
corresponding to partition key. Based on my experiment, it wasn't well distributed.
For example, when I generate 'order_created' event, it takes 368 bytes for every record and I generated
1/0.09(=11.1) transactions per sec which means 4 megabytes. Additionally 'order_assgined', 'order_completed' events
will occur once driver accepts order.
I realized I can resolve these bottleneck if I can control shard by explicitly choosing one [Explicit Hash key](https://stackoverflow.com/questions/46634357/how-to-write-data-to-a-specific-shard-in-kinesis)


#### Reference

1. [API Explanation](https://docs.aws.amazon.com/kinesis/latest/APIReference/API_DescribeStreamSummary.html)
2. [Python API](https://boto3.readthedocs.io/en/latest/reference/services/kinesis.html#Kinesis.Client.describe_stream_summary)
3. [Resharding](https://docs.aws.amazon.com/streams/latest/dev/kinesis-using-sdk-java-resharding-strategies.html)
4. [Explicit Hash key](https://stackoverflow.com/questions/46634357/how-to-write-data-to-a-specific-shard-in-kinesis)