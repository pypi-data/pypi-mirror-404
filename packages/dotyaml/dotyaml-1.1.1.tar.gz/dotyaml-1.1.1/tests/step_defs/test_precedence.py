"""
Step definitions for environment variable precedence
"""

import os
import tempfile
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from dotyaml import load_config

# Load all scenarios from the feature file
scenarios("../features/precedence.feature")


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
        if any(prefix in key.upper() for prefix in ["DATABASE", "API", "MYAPP"])
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


@given(parsers.parse('the environment variable "{var_name}" is set to "{value}"'))
def set_environment_variable(var_name, value):
    """Set an environment variable to specified value"""
    os.environ[var_name] = value


@given('a YAML file "config.yaml" with content:')
def create_yaml_file_precedence(temp_dir, docstring):
    """Create a YAML file with content from the step's docstring"""
    yaml_path = temp_dir / "config.yaml"
    yaml_path.write_text(docstring.strip())
    return yaml_path


@given("no YAML file exists")
def no_yaml_file_exists():
    """Ensure no YAML file exists - nothing to do"""
    pass


@when("I load the configuration")
def load_configuration(temp_dir):
    """Load configuration from config.yaml"""
    config_path = temp_dir / "config.yaml"
    if config_path.exists():
        return load_config(str(config_path))
    return {}


@when(parsers.parse('I load the configuration with prefix "{prefix}"'))
def load_configuration_with_prefix(temp_dir, prefix):
    """Load configuration with specified prefix"""
    config_path = temp_dir / "config.yaml"
    if config_path.exists():
        return load_config(str(config_path), prefix=prefix)
    return {}


@when("I load the configuration with override enabled")
def load_configuration_with_override(temp_dir):
    """Load configuration with override enabled"""
    config_path = temp_dir / "config.yaml"
    if config_path.exists():
        return load_config(str(config_path), override=True)
    return {}


@when(parsers.parse('I load the configuration from "{filename}"'))
def load_configuration_from_file(temp_dir, filename):
    """Load configuration from specified file"""
    config_path = temp_dir / filename
    return load_config(str(config_path))


@then(
    parsers.parse('the environment variable "{var_name}" should be "{expected_value}"')
)
def check_environment_variable(var_name, expected_value):
    """Check that environment variable has expected value"""
    actual_value = os.getenv(var_name)
    assert (
        actual_value == expected_value
    ), f"Expected {var_name}={expected_value}, got {actual_value}"
