import pandas as pd
from typing import Optional, List, Dict, Any
from client.client import SnowtrailClient

class StacksClient:
    """Client for Snowtrail Stacks API - versioned signal stacks with standardized read patterns."""

    def __init__(self, client: SnowtrailClient):
        self.client = client

    # =============================================================================
    # Registry Methods
    # =============================================================================

    def list_stacks(self) -> List[Dict[str, Any]]:
        """List all registered stacks with their current versions.

        Returns:
            List of stack metadata dictionaries
        """
        data = self.client._get("/stacks/registry")
        return data.get("stacks", [])

    def get_stack_info(self, stack_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific stack.

        Args:
            stack_id: Stack identifier (e.g., 'gbsi_us')

        Returns:
            Stack specification and metadata
        """
        return self.client._get(f"/stacks/registry/{stack_id}")

    # =============================================================================
    # Generic Stack Methods
    # =============================================================================

    def latest(self, stack_id: str) -> Dict[str, Any]:
        """Get the most recent signal for a stack.

        Args:
            stack_id: Stack identifier (e.g., 'gbsi_us')

        Returns:
            Latest signal data
        """
        return self.client._get(f"/stacks/{stack_id}/latest")

    def history(
        self,
        stack_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """Get historical signals for a stack.

        Args:
            stack_id: Stack identifier (e.g., 'gbsi_us')
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            limit: Maximum number of records (default: 500)

        Returns:
            DataFrame with historical signals
        """
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit

        data = self.client._get(f"/stacks/{stack_id}/history", params=params)

        if data.get("signals"):
            return pd.DataFrame(data["signals"])
        return pd.DataFrame()

    def events(
        self,
        stack_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get events filtered to a stack's scope.

        Args:
            stack_id: Stack identifier (e.g., 'gbsi_us')
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            event_types: List of event types to filter
            limit: Maximum number of records (default: 100)

        Returns:
            DataFrame with events
        """
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if event_types:
            params['event_types'] = ','.join(event_types)
        if limit:
            params['limit'] = limit

        data = self.client._get(f"/stacks/{stack_id}/events", params=params)

        if data.get("events"):
            return pd.DataFrame(data["events"])
        return pd.DataFrame()

    def explain(
        self,
        stack_id: str,
        week_ending: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed signal breakdown with features and context.

        Args:
            stack_id: Stack identifier (e.g., 'gbsi_us')
            week_ending: Specific week to explain (YYYY-MM-DD), defaults to latest

        Returns:
            Full explainability data
        """
        params = {}
        if week_ending:
            params['week_ending'] = week_ending

        return self.client._get(f"/stacks/{stack_id}/explain", params=params)

    # =============================================================================
    # GBSI-Specific Convenience Methods
    # =============================================================================

    def gbsi_us(self):
        """Get a GBSI-US specific client with convenience methods.

        Returns:
            GBSIStackClient instance
        """
        return GBSIStackClient(self.client)


class GBSIStackClient:
    """Convenience client for GBSI-US stack with human-friendly methods."""

    def __init__(self, client: SnowtrailClient):
        self.client = client
        self.stack_id = "gbsi_us"

    def latest(self) -> Dict[str, Any]:
        """Get latest GBSI signal."""
        return self.client._get(f"/stacks/{self.stack_id}/latest")

    def latest_summary(self) -> Dict[str, Any]:
        """Get latest GBSI signal in human-friendly format.

        Returns:
            Dictionary with structured signal including:
            - gbsi_signal: Quantitative z-score
            - gbsi_signal_label: Human-readable description
            - trade_bias: "Bullish Gas" / "Bearish Gas" / "Neutral"
            - trade_bias_strength: "Extreme" / "Strong" / "Moderate" / "Weak" / "None"
        """
        return self.client._get(f"/stacks/{self.stack_id}/latest/summary")

    def history(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """Get GBSI historical signals.

        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            limit: Maximum number of records

        Returns:
            DataFrame with v3.1 fields including signal labels and trade bias
        """
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit

        data = self.client._get(f"/stacks/{self.stack_id}/history", params=params)

        if data.get("signals"):
            return pd.DataFrame(data["signals"])
        return pd.DataFrame()

    def events(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get GBSI-related events.

        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            event_types: Filter by event types (e.g., ['GBSI_REGIME_SHIFT'])
            limit: Maximum number of records

        Returns:
            DataFrame with events
        """
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if event_types:
            params['event_types'] = ','.join(event_types)
        if limit:
            params['limit'] = limit

        data = self.client._get(f"/stacks/{self.stack_id}/events", params=params)

        if data.get("events"):
            return pd.DataFrame(data["events"])
        return pd.DataFrame()

    def explain(self, week_ending: Optional[str] = None) -> Dict[str, Any]:
        """Get full GBSI explainability with features and components.

        Args:
            week_ending: Specific week (YYYY-MM-DD), defaults to latest

        Returns:
            Full signal breakdown with features and context
        """
        params = {}
        if week_ending:
            params['week_ending'] = week_ending

        return self.client._get(f"/stacks/{self.stack_id}/explain", params=params)
