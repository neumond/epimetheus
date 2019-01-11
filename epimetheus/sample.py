import math
import re
import time
from typing import Dict

import attr
from cached_property import cached_property

METRIC_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@attr.s
class SampleKey:
    _name: str = attr.ib()
    _labels: Dict[str, str] = attr.ib(factory=dict)

    @_name.validator
    def _validate_name(self, attribute, value):
        if METRIC_NAME_RE.fullmatch(value) is None:
            raise ValueError('Invalid sample name')

    @_labels.validator
    def _validate_labels(self, attribute, value):
        for k, v in value.items():
            if k.startswith('__'):
                raise ValueError('Label names starting with __ are reserved by Prometheus')
            if LABEL_NAME_RE.fullmatch(k) is None:
                raise ValueError('Invalid label name')

    def with_suffix(self, suffix: str) -> 'SampleKey':
        return type(self)(
            name=self._name + suffix,
            labels=self._labels,
        )

    def with_labels(self, **new_labels: Dict[str, str]):
        return type(self)(
            name=self._name,
            labels={**self._labels, **new_labels},
        )

    @staticmethod
    def expose_label_value(v) -> str:
        return str(v).replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"')

    @classmethod
    def expose_label_set(cls, labels: Dict[str, str]) -> str:
        if not labels:
            return ''
        x = ','.join(f'{k}="{cls.expose_label_value(v)}"' for k, v in labels.items())
        return '{' + x + '}'

    @cached_property
    def full_key(self):
        return f'{self.name}{self.expose_label_set(self._labels)}'

    def expose(self):
        return self.full_key


@attr.s
class SampleValue:
    value: float = attr.ib(default=0)
    timestamp: int = attr.ib(default=None)

    @classmethod
    def create(cls, value: float, use_ts=False):
        if use_ts:
            return cls(value, int(time.time() * 1000))
        return cls(value)

    @staticmethod
    def expose_value(value):
        if value == math.inf:
            return 'Inf'
        elif value == -math.inf:
            return '-Inf'
        elif math.isnan(value):
            return 'Nan'
        return str(value)

    @staticmethod
    def expose_timestamp(ts):
        return str(ts)

    def expose(self):
        if self.timestamp is not None:
            return f'{self.expose_value(self.value)} {self.expose_timestamp(self.timestamp)}'
        return f'{self.expose_value(self.value)}'
