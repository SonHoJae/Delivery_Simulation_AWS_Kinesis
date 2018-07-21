
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
"# Delivery_Simulation_AWS_Kinesis" 
