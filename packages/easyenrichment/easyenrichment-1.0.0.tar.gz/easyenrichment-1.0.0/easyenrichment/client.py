"""Easy Enrichment API client for Python.

Enrich bank transaction descriptions with merchant name, logo, category,
subscription detection, and more. A powerful alternative to Plaid Enrich,
Ntropy, and Mastercard Ethoca.

Usage:
    from easyenrichment import EasyEnrichment

    client = EasyEnrichment("your-api-key")
    result = client.enrich("AMZN Mktp US*RT5KN1Y24")
    print(result["data"]["merchant_name"])  # "Amazon"
"""

from typing import Any, Dict, List, Optional

import requests

from .exceptions import EasyEnrichmentError

__version__ = "1.0.0"


class EasyEnrichment:
    """Client for the Easy Enrichment Transaction Enrichment API.

    Args:
        api_key: Your Easy Enrichment API key. Get one at https://easyenrichment.com
        base_url: API base URL. Defaults to https://api.easyenrichment.com
        timeout: Request timeout in seconds. Defaults to 30.

    Example:
        >>> client = EasyEnrichment("your-api-key")
        >>> result = client.enrich("NETFLIX.COM")
        >>> print(result["data"]["merchant_name"])
        'Netflix'
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.easyenrichment.com",
        timeout: int = 30,
    ):
        if not api_key:
            raise EasyEnrichmentError(
                "API key is required. Get one at https://easyenrichment.com",
                code="MISSING_API_KEY",
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"easyenrichment-python/{__version__}",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Easy Enrichment API.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path (e.g., '/enrich').
            json: Optional JSON body for POST requests.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            EasyEnrichmentError: If the API returns an error or the request fails.
        """
        url = f"{self.base_url}{path}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            raise EasyEnrichmentError(
                f"Request timed out after {self.timeout}s",
                code="TIMEOUT",
            )
        except requests.exceptions.ConnectionError:
            raise EasyEnrichmentError(
                "Failed to connect to Easy Enrichment API. Check your network connection.",
                code="CONNECTION_ERROR",
            )
        except requests.exceptions.RequestException as e:
            raise EasyEnrichmentError(
                f"Request failed: {str(e)}",
                code="REQUEST_ERROR",
            )

        # Try to parse JSON response
        try:
            data = response.json()
        except ValueError:
            raise EasyEnrichmentError(
                f"Invalid JSON response from API (HTTP {response.status_code})",
                code="INVALID_RESPONSE",
                status=response.status_code,
            )

        # Handle error responses
        if not response.ok:
            error_message = data.get("error", data.get("message", "Unknown API error"))
            error_code = data.get("code", "API_ERROR")
            raise EasyEnrichmentError(
                message=error_message,
                code=error_code,
                status=response.status_code,
            )

        return data

    def enrich(self, description: str) -> Dict[str, Any]:
        """Enrich a single bank transaction description.

        Takes a raw transaction description (e.g., 'AMZN Mktp US*RT5KN1Y24')
        and returns enriched data including merchant name, logo, category,
        subscription status, and more.

        Args:
            description: The raw bank transaction description to enrich.

        Returns:
            Dictionary containing the enriched transaction data.
            See EnrichResponse type for full structure.

        Raises:
            EasyEnrichmentError: If the API returns an error.

        Example:
            >>> client = EasyEnrichment("your-api-key")
            >>> result = client.enrich("APPLE.COM/BILL")
            >>> print(result["data"]["merchant_name"])
            'Apple'
            >>> print(result["data"]["is_subscription"])
            True
        """
        return self._request("POST", "/enrich", json={"description": description})

    def enrich_batch(self, transactions: List[str]) -> Dict[str, Any]:
        """Enrich multiple bank transaction descriptions in a single request.

        More efficient than calling enrich() multiple times. Supports up to
        100 transactions per batch request.

        Args:
            transactions: List of raw transaction description strings.

        Returns:
            Dictionary containing a list of enriched transaction results.
            See BatchResponse type for full structure.

        Raises:
            EasyEnrichmentError: If the API returns an error.

        Example:
            >>> client = EasyEnrichment("your-api-key")
            >>> result = client.enrich_batch([
            ...     "NETFLIX.COM",
            ...     "UBER *EATS",
            ...     "AMZN Mktp US*RT5KN1Y24",
            ... ])
            >>> for item in result["data"]:
            ...     print(item["merchant_name"])
            'Netflix'
            'Uber Eats'
            'Amazon'
        """
        return self._request(
            "POST", "/enrich/batch", json={"transactions": transactions}
        )

    def usage(self) -> Dict[str, Any]:
        """Get current API usage statistics.

        Returns the number of API requests used and remaining in the
        current billing period.

        Returns:
            Dictionary containing usage information.
            See UsageResponse type for full structure.

        Raises:
            EasyEnrichmentError: If the API returns an error.

        Example:
            >>> client = EasyEnrichment("your-api-key")
            >>> usage = client.usage()
            >>> print(f"Used: {usage['requests_used']} / {usage['requests_limit']}")
        """
        return self._request("GET", "/usage")

    def balance(self) -> Dict[str, Any]:
        """Get current account balance.

        Returns the current balance and currency for your
        Easy Enrichment account.

        Returns:
            Dictionary containing balance information.
            See BalanceResponse type for full structure.

        Raises:
            EasyEnrichmentError: If the API returns an error.

        Example:
            >>> client = EasyEnrichment("your-api-key")
            >>> balance = client.balance()
            >>> print(f"Balance: ${balance['balance']:.2f} {balance['currency']}")
        """
        return self._request("GET", "/balance")
