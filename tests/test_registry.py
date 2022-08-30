from epimetheus.registry import Registry


def test_all_at_once(frozen_sample_time):
    registry = Registry()

    c = registry.counter(
        name='http_requests_total',
        labels={'method': 'post'},
    )
    c200 = c.with_labels(code=200)
    c200.inc(1026)

    c400 = c.with_labels(code=400)
    c400.inc(3)

    c200a = c.with_labels(code=200)
    assert c200 is c200a
    c200a.inc()

    assert list(registry.expose()) == [
        '# TYPE http_requests_total counter',
        'http_requests_total{method="post",code="200"} 1027 '
        + f'{frozen_sample_time}',
        'http_requests_total{method="post",code="400"} 3 '
        + f'{frozen_sample_time}',
        '',
    ]
