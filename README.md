
# Kinesis - Collect, Process streaming data in real time.
#### SDK(bogo for Python) ** bogo is used for the simulation **
#### KPL(Kinesis Producer Library)-only java KCL(Kinesis Consumer Library)-support with various languages
#### RESTful API

<hr/>

![Alt text](https://docs.aws.amazon.com/streams/latest/dev/images/architecture.png "Kinesis Architecture")

#### Producer
> ###### PUT records to stream
#### Streams
> ##### Shards : Indentified sequence of data records(1 Shard upto 5 transactions/sec(Read), 2MB/sec(Read) 1,000 records per second(Write), 1MB/sec(Write))
>> ##### Data records
>>> ##### Sequence number : data record identifier
>>> ##### Partition key : determine which shard is going to be used

#### Retention Period
#### Consumer
> ##### GET records from stream and PROCESS

<hr/>

## Delivery_Simulation
#### 0. Kinesis
##### Instructions
> 1. Install [bogo](http://boto.cloudhackers.com/en/latest/ref/kinesis.html) & [aws cli](https://aws.amazon.com/ko/cli/)
> 2. cmd > aws configure
> 3. aws kinesis create-stream --stream-name=DeliveryStream --shard-count=1
> 4. aws kinesis describe-stream --stream-name=DeliveryStream

#### 1. Producer
> Event is randomly generated
> Data stream capacity parameter
#### 2. Consumer
> ship from regions
> total amount of price that are in created orders, and that are in completed orders
> average time completion time (from created to completed), average response time (from created to assigned)
#### 3. Controlling shards(Split and Merge)


#### My issues
> 1. I needed to make a decision over storages for the result.
> With Mongodb I can store and query data on memory there was no issue. However the take is about making top-10 list
which needs 'Online Sorting' for better performance. so I decided to go with dictionary for ranking

> 2. Working with Shards, data transmitted corresponding to partition key. Based on my experiment, it wasn't well
distributed. For example, when I generate 'order_created' event, it takes 368 bytes for every record and I generated
1/0.09(=11.1) transactions per sec which means 4 megabytes. Additionally 'order_assgined', 'order_completed' events
will occur once driver accepts order.
If I split & merge shards depending on the traffic situation, I realized I can resolve these bottleneck
Since the Read limit of shard is 5 transactions, 2MB.
I assumed there are 50x50 region dimension and there are 10 drivers on the map.
when 10 drivers accept or complete order, the worst case 20 times events on a second
[Resharding](https://docs.aws.amazon.com/streams/latest/dev/kinesis-using-sdk-java-resharding-strategies.html)