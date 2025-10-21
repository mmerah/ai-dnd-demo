"""Unit tests for CharacterComputeService computation functions."""

from unittest.mock import Mock

from app.models.attributes import Abilities, AbilityModifiers
from app.services.character.compute_service import CharacterComputeService


class TestCharacterComputeService:
    """Test cases for CharacterComputeService computation methods."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository_provider = Mock()
        self.service = CharacterComputeService(self.repository_provider)

    def test_compute_ability_modifiers(self) -> None:
        """Test ability modifier calculations."""
        abilities = Abilities(STR=10, DEX=14, CON=16, INT=8, WIS=13, CHA=11)
        modifiers = self.service.compute_ability_modifiers(abilities)
        # (10-10)//2 = 0
        assert modifiers.STR == 0
        # (14-10)//2 = 2
        assert modifiers.DEX == 2
        # (16-10)//2 = 3
        assert modifiers.CON == 3
        # (8-10)//2 = -1
        assert modifiers.INT == -1
        # (13-10)//2 = 1
        assert modifiers.WIS == 1
        # (11-10)//2 = 0
        assert modifiers.CHA == 0

    def test_compute_ability_modifiers_edge_cases(self) -> None:
        """Test ability modifier calculations with edge values."""
        # Minimum abilities
        abilities_min = Abilities(STR=1, DEX=1, CON=1, INT=1, WIS=1, CHA=1)
        modifiers_min = self.service.compute_ability_modifiers(abilities_min)
        assert all(
            mod == -5
            for mod in [
                modifiers_min.STR,
                modifiers_min.DEX,
                modifiers_min.CON,
                modifiers_min.INT,
                modifiers_min.WIS,
                modifiers_min.CHA,
            ]
        )

        # Maximum abilities
        abilities_max = Abilities(STR=20, DEX=20, CON=20, INT=20, WIS=20, CHA=20)
        modifiers_max = self.service.compute_ability_modifiers(abilities_max)
        assert all(
            mod == 5
            for mod in [
                modifiers_max.STR,
                modifiers_max.DEX,
                modifiers_max.CON,
                modifiers_max.INT,
                modifiers_max.WIS,
                modifiers_max.CHA,
            ]
        )

        # Odd values
        abilities_odd = Abilities(STR=15, DEX=17, CON=19, INT=9, WIS=11, CHA=13)
        modifiers_odd = self.service.compute_ability_modifiers(abilities_odd)
        # (15-10)//2 = 2
        assert modifiers_odd.STR == 2
        # (17-10)//2 = 3
        assert modifiers_odd.DEX == 3
        # (19-10)//2 = 4
        assert modifiers_odd.CON == 4
        # (9-10)//2 = -1
        assert modifiers_odd.INT == -1
        # (11-10)//2 = 0
        assert modifiers_odd.WIS == 0
        # (13-10)//2 = 1
        assert modifiers_odd.CHA == 1

    def test_compute_proficiency_bonus(self) -> None:
        """Test proficiency bonus calculation by level."""
        # Level 1-4: +2
        assert self.service.compute_proficiency_bonus(1) == 2
        assert self.service.compute_proficiency_bonus(2) == 2
        assert self.service.compute_proficiency_bonus(3) == 2
        assert self.service.compute_proficiency_bonus(4) == 2

        # Level 5-8: +3
        assert self.service.compute_proficiency_bonus(5) == 3
        assert self.service.compute_proficiency_bonus(6) == 3
        assert self.service.compute_proficiency_bonus(7) == 3
        assert self.service.compute_proficiency_bonus(8) == 3

        # Level 9-12: +4
        assert self.service.compute_proficiency_bonus(9) == 4
        assert self.service.compute_proficiency_bonus(10) == 4
        assert self.service.compute_proficiency_bonus(11) == 4
        assert self.service.compute_proficiency_bonus(12) == 4

        # Level 13-16: +5
        assert self.service.compute_proficiency_bonus(13) == 5
        assert self.service.compute_proficiency_bonus(14) == 5
        assert self.service.compute_proficiency_bonus(15) == 5
        assert self.service.compute_proficiency_bonus(16) == 5

        # Level 17-20: +6
        assert self.service.compute_proficiency_bonus(17) == 6
        assert self.service.compute_proficiency_bonus(18) == 6
        assert self.service.compute_proficiency_bonus(19) == 6
        assert self.service.compute_proficiency_bonus(20) == 6

    def test_compute_initiative_bonus(self) -> None:
        """Test initiative bonus calculation."""
        modifiers = AbilityModifiers(STR=1, DEX=3, CON=2, INT=0, WIS=-1, CHA=1)
        initiative = self.service.compute_initiative_bonus(modifiers)
        # Initiative is based on DEX modifier
        assert initiative == 3

    def test_compute_initiative_bonus_negative(self) -> None:
        """Test initiative bonus with negative DEX modifier."""
        modifiers = AbilityModifiers(STR=2, DEX=-2, CON=1, INT=0, WIS=1, CHA=0)
        initiative = self.service.compute_initiative_bonus(modifiers)
        assert initiative == -2

    def test_compute_hit_points_and_dice_level_1(self) -> None:
        """Test HP and hit dice calculation for level 1."""
        game_state = Mock()

        # Mock class repository
        class_repo = Mock()
        class_def = Mock()
        class_def.hit_die = 10
        class_repo.get.return_value = class_def
        self.repository_provider.get_class_repository_for.return_value = class_repo

        # CON modifier of 2
        max_hp, hit_dice_total, hit_die_type = self.service.compute_hit_points_and_dice(game_state, "fighter", 1, 2)
        # 10 (hit die) + 2 (CON mod)
        assert max_hp == 12
        assert hit_dice_total == 1
        assert hit_die_type == "d10"

    def test_compute_hit_points_and_dice_higher_levels(self) -> None:
        """Test HP and hit dice calculation for higher levels."""
        game_state = Mock()

        # Mock class repository
        class_repo = Mock()
        class_def = Mock()
        class_def.hit_die = 8
        class_repo.get.return_value = class_def
        self.repository_provider.get_class_repository_for.return_value = class_repo

        # Level 5 with CON modifier 3
        max_hp, hit_dice_total, hit_die_type = self.service.compute_hit_points_and_dice(game_state, "ranger", 5, 3)

        # Level 1: 8 + 3 = 11
        # Levels 2-5: 4 levels * (5 + 3) = 32  (average of d8 is 4.5, rounds to 5)
        # Total: 11 + 32 = 43
        assert max_hp == 11 + (4 * 8)
        assert hit_dice_total == 5
        assert hit_die_type == "d8"

    def test_compute_hit_points_and_dice_negative_con(self) -> None:
        """Test HP calculation with negative CON modifier."""
        game_state = Mock()

        # Mock class repository
        class_repo = Mock()
        class_def = Mock()
        class_def.hit_die = 6
        class_repo.get.return_value = class_def
        self.repository_provider.get_class_repository_for.return_value = class_repo

        # Level 3 with CON modifier -2
        max_hp, hit_dice_total, hit_die_type = self.service.compute_hit_points_and_dice(game_state, "wizard", 3, -2)

        # Level 1: max(1, 6 - 2) = 4
        # Levels 2-3: 2 levels * max(1, 4 - 2) = 2 * 2 = 4
        # Total: 4 + 4 = 8
        assert max_hp == 4 + 4
        assert hit_dice_total == 3
        assert hit_die_type == "d6"

    def test_format_damage_with_mod(self) -> None:
        """Test damage string formatting with modifiers."""
        # Positive modifier
        assert self.service._format_damage_with_mod("1d8", 3) == "1d8+3"

        # Negative modifier
        assert self.service._format_damage_with_mod("2d6", -2) == "2d6-2"

        # Zero modifier
        assert self.service._format_damage_with_mod("1d10", 0) == "1d10"

    def test_text_index_from_name(self) -> None:
        """Test name to index conversion."""
        assert self.service._text_index_from_name("Long Sword") == "long-sword"
        assert self.service._text_index_from_name("Leather Armor, Studded") == "leather-armor-studded"
        assert self.service._text_index_from_name("SHIELD") == "shield"
        assert self.service._text_index_from_name("Two-Handed Sword") == "two-handed-sword"

    def test_get_background_skill_proficiencies(self) -> None:
        """Test extraction of background proficiencies."""
        game_state = Mock()
        background_repo = Mock()
        background_def = Mock()
        background_def.skill_proficiencies = ["insight", "religion"]
        background_repo.get.return_value = background_def
        self.repository_provider.get_background_repository_for.return_value = background_repo

        skills = self.service.get_background_skill_proficiencies(game_state, "acolyte")

        assert skills == ["insight", "religion"]
