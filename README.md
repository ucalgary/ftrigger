# Triggers for Functions as a Service (FaaS) Functions

Functions as a Service (FaaS) is a framework by Alex Ellis for building serverless functions on Docker Swarm. This repo provides a tool called `ftrigger` that is designed to sit alongside a FaaS gateway, observe labels on function services, and then automatically trigger functions based on the conditions described in the labels.

The only supported trigger at the moment is for Kafka topics. A time-based trigger (something like cron) will be developed next.

## Configuring Function Services to Respond to Kafka Messages

FaaS functions can be declared as Docker services. If the service containers are labeled with `function: 'true'`, they will be automatically registered to a running gateway and made available.

```
echoit:
  image: functions/alpine:health
  labels:
    function: "true"
  environment:
    fprocess: "cat"
```

ftrigger watches a running gateway and scans functions for service labels matching the pattern `ftrigger.*`, where the wildcard matches the name of a trigger service (only `kafka` is available). The trigger can be configured with labels extending from that, such as the pattern `ftrigger.kafka.*` for the kafka trigger service.

In the following example, the `echoit` function is labeled to respond to Kafka messages on the `echo` topic.

```
echoit:
  image: functions/alpine:health
  labels:
    function: "true"
  environment:
    fprocess: "cat"
  deploy:
    labels:
      ftrigger.kafka: 'true'
      ftrigger.kafka.topic: 'echo'
```

By default, the kafka trigger sends the Kafka message value as the function request body. This can be changed to a JSON object with the message key and value by setting `ftrigger.kafka.data` to `key-value`.

```
echoit:
  ...
  deploy:
    labels:
      ftrigger.kafka: 'true'
      ftrigger.kafka.topic: 'echo'
      ftrigger.kafka.data: 'key-value'
```

There are no other options at this time.

## Test Drive

You can quickly deploy ftrigger on Play with Docker, a community-run Docker playground, by clicking the following button.

[![Try in PWD](https://cdn.rawgit.com/play-with-docker/stacks/cff22438/assets/images/button.png)](http://play-with-docker.com?stack=https://raw.githubusercontent.com/ucalgary/ftrigger/master/docker-compose.yml&stack_name=ftrigger)

The demo stack is configured with an `echoit` function configured to respond to messages on the Kafka topic named `echo`. You can produce messages in the topic by running `kafka-console-producer` in the kafka service's container, then typing into the console. Every line is published as a message in the topic.

```
SERVICE_NAME=ftrigger_kafka
TASK_ID=$(docker service ps --filter 'desired-state=running' $SERVICE_NAME -q)
CONTAINER_ID=$(docker inspect --format '{{ .Status.ContainerStatus.ContainerID }}' $TASK_ID)
docker exec -it $CONTAINER_ID kafka-console-producer --broker-list kafka:9092 --topic echo
(type messages here, one per line)
```

The gateway logs will show that the function is being called for every message. Here is an example run in Play with Docker, with two messages (“abc” and “def” produced to the topic), and the gateway logs showing the echoit function called two times in response.

```
[node1] (local) root@10.0.2.3 ~
$ SERVICE_NAME=ftrigger_kafka
[node1] (local) root@10.0.2.3 ~
$ TASK_ID=$(docker service ps --filter 'desired-state=running' $SERVICE_NAME -q)
[node1] (local) root@10.0.2.3 ~
$ CONTAINER_ID=$(docker inspect --format '{{ .Status.ContainerStatus.ContainerID }}' $TASK_ID)
[node1] (local) root@10.0.2.3 ~
$ docker exec -it $CONTAINER_ID kafka-console-producer --broker-list kafka:9092 --topic echo
abc
def
^C[node1] (local) root@10.0.2.3 ~
$ docker service logs ftrigger_gateway
ftrigger_gateway.1.p86ucxfnkubk@node1    | 2017/10/11 22:36:18 HTTP Read Timeout: 8s
ftrigger_gateway.1.p86ucxfnkubk@node1    | 2017/10/11 22:36:18 HTTP Write Timeout: 8s
ftrigger_gateway.1.p86ucxfnkubk@node1    | 2017/10/11 22:36:18 Docker API version: 1.32, 17.09.0-ce
ftrigger_gateway.1.p86ucxfnkubk@node1    | Resolving: 'ftrigger_echoit'
ftrigger_gateway.1.p86ucxfnkubk@node1    | [1507761443] Forwarding request [] to: http://10.0.1.5:8080/
ftrigger_gateway.1.p86ucxfnkubk@node1    | [1507761443] took 0.009424 seconds
ftrigger_gateway.1.p86ucxfnkubk@node1    | Resolving: 'ftrigger_echoit'
ftrigger_gateway.1.p86ucxfnkubk@node1    | [1507761445] Forwarding request [] to: http://10.0.1.5:8080/
ftrigger_gateway.1.p86ucxfnkubk@node1    | [1507761445] took 0.002649 seconds
```

## Maintenance

This repository and image are currently maintained by the Research Management Systems project at the [University of Calgary](http://www.ucalgary.ca/).
