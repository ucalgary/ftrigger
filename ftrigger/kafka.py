import atexit
import collections
import logging
import os

try:
    import ujson as json
except:
    import json
from confluent_kafka import Consumer

from .trigger import Functions


log = None


class KafkaTrigger(object):

    def __init__(self, label='ftrigger', name='kafka', refresh_interval=5,
                 kafka='kafka:9092'):
        self.functions = Functions(name='kafka')
        self.config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', kafka),
            'group.id': os.getenv('KAFKA_CONSUMER_GROUP', self.functions._register_label),
            'default.topic.config': {
                'auto.offset.reset': 'largest',
                'auto.commit.interval.ms': 5000
            }
        }

    def run(self):
        consumer = Consumer(self.config)
        callbacks = collections.defaultdict(list)
        functions = self.functions

        def close():
            log.info('Closing consumer')
            consumer.close()
        atexit.register(close)

        while True:
            add, update, remove = functions.refresh()
            if add or update or remove:
                existing_topics = set(callbacks.keys())

                for f in add:
                    callbacks[functions.arguments(f).get('topic')].append(f)
                for f in update:
                    pass
                for f in remove:
                    callbacks[functions.arguments(f).get('topic')].remove(f)

                interested_topics = set(callbacks.keys())

                if existing_topics.symmetric_difference(interested_topics):
                    log.debug(f'Subscribing to {interested_topics}')
                    consumer.subscribe(list(interested_topics))

            message = consumer.poll(timeout=functions.refresh_interval)
            if not message:
                # log.debug('Empty message received')
                pass
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
                log.debug('topic: %s, key: %s, value: %s' % (topic, key, value))
                for function in callbacks[topic]:
                    data = self.function_data(function, topic, key, value)
                    log.debug('  posting function: %s(%s)' % (function['name'], data))
                    resp = functions.gateway.post(functions._gateway_base + f'/function/{function["name"]}', data=data)
                    if resp.status_code != 200:
                        log.error('FAAS request failed: url: %s data: %s' % (functions._gateway_base + f'/function/{function["name"]}', data))
                        log.error('FAAS request failed: http_code:%s text: %s' % (resp, resp.text))
                    else:
                        log.debug('  posted function. response=%s %s' % (resp, resp.text))

    def function_data(self, function, topic, key, value):
        data_opt = self.functions.arguments(function).get('data', 'key')

        if data_opt == 'key-value':
            return json.dumps({'key': key, 'value': value})
        else:
            return key


def main():
    global log

    logging.basicConfig(level=os.environ.get('LOGGER_LEVEL', 'INFO').upper())
    log = logging.getLogger(__name__)

    trigger = KafkaTrigger()
    trigger.run()
