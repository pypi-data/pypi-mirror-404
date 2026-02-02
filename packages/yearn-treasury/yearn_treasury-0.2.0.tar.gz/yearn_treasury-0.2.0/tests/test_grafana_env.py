import pytest

from yearn_treasury._grafana import require_grafana_admin_env


def test_require_grafana_admin_env_missing_both(monkeypatch):
    monkeypatch.delenv("GF_SECURITY_ADMIN_USER", raising=False)
    monkeypatch.delenv("GF_SECURITY_ADMIN_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="GF_SECURITY_ADMIN_USER.*GF_SECURITY_ADMIN_PASSWORD"):
        require_grafana_admin_env()


def test_require_grafana_admin_env_missing_user(monkeypatch):
    monkeypatch.delenv("GF_SECURITY_ADMIN_USER", raising=False)
    monkeypatch.setenv("GF_SECURITY_ADMIN_PASSWORD", "secret")
    with pytest.raises(RuntimeError, match="GF_SECURITY_ADMIN_USER"):
        require_grafana_admin_env()


def test_require_grafana_admin_env_missing_password(monkeypatch):
    monkeypatch.setenv("GF_SECURITY_ADMIN_USER", "admin")
    monkeypatch.delenv("GF_SECURITY_ADMIN_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="GF_SECURITY_ADMIN_PASSWORD"):
        require_grafana_admin_env()


def test_require_grafana_admin_env_success(monkeypatch):
    monkeypatch.setenv("GF_SECURITY_ADMIN_USER", "admin")
    monkeypatch.setenv("GF_SECURITY_ADMIN_PASSWORD", "secret")
    user, password = require_grafana_admin_env()
    assert user == "admin"
    assert password == "secret"
