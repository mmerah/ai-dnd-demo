"""Context accumulator for progressive context building."""


class ContextAccumulator:
    """Progressively accumulates context sections for AI prompts.

    Provides a clean API for building context strings section by section,
    automatically filtering out None values and joining with consistent separators.
    """

    def __init__(self) -> None:
        """Initialize an empty accumulator."""
        self.sections: list[str] = []

    def add(self, content: str | None) -> None:
        """Add a context section if not None.

        Args:
            content: Context string to add, or None to skip
        """
        if content:
            self.sections.append(content)

    def add_all(self, contents: list[str]) -> None:
        """Add multiple context sections at once.

        Args:
            contents: List of context strings to add (should not contain None)
        """
        self.sections.extend(contents)

    def build(self, separator: str = "\n\n") -> str:
        """Build the final context string.

        Args:
            separator: String to use between sections (default: double newline)

        Returns:
            Joined context string
        """
        return separator.join(self.sections)

    def is_empty(self) -> bool:
        """Check if accumulator has no sections.

        Returns:
            True if no sections have been added
        """
        return len(self.sections) == 0
