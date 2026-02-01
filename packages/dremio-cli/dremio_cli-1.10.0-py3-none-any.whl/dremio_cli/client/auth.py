"""Authentication handlers for Dremio API."""

from typing import Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth

from dremio_cli.utils.exceptions import AuthenticationError


def authenticate_with_username_password(
    base_url: str,
    username: str,
    password: str,
) -> str:
    """Authenticate with username and password (Dremio Software only).
    
    Args:
        base_url: Base URL for Dremio
        username: Username
        password: Password
        
    Returns:
        Authentication token
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # Use v2 API for login
    # Normalize base_url to get root
    root_url = base_url.rstrip("/")
    if root_url.endswith("/api/v3"):
        root_url = root_url[:-7] # remove /api/v3
    
    login_url = f"{root_url}/apiv2/login"
    
    try:
        response = requests.post(
            login_url,
            json={"userName": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"Authentication failed: {response.text}")
        
        data = response.json()
        token = data.get("token")
        
        if not token:
            raise AuthenticationError("No token in authentication response")
        
        # Return raw token (BaseClient adds prefix)
        return token
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Authentication request failed: {e}")


def exchange_pat_for_oauth(
    base_url: str,
    pat: str,
) -> Dict[str, Any]:
    """Exchange PAT for OAuth token.
    
    Args:
        base_url: Base URL for Dremio
        pat: Personal Access Token
        
    Returns:
        Dictionary with access_token (and optionally refresh_token)
        
    Raises:
        AuthenticationError: If exchange fails
    """
    oauth_url = f"{base_url}/oauth/token"
    
    # Standard RFC 8693 Token Exchange params for Dremio
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": pat,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
    }
    
    try:
        response = requests.post(
            oauth_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"PAT exchange failed: {response.text}")
        
        return response.json()
        
    except requests.RequestException as e:
        raise AuthenticationError(f"PAT exchange request failed: {e}")


def authenticate_client_credentials(
    base_url: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Authenticate using OAuth Client Credentials.
    
    Args:
        base_url: Base URL for Dremio
        client_id: Client ID
        client_secret: Client Secret
        
    Returns:
        Dictionary with access_token
        
    Raises:
        AuthenticationError: If authentication fails
    """
    oauth_url = f"{base_url}/oauth/token"
    
    data = {
        "grant_type": "client_credentials"
    }
    
    try:
        # Client credentials usually sent via Basic Auth header or body
        # Dremio often accepts them in body or basic auth. Using Basic Auth is safer standard.
        response = requests.post(
            oauth_url,
            data=data,  # form-encoded for standard OAuth, but Dremio might expect JSON
                        # Dremio docs usually imply JSON body for other endpoints, but let's check.
                        # Actually standard Dremio /oauth/token often takes JSON.
                        # Let's try JSON body first as it matches other methods here.
            json=data | {"client_id": client_id, "client_secret": client_secret},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"Client credentials auth failed: {response.text}")
        
        return response.json()
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Client credentials request failed: {e}")


def refresh_oauth_token(
    base_url: str,
    refresh_token: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """Refresh OAuth token.
    
    Args:
        base_url: Base URL for Dremio
        refresh_token: Refresh token
        client_id: OAuth client ID
        client_secret: OAuth client secret
        
    Returns:
        Dictionary with new access_token and refresh_token
        
    Raises:
        AuthenticationError: If refresh fails
    """
    oauth_url = f"{base_url}/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    
    if client_id:
        data["client_id"] = client_id
    if client_secret:
        data["client_secret"] = client_secret
    
    try:
        response = requests.post(
            oauth_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"Token refresh failed: {response.text}")
        
        return response.json()
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Token refresh request failed: {e}")
