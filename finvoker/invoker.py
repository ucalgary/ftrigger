import asyncio
import datetime
import re

import docker


class InvocationManager(object):

    def __init__(self, refresh_interval=5):
        self.client = docker.from_env()
        self.loop = asyncio.new_event_loop()
        self.refresh_interval = refresh_interval
        self.last_refresh = ''
        self._invokers = []

    def register(self, matchstr, add_f, remove_f=None):
        invokers.add((re.compile(matchstr, flags), add_f, remove_f))
        logger.info(f'Registered {func.__name__} for {matchstr}')

    def run(self):
        self.refresh_services()
        self.loop.run_forever()

    def refresh_services(self):
        services = filter(lambda s: s.attrs['UpdatedAt'] > self.last_refresh,
                          self.client.services.list())
        print([s.attrs['Spec']['Name'] for s in services])
        self.last_refresh = datetime.datetime.utcnow().isoformat()
        self.loop.call_later(self.refresh_interval, self.refresh_services)
