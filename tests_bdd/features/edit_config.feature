Feature: Edit a project config file without losing its formatting
  As a Python developer who keeps tool settings in pyproject.toml
  I want to change one value through tomlkit
  So that my comments, spacing and key order survive the edit

  # Level: acceptance (end to end: real file on disk -> TOMLFile -> edit -> file on disk)
  # RTM: R03 (edits preserve untouched layout), R07 (file round-trip)
  Scenario: Bump the version and keep every comment and blank line
    Given a config file containing:
      """
      # Project settings
      [project]
      name = "demo"  # do not rename
      version = "1.4.2"

      # Tools
      [tool.pytest]
      addopts = "-q"
      """
    When I open the file with tomlkit and set "project.version" to "1.5.0"
    And I save the file
    Then the file on disk is exactly:
      """
      # Project settings
      [project]
      name = "demo"  # do not rename
      version = "1.5.0"

      # Tools
      [tool.pytest]
      addopts = "-q"
      """
    And reading "project.version" from the saved file gives "1.5.0"
