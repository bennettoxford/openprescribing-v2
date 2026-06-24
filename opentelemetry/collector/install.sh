#!/bin/bash
set -eu -o pipefail

# Installs the binary and configuration files to TARGET_DIR.
# The binary should already exist in this directory.

TARGET_DIR=/opt/opentelemetry/collector

mkdir -p "$TARGET_DIR"

cp secrets-dotenv-sample secrets.env

cp ./* "$TARGET_DIR"

chown -R openprescribing:openprescribing "$TARGET_DIR"

systemctl enable "$TARGET_DIR/collector.service"

systemctl start collector.service || {
	journalctl -u collector.service
	exit 1
}
