"""Name utilities for display name de-duplication and formatting."""


def dedupe_display_name(existing: list[str], desired: str) -> str:
    """Ensure `desired` is unique within `existing` by suffixing a counter.

    If `desired` already exists, returns "{desired} N" with the smallest N>=2 not used.
    """
    if desired not in existing:
        return desired
    base = desired
    n = 2
    while f"{base} {n}" in existing:
        n += 1
    return f"{base} {n}"
