import requests
import sys
import time
from lib.tracing import init_tracer
from opentracing.ext import tags
from opentracing.propagation import Format


def say_hello(hello_to, greeting):
    with tracer.start_span('say-hello') as span:
        span.set_tag('hello-to', hello_to)
        span.set_baggage_item('greeting', greeting)
        hello_str = format_string(hello_to, span)
        print_hello(hello_str, span)

def format_string(hello_to, parent_span):
    with tracer.start_span('format', child_of=parent_span) as span:
        hello_str = http_get(8081, 'format', 'helloTo', hello_to, span)
        span.log_kv({'event': 'string-format', 'value': hello_str})
        return hello_str

def print_hello(hello_str, parent_span):
    with tracer.start_span('println', child_of=parent_span) as span:
        http_get(8082, 'publish', 'helloStr', hello_str, span)
        span.log_kv({'event': 'println'})

def http_get(port, path, param, value, span):
    url = 'http://localhost:%s/%s' % (port, path)

    span.set_tag(tags.HTTP_METHOD, 'GET')
    span.set_tag(tags.HTTP_URL, url)
    span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
    headers = {}
    tracer.inject(span, Format.HTTP_HEADERS, headers)

    r = requests.get(url, params={param: value}, headers=headers)
    assert r.status_code == 200
    return r.text
        

# main
assert len(sys.argv) == 3

tracer = init_tracer('hello-world')

hello_to = sys.argv[1]
greeting = sys.argv[2]
say_hello(hello_to, greeting)

# yield to IOLoop to flush the spans
time.sleep(2)
tracer.close()
