from . import validate


class Metric:
    def __init__(self, name: str, help: str = None, labels=None):
        assert validate.metric_name(name)
        self._name = name
        self._help = help
        self._labels = labels

    def labels(self, **new_labels):
        assert new_labels
        return self.__class__(
            self._name,
            help=self._help,
            labels={**(self._labels or {}), **new_labels},
        )


class Counter(Metric):
    def inc(self, value: float = 1):
        assert value >= 0


class Gauge(Metric):
    def inc(self, value: float = 1):
        pass

    def dec(self, value: float = 1):
        pass

    def set(self, value: float):
        pass


class Summary(Metric):
    def observe(self, value: float):
        pass


class Histogram(Metric):
    def observe(self, value: float):
        pass


c = Counter('name', help='help text')
subc = c.labels(name='value')
subc.inc()
