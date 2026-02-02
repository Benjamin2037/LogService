from backend.loki_adapter import build_logql


def test_build_logql_escapes_keywords():
    labels = {"cluster": "us-east-1-f02", "component": "pd"}
    logql = build_logql(labels, ["leader", 'ready"slow'])
    assert '{cluster="us-east-1-f02",component="pd"}' in logql
    assert '"ready\\"slow"' in logql
