from functools import wraps
from typing import Dict, Tuple

import attr
from sortedcontainers import SortedDict

from . import metrics
from .sample import SampleKey

__all__ = ('counter', 'gauge', 'histogram', 'summary')


@attr.s
class Registry:
    _metrics = attr.ib(init=False, factory=dict)
    _exposers = attr.ib(init=False, factory=SortedDict)

    def get(self, key: SampleKey):
        return self._metrics.get(key)

    def register(self, key, instance, help=None):
        assert key not in self._metrics
        self._metrics[key] = instance
        self._exposers[key] = metrics.Exposer(instance, key, help)

    def unregister(self, key):
        del self._metrics[key]
        del self._exposers[key]

    def expose(self):
        for exp in self._exposers.values():
            yield from exp.expose()


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
        instance = registry.get(key)

        # we do not check there equality of instances
        # TODO: may be we should?

        if instance is None:
            instance = fn(**kwargs)
            registry.register(key, instance, help=help)
        return instance
    return builder


@_create_builder
def counter() -> metrics.Counter:
    return metrics.Counter()


@_create_builder
def gauge() -> metrics.Gauge:
    return metrics.Gauge()


@_create_builder
def histogram(*, buckets: Tuple[float]) -> metrics.Histogram:
    return metrics.Histogram(buckets)


@_create_builder
def summary(
    *, buckets: Tuple[float], time_window: float = attr.NOTHING,
) -> metrics.Summary:
    return metrics.Summary(buckets, time_window)
