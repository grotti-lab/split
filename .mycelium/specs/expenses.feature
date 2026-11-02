@feature:expenses @owner:kairat-rakhimov @area:expenses
Feature: Expenses
  An expense is something one member paid for the group: what it was, how much,
  who paid, and how it is shared. Amounts are in the group's currency, with two decimals.

  Scenario: Share an expense equally
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    When Ana adds an expense "Dinner" of 30.00 paid by Ana, split equally
    Then the expense "Dinner" shows 30.00 paid by Ana
    And the shares of "Dinner" are Ana 10.00, Ben 10.00 and Chloé 10.00

  Scenario: Share an expense between some members
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    When Ben adds an expense "Taxi" of 12.00 paid by Ben, split between Ben and Chloé
    Then the shares of "Taxi" are Ana 0.00, Ben 6.00 and Chloé 6.00

  Scenario: Share an expense by exact amounts
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    When Chloé adds an expense "Groceries" of 25.00 paid by Chloé, split by amounts Ana 10.00, Ben 5.00 and Chloé 10.00
    Then the shares of "Groceries" are Ana 10.00, Ben 5.00 and Chloé 10.00

  Scenario: Exact amounts must add up to the total
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    When Chloé adds an expense "Groceries" of 25.00 paid by Chloé, split by amounts Ana 10.00, Ben 5.00 and Chloé 9.00
    Then they see the message "The shares add up to 24.00, not 25.00"
    And the group has no expenses

  Scenario: An expense needs an amount above zero
    Given a group "Lisbon trip" with members Ana and Ben
    When Ana adds an expense "Coffee" of 0.00 paid by Ana, split equally
    Then they see the message "Enter an amount above zero"
    And the group has no expenses

  Scenario: Change an expense
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    When someone changes the amount of "Dinner" to 36.00
    Then the shares of "Dinner" are Ana 12.00, Ben 12.00 and Chloé 12.00

  Scenario: Delete an expense
    Given a group "Lisbon trip" with members Ana and Ben
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    When someone deletes the expense "Dinner"
    Then the group has no expenses
    And Ana is settled up
    And Ben is settled up
