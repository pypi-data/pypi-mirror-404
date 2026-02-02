"""
GraphQL availability test

This module implements a test that checks if the provided URL is hosting GraphQL or not

Contains:
- IsGraphQL to perform the availability test
- run() function as an entry point for running the test
"""
from http import HTTPStatus
from ptlibs.ptjsonlib import PtJsonLib
from ptlibs.http.http_client import HttpClient
from argparse import Namespace
from ptlibs.ptprinthelper import ptprint
from urllib.parse import urlparse
from requests.exceptions import JSONDecodeError
from requests import Response
import os, requests

__TESTLABEL__ = "GraphQL availability test"

class IsGraphQL:
    """Class for executing the GraphQL availability test"""
    def __init__(self, args: Namespace, ptjsonlib: PtJsonLib, helpers: object, http_client: HttpClient, supported_methods: set) -> None:
        self.args = args
        self.ptjsonlib = ptjsonlib
        self.helpers = helpers
        self.http_client = http_client
        self.supported_methods = supported_methods

        self.helpers.print_header(__TESTLABEL__)


    def _check_JSON(self, response: Response) -> bool:
        """
        This method checks if the JSON response is equal to the expected response of a basic GraphQL query {"query": "query{__typename}"}.

        Parameters
        ----------
        response
            HTTP response of the host
        Returns
        -------
        bool
            True if the received response matches the expected. False otherwise
        """
        expected = [{"data": {"__typename": "Query"}}, {"data":{"__typename":"RootQueryType"}}]

        try:
            json_response = response.json()
        except JSONDecodeError as e:
            ptprint(f"Error decoding JSON from response: {e}", "ADDITIONS", self.args.verbose, indent=4, colortext=True)
            return False

        return json_response in expected


    def _check_response_GET(self, url: str, endpoint: str) -> bool:
        """
        This method test the presence of GraphQL on a given endpoint with the HTTP method GET.
        
        Parameters
        ----------
        url: str
            URL of the host
        endpoint: str
            Suspected GraphQL endpoint
            
        Returns
        -------
        bool
            True if the method detects GraphQL on the endpoint with the GET HTTP method. False otherwise
        """
        final_url = url+endpoint+"?query=query%7B__typename%7D"

        ptprint(f"Trying endpoint {url+endpoint} with method GET", "ADDITIONS", self.args.verbose, indent=4, colortext=True)
        response = self.http_client.send_request(url=final_url, method="GET", allow_redirects=True)

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            ptprint(f"The host has authentication enabled for method GET at {url+endpoint}", "OK", not self.args.json,
                    indent=4)
            return False

        if response.status_code != HTTPStatus.OK:
            ptprint(f"Could not GET {final_url}. Received status code: {response.status_code}", "ADDITIONS", self.args.verbose,
                    indent=4, colortext=True)
            return False

        return self._check_JSON(response)


    def _check_response_POST(self, url: str, endpoint: str) -> bool:
        """
        This method test the presence of GraphQL on a given endpoint with the HTTP method POST.
        
        Parameters
        ----------
        url: str
            URL of the host
        endpoint: str
            Suspected GraphQL endpoint
            
        Returns
        -------
        bool
            True if the method detects GraphQL on the endpoint with the POST HTTP method. False otherwise
        """
        payload = '{"query": "query{__typename}"}'

        ptprint(f"Trying {url+endpoint} with method POST", "ADDITIONS", self.args.verbose, indent=4, colortext=True)
        response = self.http_client.send_request(method="POST", url=url + endpoint, data=payload, allow_redirects=True)

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            ptprint(f"The host has authentication enabled for method POST at {url+endpoint}", "OK", not self.args.json, indent=4)
            return False

        if response.status_code != HTTPStatus.OK:
            ptprint(f"Could not POST {url+endpoint}. Received status code: {response.status_code}", "ADDITIONS",
                    self.args.verbose,
                    indent=4, colortext=True)
            return False

        return self._check_JSON(response)


    def _brute_force(self) -> str:
        """
        This method probes suspected GraphQL endpoints from a wordlist specified with the -w/--wordlist argument (default data/wordlists/endpoints.txt).
        If the response is verified with the _check_response() method to be a GraphQL response. We return a URL of the host and verified endpoint.

        Returns
        -------
        str
            URL of the verified GraphQL endpoint. Empty string if none is found
        """
        parsed = urlparse(self.args.url)
        url = parsed.scheme + "://" + parsed.netloc

        current_dir = os.path.dirname(os.path.abspath(__file__))
        wordlist_path = os.path.join(current_dir, f"../data/wordlists/endpoints.txt")

        with open(self.args.wordlist or wordlist_path, "r") as wordlist:
            endpoints = set(wordlist.read().split('\n'))

        for endpoint in endpoints:
            if self._check_response(url, endpoint):
                return url+endpoint

        return ""


    def _check_response(self, url:str, endpoint: str) -> bool:
        """
        This method tests to see if the provided endpoint hosts GraphQL or not.
        It first tries to detect GraphQL with the HTTP GET method and then with the HTTP POST method.
        If any of the HTTP methods is successful, the HTTP method is added to a set of supported HTTP methods.

        Returns
        -------
        bool
            True if any of the two HTTP methods successfully detects GraphQL
        """
        found = False

        try:
            if self._check_response_GET(url, endpoint):
                found = True
                self.supported_methods.add("GET")

            if self._check_response_POST(url, endpoint):
                found = True
                self.supported_methods.add("POST")
        except requests.exceptions.RequestException as error_msg:
            ptprint(f"Error trying to connect with HTTPS: {error_msg}.", "ADDITIONS",
                    self.args.verbose, indent=4, colortext=True)
            self.ptjsonlib.end_error(f"Error retrieving initial responses:", details=error_msg,
                                     condition=self.args.json)

        return found


    def run(self) -> None:
        """
        Executes the GraphQL availability test

        Sends the following query to test if GraphQL is present on the provided URL: {'query': 'query{__typename}'}.
        If GraphQL is not detected on the provided URL, we try to bruteforce common GraphQL endpoints with a wordlist.
        Ends with an error if GraphQL is not detected.
        """
        if self._check_response(self.args.url, ""):
            ptprint(f"{self.args.url} is hosting GraphQL. Supported methods: {", ".join(self.supported_methods)}", "VULN", not self.args.json, indent=4)
            return
        else:
            if new_url := self._brute_force():
                ptprint(f"{new_url} is hosting GraphQL. Supported methods: {", ".join(self.supported_methods)}", "VULN", not self.args.json, indent=4)
                self.args.url = new_url
            else:
                self.ptjsonlib.end_error("GraphQL is not present on the provided URL.", self.args.json)


def run(args, ptjsonlib, helpers, http_client, supported_methods):
    """Entry point for running the IsGraphQL test"""
    IsGraphQL(args, ptjsonlib, helpers, http_client, supported_methods  ).run()
