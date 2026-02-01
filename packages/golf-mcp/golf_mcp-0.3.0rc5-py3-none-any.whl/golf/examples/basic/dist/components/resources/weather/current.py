"Current weather resource example."

from datetime import datetime
from typing import Any
from components.resources.weather.client import weather_client

resource_uri = 'weather://current'

async def current_weather() -> dict[str, Any]:
    """Provide current weather for a default city.

    This example demonstrates:
    1. Nested resource organization (resources/weather/current.py)
    2. Resource without URI parameters
    3. Using shared client from the client.py file
    """
    weather_data = await weather_client.get_current('New York')
    weather_data.update({'time': datetime.now().isoformat(), 'source': 'GolfMCP Weather API', 'unit': 'fahrenheit'})
    return weather_data
export = current_weather