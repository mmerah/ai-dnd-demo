"""Unit tests for MonsterManagerService."""

from app.models.attributes import AttackAction
from app.services.game.monster_manager_service import MonsterManagerService
from tests.factories import make_monster_sheet


class BadSpeed:
    def __str__(self) -> str:
        raise ValueError("unreadable speed")


class TestMonsterManagerService:
    def setup_method(self) -> None:
        self.monster_manager_service = MonsterManagerService()
        self.location_id = "dungeon-entry"
        self.base_sheet = make_monster_sheet(name="Dire Wolf", hit_points=16)

    def test_create_monster_instance_maps_stats(self) -> None:
        attack = AttackAction(name="Bite", attack_roll_bonus=5, damage="2d6+3", damage_type="piercing")
        sheet = self.base_sheet.model_copy(
            update={
                "hit_dice": "3d10+6",
                "speed": "40 ft., fly 20 ft.",
                "attacks": [attack],
            }
        )

        instance = self.monster_manager_service.create(sheet, self.location_id)

        assert instance.template_id == sheet.index
        assert instance.current_location_id == self.location_id
        assert instance.state.hit_dice.total == 3
        assert instance.state.hit_dice.type == "d10"
        assert instance.state.initiative_bonus == (sheet.abilities.DEX - 10) // 2
        assert instance.state.speed == 40
        assert instance.state.attacks and instance.state.attacks[0] == attack
        assert instance.state.attacks[0] is not attack

    def test_create_monster_instance_handles_invalid_inputs(self) -> None:
        sheet = self.base_sheet.model_copy(deep=True)
        object.__setattr__(sheet, "hit_dice", "invalid")
        object.__setattr__(sheet, "speed", BadSpeed())
        object.__setattr__(sheet, "attacks", ["not-an-attack"])

        instance = self.monster_manager_service.create(sheet, "wilds")

        assert instance.state.hit_dice.total == 0
        assert instance.state.hit_dice.type == "d6"
        assert instance.state.speed == 30
        assert instance.state.attacks == []
