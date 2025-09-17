"""Unit tests for entity resolver utilities."""

from _pytest.logging import LogCaptureFixture

from app.models.attributes import EntityType
from app.utils.entity_resolver import find_similar_entity, resolve_entity_with_fallback
from tests.factories import make_game_state, make_monster_instance, make_npc_instance


class TestEntityResolver:
    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.npc = make_npc_instance(instance_id="npc-guardian")
        self.monster = make_monster_instance(instance_id="wolf-alpha")
        self.game_state.npcs.append(self.npc)
        self.game_state.monsters.append(self.monster)
        self.player_id = self.game_state.character.instance_id

    def test_find_similar_entity_exact_and_fuzzy(self, caplog: LogCaptureFixture) -> None:
        exact = find_similar_entity(self.game_state, EntityType.NPC, self.npc.instance_id)
        assert exact is self.npc

        caplog.set_level("WARNING", logger="app.utils.entity_resolver")
        fuzzy_id = self.npc.instance_id.replace("-", "")
        fuzzy = find_similar_entity(self.game_state, EntityType.NPC, fuzzy_id)
        assert fuzzy is self.npc
        assert any("Fuzzy matched entity ID" in record.message for record in caplog.records)

        player = find_similar_entity(self.game_state, EntityType.PLAYER, self.player_id)
        assert player is self.game_state.character

        monster = find_similar_entity(self.game_state, EntityType.MONSTER, self.monster.instance_id)
        assert monster is self.monster

        missing = find_similar_entity(self.game_state, EntityType.MONSTER, "unknown-target")
        assert missing is None

    def test_resolve_entity_variants(self, caplog: LogCaptureFixture) -> None:
        monster = resolve_entity_with_fallback(
            self.game_state,
            entity_id=self.monster.instance_id,
            entity_type=EntityType.MONSTER,
        )
        assert monster == (self.monster, EntityType.MONSTER)

        missing = resolve_entity_with_fallback(
            self.game_state,
            entity_id="unknown",
            entity_type=EntityType.NPC,
        )
        assert missing == (None, None)

        caplog.set_level("WARNING", logger="app.utils.entity_resolver")
        npc_fuzzy = resolve_entity_with_fallback(self.game_state, entity_id=self.npc.instance_id.upper())
        assert npc_fuzzy == (self.npc, EntityType.NPC)
        assert any(self.npc.instance_id in record.message for record in caplog.records)

        player = resolve_entity_with_fallback(self.game_state, entity_id="player")
        assert player == (self.game_state.character, EntityType.PLAYER)
