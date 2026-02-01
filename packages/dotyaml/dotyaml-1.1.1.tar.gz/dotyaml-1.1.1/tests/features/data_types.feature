Feature: Data type handling
  As a developer
  I want different YAML data types to be properly converted to environment variables
  So that my application can handle various configuration values correctly

  Background:
    Given the environment is clean

  Scenario: Handle different data types
    Given a YAML file "config.yaml" with content:
      """
      string_value: hello world
      integer_value: 42
      float_value: 3.14
      boolean_true: true
      boolean_false: false
      null_value: null
      empty_string: ""
      """
    When I load the configuration
    Then the environment variable "STRING_VALUE" should be "hello world"
    And the environment variable "INTEGER_VALUE" should be "42"
    And the environment variable "FLOAT_VALUE" should be "3.14"
    And the environment variable "BOOLEAN_TRUE" should be "true"
    And the environment variable "BOOLEAN_FALSE" should be "false"
    And the environment variable "NULL_VALUE" should be ""
    And the environment variable "EMPTY_STRING" should be ""

  Scenario: Handle list values
    Given a YAML file "config.yaml" with content:
      """
      simple_list:
        - item1
        - item2
        - item3
      mixed_list:
        - string
        - 42
        - true
      nested_config:
        allowed_hosts:
          - localhost
          - 127.0.0.1
          - example.com
      """
    When I load the configuration
    Then the environment variable "SIMPLE_LIST" should be "item1,item2,item3"
    And the environment variable "MIXED_LIST" should be "string,42,true"
    And the environment variable "NESTED_CONFIG_ALLOWED_HOSTS" should be "localhost,127.0.0.1,example.com"

  Scenario: Handle complex nested structures
    Given a YAML file "config.yaml" with content:
      """
      app:
        database:
          primary:
            host: db1.example.com
            port: 5432
            ssl: true
          replicas:
            - host: db2.example.com
              port: 5432
            - host: db3.example.com
              port: 5432
        cache:
          redis:
            urls:
              - redis://cache1:6379
              - redis://cache2:6379
      """
    When I load the configuration
    Then the environment variable "APP_DATABASE_PRIMARY_HOST" should be "db1.example.com"
    And the environment variable "APP_DATABASE_PRIMARY_PORT" should be "5432"
    And the environment variable "APP_DATABASE_PRIMARY_SSL" should be "true"
    And the environment variable "APP_DATABASE_REPLICAS" should contain database replica information
    And the environment variable "APP_CACHE_REDIS_URLS" should be "redis://cache1:6379,redis://cache2:6379"