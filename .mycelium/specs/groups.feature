@feature:groups @owner:kairat-rakhimov @area:groups
Feature: Groups
  A group is the people who share costs, such as friends on a trip or flatmates.
  There are no accounts in the first release: anyone with a group's link can use it,
  and members are names.

  Scenario: Create a group with its members
    Given no groups exist
    When Ana creates a group "Lisbon trip" with members Ana, Ben and Chloé
    Then the group "Lisbon trip" has the members Ana, Ben and Chloé

  Scenario: Add a member later
    Given a group "Lisbon trip" with members Ana and Ben
    When someone adds Chloé to the group
    Then the group "Lisbon trip" has the members Ana, Ben and Chloé

  Scenario: Two members can't have the same name
    Given a group "Lisbon trip" with members Ana and Ben
    When someone adds another member called Ana
    Then they see the message "There is already an Ana in this group"
    And the group "Lisbon trip" has the members Ana and Ben

  Scenario: Anyone with the link sees the group
    Given a group "Lisbon trip" with members Ana and Ben
    And an expense "Dinner" of 30.00 paid by Ana, split equally
    When Ben opens the group's link
    Then Ben sees the members Ana and Ben
    And Ben sees the expense "Dinner" of 30.00

  Scenario: A member who has expenses can't be removed
    Given a group "Lisbon trip" with members Ana, Ben and Chloé
    And an expense "Taxi" of 12.00 paid by Chloé, split equally
    When someone removes Chloé from the group
    Then they see the message "Chloé has expenses in this group, so they can't be removed"
    And the group "Lisbon trip" has the members Ana, Ben and Chloé

  Scenario: Names that differ only in capitals are the same name
    Given a group "Lisbon trip" with members Ana and Ben
    When someone adds another member called ana
    Then they see the message "There is already an Ana in this group"
    And the group "Lisbon trip" has the members Ana and Ben
