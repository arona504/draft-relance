"""Casbin enforcer initialisation and helpers."""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Optional

import casbin
from casbin_sqlalchemy_adapter import Adapter

from .settings import Settings, get_settings

_enforcer: Optional[casbin.Enforcer] = None
_lock = asyncio.Lock()


def _seed_policies(enforcer: casbin.Enforcer, policy_path: Path) -> None:
    """Seed the Casbin policy store if empty."""
    adapter: Adapter = enforcer.adapter  # type: ignore[assignment]
    with adapter.session_maker() as session:
        model = adapter.model_class
        has_policy = session.query(model).first() is not None

    if has_policy:
        return

    with policy_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row:
                continue
            kind, *policy_parts = [part.strip() for part in row]
            if kind == "p":
                enforcer.add_policy(*policy_parts)
            elif kind == "g":
                enforcer.add_grouping_policy(*policy_parts)

    enforcer.save_policy()


async def _initialise_enforcer(settings: Settings) -> casbin.Enforcer:
    """Create and configure the Casbin enforcer singleton."""
    global _enforcer

    model_path = settings.resolve_path(settings.casbin_model_path)
    adapter = Adapter(settings.sync_casbin_db_url, engine_options={"pool_pre_ping": True})
    enforcer = casbin.Enforcer(str(model_path), adapter, enable_log=False)
    enforcer.enable_auto_save(True)

    policy_path = settings.resolve_path(settings.casbin_policy_path)
    if policy_path.exists():
        _seed_policies(enforcer, policy_path)

    enforcer.load_policy()
    _enforcer = enforcer
    return enforcer


async def get_enforcer(settings: Settings | None = None) -> casbin.Enforcer:
    """Return the cached enforcer, initialising it if necessary."""
    global _enforcer
    if _enforcer:
        return _enforcer

    settings = settings or get_settings()

    async with _lock:
        if _enforcer:
            return _enforcer
        return await _initialise_enforcer(settings)

