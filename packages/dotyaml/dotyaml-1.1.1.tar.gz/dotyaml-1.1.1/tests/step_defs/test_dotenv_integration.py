"""
Test dotenv integration functionality
"""

import os
import tempfile
from pathlib import Path
import pytest
from dotyaml import load_config, ConfigLoader


class TestDotenvIntegration:
    """Test automatic .env file loading and integration"""

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
            "TEST_SECRET",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def test_automatic_dotenv_loading(self):
        """Test that .env file is automatically loaded"""
        # Create temporary directory to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .env file
            env_file = temp_path / ".env"
            env_file.write_text(
                """
DB_USERNAME=env_admin
DB_PASSWORD=env_secret_password
API_KEY=env_api_key_123
TEST_SECRET=very_secret_value
"""
            )

            # Create YAML config file
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
database:
  host: localhost
  port: 5432
  name: myapp
api:
  timeout: 30
  retries: 3
"""
            )

            # Change to temp directory so .env is found automatically
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Load config - should automatically load .env
                config = load_config("config.yaml", prefix="APP")

                # Verify .env variables were loaded
                assert os.getenv("DB_USERNAME") == "env_admin"
                assert os.getenv("DB_PASSWORD") == "env_secret_password"
                assert os.getenv("API_KEY") == "env_api_key_123"
                assert os.getenv("TEST_SECRET") == "very_secret_value"

                # Verify YAML config was still processed
                assert config["APP_DATABASE_HOST"] == "localhost"
                assert config["APP_DATABASE_PORT"] == "5432"

            finally:
                os.chdir(original_cwd)

    def test_custom_dotenv_path(self):
        """Test loading .env from custom path"""
        # Create custom .env file
        env_content = """
CUSTOM_USERNAME=custom_admin
CUSTOM_PASSWORD=custom_secret
CUSTOM_API_KEY=custom_key_456
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            custom_env_path = f.name

        yaml_content = """
database:
  host: localhost
  username: "{{ CUSTOM_USERNAME }}"
  password: "{{ CUSTOM_PASSWORD }}"
api:
  key: "{{ CUSTOM_API_KEY }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load with custom .env path
            config = load_config(yaml_path, prefix="APP", dotenv_path=custom_env_path)

            # Verify custom .env was loaded and interpolated
            assert config["APP_DATABASE_USERNAME"] == "custom_admin"
            assert config["APP_DATABASE_PASSWORD"] == "custom_secret"
            assert config["APP_API_KEY"] == "custom_key_456"

        finally:
            Path(yaml_path).unlink()
            Path(custom_env_path).unlink()

    def test_disable_dotenv_loading(self):
        """Test disabling automatic .env loading"""
        # Create temporary directory with .env file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .env file
            env_file = temp_path / ".env"
            env_file.write_text("SHOULD_NOT_LOAD=should_not_be_loaded\n")

            # Create YAML config
            yaml_file = temp_path / "config.yaml"
            yaml_file.write_text(
                """
database:
  host: localhost
  username: "{{ DB_USERNAME|default_user }}"
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Load config with dotenv disabled
                config = load_config(
                    "config.yaml", prefix="APP", load_dotenv_first=False
                )

                # Verify .env was NOT loaded
                assert os.getenv("SHOULD_NOT_LOAD") is None
                assert config["APP_DATABASE_USERNAME"] == "default_user"  # used default

            finally:
                os.chdir(original_cwd)

    def test_dotenv_precedence_over_yaml_interpolation(self):
        """Test that .env values are used in YAML interpolation"""
        # Create .env file
        env_content = """
DB_USERNAME=dotenv_user
DB_PASSWORD=dotenv_password
API_ENDPOINT=https://api.production.com
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_path = f.name

        # Create YAML with interpolation and defaults
        yaml_content = """
database:
  username: "{{ DB_USERNAME|yaml_default_user }}"
  password: "{{ DB_PASSWORD|yaml_default_pass }}"
  host: "{{ DB_HOST|localhost }}"
api:
  endpoint: "{{ API_ENDPOINT|https://api.dev.com }}"
  timeout: 30
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration
            config = load_config(yaml_path, prefix="APP", dotenv_path=env_path)

            # Verify .env values were used instead of YAML defaults
            assert config["APP_DATABASE_USERNAME"] == "dotenv_user"  # from .env
            assert config["APP_DATABASE_PASSWORD"] == "dotenv_password"  # from .env
            assert (
                config["APP_DATABASE_HOST"] == "localhost"
            )  # YAML default (no .env value)
            assert (
                config["APP_API_ENDPOINT"] == "https://api.production.com"
            )  # from .env

        finally:
            Path(yaml_path).unlink()
            Path(env_path).unlink()

    def test_existing_env_vars_take_precedence_over_dotenv(self):
        """Test that existing environment variables take precedence over .env"""
        # Set existing environment variable
        os.environ["EXISTING_VAR"] = "existing_value"

        # Create .env file with same variable
        env_content = """
EXISTING_VAR=dotenv_value
NEW_VAR=new_value
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_path = f.name

        yaml_content = """
config:
  existing: "{{ EXISTING_VAR }}"
  new: "{{ NEW_VAR }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = load_config(yaml_path, prefix="APP", dotenv_path=env_path)

            # Verify existing env var takes precedence
            assert (
                config["APP_CONFIG_EXISTING"] == "existing_value"
            )  # from existing env
            assert config["APP_CONFIG_NEW"] == "new_value"  # from .env

        finally:
            Path(yaml_path).unlink()
            Path(env_path).unlink()
            if "EXISTING_VAR" in os.environ:
                del os.environ["EXISTING_VAR"]

    def test_config_loader_with_dotenv(self):
        """Test ConfigLoader with .env integration"""
        # Create .env file
        env_content = """
LOADER_DB_USER=loader_admin
LOADER_DB_PASS=loader_secret
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_path = f.name

        yaml_content = """
database:
  username: "{{ LOADER_DB_USER }}"
  password: "{{ LOADER_DB_PASS }}"
  host: localhost
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Create ConfigLoader with custom .env path
            loader = ConfigLoader(prefix="TEST", dotenv_path=env_path)

            # Load YAML config
            config = loader.load_from_yaml(yaml_path)

            # Verify .env variables were loaded and interpolated
            assert config["database"]["username"] == "loader_admin"
            assert config["database"]["password"] == "loader_secret"

        finally:
            Path(yaml_path).unlink()
            Path(env_path).unlink()

    def test_env_file_same_directory_as_yaml(self):
        """Test .env file discovery in same directory as YAML file"""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create subdirectory for config files
            config_dir = temp_path / "config"
            config_dir.mkdir()

            # Create .env file in the config directory
            env_file = config_dir / ".env"
            env_file.write_text(
                """
CONFIG_DB_USER=config_dir_admin
CONFIG_DB_PASS=config_dir_secret
CONFIG_API_KEY=config_dir_api_123
"""
            )

            # Create YAML file in the same config directory
            yaml_file = config_dir / "app.yaml"
            yaml_file.write_text(
                """
database:
  username: "{{ CONFIG_DB_USER }}"
  password: "{{ CONFIG_DB_PASS }}"
  host: localhost
api:
  key: "{{ CONFIG_API_KEY }}"
  timeout: 30
"""
            )

            # Important: Change to parent directory (not config dir)
            # This tests that .env is found in YAML directory, not CWD
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)  # CWD is parent of config dir

                # Load config using relative path to YAML in subdirectory
                config = load_config("config/app.yaml", prefix="TEST")

                # Verify .env from YAML directory was loaded and interpolated
                assert config["TEST_DATABASE_USERNAME"] == "config_dir_admin"
                assert config["TEST_DATABASE_PASSWORD"] == "config_dir_secret"
                assert config["TEST_API_KEY"] == "config_dir_api_123"

                # Verify environment variables were set
                assert os.getenv("CONFIG_DB_USER") == "config_dir_admin"
                assert os.getenv("CONFIG_DB_PASS") == "config_dir_secret"

            finally:
                os.chdir(original_cwd)

    def test_env_file_search_priority(self):
        """Test .env file search priority: CWD takes precedence over YAML directory"""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create subdirectory for YAML
            yaml_dir = temp_path / "configs"
            yaml_dir.mkdir()

            # Create .env in root directory (higher priority)
            root_env = temp_path / ".env"
            root_env.write_text("PRIORITY_VAR=from_root\n")

            # Create .env in YAML directory (lower priority)
            yaml_env = yaml_dir / ".env"
            yaml_env.write_text("PRIORITY_VAR=from_yaml_dir\n")

            # Create YAML file
            yaml_file = yaml_dir / "config.yaml"
            yaml_file.write_text(
                """
test:
  value: "{{ PRIORITY_VAR }}"
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Load config - should use .env from CWD, not YAML directory
                config = load_config("configs/config.yaml", prefix="PRIORITY")

                # Verify CWD .env took precedence
                assert config["PRIORITY_TEST_VALUE"] == "from_root"
                assert os.getenv("PRIORITY_VAR") == "from_root"

            finally:
                os.chdir(original_cwd)

    def test_config_loader_env_file_same_directory(self):
        """Test ConfigLoader .env discovery in same directory as YAML"""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()

            # Create .env in subdirectory
            env_file = sub_dir / ".env"
            env_file.write_text(
                """
LOADER_VAR1=loader_value1
LOADER_VAR2=loader_value2
"""
            )

            # Create YAML in same subdirectory
            yaml_file = sub_dir / "config.yaml"
            yaml_file.write_text(
                """
config:
  var1: "{{ LOADER_VAR1 }}"
  var2: "{{ LOADER_VAR2 }}"
"""
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)  # CWD is parent directory

                # Create ConfigLoader - should find .env in YAML directory
                loader = ConfigLoader(prefix="LOADER")
                config_data = loader.load_from_yaml("subdir/config.yaml")

                # Verify .env was loaded and interpolated
                assert config_data["config"]["var1"] == "loader_value1"
                assert config_data["config"]["var2"] == "loader_value2"

            finally:
                os.chdir(original_cwd)

    def test_realistic_secrets_management_scenario(self):
        """Test realistic scenario: secrets in .env, config in YAML"""
        # Create .env file with secrets (this would be .gitignored)
        env_content = """
# Database credentials - keep secret!
DB_USERNAME=production_admin
DB_PASSWORD=super_secret_password_123!
API_SECRET_KEY=sk_live_abc123def456ghi789
JWT_SECRET=jwt_signing_secret_xyz789

# Third-party service credentials
STRIPE_SECRET_KEY=sk_test_stripe_key_123
SENDGRID_API_KEY=SG.sendgrid_key_456
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_path = f.name

        # Create YAML config file (this would be committed to git)
        yaml_content = """
# Application configuration
app:
  name: MyApp
  version: "1.0.0"
  debug: false

# Database configuration - secrets come from .env
database:
  host: "{{ DB_HOST|localhost }}"
  port: 5432
  name: "{{ DB_NAME|myapp_production }}"
  username: "{{ DB_USERNAME }}"
  password: "{{ DB_PASSWORD }}"
  pool_size: 10
  ssl: true

# API configuration
api:
  secret_key: "{{ API_SECRET_KEY }}"
  jwt_secret: "{{ JWT_SECRET }}"
  rate_limit: 1000
  timeout: 30

# External services
services:
  stripe:
    secret_key: "{{ STRIPE_SECRET_KEY }}"
    webhook_secret: "{{ STRIPE_WEBHOOK_SECRET|default_webhook_secret }}"
  sendgrid:
    api_key: "{{ SENDGRID_API_KEY }}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load configuration - this is what would happen in production
            config = load_config(yaml_path, prefix="MYAPP", dotenv_path=env_path)

            # Verify secrets were loaded from .env and applied
            assert config["MYAPP_DATABASE_USERNAME"] == "production_admin"
            assert config["MYAPP_DATABASE_PASSWORD"] == "super_secret_password_123!"
            assert config["MYAPP_API_SECRET_KEY"] == "sk_live_abc123def456ghi789"
            assert (
                config["MYAPP_SERVICES_STRIPE_SECRET_KEY"] == "sk_test_stripe_key_123"
            )

            # Verify non-secret config from YAML
            assert config["MYAPP_APP_NAME"] == "MyApp"
            assert config["MYAPP_DATABASE_HOST"] == "localhost"  # default value
            assert config["MYAPP_DATABASE_NAME"] == "myapp_production"  # default value
            assert config["MYAPP_DATABASE_SSL"] == "true"
            assert (
                config["MYAPP_SERVICES_STRIPE_WEBHOOK_SECRET"]
                == "default_webhook_secret"
            )  # default

            # Verify environment variables are available to the application
            assert os.getenv("MYAPP_DATABASE_USERNAME") == "production_admin"
            assert os.getenv("MYAPP_API_SECRET_KEY") == "sk_live_abc123def456ghi789"

        finally:
            Path(yaml_path).unlink()
            Path(env_path).unlink()

    def teardown_method(self):
        """Clean up test environment"""
        test_vars = [
            "DB_USERNAME",
            "DB_PASSWORD",
            "API_KEY",
            "SECRET_TOKEN",
            "TEST_SECRET",
            "APP_DB_USERNAME",
            "APP_DB_PASSWORD",
            "APP_API_KEY",
            "CUSTOM_USERNAME",
            "CUSTOM_PASSWORD",
            "CUSTOM_API_KEY",
            "SHOULD_NOT_LOAD",
            "EXISTING_VAR",
            "NEW_VAR",
            "LOADER_DB_USER",
            "LOADER_DB_PASS",
            "DB_HOST",
            "DB_NAME",
            "API_SECRET_KEY",
            "JWT_SECRET",
            "STRIPE_SECRET_KEY",
            "SENDGRID_API_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "CONFIG_DB_USER",
            "CONFIG_DB_PASS",
            "CONFIG_API_KEY",
            "PRIORITY_VAR",
            "LOADER_VAR1",
            "LOADER_VAR2",
        ]

        # Also clean up any MYAPP_ and APP_ prefixed vars
        all_env_vars = list(os.environ.keys())
        for var in all_env_vars:
            if var.startswith(("MYAPP_", "APP_", "TEST_")) or var in test_vars:
                if var in os.environ:
                    del os.environ[var]
