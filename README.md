This library provides primitives to create prometheus metrics text report.
Usually you output this as text at some address, e.g. `/metrics`.
Library doesn't assume any framework, sync or async app, and doesn't
provide any integrations. It's easy to integrate and use though.


```py
from epimetheus import Registry

registry = Registry()
c = registry.counter(
    name='http_requests_total',
    labels={'instance': 'dev'},
    use_clock=False,
)
c.with_labels(url='/hello', code=200).inc(3)
c.with_labels(url='/notexists', code=404).inc()
c.with_labels().inc(5)

print('\n'.join(registry.expose()))
```

Output is just a text:

```
# TYPE http_requests_total counter
http_requests_total{instance="dev",url="/hello",code="200"} 3
http_requests_total{instance="dev",url="/notexists",code="404"} 1
http_requests_total{instance="dev"} 5
```

That text must be exposed via HTTP to be collected by Prometheus.
E.g., with aiohttp library:

```py
from random import gauss
from math import floor, sin
from time import time

from aiohttp import web
from epimetheus import Registry


registry = Registry()
hello_counter = registry.counter(name='hello_total', use_clock=False)
hello_output = registry.summary(name='hello_output', buckets=[0.1, 0.5, 0.9])
temperature = registry.gauge(name='temperature')


def measure_temperature():
    # fake values for illustration
    return 60 + sin(time() / 600) * 20 + gauss(0, 1)


async def hello(request):
    hello_counter.with_labels().inc()
    output = floor(gauss(0, 20))
    hello_output.with_labels().observe(output)
    return web.Response(text=f'Hello, world! Output is {output}.')


async def metrics(_):
    # You may update some values only when necessary
    temperature.with_labels().set(measure_temperature())

    text = '\n'.join(registry.expose())
    return web.Response(text=text, headers={
        # Prometheus recommended header
        'Content-Type': 'text/plain; version=0.0.4',
    })


app = web.Application()
app.add_routes([
    web.get('/', hello),
    web.get('/metrics', metrics),
])
web.run_app(app)
```
