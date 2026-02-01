Feature: Environment variable precedence
  As a developer
  I want existing environment variables to take precedence over YAML configuration
  So that I can override configuration at runtime without changing files

  Background:
    Given the environment is clean

  Scenario: Environment variables override YAML values
    Given the environment variable "DATABASE_HOST" is set to "production-db.example.com"
    And the environment variable "API_TIMEOUT" is set to "60"
    And a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: 5432
      api:
        timeout: 30
        retries: 3
      """
    When I load the configuration
    Then the environment variable "DATABASE_HOST" should be "production-db.example.com"
    And the environment variable "DATABASE_PORT" should be "5432"
    And the environment variable "API_TIMEOUT" should be "60"
    And the environment variable "API_RETRIES" should be "3"

  Scenario: Environment variables override YAML values with prefix
    Given the environment variable "MYAPP_DATABASE_HOST" is set to "prod-db.example.com"
    And a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: 5432
      """
    When I load the configuration with prefix "MYAPP"
    Then the environment variable "MYAPP_DATABASE_HOST" should be "prod-db.example.com"
    And the environment variable "MYAPP_DATABASE_PORT" should be "5432"

  Scenario: Force override existing environment variables
    Given the environment variable "DATABASE_HOST" is set to "old-db.example.com"
    And a YAML file "config.yaml" with content:
      """
      database:
        host: new-db.example.com
        port: 5432
      """
    When I load the configuration with override enabled
    Then the environment variable "DATABASE_HOST" should be "new-db.example.com"
    And the environment variable "DATABASE_PORT" should be "5432"

  Scenario: Work with only environment variables (no YAML file)
    Given the environment variable "DATABASE_HOST" is set to "env-only-db.example.com"
    And the environment variable "DATABASE_PORT" is set to "3306"
    And no YAML file exists
    When I load the configuration from "nonexistent.yaml"
    Then the environment variable "DATABASE_HOST" should be "env-only-db.example.com"
    And the environment variable "DATABASE_PORT" should be "3306"