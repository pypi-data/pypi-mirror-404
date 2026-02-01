from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.resources import Resource, ResourceTemplate
from fastmcp.prompts import Prompt
import os
import sys
from dotenv import load_dotenv
import logging

# Suppress FastMCP INFO logs
logging.getLogger("FastMCP").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)

# Golf utilities for MCP features (available for tool functions)
# from golf.utilities import elicit, sample, get_current_context

import os
import sys
from golf.auth.factory import create_auth_provider
from golf.auth.providers import (
    RemoteAuthConfig,
    JWTAuthConfig,
    StaticTokenConfig,
    OAuthServerConfig,
    OAuthProxyConfig,
)

# Import tools
import components.tools.calculator
import components.tools.say.hello

# Import resources
import components.resources.current_time
import components.resources.info
import components.resources.weather.city
import components.resources.weather.forecast
import components.resources.weather.current

# Import prompts
import components.prompts.welcome


# Load environment variables from .env file if it exists
# Note: dotenv will not override existing environment variables by default
load_dotenv()

# Modern FastMCP 2.11+ authentication setup with embedded configuration
auth_config = StaticTokenConfig(
    provider_type="static",
    tokens={
        "dev-token-123": {"client_id": "dev-client", "scopes": ["read", "write"]},
        "admin-token-456": {
            "client_id": "admin-client",
            "scopes": ["read", "write", "admin"],
        },
    },
    required_scopes=["read"],
)
try:
    auth_provider = create_auth_provider(auth_config)
    # Authentication configured with {auth_config.provider_type} provider
except Exception as e:
    print(f"Authentication setup failed: {e}", file=sys.stderr)
    auth_provider = None

# Create FastMCP server
mcp = FastMCP("basic-server-example", auth=auth_provider)

# Register tools
# Register the tool 'calculator' from components.tools.calculator
_tool = Tool.from_function(
    components.tools.calculator.calculate,
    name="calculator",
    description='Evaluate a mathematical expression with optional LLM explanation.\n\nThis enhanced calculator can:\n- Perform basic arithmetic operations (+, -, *, /, parentheses)\n- Handle decimal numbers\n- Optionally provide LLM-powered step-by-step explanations\n\nExamples:\n- calculate("2 + 3") → 5\n- calculate("10 * 5.5") → 55.0\n- calculate("(8 - 3) * 2", explain=True) → 10 with explanation',
)
mcp.add_tool(_tool)
# Register the tool 'hello_say' from components.tools.say.hello
_tool = Tool.from_function(
    components.tools.say.hello.hello,
    name="hello_say",
    description='Say hello with optional personalized elicitation.\n\nThis enhanced tool can:\n- Provide basic greetings\n- Elicit additional personal information for personalized messages\n- Demonstrate Golf\'s elicitation capabilities\n\nExamples:\n- hello("Alice") → "Hello, Alice!"\n- hello("Bob", personalized=True) → Asks for details, then personalized greeting',
)
mcp.add_tool(_tool)

# Register resources
# Register the resource 'current_time' from components.resources.current_time
_resource = Resource.from_function(
    components.resources.current_time.current_time,
    uri="system://time",
    name="current_time",
    description="Provide the current time in various formats.\n\nThis is a simple resource example that returns time in all formats.",
)
mcp.add_resource(_resource)
# Register the resource 'info' from components.resources.info
_resource = Resource.from_function(
    components.resources.info.info,
    uri="info://system",
    name="info",
    description="Provide system information as a resource.\n\nThis is a simple example resource that demonstrates how to expose\ndata to an LLM client through the MCP protocol.",
)
mcp.add_resource(_resource)
# Register the resource template 'city_weather' from components.resources.weather.city
_template = ResourceTemplate.from_function(
    components.resources.weather.city.get_weather_for_city,
    uri_template="weather://city/{city}",
    name="city_weather",
    description="Provide current weather for a specific city.\n\nThis example demonstrates:\n1. Resource templates with URI parameters ({city})\n2. Dynamic resource access based on parameters\n3. Using shared client from the client.py file\n4. FastMCP 2.11+ ResourceTemplate.from_function() usage\n\nArgs:\n    city: The city name to get weather for\n\nReturns:\n    Weather data for the specified city",
)
mcp.add_template(_template)
# Register the resource 'forecast_weather' from components.resources.weather.forecast
_resource = Resource.from_function(
    components.resources.weather.forecast.forecast_weather,
    uri="weather://forecast",
    name="forecast_weather",
    description="Provide a weather forecast for a default city.\n\nThis example demonstrates:\n1. Nested resource organization (resources/weather/forecast.py)\n2. Resource without URI parameters\n3. Using shared client from the client.py file",
)
mcp.add_resource(_resource)
# Register the resource 'current_weather' from components.resources.weather.current
_resource = Resource.from_function(
    components.resources.weather.current.current_weather,
    uri="weather://current",
    name="current_weather",
    description="Provide current weather for a default city.\n\nThis example demonstrates:\n1. Nested resource organization (resources/weather/current.py)\n2. Resource without URI parameters\n3. Using shared client from the client.py file",
)
mcp.add_resource(_resource)

# Register prompts
# Register the prompt 'welcome' from components.prompts.welcome
_prompt = Prompt.from_function(
    components.prompts.welcome.welcome,
    name="welcome",
    description="Provide a welcome prompt for new users.\n\nThis is a simple example prompt that demonstrates how to define\na prompt template in GolfMCP.",
)
mcp.add_prompt(_prompt)


# Add OAuth metadata routes from auth provider
if auth_provider and hasattr(auth_provider, "get_routes"):
    auth_routes = auth_provider.get_routes()
    if auth_routes:
        # Add routes to FastMCP's additional HTTP routes list
        try:
            mcp._additional_http_routes.extend(auth_routes)
            # Added {len(auth_routes)} OAuth metadata routes
        except Exception as e:
            print(f"Warning: Failed to add OAuth routes: {e}")


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    # Get configuration from environment variables or use defaults
    host = os.environ.get("HOST", "localhost")
    port = int(os.environ.get("PORT", 3000))
    transport_to_run = "http"

    from middleware import *
    from starlette.middleware import Middleware

    middleware = [
        Middleware(RequestLoggingMiddleware()),
        Middleware(SecurityHeadersMiddleware()),
    ]

    # Run HTTP server with middleware using FastMCP's run method
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        log_level="info",
        middleware=middleware,
        show_banner=False,
    )
