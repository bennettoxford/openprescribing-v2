# This would be best exercised by some form of Docker smoketest which tries to launch
# the app and connect to it. But that won't show up in coverage so we'll still have to
# exclude it here.
# pragma: no cover file
import os


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
