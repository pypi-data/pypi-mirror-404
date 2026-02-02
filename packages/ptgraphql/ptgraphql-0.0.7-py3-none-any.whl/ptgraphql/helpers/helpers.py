"""
Helpers module for shared functionality used across test modules.
"""
from http.client import HTTPResponse

from ptlibs import ptprint
from urllib.parse import urlencode
import json

class Helpers:
    def __init__(self, args: object, ptjsonlib: object, http_client: object):
        """Helpers provides utility methods"""
        self.args = args
        self.ptjsonlib = ptjsonlib
        self.http_client = http_client

    def print_header(self, test_label):
        ptprint(f"Testing: {test_label}", "TITLE", not self.args.json, colortext=True)

    def send_request(self, supported_methods: set, payload: object) -> HTTPResponse:
        response = None

        if "POST" in supported_methods:
            response = self.http_client.send_request(url=self.args.url, method="POST", data=json.dumps(payload), allow_redirects=True)
            return response
        elif "GET" in supported_methods:
            url = self.args.url + '?' + urlencode(payload)
            response = self.http_client.send_request(url=url, method="GET", allow_redirects=True)

        return response