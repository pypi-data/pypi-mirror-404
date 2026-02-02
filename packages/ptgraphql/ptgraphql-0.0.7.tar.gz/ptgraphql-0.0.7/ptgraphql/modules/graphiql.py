"""
GraphiQL test

This module implements a test that checks if the given GraphQL instance provides the GraphiQL graphical interface

Contains:
- GraphiQL class to perform the test
- run() function as an entry point for running the test
"""
from http import HTTPStatus
from ptlibs.ptprinthelper import ptprint
from ptlibs.ptjsonlib import PtJsonLib
from ptlibs.http.http_client import HttpClient
from argparse import Namespace
from urllib.parse import urlparse
from requests import Response
import os

__TESTLABEL__ = "GraphiQL test"


class GraphiQL:
    """Class for executing the GraphiQL availability test"""

    def __init__(self, args: Namespace, ptjsonlib: PtJsonLib, helpers: object, http_client: HttpClient, supported_methods: set) -> None:
        self.args = args
        self.ptjsonlib = ptjsonlib
        self.helpers = helpers
        self.http_client = http_client
        self.supported_methods = supported_methods

        self.helpers.print_header(__TESTLABEL__)


    def _brute_force(self) -> str:
        """
        This method probes suspected GraphiQL endpoints from a wordlist specified with the -w/--wordlist argument (default data/wordlists/endpoints.txt).
        If the response contains the string 'graphiql', we return the endpoint

        :return: URL of the verified GraphiQL endpoint. Empty string if none is found
        """
        parsed = urlparse(self.args.url)
        url = parsed.scheme + "://" + parsed.netloc

        current_dir = os.path.dirname(os.path.abspath(__file__))
        wordlist_path = os.path.join(current_dir, f"../data/wordlists/endpoints.txt")

        with open(self.args.wordlist or wordlist_path, "r") as wordlist:
            endpoints = set(wordlist.read().split('\n'))

        for endpoint in endpoints:
            ptprint(f"Trying endpoint {endpoint}...", "ADDITIONS", self.args.verbose, indent=4, colortext=True)

            headers = self.args.headers.copy()
            headers.update({"Accept": "text/html"})

            response: Response = self.http_client.send_request(method="GET", url=url + endpoint,
                                                     allow_redirects=False, headers=headers, merge_headers=False)

            ptprint(f"Received response: {response.text}", "ADDITIONS", self.args.verbose, indent=4, colortext=True)

            if response.status_code != HTTPStatus.OK:
                ptprint(f"Could not get {url+endpoint}. Received status code: {response.status_code}", "ADDITIONS",
                        self.args.verbose, indent=4, colortext=True)
                continue

            elif "graphiql" in response.text.lower():
                return url+endpoint

        return ""


    def run(self) -> None:
        """
        Executes the GraphiQL test

        Sends an HTTP GET request to the GraphQL URL with the 'Accept' header set to 'text/html'. If the response contains
        the string 'graphiql' we print that we've detected GraphiQL. In the opposite case we run a dictionary attack to try
        to locate a valid GraphiQL endpoint.
        """

        headers = self.args.headers.copy()
        headers.update({"Accept": "text/html"})

        response: Response = self.http_client.send_request(method="GET",url=self.args.url, allow_redirects=False,
                                                           headers=headers, merge_headers=False)

        if "graphiql" in response.text.lower():
            ptprint(f"{self.args.url} provides GraphiQL", "VULN", not self.args.json, indent=4)
            self.ptjsonlib.add_vulnerability("PTV-GRAPHQL-GRAPHIQL")
        elif graphiql_url := self._brute_force():
            ptprint(f"{graphiql_url} provides GraphiQL", "VULN", not self.args.json, indent=4)
            self.ptjsonlib.add_vulnerability("PTV-GRAPHQL-GRAPHIQL")
        else:
            ptprint(f"Could not find GraphiQL or other graphical interfaces", "OK", not self.args.json, indent=4)


def run(args, ptjsonlib, helpers, http_client, supported_methods):
    """Entry point for running the GraphiQL test"""
    GraphiQL(args, ptjsonlib, helpers, http_client, supported_methods).run()
