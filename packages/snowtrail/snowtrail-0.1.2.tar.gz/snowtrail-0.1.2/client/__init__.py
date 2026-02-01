from client.client import SnowtrailClient
from client.signals import SignalsClient
from client.features import FeaturesClient
from client.events import EventsClient
from client.datasets import DatasetRegistryClient
from client.stacks import StacksClient

class Snowtrail:
    """Main client for Snowtrail Research APIs."""
    def __init__(self, base_url: str, api_key: str | None = None, timeout: int = 30):
        client = SnowtrailClient(base_url=base_url, api_key=api_key, timeout=timeout)

        self.stacks = StacksClient(client)
        self.signals = SignalsClient(client)
        self.features = FeaturesClient(client)
        self.events = EventsClient(client)
        self.datasets = DatasetRegistryClient(client)
