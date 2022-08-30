import math
import re
import time
from dataclasses import dataclass, field
from typing import Dict

from sortedcontainers import SortedDict

__all__ = ('SampleKey', 'SampleValue', 'clock')
METRIC_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@dataclass(eq=True, frozen=True)
class SampleKey:
    name: str = field(compare=False, repr=False)
    labels: Dict[str, str] = field(default=None, compare=False, repr=False)
    _line: str = field(init=False, compare=False, repr=True)
    _cmp_line: str = field(init=False, compare=True, repr=False)

    def __post_init__(self):
        if METRIC_NAME_RE.fullmatch(self.name) is None:
            raise ValueError('Invalid sample name')

        clab = {}
        if self.labels is not None:
            for k, v in self.labels.items():
                v = str(v)
                if k.startswith('__'):
                    raise ValueError(
                        'Label names starting with __ '
                        'are reserved by Prometheus')
                if LABEL_NAME_RE.fullmatch(k) is None:
                    raise ValueError('Invalid label name')
                clab[k] = v
        object.__setattr__(self, 'labels', clab)

        # TODO: need this difference?
        object.__setattr__(
            self, '_line',
            f'{self.name}{self.expose_label_set(self.labels)}')
        object.__setattr__(
            self, '_cmp_line',
            f'{self.name}{self.expose_label_set(SortedDict(self.labels))}')

    def with_suffix(self, suffix: str) -> 'SampleKey':
        return type(self)(
            name=self.name + suffix,
            labels=self.labels,
        )

    def with_labels(self, **new_labels: Dict[str, str]):
        return type(self)(
            name=self.name,
            labels={**self.labels, **new_labels},
        )

    @staticmethod
    def expose_label_value(v) -> str:
        return (
            str(v)
            .replace('\\', r'\\')
            .replace('\n', r'\n')
            .replace('"', r'\"')
        )

    @classmethod
    def expose_label_set(cls, labels: Dict[str, str]) -> str:
        if not labels:
            return ''
        x = ','.join(
            f'{k}="{cls.expose_label_value(v)}"'
            for k, v in labels.items())
        return '{' + x + '}'

    def expose(self):
        return self._line


@dataclass
class SampleValue:
    value: float = 0.0
    timestamp: int = None

    @classmethod
    def create(cls, value: float, use_ts=False):
        if use_ts:
            return cls(value, clock())
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
        val = self.expose_value(self.value)
        if self.timestamp is not None:
            return f'{val} {self.expose_timestamp(self.timestamp)}'
        return f'{val}'


def clock():
    return int(time.time() * 1000)
