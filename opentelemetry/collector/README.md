# OpenTelemetry Collector

We run an OpenTelemetry collector that gathers metrics from dokku5 and sends them to [Honeycomb][].
For convenience, we store the configuration files here.

* `collector.service`. The [systemd][] unit file. Configures the service.
* `config.yaml`. Configures the collector.
* `install.sh`. Installs the binary and configuration files.
* `justfile`. Commands for managing the collector. `just` isn't installed on dokku5, so these commands are included for reference.
* `secrets-dotenv-sample`. Environment variables used by the service.

Currently, the binary and collector configuration are that of
[honeycombio/opentelemetry-collector-configs][] v1.8.0.
Contra [the documentation][1],
don't use the [open-telemetry/opentelemetry-collector-releases][] binary,
as it is incompatible with the collector configuration.

[1]: https://docs.honeycomb.io/send-data/metrics/system
[Honeycomb]: https://www.honeycomb.io/
[honeycombio/opentelemetry-collector-configs]: https://github.com/honeycombio/opentelemetry-collector-configs
[open-telemetry/opentelemetry-collector-releases]: https://github.com/open-telemetry/opentelemetry-collector-releases
[systemd]: https://en.wikipedia.org/wiki/Systemd
