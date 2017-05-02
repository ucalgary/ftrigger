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
        self._invoker_label = label
        self._invoker_name = name
        self._type_pattern = re.compile(f'^{label}\\.([^.]+)$')
        self._arg_pattern = re.compile(f'^{label}\\.([^.]+)$.([^.]+)$')

    def run(self):
        pass

    def refresh_services(self):
        services = list(filter(lambda s: any(self._type_pattern.match(k)
                                             for k
                                             in s.attrs.get('Spec', {}).get('Labels', {}).keys()),
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
