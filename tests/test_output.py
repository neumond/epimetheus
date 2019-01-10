import math

import pytest
from epimetheus import output


@pytest.mark.parametrize('inp,out', (
    ('text', 'text'),
    ('"', '/"'),
    ('/', '//'),
    ('/"', '///"'),
    ('\n', '/n'),
    ('/\n/', '///n//'),
))
def test_label_value(inp, out):
    inp = inp.replace('/', '\\')
    out = out.replace('/', '\\')
    assert output.label_value(inp) == out


def test_label_set():
    assert output.label_set({'status': '500'}) == \
        r'{status="500"}'
    assert output.label_set({'status': '500', 'endpoint': '/path'}) == \
        r'{status="500",endpoint="/path"}'
    assert output.label_set({'value': '"'}) == \
        r'{value="\""}'


@pytest.mark.parametrize('inp,out', (
    (0, '0'),
    (1, '1'),
    (0.1, '0.1'),
    (math.inf, 'Inf'),
    (-math.inf, '-Inf'),
    (math.nan, 'Nan'),
))
def test_sample_value(inp, out):
    assert output.sample_value(inp) == out
