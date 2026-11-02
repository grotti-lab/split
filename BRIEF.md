# Split: the brief

*The brief for Grotti's sample product, in the shape a shaping conversation produces ([../../docs/PROCESS.md](../../docs/PROCESS.md)). Drafted 2026-11-02 for Kairat, the product owner, to check. The golden sets in [.mycelium/specs](.mycelium/specs) are the first release's use cases.*

## The problem

Friends on a trip, or flatmates, pay for things in turn and lose track of who owes whom. Today they keep a note on a phone, or they guess, and someone ends up out of pocket.

## Who it's for

Small groups of friends or flatmates, 2 to 10 people, mostly on their phones.

## What success looks like

*"Split: everyone knows who owes whom."* Someone makes a group for a trip and shares its link. Each person adds what they paid. At the end, Split shows the fewest payments that settle everyone, and the group records them as people pay. Nobody needs an account, and nobody does sums.

## First release

Four features, 21 use cases.

| Feature | Use cases | What it covers |
|---|---|---|
| [Groups](.mycelium/specs/groups.feature) | 5 | Making a group, adding people, opening it by its link |
| [Expenses](.mycelium/specs/expenses.feature) | 7 | Adding what someone paid, shared equally, between some people or by exact amounts; changing and deleting it |
| [Balances](.mycelium/specs/balances.feature) | 5 | Who is owed and who owes, the leftover cent, and the fewest payments |
| [Settle up](.mycelium/specs/settle-up.feature) | 4 | Recording payments between members, in full or in part, and undoing one |

## Not now

- Accounts and sign-in: anyone with a group's link can use it.
- More than one currency in a group.
- Photos of receipts.
- Notifications and reminders.
- Phone apps in the app stores.

## Risks

- **Rounding.** Shares that don't divide evenly must still add up to the total. The first slice covers it with "The person who paid covers the leftover cent".
- **Two people editing a group at the same moment.** The first release accepts last-write-wins; nobody has asked for more.

## Left open on purpose

A real brief has gaps, and the team is expected to notice them and bring each one to the person as a decision, explained. Three are known:
- What happens when someone changes an expense after the group has settled up?
- What happens when someone records paying more than they owe?
- Who covers the leftover cent when the person who paid isn't one of the people sharing the expense?

## How it's built

A website that works on phones and computers, built with Python, FastAPI and server-rendered pages. Data is kept in SQLite, and money is stored as whole cents. Every use case is an automatic test, run with pytest-bdd straight from the golden sets. The team records any change to this, with its reasons, as a decision record.

## Where it runs

In evidence runs, on Grotti's server, behind a private link.

## Budget and time

Set for each evidence run, and recorded in [../../docs/STATUS.md](../../docs/STATUS.md) along with the run.
