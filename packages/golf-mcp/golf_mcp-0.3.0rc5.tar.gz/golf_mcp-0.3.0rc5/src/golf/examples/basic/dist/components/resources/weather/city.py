"Weather resource template example with URI parameters."

from datetime import datetime
from typing import Any
from components.resources.weather.client import weather_client

resource_uri = 'weather://city/{city}'

async def get_weather_for_city(city: str) -> dict[str, Any]:
    """Provide current weather for a specific city.

    This example demonstrates:
    1. Resource templates with URI parameters ({city})
    2. Dynamic resource access based on parameters
    3. Using shared client from the client.py file
    4. FastMCP 2.11+ ResourceTemplate.from_function() usage

    Args:
        city: The city name to get weather for

    Returns:
        Weather data for the specified city
    """
    weather_data = await weather_client.get_current(city)
    weather_data.update({'city': city, 'time': datetime.now().isoformat(), 'source': 'GolfMCP Weather API', 'unit': 'fahrenheit', 'resource_type': 'template'})
    return weather_data
export = get_weather_for_city