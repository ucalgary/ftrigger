import asyncio
import datetime
import logging
import re

import docker


log = logging.getLogger(__name__)


class InvokerBase(object):

    invokers = []

    def __init__(self, refresh_interval=5, label='finvoker'):
        self.client = docker.from_env()
        self.loop = asyncio.new_event_loop()
        self.refresh_interval = refresh_interval
        self.last_refresh = ''
        self._services = {}
        self._invoker_label = label
        self._type_pattern = re.compile(f'^{label}\\.([^.]+)$')
        self._arg_pattern = re.compile(f'^{label}\\.([^.]+)$.([^.]+)$')

    def run(self):
        pass

    def refresh_services(self):
        services = list(filter(lambda s: any(self._type_pattern.match(k)
                                             for k
                                             in s.attrs.get('Spec', {}).get('Labels', {}).keys()),
                               self.client.services.list()))

        # Scan for new and updated services
        for service in services:
            existing_service = self._services.get(service.id)

            if not existing_service:
                # register a new service
                log.debug(f'New service: {service.attrs["Spec"]["Name"]} ({service.id})')
                self._notify_for_service(service, 1)
                self._services[service.id] = service
            elif service.attrs['UpdatedAt'] > existing_service.attrs['UpdatedAt']:
                # maybe update an already registered service
                log.debug(f'Updated service: {service.attrs["Spec"]["Name"]} ({service.id})')
                self._notify_for_service(service, 2)

        # Scan for removed services
        for service_id in set(self._services.keys()) - set([s.id for s in services]):
            service = self._services.pop(service_id)
            log.debug(f'Removed service: {service.attrs["Spec"]["Name"]} ({service.id})')
            self._notify_for_service(service, 3)

        self.last_refresh = datetime.datetime.utcnow().isoformat()
        self.loop.call_later(self.refresh_interval, self.refresh_services)

    def _notify_for_service(self, service, function_idx):
        labels = service.attrs.get('Spec', {}).get('Labels', {})
        invoker_types = [m.group(1) for m
                         in [self._type_pattern.match(k) for k in labels.keys()] if m]

        for invoker_type in invoker_types:
            matching_invokers = list(filter(lambda i: i[0].match(invoker_type), self.invokers))
            if not matching_invokers:
                continue

            invoker_arg_pattern = re.compile(f'^{self._invoker_label}\\.{invoker_type}\\.([^.]+)$')
            invoker_args = {m.group(1): v for m, v
                            in [(invoker_arg_pattern.match(k), v) for k, v in labels.items()] if m}
            log.debug(f'Invoker arguments: {invoker_args}')
            [i[function_idx](service, **finvoker_args) for i in matching_invokers if i[function_idx]]


def register(matchstr, add_f, update_f=None, remove_f=None, flags=0):
    InvocationManager.invokers.append((re.compile(matchstr, flags), add_f, update_f, remove_f))
    log.info(f'Registered {add_f.__name__} for {matchstr}')
