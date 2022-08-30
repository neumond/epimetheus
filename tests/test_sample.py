import math

import pytest
from epimetheus.sample import SampleKey, SampleValue


class TestExposeOutput:
    @pytest.mark.parametrize('inp,out', (
        ('text', 'text'),
        ('"', '/"'),
        ('/', '//'),
        ('/"', '///"'),
        ('\n', '/n'),
        ('/\n/', '///n//'),
    ))
    def test_label_value(self, inp, out):
        inp = inp.replace('/', '\\')
        out = out.replace('/', '\\')
        assert SampleKey.expose_label_value(inp) == out

    def test_label_set(self):
        assert SampleKey.expose_label_set({'status': '500'}) == \
            r'{status="500"}'
        assert SampleKey.expose_label_set(
            {'status': 500, 'endpoint': '/path'}
        ) == r'{status="500",endpoint="/path"}'
        assert SampleKey.expose_label_set({'value': '"'}) == \
            r'{value="\""}'

    @pytest.mark.parametrize('inp,out', (
        (0, '0'),
        (1, '1'),
        (0.1, '0.1'),
        (math.inf, 'Inf'),
        (-math.inf, '-Inf'),
        (math.nan, 'Nan'),
    ))
    def test_sample_value(self, inp, out):
        assert SampleValue.expose_value(inp) == out


class TestValidation:
    def _do_test(self, fn, is_valid):
        if is_valid:
            fn()
        else:
            with pytest.raises(ValueError):
                fn()

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
        ('a:b', False),  # colons are reserved for prometheus rules
    ))
    def test_metric_name(self, text, is_valid):
        def do():
            SampleKey(name=text)

        self._do_test(do, is_valid)

    @pytest.mark.parametrize('text,is_valid', (
        ('name', True),
        ('你好', False),
        ('    ', False),
        ('   name', False),
        ('\n\n\n', False),
        ('name\n', False),
        ('000', False),
        ('a000', True),
        ('_name', True),
        # Label names beginning with __ are reserved for internal use
        ('__name', False),
        ('___name', False),
    ))
    def test_label_name(self, text, is_valid):
        def do():
            SampleKey(name='name', labels={text: 'value'})

        self._do_test(do, is_valid)


class TestSampleKey:
    def test_equality(self):
        ski = SampleKey(name='name', labels={'x': 3})
        sks = SampleKey(name='name', labels={'x': '3'})
        assert ski == sks

    def test_equality2(self):
        a = SampleKey(name='name', labels={'a': 1, 'b': 2})
        b = SampleKey(name='name', labels={'b': 2, 'a': 1})
        assert a == b

        d = {}
        d[a] = 3
        d[b] = 4
        assert d[a] == 4

    def test_hashable(self):
        hash(SampleKey(name='name'))
        hash(SampleKey(name='name', labels={'x': 3}))

    def test_label_order(self):
        k = SampleKey(name='name', labels={'k': 1, 'a': 2})
        assert k.expose() == 'name{k="1",a="2"}'
        kb = k.with_labels(b=3)
        assert kb.expose() == 'name{k="1",a="2",b="3"}'
