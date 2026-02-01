Feature: Basic YAML configuration loading
  As a developer
  I want to load configuration from YAML files into environment variables
  So that my application can access configuration consistently

  Background:
    Given the environment is clean

  Scenario: Load simple YAML configuration
    Given a YAML file "config.yaml" with content:
      """
      database_host: localhost
      database_port: 5432
      api_key: secret123
      """
    When I load the configuration
    Then the environment variable "DATABASE_HOST" should be "localhost"
    And the environment variable "DATABASE_PORT" should be "5432"
    And the environment variable "API_KEY" should be "secret123"

  Scenario: Load nested YAML configuration
    Given a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: 5432
        credentials:
          username: admin
          password: secret
      api:
        timeout: 30
        retries: 3
      """
    When I load the configuration
    Then the environment variable "DATABASE_HOST" should be "localhost"
    And the environment variable "DATABASE_PORT" should be "5432"
    And the environment variable "DATABASE_CREDENTIALS_USERNAME" should be "admin"
    And the environment variable "DATABASE_CREDENTIALS_PASSWORD" should be "secret"
    And the environment variable "API_TIMEOUT" should be "30"
    And the environment variable "API_RETRIES" should be "3"

  Scenario: Load configuration with prefix
    Given a YAML file "config.yaml" with content:
      """
      database:
        host: localhost
        port: 5432
      """
    When I load the configuration with prefix "MYAPP"
    Then the environment variable "MYAPP_DATABASE_HOST" should be "localhost"
    And the environment variable "MYAPP_DATABASE_PORT" should be "5432"

  Scenario: Handle missing YAML file gracefully
    Given no YAML file exists
    When I load the configuration from "nonexistent.yaml"
    Then no environment variables should be set
    And no error should occur