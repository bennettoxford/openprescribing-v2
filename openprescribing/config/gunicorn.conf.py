# This would be best exercised by some form of Docker smoketest which tries to launch
# the app and connect to it. But that won't show up in coverage so we'll still have to
# exclude it here.
# pragma: no cover file

wsgi_app = "openprescribing.config.wsgi"
