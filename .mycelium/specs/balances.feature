@feature:balances @owner:kairat-rakhimov @area:balances
Feature: Balances
  What each member is owed or owes, from all the group's expenses and payments,
  and the fewest payments that settle everyone.

  Scenario: Balances after one expense
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    Then Ana is owed 20.00
    And Ben owes 10.00
    And Chloé owes 10.00

  Scenario: Balances from several expenses
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    And an expense "Taxi" of 12.00 paid by Ben, split between Ben and Chloé
    And an expense "Groceries" of 25.00 paid by Chloé, split by amounts Ana 10.00, Ben 5.00 and Chloé 10.00
    Then Ana is owed 10.00
    And Ben owes 9.00
    And Chloé owes 1.00

  Scenario: The person who paid covers the leftover cent
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Snacks" of 10.00 paid by Ana, split equally
    Then the shares of "Snacks" are Ana 3.34, Ben 3.33 and Chloé 3.33
    And Ana is owed 6.66
    And Ben owes 3.33
    And Chloé owes 3.33

  Scenario: Who owes whom
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    Then the suggested payments are "Ben pays Ana 10.00" and "Chloé pays Ana 10.00"

  Scenario: Debts pass through to the fewest payments
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Tickets" of 10.00 paid by Ana, for Ben only
    And an expense "Lunch" of 10.00 paid by Ben, for Chloé only
    Then Ben is settled up
    And the only suggested payment is "Chloé pays Ana 10.00"

  Scenario: The first person sharing covers the leftover cent when the payer isn't sharing
    Given a group "Lisbon trip" with members Ana, Ben, Chloé and Dan
    And an expense "Snacks" of 10.00 paid by Ana, split between Ben, Chloé and Dan
    Then the shares of "Snacks" are Ana 0.00, Ben 3.34, Chloé 3.33 and Dan 3.33
    And Ana is owed 10.00
