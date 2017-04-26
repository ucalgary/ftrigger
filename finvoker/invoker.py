import asyncio
import datetime
import re

import docker

invokers = []


def invoke_for(matchstr, flags=0):
    def wrapper(func):
        invokers.add((re.compile(matchstr, flags), func))
        logger.info(f'Registered {func.__name__} for {matchstr}')
        return func
    return wrapper
