"""Base HTTP client for Dremio API."""

from typing import Any, Dict, Optional, Callable
from urllib.parse import urljoin
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dremio_cli.utils.exceptions import ApiError, AuthenticationError
from dremio_cli.client.auth import refresh_oauth_token


class BaseClient:
    """Base HTTP client for Dremio API."""

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize base client.
        
        Args:
            base_url: Base URL for API
            token: Authentication token (Access Token)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            refresh_token: OAuth Refresh Token
            client_id: OAuth Client ID (for refresh)
            client_secret: OAuth Client Secret (for refresh)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _refresh_token(self) -> bool:
        """Attempt to refresh auth token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            return False
            
        try:
            # Determine base URL for auth (could be different if v0/v3 messiness, but auth.py handles logic usually)
            # auth.refresh_oauth_token expects base_url used for API usually
            new_tokens = refresh_oauth_token(
                self.base_url,
                self.refresh_token,
                self.client_id,
                self.client_secret
            )
            
            self.token = new_tokens.get("access_token")
            # Update refresh token if provided (rolling refresh)
            if "refresh_token" in new_tokens:
                self.refresh_token = new_tokens["refresh_token"]
                
            return True
        except Exception:
            # If refresh fails, we can't recover
            return False

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Internal request wrapper with 401 retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Arguments for requests.session.request
            
        Returns:
            Response data
        """
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self.timeout)
        
        # First attempt
        kwargs["headers"] = self._get_headers()
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise ApiError(f"Request failed: {e}")

        # Check for 401 and attempt refresh
        if response.status_code == 401 and self.refresh_token:
            if self._refresh_token():
                # Retry with new token
                kwargs["headers"] = self._get_headers()
                try:
                    response = self.session.request(method, url, **kwargs)
                except requests.RequestException as e:
                    raise ApiError(f"Retry request failed: {e}")

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response.
        
        Args:
            response: HTTP response
            
        Returns:
            Parsed JSON response
            
        Raises:
            AuthenticationError: If authentication fails
            ApiError: If API request fails
        """
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed. Token expired or invalid.")
        
        if response.status_code == 403:
            raise ApiError("Access forbidden. Check your permissions.", status_code=403)
        
        if response.status_code == 404:
            raise ApiError("Resource not found.", status_code=404)
        
        if not response.ok:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if "errorMessage" in error_data:
                    error_msg = error_data["errorMessage"]
                    if "moreInfo" in error_data:
                        error_msg += f": {error_data['moreInfo']}"
            except Exception:
                error_msg += f": {response.text}"
            
            raise ApiError(error_msg, status_code=response.status_code, response_body=response.text)
        
        # Return empty dict for 204 No Content
        if response.status_code == 204:
            return {}
        
        try:
            return response.json()
        except Exception:
            return response.text

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, json=data)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PUT", endpoint, json=data)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PATCH", endpoint, json=data)
