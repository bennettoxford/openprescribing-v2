# noqa: INP001
# We don't need an `__init__.py` in `scripts`

# This is tested implicitly as part of the docker build
# pragma: no cover file

import gzip
import re
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import requests


def install_sqlite_extension():
    extension_dir = Path(sys.prefix) / "duckdb"
    conn = duckdb.connect(config={"extension_directory": str(extension_dir)})
    # INSTALL is a no-op if the extension's already installed but we only want to show a
    # message if we're actually installing something
    result = conn.sql(
        "SELECT installed FROM duckdb_extensions() WHERE extension_name='sqlite_scanner'"
    )
    if not result.fetchone()[0]:
        print(f"Installing DuckDB SQLite extension to {extension_dir}")
        conn.sql("INSTALL sqlite_scanner")


def install_cli():
    lib_version = duckdb.__version__

    target_bin = Path(sys.prefix) / "bin" / "duckdb"
    if target_bin.exists():
        version_cmd = subprocess.run(
            [target_bin, "--version"], check=True, stdout=subprocess.PIPE, text=True
        )
        cli_version = re.match(r"v([^ ]+) ", version_cmd.stdout).group(1)
    else:
        cli_version = None

    if cli_version == lib_version:
        return

    url = (
        f"https://github.com/duckdb/duckdb/releases/download/"
        f"v{lib_version}/duckdb_cli-linux-amd64.gz"
    )
    print(f"Installing DuckDB v{lib_version} to {target_bin}")
    print(f"Downloading from: {url}")
    response = requests.get(url, stream=True)
    contents = gzip.open(response.raw)
    tmp_file = target_bin.with_suffix(".tmp")
    with tmp_file.open("wb") as f:
        shutil.copyfileobj(contents, f, 64 * 1024)
    tmp_file.chmod(0o755)
    tmp_file.replace(target_bin)


if __name__ == "__main__":
    install_sqlite_extension()
    install_cli()
