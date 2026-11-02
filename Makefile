.PHONY: run test smoke golden report

run:  ## the app at http://localhost:8000
	uv run uvicorn --factory split.app:create_app --reload

test:  ## everything: the scaffold and the golden sets
	uv run pytest -q

smoke:  ## the scaffold only
	uv run pytest -q tests/test_smoke.py

golden:  ## the golden sets, then how many use cases work
	-uv run pytest -q tests/golden
	@uv run python scripts/report_to_mycelium.py

report:  ## send each scenario's last result to Mycelium (MYCELIUM_URL, MYCELIUM_TOKEN)
	uv run python scripts/report_to_mycelium.py --send
