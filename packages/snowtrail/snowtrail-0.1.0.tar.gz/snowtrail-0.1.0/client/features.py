import pandas as pd
from client.client import SnowtrailClient

class FeaturesClient:
    def __init__(self, client: SnowtrailClient):
        self.client = client

    def get(
        self,
        name: str,
        start: str | None = None,
        end: str | None = None,
        as_of: str | None = None,
    ) -> pd.DataFrame:
        params = {
            "start": start,
            "end": end,
            "as_of": as_of,
        }

        params = {k: v for k, v in params.items() if v is not None}

        data = self.client._get(f"/features/{name}", params=params)
        return pd.DataFrame(data)
