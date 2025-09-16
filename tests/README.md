# Testing Guidelines

- Prefer the shared factories in `tests/factories/` for characters, locations, scenarios, and monsters. They keep data consistent and highlight just the variations each test cares about.
- Keep unit tests class-based with a `setup_method` and focus assertions on values derived from the fixtures (e.g., compare to `self.start_location.name` instead of repeating literals).
- For anything touching persistence, favor temporary directories and patching so tests stay isolated.
- Always run `PYTHONPATH=. pytest …` and `mypy --strict …` after adding tests to confirm everything stays healthy.
