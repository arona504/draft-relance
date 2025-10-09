"""Casbin enforcer initialisation and helpers."""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Optional

import casbin
from casbin_sqlalchemy_adapter import Adapter
from fastapi.concurrency import run_in_threadpool

from .settings import Settings, get_settings

_enforcer: Optional[casbin.Enforcer] = None
_lock = asyncio.Lock()


def _seed_policies(enforcer: casbin.Enforcer, policy_path: Path) -> None:
    """Seed the Casbin policy store if the current policy set is empty."""
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
    enforcer.load_policy()


async def _initialise_enforcer(settings: Settings) -> casbin.Enforcer:
    """Create and configure the Casbin enforcer singleton."""
    global _enforcer

    model_path = settings.resolve_path(settings.casbin_model_path)
    adapter = Adapter(settings.sync_casbin_db_url)
    enforcer = casbin.Enforcer(str(model_path), adapter, enable_log=False)
    enforcer.enable_auto_save(True)

    enforcer.load_policy()
    policy_path = settings.resolve_path(settings.casbin_policy_path)
    if policy_path.exists() and not enforcer.get_policy() and not enforcer.get_grouping_policy():
        _seed_policies(enforcer, policy_path)

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


async def authorize(subject_or_role: str, tenant: str, obj: str, act: str) -> bool:
    """Run a Casbin enforcement call in a threadpool."""
    enforcer = await get_enforcer()
    return bool(await run_in_threadpool(enforcer.enforce, subject_or_role, tenant, obj, act))
