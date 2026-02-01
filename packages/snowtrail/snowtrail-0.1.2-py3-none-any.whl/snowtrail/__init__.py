"""
Snowtrail Research Python SDK.

Commodities intelligence for systematic trading.

Usage:
    from snowtrail import Snowtrail

    client = Snowtrail(api_key="your-api-key")

    # Get latest GBSI-US system stress signal
    df = client.gbsi_us.system_stress()

    # Get historical data
    df = client.gbsi_us.system_stress(start="2024-01-01", end="2024-12-31")

    # Access other products
    df = client.gbsi_eu.composite()
    df = client.pemi.power_stress()
    df = client.glmi.lng_stress()
    df = client.wrsi.weather_risk()
    df = client.wssi_us.weather_shock()

Products:
    - gbsi_us: US Natural Gas Balance Stress Index (weekly)
    - gbsi_eu: EU Natural Gas Balance Stress Index (daily)
    - pemi: Power Event Market Intelligence (EU power outages)
    - glmi: Global LNG Market Intelligence
    - wrsi: Weather Risk Signal Intelligence
    - wssi_us: Weather Storage Shock Index

Documentation:
    https://docs.snowtrail.ai

API Reference:
    https://api.snowtrail.ai/docs
"""
from __future__ import annotations

__version__ = "0.1.2"

from snowtrail._client import (
    APIError,
    AuthenticationError,
    HTTPClient,
    NotFoundError,
    RateLimitError,
    SnowtrailError,
)
from snowtrail._products import (
    GbsiEu,
    GbsiUs,
    Glmi,
    Pemi,
    Wrsi,
    WssiUs,
)

__all__ = [
    "Snowtrail",
    "SnowtrailError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "APIError",
]


class Snowtrail:
    """
    Main client for Snowtrail Research API.

    Provides access to all product endpoints through typed accessors.

    Args:
        api_key: API key for authentication (required for data endpoints)
        base_url: API base URL (default: https://api.snowtrail.ai)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> from snowtrail import Snowtrail
        >>> client = Snowtrail(api_key="your-api-key")
        >>> df = client.gbsi_us.system_stress()
        >>> print(df.head())

    Products:
        gbsi_us: US Natural Gas Balance Stress Index
        gbsi_eu: EU Natural Gas Balance Stress Index
        pemi: Power Event Market Intelligence
        glmi: Global LNG Market Intelligence
        wrsi: Weather Risk Signal Intelligence
        wssi_us: Weather Storage Shock Index
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.snowtrail.ai",
        timeout: int = 30,
    ):
        self._client = HTTPClient(base_url=base_url, api_key=api_key, timeout=timeout)

        # Initialize product accessors
        self._gbsi_us: GbsiUs | None = None
        self._gbsi_eu: GbsiEu | None = None
        self._pemi: Pemi | None = None
        self._glmi: Glmi | None = None
        self._wrsi: Wrsi | None = None
        self._wssi_us: WssiUs | None = None

    # --- Lazy-loaded product accessors ---

    @property
    def gbsi_us(self) -> GbsiUs:
        """US Natural Gas Balance Stress Index (weekly signals)."""
        if self._gbsi_us is None:
            self._gbsi_us = GbsiUs(self._client)
        return self._gbsi_us

    @property
    def gbsi_eu(self) -> GbsiEu:
        """EU Natural Gas Balance Stress Index (daily signals)."""
        if self._gbsi_eu is None:
            self._gbsi_eu = GbsiEu(self._client)
        return self._gbsi_eu

    @property
    def pemi(self) -> Pemi:
        """Power Event Market Intelligence (EU power outages)."""
        if self._pemi is None:
            self._pemi = Pemi(self._client)
        return self._pemi

    @property
    def glmi(self) -> Glmi:
        """Global LNG Market Intelligence."""
        if self._glmi is None:
            self._glmi = Glmi(self._client)
        return self._glmi

    @property
    def wrsi(self) -> Wrsi:
        """Weather Risk Signal Intelligence."""
        if self._wrsi is None:
            self._wrsi = Wrsi(self._client)
        return self._wrsi

    @property
    def wssi_us(self) -> WssiUs:
        """Weather Storage Shock Index."""
        if self._wssi_us is None:
            self._wssi_us = WssiUs(self._client)
        return self._wssi_us

    # --- Meta endpoints ---

    def health(self, deep: bool = False) -> dict:
        """
        Check API health status.

        Args:
            deep: Run deep health check including database connectivity

        Returns:
            Health status dict with 'status' key
        """
        return self._client.health(deep=deep)

    def products(self) -> list[dict]:
        """
        List all available products.

        Returns:
            List of product dicts with 'id', 'name', 'description'
        """
        return self._client.list_products()
