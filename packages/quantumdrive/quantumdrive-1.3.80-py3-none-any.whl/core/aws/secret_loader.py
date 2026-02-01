from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Mapping, Any
import tomllib

from core.aws.secrets_manager import SecretsManager

logger = logging.getLogger(__name__)


def load_env_from_secret(secret_name: str | None = None, *, region_name: str | None = None, overwrite: bool = False) -> dict:
    """
    Load key/value pairs from AWS Secrets Manager and inject them into os.environ.

    - secret_name: The name/ARN of the secret. Defaults to env QUANTIFY_CONFIG_SECRET
      or 'quantify/app/config' when not set.
    - region_name: Optional region override (falls back to default boto3 resolution).
    - overwrite: When True, overwrites existing environment variables; otherwise only sets
      variables that are not already present in the process environment.

    Returns a dict of the keys that were applied to the environment.
    """
    name = secret_name or os.getenv('QUANTIFY_CONFIG_SECRET') or 'quantify/app/config'  # noqa
    logger.info(f"AWS SecretsManager name: {name}")
    sm = SecretsManager(name, region_name=region_name or os.getenv('AWS_REGION', 'us-east-1'))  # noqa
    data = sm.get_secret() or {}
    if not data:
        logger.warning(f"No secret data found for {name}")
        raise SystemError("No secret data found in AWS SecretsManager")
    logger.debug(f"Secret data type: {type(data)}")
    applied: dict[str, str] = {}
    for k, v in data.items():
        logger.debug(f"Key from SecretsManager: {k}")
        key = str(k)
        val = '' if v is None else str(v)
        if overwrite or key not in os.environ:
            logger.info(f"Key not found or being overwritten: {key}:{val}")
            os.environ[key] = val
            applied[key] = val
        else:
            logger.debug(f"Key found and not being overwritten: {key}")
        # Normalize dotted keys to underscore form expected by env lookups, e.g. CHROMA.URL -> CHROMA_URL
        if '.' in key:
            norm = key.replace('.', '_')
            if overwrite or norm not in os.environ:
                os.environ[norm] = val
                applied[norm] = val
    logger.info(f"AWS SecretsManager variables: {applied}")
    return applied


def load_env_from_toml(path: str | Path, overwrite: bool = False, logger=None) -> dict[str, str]:
    """
    Load key/value pairs from a TOML file into os.environ.

    Nested tables are flattened with underscores and keys are uppercased.
    """
    p = Path(path)  # noqa
    applied: dict[str, str] = {}
    if not p.exists():
        return applied
    try:
        with p.open("rb") as fh:
            data = tomllib.load(fh) or {}
    except Exception as exc:  # pragma: no cover - defensive
        if logger:
            logger.warning("Failed to read %s: %s", p, exc)
        return applied

    def _flatten(prefix: str, obj: Mapping[str, Any]) -> None:
        for k, v in obj.items():
            key_prefix = f"{prefix}{k}"
            if isinstance(v, Mapping):
                _flatten(f"{key_prefix}_", v)
            else:
                env_key = key_prefix.upper()
                val = "" if v is None else str(v)
                if overwrite or env_key not in os.environ:
                    os.environ[env_key] = val
                    applied[env_key] = val

    if isinstance(data, Mapping):
        _flatten("", data)
    if applied and logger:
        logger.info("Loaded %d key(s) from %s into environment", len(applied), p)
        logger.info(f"Environment variables: {applied}")
    return applied
