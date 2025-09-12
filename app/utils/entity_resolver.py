"""Entity resolution utilities with fuzzy matching for handling typos in entity IDs."""

import logging
from difflib import SequenceMatcher

from app.models.attributes import EntityType
from app.models.entity import IEntity
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


def find_similar_entity(
    game_state: GameState,
    entity_type: EntityType,
    entity_id: str,
    similarity_threshold: float = 0.85,
) -> IEntity | None:
    """Find an entity by ID with fuzzy matching for typos.

    Logs once if a fuzzy match is used. Returns the entity if a match is found.
    """
    # First try exact match
    entity = game_state.get_entity_by_id(entity_type, entity_id)
    if entity:
        return entity

    # Get all entities of the specified type
    candidates: list[tuple[str, IEntity]] = []

    match entity_type:
        case EntityType.PLAYER:
            candidates = [(game_state.character.instance_id, game_state.character)]
        case EntityType.NPC:
            candidates = [(npc.instance_id, npc) for npc in game_state.npcs]
        case EntityType.MONSTER:
            candidates = [(mon.instance_id, mon) for mon in game_state.monsters]

    # Find best fuzzy match
    best_match = None
    best_ratio = 0.0
    best_entity = None

    for candidate_id, candidate_entity in candidates:
        ratio = SequenceMatcher(None, entity_id.lower(), candidate_id.lower()).ratio()
        if ratio > best_ratio and ratio >= similarity_threshold:
            best_ratio = ratio
            best_match = candidate_id
            best_entity = candidate_entity

    if best_entity and best_match is not None:
        logger.warning(
            f"Fuzzy matched entity ID '{entity_id}' to '{best_match}' "
            f"(similarity: {best_ratio:.2%}) for {entity_type.value}"
        )
        return best_entity

    return None


def resolve_entity_with_fallback(
    game_state: GameState,
    entity_id: str,
    entity_type: EntityType | None = None,
) -> tuple[IEntity | None, EntityType | None]:
    """Resolve an entity with multiple fallback strategies.

    1. If entity_id is "player", map to player's actual ID
    2. Try exact match with specified entity_type
    3. Try fuzzy match with specified entity_type
    4. If no entity_type specified, try all types with exact match
    5. If no entity_type specified, try all types with fuzzy match

    Args:
        game_state: Current game state
        entity_id: The entity ID to resolve
        entity_type: Optional entity type hint

    Returns:
        Tuple of (entity or None, resolved_entity_type or None)
    """
    # Special case: "player" maps to actual player ID
    if entity_id.lower() == "player":
        return game_state.character, EntityType.PLAYER

    # If entity_type is specified, try that first
    if entity_type:
        entity = find_similar_entity(game_state, entity_type, entity_id)
        if entity:
            return entity, entity_type

    # Try auto-detecting entity type by searching all types
    else:
        # First pass: exact matches
        for etype in EntityType:
            entity = game_state.get_entity_by_id(etype, entity_id)
            if entity:
                return entity, etype

        # Second pass: fuzzy matches
        best_entity: IEntity | None = None
        best_type: EntityType | None = None
        best_ratio = 0.0

        # Compute best fuzzy match across all types
        def consider(candidate_id: str, candidate_entity: IEntity, etype: EntityType) -> None:
            nonlocal best_entity, best_type, best_ratio
            ratio = SequenceMatcher(None, entity_id.lower(), candidate_id.lower()).ratio()
            if ratio >= 0.85 and ratio > best_ratio:
                best_ratio = ratio
                best_entity = candidate_entity
                best_type = etype

        # Players
        consider(game_state.character.instance_id, game_state.character, EntityType.PLAYER)
        # NPCs
        for npc in game_state.npcs:
            consider(npc.instance_id, npc, EntityType.NPC)
        # Monsters
        for mon in game_state.monsters:
            consider(mon.instance_id, mon, EntityType.MONSTER)

        if best_entity and best_type is not None:
            logger.warning(
                f"Fuzzy matched entity ID '{entity_id}' to '{getattr(best_entity, 'instance_id', '?')}' "
                f"(similarity: {best_ratio:.2%}) for {best_type.value}"
            )
            return best_entity, best_type

    return None, None
