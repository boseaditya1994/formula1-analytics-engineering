"""Resolve local credentials without logging them; never fall back to an admin role."""

import os
from pathlib import Path

import snowflake.connector
import yaml
from dotenv import load_dotenv


def connect(profile_path: Path | None = None):
    load_dotenv(override=False)
    if profile_path:
        profiles = yaml.safe_load(profile_path.read_text(encoding="utf-8-sig")) or {}
        outputs = [
            o
            for p in profiles.values()
            if isinstance(p, dict)
            for o in p.get("outputs", {}).values()
            if isinstance(o, dict) and o.get("type") == "snowflake"
        ]
        if len(outputs) != 1:
            raise ValueError("Select a profile file with exactly one Snowflake output")
        allowed = (
            "account",
            "user",
            "password",
            "authenticator",
            "private_key_file",
            "private_key_file_pwd",
            "token",
        )
        params = {k: v for k, v in outputs[0].items() if k in allowed and v}
        if any("{{" in str(v) for v in params.values()):
            raise ValueError("Templated profiles are unsupported; use environment variables")
    else:
        mapping = {
            "account": "SNOWFLAKE_ACCOUNT",
            "user": "SNOWFLAKE_USER",
            "password": "SNOWFLAKE_PASSWORD",
            "authenticator": "SNOWFLAKE_AUTHENTICATOR",
            "private_key_file": "SNOWFLAKE_PRIVATE_KEY_FILE",
            "private_key_file_pwd": "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE",
        }
        params = {k: os.environ[v] for k, v in mapping.items() if os.environ.get(v)}
    if not params.get("account") or not params.get("user"):
        raise ValueError("Snowflake account and user are required")
    connection = snowflake.connector.connect(
        **params,
        role="F1_INGESTOR",
        warehouse="COMPUTE_WH",
        database="F1_ANALYTICS",
        schema="RAW",
        login_timeout=60,
        network_timeout=60,
        socket_timeout=10,
        session_parameters={"QUERY_TAG": "f1_pipeline:ingestion"},
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("USE SECONDARY ROLES NONE")
    except Exception:
        connection.close()
        raise
    return connection
