# Drafted in Week 8, to be automated in Week 9 (not yet bound to step definitions).
Feature: Work with real-world TOML files safely

  # Level: acceptance
  # RTM: R04 (malformed input reports line and column)
  Scenario: A typo in a config file is reported at the right place
    Given a config file whose third line is "version = 1.4.2"
    When I try to open it with tomlkit
    Then I get a parse error that names line 3
    And the file on disk is unchanged

  # Level: acceptance
  # RTM: R07 (TOMLFile preserves Windows line endings)
  Scenario: Editing a Windows file keeps CRLF line endings
    Given a config file saved with CRLF line endings
    When I add the key "tool.ruff.line-length" with value 100 and save
    Then every line in the file ends with CRLF
    And the new key reads back as 100
