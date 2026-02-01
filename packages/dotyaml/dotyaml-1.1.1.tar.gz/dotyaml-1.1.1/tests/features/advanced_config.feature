Feature: Advanced configuration scenarios
  As a developer
  I want advanced configuration options and proper error handling
  So that I can use yamlenv in complex deployment scenarios

  Background:
    Given the environment is clean

  Scenario: Custom key transformation
    Given a YAML file "config.yaml" with content:
      """
      database-host: localhost
      api_endpoint: https://api.example.com
      cache.redis.url: redis://localhost:6379
      """
    When I load the configuration with custom key transformation
    Then the environment variable "DATABASE_HOST" should be "localhost"
    And the environment variable "API_ENDPOINT" should be "https://api.example.com"
    And the environment variable "CACHE_REDIS_URL" should be "redis://localhost:6379"

  Scenario: Handle malformed YAML file
    Given a YAML file "config.yaml" with invalid content:
      """
      database:
        host: localhost
        port: 5432
      invalid_yaml: [unclosed list
      """
    When I attempt to load the configuration
    Then a configuration error should occur
    And the error message should indicate YAML parsing failure

  Scenario: Load configuration without setting environment variables
    Given a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: 5432
      """
    When I load the configuration without setting environment variables
    Then a configuration dictionary should be returned
    And the configuration should contain "database.host" with value "localhost"
    And the configuration should contain "database.port" with value 5432
    And no environment variables should be set

  Scenario: Selective environment variable loading
    Given the environment variable "APP_DATABASE_HOST" is set to "db.example.com"
    And the environment variable "APP_DATABASE_PORT" is set to "5432"
    And the environment variable "OTHER_SERVICE_URL" is set to "https://other.example.com"
    When I load configuration from environment variables with prefix "APP"
    Then the loaded configuration should contain database settings
    And the loaded configuration should not contain other service settings

  Scenario: Configuration validation
    Given a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: not_a_number
      required_field: null
      """
    When I load the configuration with validation enabled
    Then a validation error should occur
    And the error should indicate invalid port type
    And the error should indicate missing required field