# Testing Guidelines

- Prefer the shared factories in `tests/factories/` for characters, locations, scenarios, monsters, and whole `GameState` objects. They keep data consistent and highlight just the variations each test cares about.
- Keep unit tests class-based with a `setup_method` and focus assertions on values derived from the fixtures (e.g., compare to `self.start_location.name` instead of repeating literals).
- For anything touching persistence, favor temporary directories and patching so tests stay isolated.
- When testing AI flows, stub the agents/orchestrator pieces so no OpenRouter traffic is triggered (e.g., patch `AgentFactory.create_agent`, agent `process` methods, or orchestrator helpers to yield deterministic events).
- Always run `PYTHONPATH=. pytest …` and `mypy --strict …` after adding tests to confirm everything stays healthy.
