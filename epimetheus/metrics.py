from collections import deque
from math import ceil, floor
from typing import Tuple

import attr

from .sample import SampleKey, SampleValue, clock

# Metrics should be optimized for fast receiving of data
# And relatively rare reporting

__all__ = ('Counter', 'Gauge', 'Histogram', 'Summary', 'Exposer')


@attr.s
class Counter:
    TYPE = 'counter'

    _count = attr.ib(init=False, default=0)
    _ts = attr.ib(init=False, factory=clock)

    def inc(self, delta: float = 1):
        assert delta >= 0
        self._count += delta
        self._ts = clock()

    def sample_group(self, skey: SampleKey):
        yield skey

    def sample_values(self):
        yield SampleValue(self._count, self._ts)


@attr.s
class Gauge:
    TYPE = 'gauge'

    _value = attr.ib(init=False, default=0)
    _ts = attr.ib(init=False, factory=clock)

    def inc(self, delta: float = 1):
        self._value += delta
        self._ts = clock()

    def dec(self, delta: float = 1):
        self._value -= delta
        self._ts = clock()

    def set(self, value: float):
        self._value = value
        self._ts = clock()

    # TODO: set_to_current_time

    def sample_group(self, skey: SampleKey):
        yield skey

    def sample_values(self):
        yield SampleValue(self._value, self._ts)


def to_sorted_tuple(x):
    return tuple(sorted(x))


@attr.s
class Histogram:
    TYPE = 'histogram'
    RESERVED_LABELS = frozenset(['le'])

    _buckets: Tuple[float] = attr.ib(converter=to_sorted_tuple)
    _bcounts = attr.ib(init=False)
    _inf_bcount = attr.ib(init=False, default=0)
    _sum = attr.ib(init=False, default=0)
    _count = attr.ib(init=False, default=0)

    def __attrs_post_init__(self):
        self._bcounts = [0 for _ in self._buckets]

    def observe(self, value: float):
        # TODO: optimize, use bisect
        for index, upper in enumerate(self._buckets):
            if value <= upper:
                self._bcounts[index] += 1
                break
        else:
            self._inf_bcount += 1
        self._sum += value
        self._count += 1

    def sample_group(self, skey: SampleKey):
        bkey = skey.with_suffix('_bucket')
        for b in self._buckets:
            yield bkey.with_labels(le=b)
        yield bkey.with_labels(le='+Inf')
        yield skey.with_suffix('_sum')
        yield skey.with_suffix('_count')

    def sample_values(self):
        for v in self._bcounts:
            yield SampleValue(v)
        yield SampleValue(self._inf_bcount)
        yield SampleValue(self._sum)
        yield SampleValue(self._count)


@attr.s
class Summary:
    TYPE = 'summary'
    RESERVED_LABELS = frozenset(['quantile'])

    # TODO: validate range 0..1
    _buckets: Tuple[float] = attr.ib(converter=to_sorted_tuple)
    _time_window: float = attr.ib(default=3600)
    _samples = attr.ib(init=False, factory=deque)

    @_buckets.validator
    def _validate_buckets(self, attribute, value):
        for x in value:
            if not (0 <= x <= 1):
                raise ValueError('Quantiles must be in range 0..1')

    def _clean_old_samples(self):
        before = clock() - int(self._time_window * 1000)
        while self._samples and self._samples[0].timestamp <= before:
            self._samples.popleft()

    def observe(self, value: float):
        self._samples.append(SampleValue.create(value, clock()))
        self._clean_old_samples()

    def sample_group(self, skey: SampleKey):
        for b in self._buckets:
            yield skey.with_labels(quantile=b)
        yield skey.with_suffix('_sum')
        yield skey.with_suffix('_count')

    def sample_values(self):
        self._clean_old_samples()
        if not self._samples:
            return

        quantiles = []
        ss = list(sorted(self._samples, key=lambda s: s.value))
        n = len(ss)
        ss.append(ss[-1])

        for qp in self._buckets:
            k = (n - 1) * qp
            f, c = floor(k), ceil(k)
            if f == c:
                qval = ss[f].value
            else:
                qval = (
                    ss[f].value * (c - k)
                    +
                    ss[c].value * (k - f)
                )
            quantiles.append(qval)

        for v in quantiles:
            yield SampleValue(v)
        yield SampleValue(sum(s.value for s in ss[:n]))
        yield SampleValue(n)


@attr.s
class Exposer:
    _metric = attr.ib()
    _key: SampleKey = attr.ib()
    _help: str = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._keys = tuple(
            k.full_key for k in self._metric.sample_group(self._key))

    def expose_header(self):
        if self._help is not None:
            yield f'# HELP {self._help}'
        yield f'# TYPE {self._key.name} {self._metric.TYPE}'

    def expose(self):
        he = False
        for k, v in zip(
            self._keys,
            (v.expose() for v in self._metric.sample_values()),
        ):
            # expose header only if we have samples
            if not he:
                yield from self.expose_header()
                he = True
            yield f'{k} {v}'


@attr.s
class Group:
    _key: SampleKey = attr.ib()
    _mcls: type = attr.ib()
    _args: tuple = attr.ib(default=())
    _kwargs: dict = attr.ib(factory=dict)
    _help: str = attr.ib(default=None)

    _items: dict = attr.ib(init=False, factory=dict)
    _rendered_keys: dict = attr.ib(init=False, factory=dict)

    def with_labels(self, **labels):
        k = self._key.with_labels(**labels)
        if k in self._items:
            return self._items[k]
        # TODO: RESERVED_LABELS
        m = self._mcls(*self._args, **self._kwargs)
        self._items[k] = m
        self._rendered_keys[k] = tuple(rk.full_key for rk in m.sample_group(k))
        return m

    def expose_header(self):
        if self._help is not None:
            yield f'# HELP {self._help}'
        yield f'# TYPE {self._key.name} {self._mcls.TYPE}'

    def expose(self):
        he = False
        for k, m in self._items.items():
            for rk, v in zip(self._rendered_keys[k], m.sample_values()):
                # expose header only if we have samples
                if not he:
                    yield from self.expose_header()
                    he = True
                yield f'{rk} {v.expose()}'
