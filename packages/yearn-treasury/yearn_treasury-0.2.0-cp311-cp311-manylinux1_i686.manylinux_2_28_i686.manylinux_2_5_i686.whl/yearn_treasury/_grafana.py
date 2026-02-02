"""Grafana environment validation for Yearn Treasury."""

from __future__ import annotations

import os


def require_grafana_admin_env() -> tuple[str, str]:
    """Return Grafana admin creds or raise a clear error if missing."""
    missing: list[str] = []
    admin_user = os.getenv("GF_SECURITY_ADMIN_USER")
    admin_password = os.getenv("GF_SECURITY_ADMIN_PASSWORD")
    if not admin_user:
        missing.append("GF_SECURITY_ADMIN_USER")
    if not admin_password:
        missing.append("GF_SECURITY_ADMIN_PASSWORD")
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Grafana admin credentials are required. "
            f"Missing environment variables: {missing_list}. "
            "Set DAO_TREASURY_GRAFANA_ANON_ENABLED=true only if you want anonymous access."
        )
    return admin_user, admin_password
