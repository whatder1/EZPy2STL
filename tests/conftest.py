import pytest


@pytest.fixture(autouse=True)
def _no_real_update_check(monkeypatch):
    """No test may reach the network. Tests of the update check itself pass
    their own fake fetch function."""
    monkeypatch.setenv("EZPY2STL_NO_UPDATE_CHECK", "1")
