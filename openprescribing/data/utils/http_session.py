import shutil
import time
from urllib.parse import urljoin

import requests
from requests.models import HTTPError


class HTTPSession(requests.Session):
    """
    Tiny wrapper around `requests.Session` to support:
     * setting a base URL;
     * automatically raising exceptions for failed requests;
     * logging;
     * downloading large responses to disk.
    """

    def __init__(self, url_base, log=None):
        self.url_base = url_base
        self.log = log
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        abs_url = urljoin(self.url_base, url)
        response = super().request(method, abs_url, *args, **kwargs)
        response.raise_for_status()
        return response

    def get(self, url, retries=3, **kwargs):
        for attempt in range(1, retries + 1):  # pragma: no branch
            try:
                return super().get(url, **kwargs)
            except HTTPError:
                if attempt == retries:
                    raise
                if self.log:
                    self.log(f"Retrying... (attempt {attempt} failed)")
                time.sleep(1)

    def send(self, prepared_request, **kwargs):
        if self.log:
            self.log(f"{prepared_request.method} {prepared_request.url}")
        return super().send(prepared_request, **kwargs)

    def download_to_file(self, url, output_path, buffer_size=32 * 1024, **kwargs):
        response = self.get(url, stream=True, **kwargs)
        with output_path.open("wb") as output_file:
            shutil.copyfileobj(response.raw, output_file, buffer_size)
