"""
Product clients for Snowtrail Research API.

Each product has signals, features, and events endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from snowtrail._client import HTTPClient


class BaseProduct:
    """
    Base class for product-specific API clients.

    Each product (gbsi_us, gbsi_eu, etc.) extends this class
    and adds its specific endpoints.
    """

    def __init__(self, client: HTTPClient, product_id: str):
        self._client = client
        self._product_id = product_id

    def _get(
        self,
        endpoint: str,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        **filters: Any,
    ) -> pd.DataFrame:
        """
        Generic endpoint fetcher with DataFrame conversion.

        Args:
            endpoint: Endpoint name (e.g., "system_stress")
            latest: Return only most recent record (default: True)
            start: Start date filter (overrides latest)
            end: End date filter
            limit: Maximum rows to return
            **filters: Product-specific filters (geography, basin, etc.)

        Returns:
            pandas DataFrame with the response data
        """
        params: dict[str, Any] = {"latest": latest, "limit": limit}

        if start:
            params["start"] = str(start)
            params["latest"] = False  # Date range overrides latest
        if end:
            params["end"] = str(end)

        # Add product-specific filters
        params.update(filters)

        path = f"/{self._product_id}/{endpoint}"
        response = self._client.get(path, params=params)

        # Handle both latest (single record) and history (list) responses
        data = response.get("data")
        if data is None:
            return pd.DataFrame()
        if isinstance(data, dict):
            # Single record from latest=True
            return pd.DataFrame([data])
        return pd.DataFrame(data)

    def _get_raw(
        self,
        endpoint: str,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        **filters: Any,
    ) -> dict[str, Any]:
        """
        Generic endpoint fetcher returning raw dict response.

        Same as _get() but returns the full API response dict
        including metadata, has_more, next_cursor, etc.
        """
        params: dict[str, Any] = {"latest": latest, "limit": limit}

        if start:
            params["start"] = str(start)
            params["latest"] = False
        if end:
            params["end"] = str(end)

        params.update(filters)

        path = f"/{self._product_id}/{endpoint}"
        return self._client.get(path, params=params)


# =============================================================================
# GBSI-US: US Natural Gas Balance Stress Index
# =============================================================================


class GbsiUs(BaseProduct):
    """
    GBSI-US: US Natural Gas Balance Stress Index.

    Weekly signals and features based on EIA storage data,
    production trends, and demand pressure metrics.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "gbsi_us")

    # --- Signals ---

    def system_stress(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Composite system stress signal (1-5 scale).

        Combines storage, momentum, supply elasticity, and demand pressure.
        Regime 1 = bullish stress, Regime 5 = bearish oversupply.

        Args:
            latest: Return only most recent record
            start: Start date (YYYY-MM-DD), overrides latest
            end: End date (YYYY-MM-DD)
            limit: Maximum rows (default: 200)

        Returns:
            DataFrame with stress signal data
        """
        return self._get("system_stress", latest=latest, start=start, end=end, limit=limit)

    # --- Features ---

    def balance_momentum(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Week-over-week storage balance changes vs seasonal norms.

        Tracks injection/withdrawal pace relative to 5-year averages.
        """
        return self._get("balance_momentum", latest=latest, start=start, end=end, limit=limit)

    def storage_inventory(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Current storage levels vs 5-year min/max/avg benchmarks.

        Includes deficit/surplus calculations and percentile rankings.
        """
        return self._get("storage_inventory", latest=latest, start=start, end=end, limit=limit)

    def supply_elasticity(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Supply-side responsiveness metrics.

        Includes dry gas production trends, LNG feedgas demand,
        and pipeline export flows to Mexico.
        """
        return self._get("supply_elasticity", latest=latest, start=start, end=end, limit=limit)

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Complete feature matrix with all component z-scores.

        Includes storage_score, momentum_score, supply_score, demand_score.
        """
        return self._get("features", latest=latest, start=start, end=end, limit=limit)

    # --- Events ---

    def storage_surprise(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        EIA weekly storage report surprises.

        Compares actual injection/withdrawal to Bloomberg consensus.
        Triggers on >2 Bcf deviation.
        """
        return self._get("storage_surprise", latest=latest, start=start, end=end, limit=limit)

    def regime_shift(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        GBSI regime transitions between stress levels.

        Captures shifts from bullish to bearish conditions or vice versa.
        """
        return self._get("regime_shift", latest=latest, start=start, end=end, limit=limit)

    def momentum_inflection(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Balance momentum turning points.

        Early warning signal for regime shifts.
        """
        return self._get("momentum_inflection", latest=latest, start=start, end=end, limit=limit)

    def balance_stress_threshold(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Threshold breach events when storage crosses critical boundaries.
        """
        return self._get(
            "balance_stress_threshold", latest=latest, start=start, end=end, limit=limit
        )


# =============================================================================
# GBSI-EU: EU Natural Gas Balance Stress Index
# =============================================================================


class GbsiEu(BaseProduct):
    """
    GBSI-EU: EU Natural Gas Balance Stress Index.

    Daily signals and features based on GIE AGSI+ storage data
    across major EU countries.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "gbsi_eu")

    # --- Signals ---

    def system_stress(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """
        Daily EU-wide system stress signal (1-5 scale).

        Updated after daily GIE publication (~18:00 CET).

        Args:
            country: Filter by country code (e.g., 'DE', 'FR', 'NL')
        """
        return self._get(
            "system_stress", latest=latest, start=start, end=end, limit=limit, country=country
        )

    def composite(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """
        Weighted composite signal across major EU storage countries.

        Combines storage stress, momentum, and supply metrics.
        """
        return self._get(
            "composite", latest=latest, start=start, end=end, limit=limit, country=country
        )

    def dispersion(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """
        Cross-country stress dispersion measuring regional divergence.

        High dispersion indicates arbitrage opportunities.
        """
        return self._get(
            "dispersion", latest=latest, start=start, end=end, limit=limit, country=country
        )

    # --- Features ---

    def balance_momentum(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """Daily injection/withdrawal momentum vs seasonal norms."""
        return self._get(
            "balance_momentum", latest=latest, start=start, end=end, limit=limit, country=country
        )

    def storage_inventory(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """EU aggregate and country-level storage fill rates."""
        return self._get(
            "storage_inventory", latest=latest, start=start, end=end, limit=limit, country=country
        )

    def supply_elasticity(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """Supply flexibility metrics including LNG and Norwegian flows."""
        return self._get(
            "supply_elasticity", latest=latest, start=start, end=end, limit=limit, country=country
        )

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        country: str | None = None,
    ) -> pd.DataFrame:
        """Complete EU feature matrix with country-level breakdowns."""
        return self._get(
            "features", latest=latest, start=start, end=end, limit=limit, country=country
        )


# =============================================================================
# PEMI: Power Event Market Intelligence
# =============================================================================


class Pemi(BaseProduct):
    """
    PEMI: Power Event Market Intelligence.

    EU power market stress signals from Nord Pool UMM outage data.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "pemi")

    # --- Signals ---

    def power_stress(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        bidding_zone: str | None = None,
    ) -> pd.DataFrame:
        """
        EU power market stress signal from outage data.

        Tracks aggregate outage pressure and event clustering.

        Args:
            bidding_zone: Filter by bidding zone
        """
        return self._get(
            "power_stress",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            bidding_zone=bidding_zone,
        )

    # --- Features ---

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        bidding_zone: str | None = None,
    ) -> pd.DataFrame:
        """
        Outage event features including capacity offline (MW).

        Includes duration estimates and bidding zone concentration.
        """
        return self._get(
            "features",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            bidding_zone=bidding_zone,
        )


# =============================================================================
# GLMI: Global LNG Market Intelligence
# =============================================================================


class Glmi(BaseProduct):
    """
    GLMI: Global LNG Market Intelligence.

    LNG marginality regime indicators based on GIIGNL data.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "glmi")

    # --- Signals ---

    def lng_stress(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        basin: str | None = None,
    ) -> pd.DataFrame:
        """
        LNG marginality regime indicator.

        Identifies whether Europe or Asia sets the marginal price
        for flexible LNG cargoes.

        Args:
            basin: Filter by basin ('atlantic', 'pacific', 'middle_east')
        """
        return self._get(
            "lng_stress", latest=latest, start=start, end=end, limit=limit, basin=basin
        )

    # --- Features ---

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        basin: str | None = None,
    ) -> pd.DataFrame:
        """
        Supply basin metrics with destination flow analysis.

        Includes contract vs spot ratios and competition intensity.
        """
        return self._get(
            "features", latest=latest, start=start, end=end, limit=limit, basin=basin
        )


# =============================================================================
# WRSI: Weather Risk Signal Intelligence
# =============================================================================


class Wrsi(BaseProduct):
    """
    WRSI: Weather Risk Signal Intelligence.

    Weather forecast volatility regime signals from NOAA models.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "wrsi")

    # --- Signals ---

    def weather_risk(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        geography: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """
        Weather forecast volatility regime signal.

        Tracks ensemble spread and run-to-run changes in NOAA models.
        High values indicate forecast uncertainty.

        Args:
            geography: Filter by geography (e.g., 'US', 'ERCOT')
            region_type: Filter by region type
        """
        return self._get(
            "weather_risk",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            geography=geography,
            region_type=region_type,
        )

    # --- Features ---

    def forecast_dynamics(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        geography: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """Run-to-run forecast changes measuring outlook evolution."""
        return self._get(
            "forecast_dynamics",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            geography=geography,
            region_type=region_type,
        )

    def forecast_volatility(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        geography: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """GEFS ensemble spread metrics across forecast horizons."""
        return self._get(
            "forecast_volatility",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            geography=geography,
            region_type=region_type,
        )

    def seasonal_context(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        geography: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """Climatological benchmarks and seasonal demand leverage."""
        return self._get(
            "seasonal_context",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            geography=geography,
            region_type=region_type,
        )

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        geography: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """Complete WRSI feature matrix."""
        return self._get(
            "features",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            geography=geography,
            region_type=region_type,
        )


# =============================================================================
# WSSI-US: Weather Storage Shock Index
# =============================================================================


class WssiUs(BaseProduct):
    """
    WSSI-US: Weather Storage Shock Index.

    Weather-driven storage demand shock predictor.
    """

    def __init__(self, client: HTTPClient):
        super().__init__(client, "wssi_us")

    # --- Signals ---

    def weather_shock(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        region_id: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """
        Weather-driven storage demand shock predictor.

        Forecasts EIA storage surprises using population-weighted HDD/CDD.

        Args:
            region_id: Filter by region ID
            region_type: Filter by region type
        """
        return self._get(
            "weather_shock",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            region_id=region_id,
            region_type=region_type,
        )

    # --- Features ---

    def features(
        self,
        latest: bool = True,
        start: date | str | None = None,
        end: date | str | None = None,
        limit: int = 200,
        region_id: str | None = None,
        region_type: str | None = None,
    ) -> pd.DataFrame:
        """
        Demand shock features including population-weighted degree days.
        """
        return self._get(
            "features",
            latest=latest,
            start=start,
            end=end,
            limit=limit,
            region_id=region_id,
            region_type=region_type,
        )
