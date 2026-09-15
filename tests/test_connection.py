from unittest.mock import patch

import pytest

from f1_pipeline.connection import connect


def test_profile_admin_role_is_never_used(tmp_path):
    profile = tmp_path / "profiles.yml"
    profile.write_text(
        "local:\n  outputs:\n    dev:\n      type: snowflake\n"
        "      account: example\n      user: example\n"
        "      password: dummy\n      role: ACCOUNTADMIN\n"
    )
    with patch("f1_pipeline.connection.snowflake.connector.connect") as factory:
        connection = connect(profile)
        assert factory.call_args.kwargs["role"] == "F1_INGESTOR"
        assert factory.call_args.kwargs["warehouse"] == "COMPUTE_WH"
        connection.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            "USE SECONDARY ROLES NONE"
        )


def test_templated_profile_is_rejected_without_network(tmp_path):
    profile = tmp_path / "profiles.yml"
    profile.write_text(
        "local:\n  outputs:\n    dev:\n      type: snowflake\n"
        "      account: \"{{ env_var('ACCOUNT') }}\"\n      user: example\n"
    )
    with patch("f1_pipeline.connection.snowflake.connector.connect") as factory:
        with pytest.raises(ValueError, match="Templated"):
            connect(profile)
        factory.assert_not_called()
