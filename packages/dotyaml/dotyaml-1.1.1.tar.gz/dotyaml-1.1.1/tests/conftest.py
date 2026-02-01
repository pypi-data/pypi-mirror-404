"""
Shared pytest configuration and fixtures for yamlenv tests
"""

import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide access to test data directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files during tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def isolate_environment():
    """Isolate each test's environment variables"""
    # Store original environment
    original_env = dict(os.environ)

    yield

    # Restore original environment after test
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_yaml_content():
    """Provide sample YAML content for testing"""
    return """
database:
  host: localhost
  port: 5432
  credentials:
    username: testuser
    password: testpass
api:
  base_url: https://api.example.com
  timeout: 30
  retries: 3
cache:
  redis:
    url: redis://localhost:6379
    ttl: 3600
features:
  feature_a: true
  feature_b: false
  feature_c: null
tags:
  - production
  - api
  - cache
"""


@pytest.fixture
def complex_yaml_content():
    """Provide complex nested YAML content for testing"""
    return """
app:
  name: test-app
  version: "1.0.0"
  environment: test
  services:
    database:
      primary:
        host: db1.example.com
        port: 5432
        ssl: true
        pool_size: 10
      replicas:
        - host: db2.example.com
          port: 5432
          readonly: true
        - host: db3.example.com
          port: 5432
          readonly: true
    cache:
      redis:
        nodes:
          - host: redis1.example.com
            port: 6379
          - host: redis2.example.com
            port: 6379
        cluster: true
        ttl: 7200
    messaging:
      queue:
        rabbitmq:
          host: mq.example.com
          port: 5672
          vhost: /test
          credentials:
            username: mquser
            password: mqpass
logging:
  level: DEBUG
  handlers:
    - console
    - file
  formatters:
    console: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
"""
