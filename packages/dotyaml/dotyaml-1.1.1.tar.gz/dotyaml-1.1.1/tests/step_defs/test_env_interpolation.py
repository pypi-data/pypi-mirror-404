"""
Test environment variable interpolation functionality
"""

import os
import tempfile
from pathlib import Path
import pytest
from dotyaml import load_config, ConfigLoader


class TestEnvironmentInterpolation:
    """Test environment variable interpolation with username/password examples"""

    def setup_method(self):
        """Set up test environment"""
        # Clean up any existing test env vars
        test_vars = [
            "DB_USERNAME",
            "DB_PASSWORD",
            "API_KEY",
            "SECRET_TOKEN",
            "APP_DB_USERNAME",
            "APP_DB_PASSWORD",
            "APP_API_KEY",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def test_basic_interpolation_with_credentials(self):
        """Test basic environment variable interpolation with database credentials"""
        # Set up environment variables
        os.environ["DB_USERNAME"] = "admin"
        os.environ["DB_PASSWORD"] = "secret123"

        # Create temporary YAML file with interpolation
        yaml_content = """
database:
  host: localhost
  port: 5432
  username: "{{ DB_USERNAME }}"
  password: "{{ DB_PASSWORD }}"
  name: myapp
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration
            config = load_config(yaml_path, prefix="APP", load_dotenv_first=False)

            # Verify interpolation worked
            assert config["APP_DATABASE_USERNAME"] == "admin"
            assert config["APP_DATABASE_PASSWORD"] == "secret123"
            assert config["APP_DATABASE_HOST"] == "localhost"

            # Verify env vars were set
            assert os.getenv("APP_DATABASE_USERNAME") == "admin"
            assert os.getenv("APP_DATABASE_PASSWORD") == "secret123"

        finally:
            Path(yaml_path).unlink()

    def test_interpolation_with_defaults(self):
        """Test interpolation with default values for missing credentials"""
        yaml_content = """
database:
  username: "{{ DB_USERNAME|default_user }}"
  password: "{{ DB_PASSWORD|changeme }}"
  api_key: "{{ API_KEY|dev_key_123 }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration (no env vars set, should use defaults)
            config = load_config(yaml_path, prefix="APP", load_dotenv_first=False)

            # Verify defaults were used
            assert config["APP_DATABASE_USERNAME"] == "default_user"
            assert config["APP_DATABASE_PASSWORD"] == "changeme"
            assert config["APP_DATABASE_API_KEY"] == "dev_key_123"

        finally:
            Path(yaml_path).unlink()

    def test_interpolation_with_env_override_defaults(self):
        """Test that environment variables override defaults"""
        # Set some environment variables
        os.environ["DB_USERNAME"] = "prod_admin"
        os.environ["API_KEY"] = "prod_api_key_456"

        yaml_content = """
database:
  username: "{{ DB_USERNAME|default_user }}"
  password: "{{ DB_PASSWORD|dev_password }}"
  api_key: "{{ API_KEY|dev_key_123 }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration
            config = load_config(yaml_path, prefix="APP", load_dotenv_first=False)

            # Verify env vars override defaults
            assert config["APP_DATABASE_USERNAME"] == "prod_admin"  # from env
            assert (
                config["APP_DATABASE_PASSWORD"] == "dev_password"
            )  # default (no env var)
            assert config["APP_DATABASE_API_KEY"] == "prod_api_key_456"  # from env

        finally:
            Path(yaml_path).unlink()

    def test_missing_required_env_var(self):
        """Test that missing required environment variables raise errors"""
        yaml_content = """
database:
  username: "{{ REQUIRED_USERNAME }}"
  password: "{{ REQUIRED_PASSWORD }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Should raise ValueError for missing required env var
            with pytest.raises(
                ValueError,
                match="Required environment variable 'REQUIRED_USERNAME' not found",
            ):
                load_config(yaml_path, prefix="APP", load_dotenv_first=False)

        finally:
            Path(yaml_path).unlink()

    def test_interpolation_in_nested_structures(self):
        """Test interpolation works in complex nested structures"""
        os.environ["DB_USERNAME"] = "nested_user"
        os.environ["DB_PASSWORD"] = "nested_pass"
        os.environ["REDIS_PASSWORD"] = "redis_secret"

        yaml_content = """
services:
  database:
    primary:
      username: "{{ DB_USERNAME }}"
      password: "{{ DB_PASSWORD }}"
    replica:
      username: "{{ DB_USERNAME }}"
      password: "{{ DB_PASSWORD }}"
  cache:
    redis:
      password: "{{ REDIS_PASSWORD }}"
      username: "{{ REDIS_USERNAME|default }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = load_config(yaml_path, prefix="APP", load_dotenv_first=False)

            # Verify nested interpolation
            assert config["APP_SERVICES_DATABASE_PRIMARY_USERNAME"] == "nested_user"
            assert config["APP_SERVICES_DATABASE_PRIMARY_PASSWORD"] == "nested_pass"
            assert config["APP_SERVICES_DATABASE_REPLICA_USERNAME"] == "nested_user"
            assert config["APP_SERVICES_DATABASE_REPLICA_PASSWORD"] == "nested_pass"
            assert config["APP_SERVICES_CACHE_REDIS_PASSWORD"] == "redis_secret"
            assert config["APP_SERVICES_CACHE_REDIS_USERNAME"] == "default"

        finally:
            Path(yaml_path).unlink()

    def test_interpolation_in_lists(self):
        """Test interpolation works in list values"""
        os.environ["DB_HOST1"] = "db1.example.com"
        os.environ["DB_HOST2"] = "db2.example.com"

        yaml_content = """
database:
  hosts:
    - "{{ DB_HOST1 }}"
    - "{{ DB_HOST2 }}"
    - "{{ DB_HOST3|localhost }}"
  credentials:
    - username: "{{ DB_USERNAME|user1 }}"
      password: "{{ DB_PASSWORD1|pass1 }}"
    - username: "{{ DB_USERNAME|user2 }}"
      password: "{{ DB_PASSWORD2|pass2 }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = load_config(yaml_path, prefix="APP", load_dotenv_first=False)

            # Verify list interpolation worked
            assert (
                config["APP_DATABASE_HOSTS"]
                == "db1.example.com,db2.example.com,localhost"
            )

        finally:
            Path(yaml_path).unlink()

    def test_dotenv_integration_with_credentials(self):
        """Test integration with .env file for credential management"""
        # Create temporary .env file
        env_content = """
DB_USERNAME=dotenv_admin
DB_PASSWORD=dotenv_secret_123
API_KEY=dotenv_api_key_789
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_path = f.name

        # Create YAML file with interpolation
        yaml_content = """
database:
  username: "{{ DB_USERNAME }}"
  password: "{{ DB_PASSWORD }}"
  host: localhost
api:
  key: "{{ API_KEY }}"
  timeout: 30
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration with custom .env path
            config = load_config(yaml_path, prefix="APP", dotenv_path=env_path)

            # Verify .env variables were loaded and interpolated
            assert config["APP_DATABASE_USERNAME"] == "dotenv_admin"
            assert config["APP_DATABASE_PASSWORD"] == "dotenv_secret_123"
            assert config["APP_API_KEY"] == "dotenv_api_key_789"
            assert config["APP_DATABASE_HOST"] == "localhost"
            assert config["APP_API_TIMEOUT"] == "30"

        finally:
            Path(yaml_path).unlink()
            Path(env_path).unlink()

    def test_config_loader_with_interpolation(self):
        """Test ConfigLoader class with environment interpolation"""
        os.environ["LOADER_USERNAME"] = "loader_user"
        os.environ["LOADER_PASSWORD"] = "loader_pass"

        yaml_content = """
database:
  username: "{{ LOADER_USERNAME }}"
  password: "{{ LOADER_PASSWORD }}"
  host: "{{ DB_HOST|localhost }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Use ConfigLoader
            loader = ConfigLoader(prefix="LOADER", load_dotenv_first=False)
            yaml_config = loader.load_from_yaml(yaml_path)

            # Verify interpolation in loaded config
            assert yaml_config["database"]["username"] == "loader_user"
            assert yaml_config["database"]["password"] == "loader_pass"
            assert yaml_config["database"]["host"] == "localhost"  # default value

            # Set environment variables
            loader.set_env_vars(yaml_config)

            # Verify env vars were set with prefix
            assert os.getenv("LOADER_DATABASE_USERNAME") == "loader_user"
            assert os.getenv("LOADER_DATABASE_PASSWORD") == "loader_pass"
            assert os.getenv("LOADER_DATABASE_HOST") == "localhost"

        finally:
            Path(yaml_path).unlink()

    def teardown_method(self):
        """Clean up test environment"""
        test_vars = [
            "DB_USERNAME",
            "DB_PASSWORD",
            "API_KEY",
            "SECRET_TOKEN",
            "APP_DB_USERNAME",
            "APP_DB_PASSWORD",
            "APP_API_KEY",
            "REQUIRED_USERNAME",
            "REQUIRED_PASSWORD",
            "REDIS_PASSWORD",
            "REDIS_USERNAME",
            "DB_HOST1",
            "DB_HOST2",
            "DB_HOST3",
            "DB_PASSWORD1",
            "DB_PASSWORD2",
            "LOADER_USERNAME",
            "LOADER_PASSWORD",
            "DB_HOST",
            "APP_DATABASE_USERNAME",
            "APP_DATABASE_PASSWORD",
            "APP_DATABASE_HOST",
            "APP_API_KEY",
            "APP_API_TIMEOUT",
            "APP_SERVICES_DATABASE_PRIMARY_USERNAME",
            "APP_SERVICES_DATABASE_PRIMARY_PASSWORD",
            "APP_SERVICES_DATABASE_REPLICA_USERNAME",
            "APP_SERVICES_DATABASE_REPLICA_PASSWORD",
            "APP_SERVICES_CACHE_REDIS_PASSWORD",
            "APP_SERVICES_CACHE_REDIS_USERNAME",
            "APP_DATABASE_HOSTS",
            "LOADER_DATABASE_USERNAME",
            "LOADER_DATABASE_PASSWORD",
            "LOADER_DATABASE_HOST",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
