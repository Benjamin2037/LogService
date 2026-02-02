from pathlib import Path

from backend.cluster_config import load_cluster_config


def test_cluster_config_example_valid():
    root = Path(__file__).resolve().parents[1]
    config_path = root / "config/examples/cluster.example.json"
    schema_path = root / "config/schema/cluster_config.schema.json"
    data = load_cluster_config(config_path, schema_path)
    assert data["cluster_id"]
