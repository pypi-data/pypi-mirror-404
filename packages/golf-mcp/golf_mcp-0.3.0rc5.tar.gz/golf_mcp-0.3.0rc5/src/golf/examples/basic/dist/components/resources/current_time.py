"Current time resource example."

from datetime import datetime
from typing import Any

resource_uri = 'system://time'

async def current_time() -> dict[str, Any]:
    """Provide the current time in various formats.

    This is a simple resource example that returns time in all formats.
    """
    now = datetime.now()
    all_formats = {'iso': now.isoformat(), 'rfc': now.strftime('%a, %d %b %Y %H:%M:%S %z'), 'unix': int(now.timestamp()), 'formatted': {'date': now.strftime('%Y-%m-%d'), 'time': now.strftime('%H:%M:%S'), 'timezone': now.astimezone().tzname()}}
    return all_formats
export = current_time