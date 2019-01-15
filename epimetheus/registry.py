from functools import wraps
from typing import Dict, Tuple

import attr
from sortedcontainers import SortedDict

from . import metrics
from .sample import SampleKey

__all__ = ('counter', 'gauge', 'histogram', 'summary')


@attr.s
class Registry:
    _groups = attr.ib(init=False, factory=dict)

    def get(self, key: SampleKey):
        return self._groups.get(key)

    def register(self, key, group):
        assert key not in self._groups
        self._groups[key] = group

    def unregister(self, key):
        del self._groups[key]

    def expose(self):
        for exp in self._groups.values():
            yield from exp.expose()
            yield ''


registry = Registry()


def _create_builder(fn):
    @wraps(fn)
    def builder(
        *, name: str,
        labels: Dict[str, str] = attr.NOTHING,
        help: str = None,
        **kwargs,
    ):
        key = SampleKey(name, labels)
        if registry.get(key) is not None:
            raise KeyError('Attempt to create same metric group twice')

        # we do not check there equality of instances
        # TODO: may be we should?

        group = metrics.Group(
            key=key,
            mcls=fn(),
            kwargs=kwargs,
            help=help,
        )
        registry.register(key, group)
        return group
    return builder


@_create_builder
def counter():
    return metrics.Counter


@_create_builder
def gauge():
    return metrics.Gauge


@_create_builder
def histogram():
    return metrics.Histogram


@_create_builder
def summary():
    return metrics.Summary
