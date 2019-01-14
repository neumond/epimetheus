import pytest
from epimetheus.registry import Registry, counter


@pytest.fixture
def clean_registry(mocker):
    reg = Registry()
    mocker.patch('epimetheus.registry.registry', new=reg)
    return reg


def test_all_at_once(clean_registry, frozen_sample_time):
    c200 = counter(
        name='http_requests_total',
        labels={'method': 'post', 'code': 200},
    )
    c200.inc(1026)

    c400 = counter(
        name='http_requests_total',
        labels={'method': 'post', 'code': 400},
    )
    c400.inc(3)

    c200a = counter(
        name='http_requests_total',
        labels={'method': 'post', 'code': 200},
    )
    assert c200 is c200a
    c200a.inc()

    assert list(clean_registry.expose()) == [
        '# TYPE http_requests_total counter',
        'http_requests_total{method="post",code="200"} 1027 ' + f'{frozen_sample_time}',
        'http_requests_total{method="post",code="400"} 3 ' + f'{frozen_sample_time}',
    ]
