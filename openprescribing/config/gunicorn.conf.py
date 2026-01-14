# This would be best exercised by some form of Docker smoketest which tries to launch
# the app and connect to it. But that won't show up in coverage so we'll still have to
# exclude it here.
# pragma: no cover file
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


wsgi_app = "openprescribing.config.wsgi"

# Using threads rather than separate processes for parallelism has a bad reputation in
# Python because the Global Interpreter Lock (GIL) can prevent work actually getting
# done in parallel. The OpenPrescribing app is unusual in a couple of respects:
#
#  1. Almost all the CPU-bound heavy lifting is done by third-party modules (duckdb,
#     sqlite3, numpy, pyarrow) which release the GIL during execution.
#
#  2. It relies on the standard library `functools.cache` decorator to hold expensive
#     results in memory. This is shared between threads but not between processes.
#
# For these reasons we're better off having a single worker process running multiple
# threads than using the more traditional gunicorn setup of multiple worker processes.

worker_class = "gthread"
# Use environment variables so we can adjust the default settings rapildy without
# needing to redeploy
workers = int(os.environ.get("GUNICORN_WORKERS", 1))
threads = int(os.environ.get("GUNICORN_THREADS", os.cpu_count()))


# Because of Gunicorn's pre-fork web server model, we need to initialise opentelemetry
# in gunicorn's post_fork method in order to instrument our application process, see:
# https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/README.html
def post_fork(server, worker):
    # opentelemetry initialisation needs this, so ensure its set
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openprescribing.config.settings")
    os.environ.setdefault("PYTHONPATH", "")
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    resource = Resource.create(attributes={"service.name": "openprescribing-v2"})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
        span_processor = BatchSpanProcessor(OTLPSpanExporter())
        trace.get_tracer_provider().add_span_processor(span_processor)

    from opentelemetry.instrumentation.auto_instrumentation import (  # noqa: F401
        sitecustomize,
    )
