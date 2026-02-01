import requests

class SnowtrailClient:
    """Base HTTP client for Snowtrail Research APIs."""
    def __init__(
        self,
        base_url: str = "https://api.snowtrailresearch.com",
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
