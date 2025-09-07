"""Simple instance ID generation for game entities."""

import random
import re


def generate_instance_id(base_name: str) -> str:
    """Generate a simple instance ID from a base name.

    Args:
        base_name: The base name (e.g., "Goblin", "Wolf", "Elena")

    Returns:
        A simplified ID like "goblin-1234" or "wolf-5678"

    Examples:
        "Goblin" -> "goblin-1234"
        "Goblin Boss" -> "goblin-boss-5678"
        "Ancient Red Dragon" -> "ancient-red-dragon-9012"
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    clean_name = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-")

    # Generate a 4-digit random suffix
    suffix = random.randint(1000, 9999)

    return f"{clean_name}-{suffix}"
