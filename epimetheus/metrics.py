from copy import deepcopy
from math import isnan, nan
from typing import Tuple

import attr

from . import validate


@attr.s
class Header:
    TYPE = NotImplemented
    RESERVED_LABELS = frozenset()

    _name: str = attr.ib()
    _help: str = attr.ib(default=None)

    @_name.validator
    def _validate_name(self, attribute, value):
        if not validate.metric_name(value):
            raise ValueError('Invalid metric name')

    def __attrs_post_init__(self):
        self._labels = {}
        self._parent = None
        self._children = []

    def with_labels(self, **new_labels):
        if not new_labels:
            raise ValueError('Labels required')
        if set(new_labels.keys()) & self.RESERVED_LABELS:
            raise ValueError('Labels must not contain reserved names')

        # TODO: may be suboptimal, especially for Summary
        # do not copy tracked data
        ins = deepcopy(self)
        # TODO: reset state
        ins._labels = {**self._labels, **new_labels}
        ins._parent = self if self._parent is None else self._parent
        ins._parent._children.append(ins)
        return ins

    def _output_header(self):
        if self._help is not None:
            yield f'# HELP {self._name} {self._help}'
        yield f'# TYPE {self._name} {self.TYPE}'


@attr.s
class CounterState:
    _count = attr.ib(init=False, default=0)

    def inc(self, delta: float = 1):
        assert delta >= 0
        self._count += delta

    def get_output(self):
        return {
            'count': self._count,
        }

    @staticmethod
    def merge_outputs(*outputs):
        return {
            'count': sum(m['count'] for m in outputs),
        }


@attr.s
class Counter(CounterState, Header):
    TYPE = 'counter'


@attr.s
class GaugeState:
    _value = attr.ib(init=False, default=0)

    def inc(self, delta: float = 1):
        self._value += delta

    def dec(self, delta: float = 1):
        self._value -= delta

    def set(self, value: float):
        self._value = value

    # TODO: set_to_current_time

    def get_output(self):
        return {
            'value': self._value,
        }

    @staticmethod
    def merge_outputs(*outputs):
        # TODO: implement merge strategies
        # currently is taking average
        rs = {'value': nan}
        sm, cn = 0, 0
        for m in outputs:
            if isnan(m['value']):
                continue
            sm += m['value']
            cn += 1
        if cn > 0:
            rs['value'] = sm / cn
        return rs


@attr.s
class Gauge(GaugeState, Header):
    TYPE = 'gauge'


@attr.s
class HistogramState:
    _buckets: Tuple[float] = attr.ib(converter=lambda b: tuple(sorted(b)))
    _counts = attr.ib(init=False)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._counts = [0 for _ in self._buckets]
        self._inf_count = 0

    def observe(self, value: float):
        # TODO: optimize, use bisect
        for index, upper in enumerate(self._buckets):
            if value <= upper:
                self._counts[index] += 1
                break
        else:
            self._inf_count += 1

    def get_output(self):
        return {
            'buckets': list(self._buckets),
            'counts': self._counts + [self._inf_count],
        }

    @staticmethod
    def merge_outputs(first, *outputs):
        rs = {
            'buckets': first['buckets'],
            'counts': first['counts'],
        }
        for m in outputs:
            assert rs['buckets'] == m['buckets']
            for i, v in enumerate(m['counts']):
                rs['counts'][i] += v
        return rs


@attr.s
class Histogram(HistogramState, Header):
    TYPE = 'histogram'
    RESERVED_LABELS = frozenset(['le'])


@attr.s
class SummaryState:
    _buckets: Tuple[float] = attr.ib(converter=lambda b: tuple(sorted(b)))
    _samples = attr.ib(init=False, factory=list)

    def observe(self, value: float):
        self._samples.append(value)

    def get_output(self):
        return {
            'buckets': list(self._buckets),
            'samples': self._samples.copy(),
        }


@attr.s
class Summary(SummaryState, Header):
    TYPE = 'summary'
    RESERVED_LABELS = frozenset(['quantile'])


c = Counter('name', help='help text')
subc = c.with_labels(name='value')
subc.inc()


__all__ = ('Counter', 'Gauge', 'Histogram', 'Summary')
