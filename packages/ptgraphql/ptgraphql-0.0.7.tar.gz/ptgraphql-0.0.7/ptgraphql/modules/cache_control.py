"""
GraphQL cache control test

This module implements a test to see if a GraphQL server enforces a secure cache control policy or not.

Contains:
- CacheControl to perform the cache control test
- run() function as an entry point for running the test
"""
import urllib.parse

from ptlibs.ptjsonlib import PtJsonLib
from ptlibs.http.http_client import HttpClient
from argparse import Namespace
from ptlibs.ptprinthelper import ptprint
from requests import Response

__TESTLABEL__ = "GraphQL cache control test"


class CacheControl:
    """Class for executing the GraphQL cache control test"""
    def __init__(self, args: Namespace, ptjsonlib: PtJsonLib, helpers: object, http_client: HttpClient, supported_methods) -> None:
        self.args = args
        self.ptjsonlib = ptjsonlib
        self.helpers = helpers
        self.http_client = http_client
        self.supported_methods = supported_methods

        self.helpers.print_header(__TESTLABEL__)


    def _vulnerable_headers(self, response: Response) -> bool:
        """
        This method checks the HTTP response headers from the server to see if they return a Cache-Control header.
        If they do, the method checks if they are set to no-cache, no-store or must-revalidate.
        
        Args:
            response: 
                Server HTTP response
        Returns
        -------
        bool
            True if the headers are not set to no-cache, no-store or must-revalidate or the Cache-Control header is missing. False otherwise
        """
        cc_headers = response.headers.get("cache-control", "").lower()

        if not cc_headers:
            return True

        ptprint(f"Cache-Control headers: {cc_headers}", "ADDITIONS", self.args.verbose, indent=4, colortext=True)
        cc_headers = set(cc_headers.split(", "))

        return not any(cc_headers.intersection({"no-cache", "no-store", "must-revalidate"}))


    def run(self) -> None:
        """
        Executes the GraphQL cache control test
        
        Checks the HTTP response Cache-Control headers to see if they enforce a secure cache-control policy
        """
        payload = {"query": "query{__typename}"}

        response = self.helpers.send_request(self.supported_methods, payload)

        if self._vulnerable_headers(response):
            ptprint("The host enforces an insecure cache-control policy", "VULN", not self.args.json, indent=4)
            self.ptjsonlib.add_vulnerability("PTV-CACHE-CONTROL")
        else:
            ptprint("The host enforces a secure cache-control policy", "OK", not self.args.json, indent=4)


def run(args, ptjsonlib, helpers, http_client, supported_methods):
    """Entry point for running the CacheControl test"""
    CacheControl(args, ptjsonlib, helpers, http_client, supported_methods).run()
