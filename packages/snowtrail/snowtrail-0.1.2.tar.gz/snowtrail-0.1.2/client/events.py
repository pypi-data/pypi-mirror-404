import pandas as pd
from client.client import SnowtrailClient

class EventsClient:
    """
    High-signal market events for event-driven workflows.
    Returns pandas DataFrames by default.
    """

    def __init__(self, client: SnowtrailClient):
        self.client = client

    def list(self) -> pd.DataFrame:
        """
        List available event streams (if you expose an index endpoint).
        If you don't have /events implemented as an index, you can remove this.
        """
        data = self.client._get("/events")
        return pd.DataFrame(data)

    def get(
        self,
        name: str,
        start: str | None = None,
        end: str | None = None,
        severity: str | None = None,
        limit: int | None = None,
        as_of: str | None = None,
    ) -> pd.DataFrame:
        """
        Fetch events by stream name, optionally filtered by date range,
        severity, limit, and point-in-time 'as_of' (if your API supports it).
        """
        params = {
            "start": start,
            "end": end,
            "severity": severity,
            "limit": limit,
            "as_of": as_of,
        }
        params = {k: v for k, v in params.items() if v is not None}

        data = self.client._get(f"/events/{name}", params=params)
        return pd.DataFrame(data)
