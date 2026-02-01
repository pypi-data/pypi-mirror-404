"""
Comprehensive precedence tests to ensure manual environment variables are never overridden
"""

import os
import tempfile
from pathlib import Path
import pytest
from dotyaml import load_config, ConfigLoader


class TestComprehensivePrecedence:
    """Test comprehensive precedence scenarios to ensure manual env vars always win"""

    def setup_method(self):
        """Set up test environment"""
        # Clean up any existing test env vars
        test_vars = [
            "MANUAL_FINAL_VAR",
            "APP_MANUAL_FINAL_VAR",
            "INTERPOLATION_SOURCE",
            "DOTENV_ONLY_VAR",
            "APP_SCENARIO1_VALUE",
            "APP_SCENARIO2_VALUE",
            "APP_SCENARIO3_VALUE",
            "APP_SCENARIO4_VALUE",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def test_manual_final_env_var_never_overridden_by_yaml(self):
        """Test that manually set final environment variables are never overridden by YAML"""
        # Set the FINAL environment variable that dotyaml would create
        os.environ["APP_CRITICAL_SETTING"] = "manually_set_value"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create YAML that would try to set the same final env var
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
critical:
  setting: yaml_should_not_override_this
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Verify the manual value is set before loading
                assert os.environ.get("APP_CRITICAL_SETTING") == "manually_set_value"

                # Load configuration
                config = load_config("config.yaml", prefix="APP")

                # Verify the manual value was NOT overridden
                assert os.environ.get("APP_CRITICAL_SETTING") == "manually_set_value"
                assert config.get("APP_CRITICAL_SETTING") == "manually_set_value"

            finally:
                os.chdir(original_cwd)
                if "APP_CRITICAL_SETTING" in os.environ:
                    del os.environ["APP_CRITICAL_SETTING"]

    def test_manual_final_env_var_never_overridden_by_dotenv(self):
        """Test that manually set final environment variables are never overridden by .env"""
        # Set the FINAL environment variable that dotyaml would create
        os.environ["APP_SECRET_KEY"] = "manually_set_secret"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .env file that tries to override the final env var
            env_file = temp_path / ".env"
            env_file.write_text("APP_SECRET_KEY=dotenv_should_not_override\n")

            # Create YAML that uses the env var
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
app:
  name: TestApp
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Verify the manual value is set before loading
                assert os.environ.get("APP_SECRET_KEY") == "manually_set_secret"

                # Load configuration
                config = load_config("config.yaml", prefix="APP")

                # Verify the manual value was NOT overridden by .env
                assert os.environ.get("APP_SECRET_KEY") == "manually_set_secret"

            finally:
                os.chdir(original_cwd)
                if "APP_SECRET_KEY" in os.environ:
                    del os.environ["APP_SECRET_KEY"]

    def test_complete_precedence_hierarchy(self):
        """Test the complete precedence hierarchy in one comprehensive test"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Scenario 1: Manual final env var (highest precedence - should win)
            os.environ["APP_SCENARIO1_VALUE"] = "manual_final_wins"

            # Scenario 2: Manual interpolation source (should be used in YAML interpolation)
            os.environ["INTERPOLATION_SOURCE"] = "manual_source_value"

            # Create .env file
            env_file = temp_path / ".env"
            env_file.write_text(
                """
# This should NOT override manual final env var
APP_SCENARIO1_VALUE=dotenv_should_not_win
# This should NOT override manual interpolation source
INTERPOLATION_SOURCE=dotenv_should_not_win
# This should be used since no manual override
DOTENV_ONLY_VAR=dotenv_wins_here
"""
            )

            # Create YAML
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
scenario1:
  value: yaml_should_not_win
scenario2:
  value: "{{ INTERPOLATION_SOURCE }}"
scenario3:
  value: "{{ DOTENV_ONLY_VAR }}"
scenario4:
  value: pure_yaml_value
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Load configuration
                config = load_config("config.yaml", prefix="APP")

                # Verify complete precedence hierarchy
                assert (
                    os.environ.get("APP_SCENARIO1_VALUE") == "manual_final_wins"
                )  # Manual final wins
                assert (
                    os.environ.get("APP_SCENARIO2_VALUE") == "manual_source_value"
                )  # Manual source used
                assert (
                    os.environ.get("APP_SCENARIO3_VALUE") == "dotenv_wins_here"
                )  # Dotenv when no manual
                assert (
                    os.environ.get("APP_SCENARIO4_VALUE") == "pure_yaml_value"
                )  # Pure YAML

                # Also verify in returned config
                assert config["APP_SCENARIO1_VALUE"] == "manual_final_wins"
                assert config["APP_SCENARIO2_VALUE"] == "manual_source_value"
                assert config["APP_SCENARIO3_VALUE"] == "dotenv_wins_here"
                assert config["APP_SCENARIO4_VALUE"] == "pure_yaml_value"

            finally:
                os.chdir(original_cwd)

    def test_config_loader_respects_manual_env_vars(self):
        """Test that ConfigLoader also respects manually set environment variables"""
        # Set manual environment variable
        os.environ["TEST_MANUAL_OVERRIDE"] = "manual_value"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .env file that tries to override
            env_file = temp_path / ".env"
            env_file.write_text("TEST_MANUAL_OVERRIDE=dotenv_should_not_win\n")

            # Create YAML
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
test:
  manual_override: "{{ TEST_MANUAL_OVERRIDE }}"
"""
            )

            try:
                # Create ConfigLoader with .env integration
                loader = ConfigLoader(prefix="APP", dotenv_path=str(env_file))

                # Load YAML config
                yaml_config = loader.load_from_yaml(yaml_file)

                # Set environment variables
                loader.set_env_vars(yaml_config)

                # Verify manual env var was used in interpolation
                assert yaml_config["test"]["manual_override"] == "manual_value"

                # Verify final env var respects manual setting if it exists
                if "APP_TEST_MANUAL_OVERRIDE" not in os.environ:
                    # If not set, it should be set by set_env_vars
                    assert os.environ.get("APP_TEST_MANUAL_OVERRIDE") == "manual_value"

            finally:
                if "TEST_MANUAL_OVERRIDE" in os.environ:
                    del os.environ["TEST_MANUAL_OVERRIDE"]
                if "APP_TEST_MANUAL_OVERRIDE" in os.environ:
                    del os.environ["APP_TEST_MANUAL_OVERRIDE"]

    def teardown_method(self):
        """Clean up test environment"""
        test_vars = [
            "MANUAL_FINAL_VAR",
            "APP_MANUAL_FINAL_VAR",
            "INTERPOLATION_SOURCE",
            "DOTENV_ONLY_VAR",
            "APP_SCENARIO1_VALUE",
            "APP_SCENARIO2_VALUE",
            "APP_SCENARIO3_VALUE",
            "APP_SCENARIO4_VALUE",
            "APP_CRITICAL_SETTING",
            "APP_SECRET_KEY",
            "TEST_MANUAL_OVERRIDE",
            "APP_TEST_MANUAL_OVERRIDE",
        ]

        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
