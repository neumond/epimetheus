from collections import deque
from dataclasses import dataclass, field
from math import ceil, floor
from typing import List, Tuple

from .sample import SampleKey, SampleValue, clock

# Metrics should be optimized for fast receiving of data
# And relatively rare reporting

__all__ = ('Counter', 'Gauge', 'Histogram', 'Summary')


@dataclass
class MetricWithTimestamp:
    use_clock: bool = True
    reclock_if_changed: bool = False
    _ts: float = field(init=False, default=None)

    def __post_init__(self):
        self._update_ts(1)

    def _update_ts(self, vdiff):
        if not self.use_clock:
            return
        if (not self.reclock_if_changed) or vdiff:
            self._ts = clock()


@dataclass
class Counter(MetricWithTimestamp):
    TYPE = 'counter'

    _count: float = field(init=False, default=0)

    def inc(self, delta: float = 1):
        assert delta >= 0
        self._count += delta
        self._update_ts(delta)

    def sample_group(self, skey: SampleKey):
        yield skey

    def sample_values(self):
        yield SampleValue(self._count, self._ts)


@dataclass
class Gauge(MetricWithTimestamp):
    TYPE = 'gauge'

    _value: float = field(init=False, default=0)

    def inc(self, delta: float = 1):
        self._value += delta
        self._update_ts(delta)

    def dec(self, delta: float = 1):
        self._value -= delta
        self._update_ts(delta)

    def set(self, value: float):
        vdiff = value - self._value
        self._value = value
        self._update_ts(vdiff)

    def set_with_timestamp(self, value: float, ts: int):
        "For metrics like daily active users"
        self._value = value
        self._ts = ts

    # TODO: set_to_current_time

    def sample_group(self, skey: SampleKey):
        yield skey

    def sample_values(self):
        yield SampleValue(self._value, self._ts)


def to_sorted_tuple(x):
    return tuple(sorted(x))


@dataclass
class Histogram:
    TYPE = 'histogram'
    RESERVED_LABELS = frozenset(['le'])

    buckets: Tuple[float]
    _bcounts: List[int] = field(init=False)
    _inf_bcount: int = field(init=False, default=0)
    _sum: float = field(init=False, default=0)
    _count: int = field(init=False, default=0)

    def __post_init__(self):
        self.buckets = to_sorted_tuple(self.buckets)
        self._bcounts = [0 for _ in self.buckets]

    def observe(self, value: float):
        # TODO: optimize, use bisect
        for index, upper in enumerate(self.buckets):
            if value <= upper:
                self._bcounts[index] += 1
                break
        else:
            self._inf_bcount += 1
        self._sum += value
        self._count += 1

    def sample_group(self, skey: SampleKey):
        bkey = skey.with_suffix('_bucket')
        for b in self.buckets:
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


@dataclass
class Summary:
    TYPE = 'summary'
    RESERVED_LABELS = frozenset(['quantile'])

    buckets: Tuple[float]
    time_window: float = 3600
    _samples: deque = field(init=False, default_factory=deque)

    def __post_init__(self):
        for b in self.buckets:
            if not (0 <= b <= 1):
                raise ValueError('Quantiles must be in range 0..1')
        self.buckets = to_sorted_tuple(self.buckets)

    def _clean_old_samples(self):
        before = clock() - int(self.time_window * 1000)
        while self._samples and self._samples[0].timestamp <= before:
            self._samples.popleft()

    def observe(self, value: float):
        self._samples.append(SampleValue.create(value, clock()))
        self._clean_old_samples()

    def sample_group(self, skey: SampleKey):
        for b in self.buckets:
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

        for qp in self.buckets:
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


@dataclass
class Group:
    key: SampleKey
    mcls: type
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    help: str = None

    _items: dict = field(init=False, default_factory=dict)
    _rendered_keys: dict = field(init=False, default_factory=dict)

    def with_labels(self, **labels):
        k = self.key.with_labels(**labels)
        if k in self._items:
            return self._items[k]
        # TODO: RESERVED_LABELS
        m = self.mcls(*self.args, **self.kwargs)
        self._items[k] = m
        self._rendered_keys[k] = tuple(rk.expose() for rk in m.sample_group(k))
        return m

    def expose_header(self):
        if self.help is not None:
            yield f'# HELP {self.help}'
        yield f'# TYPE {self.key.name} {self.mcls.TYPE}'

    def expose(self):
        he = False
        for k, m in self._items.items():
            for rk, v in zip(self._rendered_keys[k], m.sample_values()):
                # expose header only if we have samples
                if not he:
                    yield from self.expose_header()
                    he = True
                yield f'{rk} {v.expose()}'
