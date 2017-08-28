Feature: Registration

  Scenario: We register with an email that is not in use
    Given an email, first name, last name, and password

    When we try to register
    Then we should get a user object back

  Scenario: We register with an email that is in use
    Given an email, first name, last name, and password
    And a user that has already registered with the given email

    When we try to register
    Then we should be told that the email is taken

