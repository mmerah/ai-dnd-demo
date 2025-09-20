"""Metadata service for extracting information from messages."""

import logging
import re

from app.interfaces.services.game import IMetadataService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class MetadataService(IMetadataService):
    """Handles all metadata extraction from messages and game state."""

    def extract_npcs_mentioned(self, content: str, known_npcs: list[str]) -> list[str]:
        mentioned_npcs = []
        content_lower = content.lower()

        for npc_name in known_npcs:
            # Check if NPC name appears in content (case-insensitive)
            if npc_name.lower() in content_lower and npc_name not in mentioned_npcs:
                mentioned_npcs.append(npc_name)

        return mentioned_npcs

    def extract_targeted_npcs(self, message: str, game_state: GameState) -> list[str]:
        message = message.strip()
        if not message:
            return []

        available = self._build_npc_lookup(game_state)
        if not available:
            return []

        explicit_targets = self._extract_explicit_targets(message, available)
        if explicit_targets.unknown_tokens and not explicit_targets.matches:
            unknown_display = ", ".join(sorted(explicit_targets.unknown_tokens))
            raise ValueError(f"Unknown NPC target(s): {unknown_display}")

        ordered_hits = sorted(explicit_targets.matches, key=lambda item: item[0])
        seen: set[str] = set()
        ordered_ids: list[str] = []
        for _, npc_id in ordered_hits:
            if npc_id not in seen:
                seen.add(npc_id)
                ordered_ids.append(npc_id)

        return ordered_ids

    @staticmethod
    def _build_npc_lookup(game_state: GameState) -> dict[str, dict[str, tuple[str, ...]]]:
        current_location_id = game_state.scenario_instance.current_location_id
        lookup: dict[str, dict[str, tuple[str, ...]]] = {}
        for npc in game_state.npcs:
            if npc.current_location_id != current_location_id:
                continue
            canonical_id = npc.instance_id
            names = {
                "display": tuple(filter(None, [npc.sheet.display_name])),
                "character": (npc.sheet.character.name,),
            }
            lookup[canonical_id] = names
        return lookup

    @staticmethod
    def _normalize(token: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", token.lower())

    def _match_token(self, token: str, lookup: dict[str, dict[str, tuple[str, ...]]]) -> str | None:
        normalized = self._normalize(token)
        for npc_id, name_groups in lookup.items():
            for names in name_groups.values():
                for name in names:
                    if self._normalize(name) == normalized:
                        return npc_id
        return None

    class _ExplicitMatches:
        def __init__(self) -> None:
            self.matches: list[tuple[int, str]] = []
            self.unknown_tokens: list[str] = []

    def _extract_explicit_targets(
        self, message: str, lookup: dict[str, dict[str, tuple[str, ...]]]
    ) -> "MetadataService._ExplicitMatches":
        result = MetadataService._ExplicitMatches()
        for match in re.finditer(r"@([A-Za-z][\w'\-]*)", message):
            token = match.group(1)
            npc_id = self._match_token(token, lookup)
            if npc_id:
                result.matches.append((match.start(), npc_id))
            else:
                result.unknown_tokens.append(token)
        return result

    def get_current_location(self, game_state: GameState) -> str | None:
        return game_state.location

    def get_combat_round(self, game_state: GameState) -> int | None:
        if game_state.combat.is_active:
            return game_state.combat.round_number
        return None
