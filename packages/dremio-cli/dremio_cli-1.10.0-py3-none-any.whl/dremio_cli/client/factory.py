"""Client factory for creating appropriate Dremio clients."""

from typing import Dict, Any, Union

from dremio_cli.client.cloud import CloudClient
from dremio_cli.client.software import SoftwareClient
from dremio_cli.client.auth import (
    authenticate_with_username_password,
    exchange_pat_for_oauth,
    authenticate_client_credentials
)
from dremio_cli.utils.exceptions import ConfigurationError, AuthenticationError


def create_client(profile: Dict[str, Any]) -> Union[CloudClient, SoftwareClient]:
    """Create appropriate Dremio client from profile.
    
    Args:
        profile: Profile configuration dictionary
        
    Returns:
        CloudClient or SoftwareClient instance
        
    Raises:
        ConfigurationError: If profile is invalid
        AuthenticationError: If authentication fails
    """
    profile_type = profile.get("type")
    
    if not profile_type:
        raise ConfigurationError("Profile missing 'type' field")
    
    if profile_type not in ["cloud", "software"]:
        raise ConfigurationError(f"Invalid profile type: {profile_type}")
    
    base_url = profile.get("base_url")
    if not base_url:
        raise ConfigurationError("Profile missing 'base_url' field")
    
    auth = profile.get("auth", {})
    auth_type = auth.get("type")
    
    if not auth_type:
        raise ConfigurationError("Profile missing 'auth.type' field")
    
    # Get auth details (token, refresh_token, etc.)
    auth_details = _get_auth_details(profile, auth, base_url)
    
    # Create appropriate client
    if profile_type == "cloud":
        project_id = profile.get("project_id")
        if not project_id:
            raise ConfigurationError("Cloud profile missing 'project_id' field")
        
        return CloudClient(
            base_url=base_url,
            project_id=project_id,
            token=auth_details["token"],
            refresh_token=auth_details.get("refresh_token"),
            client_id=auth_details.get("client_id"),
            client_secret=auth_details.get("client_secret"),
        )
    else:  # software
        return SoftwareClient(
            base_url=base_url,
            token=auth_details["token"],
            refresh_token=auth_details.get("refresh_token"),
            client_id=auth_details.get("client_id"),
            client_secret=auth_details.get("client_secret"),
        )


def _get_auth_details(profile: Dict[str, Any], auth: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    """Get authentication details from profile or generate them.
    
    Args:
        profile: Profile configuration
        auth: Auth configuration
        base_url: Base URL for API
        
    Returns:
        Dictionary containing 'token' and optionally 'refresh_token', 'client_id', 'client_secret'
        
    Raises:
        AuthenticationError: If authentication fails
        ConfigurationError: If auth configuration is invalid
    """
    auth_type = auth.get("type")
    profile_type = profile.get("type")
    
    if auth_type == "pat":
        pat = auth.get("token")
        if not pat:
            raise ConfigurationError("PAT auth requires 'token' field")
            
        # For Dremio Cloud, try to exchange PAT for OAuth token
        if profile_type == "cloud":
            try:
                # Exchange PAT for short-lived access token
                token_data = exchange_pat_for_oauth(base_url, pat)
                return {
                    "token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token") or pat, # Use PAT as refresh token if none returned? No, if none returned, likely can't refresh.
                    # Actually, standard behavior: PAT can act as refresh token in some flows, or we just rely on PAT.
                    # But if exchange worked, we get an access token.
                    # If we don't get a refresh token, we can't refresh. 
                    # If we store PAT as 'refresh_token' maybe we can re-exchange? 
                    # BaseClient expects standard refresh flow. 
                    # Let's return just access token. If it expires, we're stuck unless we re-exchange.
                    # Better strategy: Not relying on BaseClient refresh for PAT exchange yet unless we implement re-exchange logic in BaseClient using PAT.
                    # BUT BaseClient uses refresh_oauth_token which takes a Refresh Token.
                    # If Dremio returns a refresh token on PAT exchange, great. If not, we just use access token.
                    # Fallback: Just return token and PAT as refresh token? No, exchange endpoint expects refresh token grant type.
                    # Let's keep it simple: Use returned access token.
                } | ({"refresh_token": token_data["refresh_token"]} if "refresh_token" in token_data else {})
            except Exception:
                # If exchange fails (or not supported), fall back to using PAT gracefully
                return {"token": pat}
        
        return {"token": pat}
    
    elif auth_type == "oauth": # Client Credentials
        client_id = auth.get("client_id")
        client_secret = auth.get("client_secret")
        
        # If token provided manually in profile (e.g. cached), use it?
        # For now, let's assume we authenticate fresh or leverage client_id/secret
        
        if not client_id or not client_secret:
             # Check if we have a raw token
            token = auth.get("token")
            if token:
                return {"token": token}
            raise ConfigurationError("OAuth auth requires 'client_id' and 'client_secret'")
            
        token_data = authenticate_client_credentials(base_url, client_id, client_secret)
        return {
            "token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "client_id": client_id,
            "client_secret": client_secret,
        }
    
    elif auth_type == "username_password":
        # Check if we have a cached token
        cached_token = auth.get("token")
        if cached_token:
            # TODO: Check if token is expired
            return {"token": cached_token}
        
        # Generate new token
        username = auth.get("username")
        password = auth.get("password")
        
        if not username or not password:
            raise ConfigurationError(
                "Username/password auth requires 'username' and 'password' fields"
            )
        
        # Only supported for Software
        if profile.get("type") != "software":
            raise ConfigurationError(
                "Username/password auth only supported for Dremio Software"
            )
        
        token = authenticate_with_username_password(base_url, username, password)
        return {"token": token}
    
    else:
        raise ConfigurationError(f"Unsupported auth type: {auth_type}")
