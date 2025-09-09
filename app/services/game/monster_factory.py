"""MonsterFactory: builds MonsterInstance from a MonsterSheet template.

Keeps GameService lean and adheres to SRP/DI by centralizing mapping logic.
"""

from __future__ import annotations

from app.interfaces.services.game import IMonsterFactory
from app.models.attributes import AttackAction, SavingThrows
from app.models.character import Currency
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.instances.monster_instance import MonsterInstance
from app.models.monster import MonsterSheet
from app.utils.id_generator import generate_instance_id


class MonsterFactory(IMonsterFactory):
    """Default implementation for creating MonsterInstance objects."""

    def create(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        # Parse hit dice like "2d8+2" best-effort for totals/type
        hd_text = sheet.hit_dice or ""
        hd_total = 0
        hd_type = "d6"
        try:
            if "d" in hd_text:
                parts = hd_text.lower().split("d", 1)
                hd_total = int(parts[0]) if parts[0].isdigit() else 0
                tail = parts[1]
                die_digits = ""
                for ch in tail:
                    if ch.isdigit():
                        die_digits += ch
                    else:
                        break
                if die_digits:
                    hd_type = f"d{die_digits}"
        except Exception:
            hd_total = 0
            hd_type = "d6"

        # Initiative modifier based on DEX
        dex_mod = (sheet.abilities.DEX - 10) // 2

        # Try to parse a primary speed from string
        speed_val = 30
        try:
            digits = ""
            for ch in str(sheet.speed):
                if ch.isdigit():
                    digits += ch
                elif digits:
                    break
            if digits:
                speed_val = int(digits)
        except Exception:
            speed_val = 30

        # Copy attacks
        attacks: list[AttackAction] = []
        try:
            for atk in sheet.attacks:
                attacks.append(atk.model_copy(deep=True))
        except Exception:
            attacks = []

        return MonsterInstance(
            instance_id=generate_instance_id(sheet.name),
            template_id=sheet.index,
            sheet=sheet,
            state=EntityState(
                abilities=sheet.abilities,
                level=1,
                experience_points=0,
                hit_points=HitPoints(current=sheet.hit_points.current, maximum=sheet.hit_points.maximum, temporary=0),
                hit_dice=HitDice(total=hd_total, current=hd_total, type=hd_type),
                armor_class=sheet.armor_class,
                initiative_bonus=dex_mod,
                speed=speed_val,
                saving_throws=SavingThrows(),
                skills=[s.model_copy(deep=True) for s in sheet.skills] if sheet.skills else [],
                attacks=attacks,
                conditions=[],
                exhaustion_level=0,
                inspiration=False,
                inventory=[],
                currency=Currency(),
                spellcasting=None,
            ),
            current_location_id=current_location_id,
        )
