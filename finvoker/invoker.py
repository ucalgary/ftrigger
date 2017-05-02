import logging
import re
import time

import docker


log = logging.getLogger(__name__)


class InvokerBase(object):

    invokers = []

    def __init__(self, label='finvoker', name=None, refresh_interval=5):
        self.client = docker.from_env()
        self.refresh_interval = refresh_interval
        self.last_refresh = 0
        self._services = {}
        self._label = label
        self._name = name
        self._register_label = f'{label}.{name}'
        self._argument_pattern = re.compile(f'^{label}\\.{name}\\.([^.]+)$')

    @property
    def label(self):
        return self._label

    @property
    def name(self):
        return self._name

    def run(self):
        pass

    def refresh_services(self):
        services = list(filter(lambda s: self._register_label in s.attrs.get('Spec', {}).get('Labels', {}),
                               self.client.services.list()))

        new_services = []
        updated_services = []
        removed_services = []

        # Scan for new and updated services
        for service in services:
            existing_service = self._services.get(service.id)

            if not existing_service:
                # register a new service
                log.debug(f'New service: {service.attrs["Spec"]["Name"]} ({service.id})')
                new_services.append(service)
                self._services[service.id] = service
            elif service.attrs['UpdatedAt'] > existing_service.attrs['UpdatedAt']:
                # maybe update an already registered service
                log.debug(f'Updated service: {service.attrs["Spec"]["Name"]} ({service.id})')
                updated_services.append(service)

        # Scan for removed services
        for service_id in set(self._services.keys()) - set([s.id for s in services]):
            service = self._services.pop(service_id)
            log.debug(f'Removed service: {service.attrs["Spec"]["Name"]} ({service.id})')
            removed_services.append(service)

        self.last_refresh = time.time()
        return new_services, updated_services, removed_services

    def arguments(self, service):
        labels = service.attrs.get('Spec', {}).get('Labels', {})
        if self._register_label not in labels:
            return None

        args = {m.group(1): v for m, v
                in [(self._argument_pattern.match(k), v) for k, v in labels.items()] if m}
        log.debug(f'{service.attrs["Spec"]["Name"]} arguments: {args}')
        return args
