import logging
import os
import re
import time

import docker
import requests


log = logging.getLogger(__name__)


class TriggerBase(object):

    def __init__(self, label='ftrigger', name=None, refresh_interval=5, gateway='http://gateway:8080'):
        self.client = docker.from_env()
        self.refresh_interval = int(os.getenv('TRIGGER_REFRESH_INTERVAL', refresh_interval))
        self.last_refresh = 0
        self._services = {}
        self._functions = {}
        self._label = os.getenv('TRIGGER_LABEL', label)
        self._name = os.getenv('TRIGGER_NAME', name)
        self._register_label = f'{label}.{name}'
        self._argument_pattern = re.compile(f'^{label}\\.{name}\\.([^.]+)$')
        self._gateway_base = gateway.rstrip('/')
        self.gateway = requests.Session()

    @property
    def label(self):
        return self._label

    @property
    def name(self):
        return self._name

    def run(self):
        pass

    def refresh_services(self, force=False):
        if not force and time.time() - self.last_refresh < self.refresh_interval:
            return [], [], []

        services = list(filter(lambda s: self._register_label in s.attrs.get('Spec', {}).get('Labels', {}),
                               self.client.services.list()))

        add_services = []
        update_services = []
        remove_services = []

        # Scan for new and updated services
        for service in services:
            existing_service = self._services.get(service.id)

            if not existing_service:
                # register a new service
                log.debug(f'Add service: {service.attrs["Spec"]["Name"]} ({service.id})')
                add_services.append(service)
                self._services[service.id] = service
            elif service.attrs['UpdatedAt'] > existing_service.attrs['UpdatedAt']:
                # maybe update an already registered service
                log.debug(f'Update service: {service.attrs["Spec"]["Name"]} ({service.id})')
                update_services.append(service)

        # Scan for removed services
        for service_id in set(self._services.keys()) - set([s.id for s in services]):
            service = self._services.pop(service_id)
            log.debug(f'Remove service: {service.attrs["Spec"]["Name"]} ({service.id})')
            remove_services.append(service)

        self.last_refresh = time.time()
        return add_services, update_services, remove_services

    def refresh_functions(self, force=False):
        if not force and time.time() - self.last_refresh < self.refresh_interval:
            return [], [], []

        add_functions = []
        update_functions = []
        remove_functions = []

        functions = self.gateway.get(self._gateway_base + '/system/functions').json()
        for function in functions:
            function['service'] = self.client.services.get(function['name'])
        functions = list(filter(lambda f: self._register_label in f['service'].attrs.get('Spec', {}).get('Labels', {}),
                                functions))

        # Scan for new and updated functions
        for function in functions:
            existing_function = self._functions.get(function['name'])

            if not existing_function:
                # register a new function
                log.debug(f'Add function: {function["name"]} ({function["service"].id})')
                add_functions.append(function)
                self._functions[function['name']] = function
            elif function['service'].attrs['UpdatedAt'] > existing_function['service'].attrs['UpdatedAt']:
                # maybe update an already registered function
                log.debug(f'Update function: {function["name"]} ({function["service"].id})')
                update_functions.append(function)
                self._functions[function['name']] = function

        # Scan for removed functions
        for function_name in set(self._functions.keys()) - set([f['name'] for f in functions]):
            function = self._functions.pop(function_name)
            log.debug(f'Remove function: {function["name"]} ({function["service"].id})')
            remove_functions.append(function)

        self.last_refresh = time.time()
        return add_functions, update_functions, remove_functions

    def arguments(self, function):
        service = function['service']
        labels = service.attrs.get('Spec', {}).get('Labels', {})
        if self._register_label not in labels:
            return None

        args = {m.group(1): v for m, v
                in [(self._argument_pattern.match(k), v) for k, v in labels.items()] if m}
        log.debug(f'{service.attrs["Spec"]["Name"]} arguments: {args}')
        return args
