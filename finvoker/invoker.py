import asyncio
import datetime
import logging
import re

import docker


log = logging.getLogger(__name__)


class InvocationManager(object):

    def __init__(self, refresh_interval=5):
        self.client = docker.from_env()
        self.loop = asyncio.new_event_loop()
        self.refresh_interval = refresh_interval
        self.last_refresh = ''
        self._invokers = []
        self._services = {}

    def register(self, matchstr, add_f, remove_f=None):
        invokers.add((re.compile(matchstr, flags), add_f, remove_f))
        log.info(f'Registered {func.__name__} for {matchstr}')

    def run(self):
        self.refresh_services()
        self.loop.run_forever()

    def refresh_services(self):
        services = list(filter(lambda s: 'finvoker' in s.attrs.get('Spec', {}).get('Labels', {}),
                               self.client.services.list()))

        # Scan for new and updated services
        for service in services:
            existing_service = self._services.get(service.id)

            if not existing_service:
                # register a new service
                log.debug(f'New service: {service.attrs["Spec"]["Name"]} ({service.id})')
            elif service.attrs['UpdatedAt'] > existing_service.attrs['UpdatedAt']:
                # maybe update an already registered service
                log.debug(f'Updated service: {service.attrs["Spec"]["Name"]} ({service.id})')

            self._services[service.id] = service

        # Scan for removed services
        for service_id in set(self._services.keys()) - set([s.id for s in services]):
            service = self._services.pop(service_id)
            log.debug(f'Removed service: {service.attrs["Spec"]["Name"]} ({service.id})')

        self.last_refresh = datetime.datetime.utcnow().isoformat()
        self.loop.call_later(self.refresh_interval, self.refresh_services)
