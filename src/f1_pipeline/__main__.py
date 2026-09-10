"""Local diagnostics; ingestion is introduced in later phases."""

import argparse
import json
import platform
from importlib.metadata import version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor"])
    parser.parse_args()
    packages = (
        "f1-analytics-engineering",
        "dbt-core",
        "dbt-snowflake",
        "snowflake-connector-python",
        "httpx",
    )
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "packages": {name: version(name) for name in packages},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
