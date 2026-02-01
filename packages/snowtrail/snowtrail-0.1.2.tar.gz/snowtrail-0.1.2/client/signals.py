import pandas as pd
from typing import Optional, Dict, Any
from client.client import SnowtrailClient

class SignalsClient:
    def __init__(self, client: SnowtrailClient):
        self.client = client

    def list(self) -> pd.DataFrame:
        data = self.client._get("/signals")
        return pd.DataFrame(data)

    def get(
        self,
        name: str,
        start: str | None = None,
        end: str | None = None,
        version: str | None = None,
    ) -> pd.DataFrame:
        params = {
            "start": start,
            "end": end,
            "version": version,
        }

        # remove None values
        params = {k: v for k, v in params.items() if v is not None}

        data = self.client._get(f"/signals/{name}", params=params)
        return pd.DataFrame(data)

    # =============================================================================
    # GBSI System Stress Methods (v3.1 with human-friendly labels)
    # =============================================================================

    def gbsi_system_stress(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """Get GBSI system stress signals with v3.1 human-friendly labels.

        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            limit: Maximum number of records (default: 500)

        Returns:
            DataFrame with columns:
            - week_ending
            - as_of_timestamp
            - stress_regime, stress_regime_label
            - stress_direction, stress_direction_label
            - gbsi_signal, gbsi_signal_label
            - trade_bias, trade_bias_strength
            - confidence_score, confidence_bucket
            - data_quality_score, signal_version
        """
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit

        data = self.client._get("/signals/gbsi-system-stress", params=params)
        return pd.DataFrame(data)

    def gbsi_system_stress_latest(self) -> Dict[str, Any]:
        """Get latest GBSI system stress signal with all v3.1 fields.

        Returns:
            Dictionary with structured response:
            - week_ending, as_of_timestamp
            - regime: {stress_regime, stress_regime_label}
            - direction: {stress_direction, stress_direction_label}
            - signal: {gbsi_signal, gbsi_signal_label, trade_bias, trade_bias_strength}
            - confidence: {confidence_score, confidence_bucket, confidence_bucket_label, ...}
            - components: {inventory, balance, supply, demand}
            - signal_version
        """
        return self.client._get("/signals/gbsi-system-stress/latest")
