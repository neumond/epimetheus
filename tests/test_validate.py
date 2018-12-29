import pytest
from epimetheus import validate


@pytest.mark.parametrize('text,is_valid', (
    ('name', True),
    ('api_http_requests_total', True),
    ('你好', False),
    ('    ', False),
    ('   name', False),
    ('\n\n\n', False),
    ('name\n', False),
    ('000', False),
    ('a000', True),
))
def test_metric_name(text, is_valid):
    assert validate.metric_name(text) is is_valid


@pytest.mark.parametrize('text,is_valid', (
    ('name', True),
    ('你好', False),
    ('    ', False),
    ('   name', False),
    ('\n\n\n', False),
    ('name\n', False),
    ('000', False),
    ('a000', True),
))
def test_label_name(text, is_valid):
    assert validate.label_name(text) is is_valid
