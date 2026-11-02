# Split

**Split bills with friends and see who owes whom.** Grotti's sample product: the app its AI team builds in evidence runs, from the person's use cases.

- [BRIEF.md](BRIEF.md): the brief. What it's for, the first release, what's left out, the risks, and the gaps left open on purpose.
- [.mycelium/specs](.mycelium/specs): the golden sets, 4 features and 21 use cases, in Mycelium's living-spec format. They are the person's words and the tests at once.
- [.mycelium/memory.yaml](.mycelium/memory.yaml): short facts every agent reads in its briefing.
- [.grotti/process.yaml](.grotti/process.yaml): how the team works, version 1.

This folder is a seed. Each evidence run copies it into a product repo of its own, which the team clones and builds in.

## Where it starts

A scaffold: the app runs and has a database, and every golden-set scenario runs as a test. **No use case works yet**; building them is the team's job.

```bash
make smoke    # the scaffold works
make golden   # the golden sets: "0 of 21 use cases work" at the start
make run      # the app at http://localhost:8000
```

`make report` sends each scenario's result to Mycelium (set `MYCELIUM_URL` and `MYCELIUM_TOKEN`). Syncing the specs and memory into the hub is Mycelium's own script: `python <mycelium>/scripts/mycelium_sync.py .mycelium --url $MYCELIUM_URL`.

## Stack

Python 3.12+, FastAPI and server-rendered pages, SQLite, money in whole cents. The golden sets run with pytest-bdd. Dependencies are managed with [uv](https://docs.astral.sh/uv/).
