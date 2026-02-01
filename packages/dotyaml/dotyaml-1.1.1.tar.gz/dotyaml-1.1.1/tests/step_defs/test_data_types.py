"""
Step definitions for data type handling
"""

import os
import tempfile
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from dotyaml import load_config

# Load all scenarios from the feature file
scenarios("../features/data_types.feature")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test"""
    # Store original env vars
    original_env = dict(os.environ)

    # Clear test-related env vars
    test_vars = [
        key
        for key in os.environ.keys()
        if any(
            prefix in key.upper()
            for prefix in [
                "STRING",
                "INTEGER",
                "FLOAT",
                "BOOLEAN",
                "NULL",
                "EMPTY",
                "SIMPLE",
                "MIXED",
                "NESTED",
                "APP",
            ]
        )
    ]
    for var in test_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@given("the environment is clean")
def environment_is_clean():
    """Ensure environment is clean - handled by clean_env fixture"""
    pass


@given('a YAML file "config.yaml" with content:')
def create_yaml_file_data_types(temp_dir, docstring):
    """Create a YAML file with content from the step's docstring"""
    yaml_path = temp_dir / "config.yaml"
    yaml_path.write_text(docstring.strip())
    return yaml_path


@when("I load the configuration")
def load_configuration(temp_dir):
    """Load configuration from config.yaml"""
    config_path = temp_dir / "config.yaml"
    if config_path.exists():
        return load_config(str(config_path))
    return {}


@then(
    parsers.parse('the environment variable "{var_name}" should be "{expected_value}"')
)
def check_environment_variable(var_name, expected_value):
    """Check that environment variable has expected value"""
    actual_value = os.getenv(var_name)
    assert (
        actual_value == expected_value
    ), f"Expected {var_name}={expected_value}, got {actual_value}"


@then(parsers.parse('the environment variable "{var_name}" should be ""'))
def check_environment_variable_empty(var_name):
    """Check that environment variable is empty"""
    actual_value = os.getenv(var_name)
    assert actual_value == "", f"Expected {var_name} to be empty, got {actual_value}"


@then(
    parsers.parse(
        'the environment variable "{var_name}" should contain database replica information'
    )
)
def check_database_replica_info(var_name):
    """Check that environment variable contains database replica information"""
    actual_value = os.getenv(var_name)
    assert actual_value is not None, f"Environment variable {var_name} not set"
    # The actual format will depend on implementation - this is a placeholder
    # Could be JSON string or comma-separated format
    assert len(actual_value) > 0, f"Environment variable {var_name} is empty"
