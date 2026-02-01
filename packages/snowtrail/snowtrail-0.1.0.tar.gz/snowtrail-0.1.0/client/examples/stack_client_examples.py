"""
Examples for using the Snowtrail Stacks API Client

Demonstrates:
- Stack registry queries
- Generic stack methods
- GBSI-specific convenience methods
- v3.1 human-friendly signal labels
"""

from client import Snowtrail

# Initialize client
client = Snowtrail(base_url="http://127.0.0.1:8001")

# =============================================================================
# Stack Registry
# =============================================================================

print("=" * 70)
print("STACK REGISTRY")
print("=" * 70)

# List all registered stacks
stacks = client.stacks.list_stacks()
print(f"\nRegistered stacks: {len(stacks)}")
for stack in stacks:
    print(f"  - {stack['stack_id']} v{stack['current_version']}: {stack['description']}")

# Get detailed stack information
gbsi_info = client.stacks.get_stack_info("gbsi_us")
print(f"\nGBSI-US Stack Info:")
print(f"  Version: {gbsi_info['current_version']}")
print(f"  Status: {gbsi_info['status']}")
print(f"  Owner: {gbsi_info['owner']}")

# =============================================================================
# Generic Stack Methods
# =============================================================================

print("\n" + "=" * 70)
print("GENERIC STACK METHODS")
print("=" * 70)

# Get latest signal using generic method
latest = client.stacks.latest("gbsi_us")
print(f"\nLatest GBSI Signal (week ending {latest['week_ending']}):")
print(f"  Regime: {latest['stress_regime_label']}")
print(f"  Signal: {latest['gbsi_signal']:.2f} - {latest['gbsi_signal_label']}")
print(f"  Trade Bias: {latest['trade_bias_strength']} {latest['trade_bias']}")
print(f"  Confidence: {latest['confidence_bucket']} ({latest['confidence_score']:.1f})")

# Get history using generic method
history_df = client.stacks.history("gbsi_us", limit=5)
print(f"\nHistory (last 5 weeks):")
print(history_df[['week_ending', 'stress_regime_label', 'gbsi_signal',
                  'gbsi_signal_label', 'trade_bias', 'trade_bias_strength']])

# =============================================================================
# GBSI-Specific Convenience Methods
# =============================================================================

print("\n" + "=" * 70)
print("GBSI-SPECIFIC CONVENIENCE METHODS")
print("=" * 70)

# Get GBSI client
gbsi = client.stacks.gbsi_us()

# Latest summary (human-friendly format)
summary = gbsi.latest_summary()
signal_data = summary['signal']

print(f"\nGBSI Summary (as of {summary['as_of']}):")
print(f"  Stack: {summary['stack_id']} v{summary['stack_version']}")
print(f"\n  Quantitative Signal:")
print(f"    Value: {signal_data['gbsi_signal']:.2f}")
print(f"    Label: {signal_data['gbsi_signal_label']}")
print(f"\n  Qualitative Signal:")
print(f"    Bias: {signal_data['trade_bias']}")
print(f"    Strength: {signal_data['trade_bias_strength']}")
print(f"\n  Market Regime:")
print(f"    Stress: {signal_data['stress_regime_label']}")
print(f"    Direction: {signal_data['stress_direction_label']}")
print(f"\n  Confidence:")
print(f"    Score: {signal_data['confidence_score']:.1f}")
print(f"    Bucket: {signal_data['confidence_bucket']}")

# Historical data with date filtering
history_df = gbsi.history(start="2025-11-01", limit=10)
print(f"\nGBSI History (since Nov 2025, {len(history_df)} rows):")
print(history_df[['week_ending', 'gbsi_signal', 'gbsi_signal_label',
                  'trade_bias', 'trade_bias_strength']].head())

# Events
events_df = gbsi.events(
    event_types=['GBSI_REGIME_SHIFT', 'GBSI_MOMENTUM_INFLECTION'],
    limit=5
)
if not events_df.empty:
    print(f"\nRecent GBSI Events ({len(events_df)} events):")
    print(events_df[['effective_at', 'event_type', 'event_name',
                     'magnitude_bucket', 'event_direction']].head())
else:
    print("\nNo recent GBSI events found")

# Full explainability
explain = gbsi.explain()
print(f"\nFull GBSI Explainability (week ending {explain['week_ending']}):")
print(f"  Signal: {explain['gbsi_signal']:.2f} - {explain['gbsi_signal_label']}")
print(f"  Trade: {explain['trade_bias_strength']} {explain['trade_bias']}")
print(f"\n  Components:")
print(f"    Inventory: {explain['inventory_component']:.1f}")
print(f"    Balance: {explain['balance_component']:.1f}")
print(f"    Supply: {explain['supply_component']:.1f}")
print(f"    Demand: {explain['demand_component']:.1f}")
print(f"\n  Features:")
print(f"    Storage: {explain['storage_bcf']:.0f} Bcf ({explain['storage_vs_5y_bcf']:+.0f} vs 5y)")
print(f"    Weekly Balance: {explain['weekly_balance_bcf']:+.1f} Bcf/d")

# =============================================================================
# Signals API - GBSI v3.1 Methods
# =============================================================================

print("\n" + "=" * 70)
print("SIGNALS API - GBSI v3.1 METHODS")
print("=" * 70)

# Latest GBSI signal (structured response)
latest_signal = client.signals.gbsi_system_stress_latest()
print(f"\nLatest GBSI Signal (Signals API):")
print(f"  Week Ending: {latest_signal['week_ending']}")
print(f"  As Of: {latest_signal['as_of_timestamp']}")
print(f"\n  Regime:")
print(f"    {latest_signal['regime']['stress_regime']} - {latest_signal['regime']['stress_regime_label']}")
print(f"\n  Direction:")
print(f"    {latest_signal['direction']['stress_direction']} - {latest_signal['direction']['stress_direction_label']}")
print(f"\n  Signal:")
print(f"    Quantitative: {latest_signal['signal']['gbsi_signal']:.2f}")
print(f"    Description: {latest_signal['signal']['gbsi_signal_label']}")
print(f"    Trade Bias: {latest_signal['signal']['trade_bias']}")
print(f"    Strength: {latest_signal['signal']['trade_bias_strength']}")
print(f"\n  Confidence:")
print(f"    Score: {latest_signal['confidence']['confidence_score']:.1f}")
print(f"    Bucket: {latest_signal['confidence']['confidence_bucket']} - {latest_signal['confidence']['confidence_bucket_label']}")
print(f"\n  Components:")
print(f"    Inventory: {latest_signal['components']['inventory']:.1f}")
print(f"    Balance: {latest_signal['components']['balance']:.1f}")
print(f"    Supply: {latest_signal['components']['supply']:.1f}")
print(f"    Demand: {latest_signal['components']['demand']:.1f}")

# GBSI time series
gbsi_df = client.signals.gbsi_system_stress(limit=5)
print(f"\nGBSI Time Series ({len(gbsi_df)} rows):")
print(gbsi_df[['week_ending', 'stress_regime_label', 'gbsi_signal',
              'gbsi_signal_label', 'trade_bias', 'trade_bias_strength']].head())

print("\n" + "=" * 70)
print("ALL EXAMPLES COMPLETE")
print("=" * 70)
