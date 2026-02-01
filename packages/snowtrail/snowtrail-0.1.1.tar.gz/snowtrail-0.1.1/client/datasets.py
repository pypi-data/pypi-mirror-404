import pandas as pd
from client.client import SnowtrailClient

class DatasetRegistryClient:
    def __init__(self, client: SnowtrailClient):
        self.client = client

    def list(self) -> pd.DataFrame:
        data = self.client._get("/datasets")
        return pd.DataFrame(data)

    def describe(self, dataset: str) -> dict:
        return self.client._get(f"/datasets/{dataset}")
