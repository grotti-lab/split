"""The golden sets: every scenario in .mycelium/specs is a test.

The scenario text is the person's and is never edited here. The steps behind it
live in tests/golden/steps.py (or a steps module per feature, imported below).
"""

from pytest_bdd import scenarios

from .steps import *  # noqa: F403  the team's step definitions

scenarios("groups.feature", "expenses.feature", "balances.feature", "settle-up.feature")
