@feature:settle-up @owner:kairat-rakhimov @area:settle-up
Feature: Settle up
  Members pay each other outside the app and record it here,
  so the balances come back to zero.

  Scenario: Record a payment
    Given a group "Lisbon trip" with members Ana and Ben
    And an expense "Dinner" of 20.00 paid by Ana, split equally
    When Ben records paying Ana 10.00
    Then Ben is settled up
    And Ana is settled up

  Scenario: Paying back part of a debt leaves the rest owed
    Given a group "Lisbon trip" with members Ana and Ben
    And an expense "Dinner" of 20.00 paid by Ana, split equally
    When Ben records paying Ana 4.00
    Then Ben owes 6.00
    And the only suggested payment is "Ben pays Ana 6.00"

  Scenario: A group where everyone has paid shows it is settled
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    When Ben records paying Ana 10.00
    And Chloé records paying Ana 10.00
    Then the group shows "Everyone is settled up"

  Scenario: Undo a payment
    Given a group "Lisbon trip" with members Ana and Ben
    And an expense "Dinner" of 20.00 paid by Ana, split equally
    And Ben recorded paying Ana 10.00
    When someone deletes Ben's payment to Ana
    Then Ben owes 10.00
