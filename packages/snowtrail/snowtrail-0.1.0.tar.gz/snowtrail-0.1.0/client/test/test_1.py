from sigstack import SigStack

ss = SigStack(
    base_url="http://localhost:8001",
    api_key=None
)

# discover datasets
ss.datasets.list()

# pull a signal
df = ss.signals.get(
    name="gas_storage_tightness_weekly_us",
    start="2022-01-01",
    end="2024-12-31"
)

# pull features
features = ss.features.get(
    name="gas_storage_weekly_us",
    as_of="2024-12-15"
)
