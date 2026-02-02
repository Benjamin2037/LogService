from backend.code_search import _is_github_url, _parse_github_url


def test_parse_github_url_basic():
    url = "https://github.com/org/repo"
    assert _is_github_url(url) is True
    ref = _parse_github_url(url)
    assert ref.owner == "org"
    assert ref.repo == "repo"
    assert ref.branch is None
    assert ref.subpath is None


def test_parse_github_url_tree_path():
    url = "https://github.com/org/repo/tree/main/src"
    ref = _parse_github_url(url)
    assert ref.branch == "main"
    assert ref.subpath == "src"
