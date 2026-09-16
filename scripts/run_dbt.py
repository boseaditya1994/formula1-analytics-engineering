"""Run the locked dbt Core runtime with local credentials redacted by dbt.

Example: uv run --frozen python scripts/run_dbt.py build --profile-file PATH
Only the existing local profile is read. Credential values remain in process memory.
"""

import argparse
import os
from pathlib import Path

import yaml
from dbt.cli.main import dbtRunner
from dotenv import load_dotenv


def main() -> None:
    load_dotenv(override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["parse", "build", "test", "compile", "ls"])
    parser.add_argument("--profile-file", type=Path)
    parser.add_argument("--offline", action="store_true")
    args, extra = parser.parse_known_args()
    if args.offline:
        if args.command not in ("parse", "ls"):
            parser.error("Offline mode supports parse or ls only")
        values = {"account": "offline-placeholder", "user": "offline-placeholder"}
        values["password"] = "offline-placeholder"
    elif args.profile_file:
        profiles = yaml.safe_load(args.profile_file.read_text(encoding="utf-8-sig")) or {}
        outputs = [
            output
            for profile in profiles.values()
            if isinstance(profile, dict)
            for output in profile.get("outputs", {}).values()
            if isinstance(output, dict) and output.get("type") == "snowflake"
        ]
        if len(outputs) != 1:
            parser.error("Expected one Snowflake output in the local credential profile")
        output = outputs[0]
        values = {
            "account": output.get("account"),
            "user": output.get("user"),
            "password": output.get("password"),
            # dbt and the Python connector name the key-pair fields differently;
            # accept either spelling from a shared credential profile.
            "private_key_path": output.get("private_key_path") or output.get("private_key_file"),
            "private_key_passphrase": output.get("private_key_passphrase")
            or output.get("private_key_file_pwd"),
        }
    else:
        values = {
            "account": os.environ.get("SNOWFLAKE_ACCOUNT"),
            "user": os.environ.get("SNOWFLAKE_USER"),
            "password": os.environ.get("SNOWFLAKE_PASSWORD"),
            "private_key_path": os.environ.get("SNOWFLAKE_PRIVATE_KEY_FILE"),
            "private_key_passphrase": os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
        }
    if not values.get("account") or "{{" in str(values["account"]):
        parser.error("Concrete account required; no credential values printed")
    if not values.get("user") or "{{" in str(values["user"]):
        parser.error("Concrete user required; no credential values printed")
    has_password = bool(values.get("password")) and "{{" not in str(values["password"])
    has_key = bool(values.get("private_key_path")) and "{{" not in str(values["private_key_path"])
    if has_password == has_key:
        parser.error(
            "Provide exactly one of password or private_key_path; no credential values printed"
        )
    for key in ("account", "user", "password", "private_key_path", "private_key_passphrase"):
        os.environ[f"DBT_ENV_SECRET_F1_{key.upper()}"] = str(values.get(key) or "")
    os.environ["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    project = Path(__file__).resolve().parents[1] / "dbt_f1"
    profile = project / "profiles.yml"
    if not profile.exists():
        profile.write_text((project / "profiles.yml.example").read_text(), encoding="utf-8")
    result = dbtRunner().invoke(
        [
            args.command,
            "--project-dir",
            str(project),
            "--profiles-dir",
            str(project),
            *extra,
        ]
    )
    raise SystemExit(0 if result.success else 1)


if __name__ == "__main__":
    main()
