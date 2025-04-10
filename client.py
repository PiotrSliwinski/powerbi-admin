import requests
import logging
from auth import PowerBIAuth

logger = logging.getLogger(__name__)

class PowerBIClient:
    """Base client for interacting with the Power BI REST API."""

    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    def __init__(self, auth: PowerBIAuth):
        self.auth = auth
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        """Returns the headers required for API requests."""
        access_token = self.auth.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Makes a request to the Power BI API.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            endpoint: API endpoint path (relative to BASE_URL).
            **kwargs: Additional arguments passed to requests.request.

        Returns:
            requests.Response: The API response.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        logger.debug(f"Making {method} request to {url}")
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logger.debug(f"Request successful: {response.status_code}")
            return response
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred: {req_err}")
            raise

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """Sends a GET request to the API.

        Args:
            endpoint: API endpoint path.
            params: Optional query parameters.

        Returns:
            dict: The JSON response from the API.
        """
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def post(self, endpoint: str, json: dict | None = None) -> dict:
        """Sends a POST request to the API.

        Args:
            endpoint: API endpoint path.
            json: Optional JSON payload.

        Returns:
            dict: The JSON response from the API.
        """
        response = self._request("POST", endpoint, json=json)
        # Handle cases where POST might not return JSON (e.g., 204 No Content)
        if response.status_code == 204:
            return {}
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
             logger.warning(f"POST request to {endpoint} did not return JSON. Status: {response.status_code}")
             return {}

    # Add methods for PUT, DELETE, PATCH as needed
    def delete(self, endpoint: str, params: dict | None = None) -> dict:
        """Sends a DELETE request to the API.

        Args:
            endpoint: API endpoint path.
            params: Optional query parameters.

        Returns:
            dict: The JSON response from the API, or an empty dict for 204 No Content.
        """
        response = self._request("DELETE", endpoint, params=params)
        # Handle cases where DELETE might not return JSON (e.g., 204 No Content or 200 OK with no body)
        if response.status_code in [200, 204] and not response.content:
             logger.debug(f"DELETE request to {endpoint} successful with status {response.status_code} and no content.")
             return {}
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
             logger.warning(f"DELETE request to {endpoint} did not return JSON. Status: {response.status_code}")
             return {} 