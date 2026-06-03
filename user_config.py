#!/usr/bin/env python3
"""Load job config: identity from EPFL_* env (~/.profile), pod extras from symlinks.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

_IDENTITY_FROM_ENV = (
    ("user", "EPFL_USER", str),
    ("uid", "EPFL_UID", int),
    ("gid", "EPFL_GID", int),
    ("group", "EPFL_GROUPNAME", str),
    ("supplemental_groups", "EPFL_SUPPLEMENTAL_GROUPS", int),
)

_IGNORED_LOCAL_KEYS = frozenset({"wandb_api_key", "hf_token"})
_IDENTITY_KEYS = frozenset(
    {"user", "uid", "gid", "group", "supplemental_groups", "working_dir", "symlinks"}
)


def expand_scratch_home(scratch_home: str, username: str) -> str:
    path = scratch_home.replace("$EPFL_USER", username)
    if not path.endswith("/"):
        path += "/"
    return path


def _cast(value: Any, caster: Callable[[Any], Any], field: str) -> Any:
    try:
        return caster(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid value for {field}: {value!r}") from exc


def _resolve_identity_from_env() -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    missing: list[str] = []

    for field, env_var, caster in _IDENTITY_FROM_ENV:
        raw = os.environ.get(env_var)
        if raw is None or raw == "":
            missing.append(f"{field} (${env_var})")
            continue
        resolved[field] = _cast(raw, caster, field)

    scratch_home = os.environ.get("EPFL_SCRATCH_HOME")
    user = resolved.get("user")
    if not scratch_home or not user:
        missing.append("working_dir ($EPFL_SCRATCH_HOME with EPFL_USER set)")
    elif not missing:
        resolved["working_dir"] = expand_scratch_home(scratch_home, str(user))

    if missing:
        print(
            "Missing required environment (from ~/.profile):\n  - "
            + "\n  - ".join(missing)
            + "\n\nRun: ./ldap_fetch.sh GASPAR && source ~/.profile",
            file=sys.stderr,
        )
        sys.exit(1)

    return resolved


def _load_local_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open() as f:
        suffix = path.suffix.lower()
        if suffix == ".json":
            data = json.load(f) or {}
        else:
            raise SystemExit(
                f"{path}: unsupported config format. Use .json (recommended)."
            )

    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object at the top level.")

    out: dict[str, Any] = {}
    if isinstance(data.get("symlinks"), dict):
        out["symlinks"] = data["symlinks"]
    else:
        symlinks = {
            k: v
            for k, v in data.items()
            if k not in _IGNORED_LOCAL_KEYS and k not in _IDENTITY_KEYS
        }
        if symlinks:
            out["symlinks"] = symlinks

    return out


def load_user_config(local_config: str | Path | None = None) -> dict[str, Any]:
    if local_config:
        path = Path(local_config)
    else:
        base_dir = Path(__file__).resolve().parent
        candidates = [
            base_dir / "symlinks.json",
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    cfg = _resolve_identity_from_env()
    cfg.update(_load_local_config(path))
    return cfg
