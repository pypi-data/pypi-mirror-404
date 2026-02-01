"""Auth module for GolfMCP."""

# Legacy ProviderConfig removed in Golf 0.2.x - use modern auth configurations
# Legacy OAuth imports removed in Golf 0.2.x - use FastMCP 2.11+ auth providers
from golf.auth.helpers import extract_token_from_header, get_api_key, set_api_key
from golf.auth.api_key import configure_api_key, get_api_key_config
from golf.auth.factory import create_auth_provider
from golf.auth.providers import RemoteAuthConfig, JWTAuthConfig, StaticTokenConfig, OAuthServerConfig
