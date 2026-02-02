from backend.rate_limit import TokenBucketLimiter


def test_rate_limit_basic():
    limiter = TokenBucketLimiter(rate_per_sec=0.0, burst=1)
    allowed, _ = limiter.allow("cluster-a")
    assert allowed is True

    allowed, retry_after = limiter.allow("cluster-a")
    assert allowed is False
    assert retry_after >= 0
