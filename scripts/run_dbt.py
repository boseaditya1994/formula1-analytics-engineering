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
        values = {k: "offline-placeholder" for k in ("account", "user", "password")}
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
        values = {k: outputs[0].get(k) for k in ("account", "user", "password")}
    else:
        values = {
            k: os.environ.get(f"SNOWFLAKE_{k.upper()}") for k in ("account", "user", "password")
        }
    if any(not v or "{{" in str(v) for v in values.values()):
        parser.error("Concrete account, user and password required; no credential values printed")
    for key, value in values.items():
        os.environ[f"DBT_ENV_SECRET_F1_{key.upper()}"] = str(value)
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
