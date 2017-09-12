import atexit
import collections
import logging
import os

try:
    import ujson as json
except:
    import json
from confluent_kafka import Consumer

from .trigger import TriggerBase


log = logging.getLogger(__name__)


class KafkaTrigger(TriggerBase):

    def __init__(self, label='ftrigger', name='kafka', refresh_interval=5,
                 kafka='kafka:9092'):
        super().__init__(label=label, name=name, refresh_interval=refresh_interval)
        self.config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', kafka),
            'group.id': os.getenv('KAFKA_CONSUMER_GROUP', self._register_label),
            'default.topic.config': {
                'auto.offset.reset': 'largest',
                'auto.commit.interval.ms': 5000
            }
        }

    def run(self):
        consumer = Consumer(self.config)
        callbacks = collections.defaultdict(list)

        def close():
            log.info('Closing consumer')
            consumer.close()
        atexit.register(close)

        while True:
            add, update, remove = self.refresh_functions()
            if add or update or remove:
                existing_topics = set(callbacks.keys())

                for f in add:
                    callbacks[self.arguments(f).get('topic')].append(f)
                for f in update:
                    pass
                for f in remove:
                    callbacks[self.arguments(f).get('topic')].remove(f)

                interested_topics = set(callbacks.keys())

                if existing_topics.symmetric_difference(interested_topics):
                    log.debug(f'Subscribing to {interested_topics}')
                    consumer.subscribe(list(interested_topics))

            message = consumer.poll(timeout=self.refresh_interval)
            if not message:
                log.debug('Empty message received')
            elif not message.error():
                topic, key, value = message.topic(), \
                                    message.key(), \
                                    message.value()
                try:
                    key = message.key().decode('utf-8')
                except:
                    pass
                try:
                    value = json.loads(value)
                except:
                    pass
                for function in callbacks[topic]:
                    data = self.function_data(function, topic, key, value)
                    self.gateway.post(self._gateway_base + '/function/{function["name"]}', data=data)

    def function_data(self, function, topic, key, value):
        service = function['service']
        data_opt = self.arguments(service).get('data', 'key')

        if data_opt == 'key-value':
            return json.dumps({'key': key, 'value': value})
        else:
            return key


def main():
    trigger = KafkaTrigger()
    trigger.run()
