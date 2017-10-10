# Triggers for Functions as a Service (FaaS) Functions

Functions as a Service (FaaS) is a framework by Alex Ellis for building serverless functions on Docker Swarm. This provides label-based triggers for FaaS functions.

## Test Drive

You can quickly deploy ftrigger on Play with Docker, a community-run Docker playground, by clicking the following button.

[![Try in PWD](https://cdn.rawgit.com/play-with-docker/stacks/cff22438/assets/images/button.png)](http://play-with-docker.com?stack=https://raw.githubusercontent.com/ucalgary/ftrigger/master/docker-compose.yml&stack_name=ftrigger)

The demo stack is configured with an `echoit` function configured to respond to messages on the Kafka topic named `echo`. You can produce messages in the topic by running `kafka-console-producer` in the kafka service's container, then typing into the console. Every line is published as a message in the topic.

```
SERVICE_NAME=ftrigger_kafka
TASK_ID=$(docker service ps --filter 'desired-state=running' $SERVICE_NAME -q)
CONTAINER_ID=$(docker inspect --format '{{ .Status.ContainerStatus.ContainerID }}' $TASK_ID)
docker exec -it $CONTAINER_ID kafka-console-producer --broker-list kafka:9092 --topic echo
```

The gateway logs will show that the function is being called for every message.

```
Resolving: 'ftrigger_echoit'
[1507597313] Forwarding request [] to: http://10.0.0.3:8080/
[1507597313] took 0.002992 seconds
```

By default, only the Kafka message value is sent as input to the function. Setting `ftrigger.kafka.data` to `key-value` will cause the function to be called with a JSON object containing both the message key and value.

```
echoit:
  deploy:
    labels:
      ftrigger.kafka: 'true'
      ftrigger.kafka.topic: 'echo'
      ftrigger.kafka.data: 'key-value'
```

## Maintenance

This repository and image are currently maintained by the Research Management Systems project at the [University of Calgary](http://www.ucalgary.ca/).
