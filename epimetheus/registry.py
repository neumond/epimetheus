from dataclasses import dataclass, field
from typing import Dict

from . import metrics
from .sample import SampleKey

__all__ = ('Registry', )


def _create_builder(mcls):
    def builder(
        self,
        name: str,
        *,
        labels: Dict[str, str] = None,
        help: str = None,
        **kwargs,
    ):
        key = SampleKey(name, labels)
        if self.get(key) is not None:
            raise KeyError('Attempt to create same metric group twice')

        # we do not check there equality of instances
        # TODO: may be we should?

        group = metrics.Group(
            key=key,
            mcls=mcls,
            kwargs=kwargs,
            help=help,
        )
        self.register(key, group)
        return group
    return builder


@dataclass
class Registry:
    _groups: dict = field(init=False, default_factory=dict)

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

    counter = _create_builder(metrics.Counter)
    gauge = _create_builder(metrics.Gauge)
    histogram = _create_builder(metrics.Histogram)
    summary = _create_builder(metrics.Summary)
