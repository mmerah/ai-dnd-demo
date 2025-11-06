/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type InstanceId = string;
export type CreatedAt = string;
export type UpdatedAt = string;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type Level = number;
export type ExperiencePoints = number;
export type Current = number;
export type Maximum = number;
export type Temporary = number;
export type Total = number;
export type Current1 = number;
export type Type = string;
export type ArmorClass = number;
export type InitiativeBonus = number;
export type Speed = number;
export type Str1 = number;
export type Dex1 = number;
export type Con1 = number;
export type Int1 = number;
export type Wis1 = number;
export type Cha1 = number;
export type Index = string;
export type Value = number;
export type Skills = SkillValue[];
export type Name = string;
export type AttackRollBonus = number;
export type Damage = string;
export type DamageType = string;
export type Range = string;
export type Properties = string[];
export type Type1 = string;
export type Reach = string;
export type Special = string;
export type Attacks = AttackAction[];
export type Conditions = string[];
export type ExhaustionLevel = number;
export type Inspiration = boolean;
export type Index1 = string;
export type Name1 = string | null;
/**
 * Types of items in the game.
 */
export type ItemType = 'Weapon' | 'Armor' | 'Potion' | 'Ammunition' | 'Adventuring Gear' | 'Equipment Pack';
export type Quantity = number;
export type Inventory = InventoryItem[];
export type Head = string | null;
export type Neck = string | null;
export type Chest = string | null;
export type Hands = string | null;
export type Feet = string | null;
export type Waist = string | null;
export type MainHand = string | null;
export type OffHand = string | null;
export type Ring1 = string | null;
export type Ring2 = string | null;
export type Back = string | null;
export type Ammunition = string | null;
export type Copper = number;
export type Silver = number;
export type Electrum = number;
export type Gold = number;
export type Platinum = number;
/**
 * Spellcasting ability scores.
 */
export type SpellcastingAbility = 'Intelligence' | 'Wisdom' | 'Charisma' | 'INT' | 'WIS' | 'CHA';
export type SpellSaveDc = number | null;
export type SpellAttackBonus = number | null;
export type SpellsKnown = string[];
export type Level1 = number;
export type Total1 = number;
export type Current2 = number;
export type SpellsPrepared = string[];
export type RitualSpells = string[];
export type TemplateId = string;
export type Index2 = string;
export type Name2 = string;
export type Type2 = string;
export type Size = string;
export type Alignment = string;
export type ArmorClass1 = number;
export type HitDice1 = string;
export type Speed1 = string;
export type ChallengeRating = number;
export type Skills1 = SkillValue[];
export type Senses = string;
export type Languages = string[];
export type Attacks1 = AttackAction[];
export type Name3 = string;
export type Description = string;
export type SpecialAbilities = MonsterSpecialAbility[];
export type DamageVulnerabilities = string[];
export type DamageResistances = string[];
export type DamageImmunities = string[];
export type ConditionImmunities = string[];
export type ContentPack = string;
export type CurrentLocationId = string;

/**
 * Dynamic monster state bound to a MonsterSheet template.
 */
export interface MonsterInstance {
  instance_id: InstanceId;
  created_at?: CreatedAt;
  updated_at?: UpdatedAt;
  state: EntityState;
  template_id: TemplateId;
  sheet: MonsterSheet;
  current_location_id: CurrentLocationId;
}
export interface EntityState {
  abilities: Abilities;
  level?: Level;
  experience_points?: ExperiencePoints;
  hit_points: HitPoints;
  hit_dice: HitDice;
  armor_class?: ArmorClass;
  initiative_bonus?: InitiativeBonus;
  speed?: Speed;
  saving_throws?: SavingThrows;
  skills?: Skills;
  attacks?: Attacks;
  conditions?: Conditions;
  exhaustion_level?: ExhaustionLevel;
  inspiration?: Inspiration;
  inventory?: Inventory;
  equipment_slots?: EquipmentSlots;
  currency: Currency;
  spellcasting?: Spellcasting | null;
}
/**
 * Character ability scores.
 */
export interface Abilities {
  STR: Str;
  DEX: Dex;
  CON: Con;
  INT: Int;
  WIS: Wis;
  CHA: Cha;
}
export interface HitPoints {
  current: Current;
  maximum: Maximum;
  temporary?: Temporary;
}
export interface HitDice {
  total: Total;
  current: Current1;
  type: Type;
}
/**
 * Saving throw modifiers by ability.
 */
export interface SavingThrows {
  STR?: Str1;
  DEX?: Dex1;
  CON?: Con1;
  INT?: Int1;
  WIS?: Wis1;
  CHA?: Cha1;
}
/**
 * Runtime skill value bound to a skill index.
 */
export interface SkillValue {
  index: Index;
  value: Value;
}
export interface AttackAction {
  name: Name;
  attack_roll_bonus: AttackRollBonus;
  damage: Damage;
  damage_type: DamageType;
  range?: Range;
  properties?: Properties;
  type?: Type1;
  reach?: Reach;
  special?: Special;
}
/**
 * Item instance in inventory.
 */
export interface InventoryItem {
  index: Index1;
  name?: Name1;
  item_type?: ItemType | null;
  quantity?: Quantity;
}
/**
 * Character equipment slots following D&D 5e conventions.
 */
export interface EquipmentSlots {
  head?: Head;
  neck?: Neck;
  chest?: Chest;
  hands?: Hands;
  feet?: Feet;
  waist?: Waist;
  main_hand?: MainHand;
  off_hand?: OffHand;
  ring_1?: Ring1;
  ring_2?: Ring2;
  back?: Back;
  ammunition?: Ammunition;
}
/**
 * Character wealth tracking.
 */
export interface Currency {
  copper?: Copper;
  silver?: Silver;
  electrum?: Electrum;
  gold?: Gold;
  platinum?: Platinum;
}
/**
 * Character spellcasting information.
 */
export interface Spellcasting {
  ability: SpellcastingAbility;
  spell_save_dc?: SpellSaveDc;
  spell_attack_bonus?: SpellAttackBonus;
  spells_known: SpellsKnown;
  spell_slots: SpellSlots;
  spells_prepared?: SpellsPrepared;
  ritual_spells?: RitualSpells;
}
export interface SpellSlots {
  [k: string]: SpellSlot;
}
/**
 * Spell slot tracking for a spell level.
 */
export interface SpellSlot {
  level: Level1;
  total: Total1;
  current: Current2;
}
/**
 * Minimal monster stat block (template).
 */
export interface MonsterSheet {
  index: Index2;
  name: Name2;
  type: Type2;
  size: Size;
  alignment: Alignment;
  armor_class: ArmorClass1;
  hit_points: HitPoints;
  hit_dice: HitDice1;
  speed: Speed1;
  challenge_rating: ChallengeRating;
  abilities: Abilities;
  skills?: Skills1;
  senses: Senses;
  languages?: Languages;
  attacks: Attacks1;
  special_abilities?: SpecialAbilities;
  damage_vulnerabilities?: DamageVulnerabilities;
  damage_resistances?: DamageResistances;
  damage_immunities?: DamageImmunities;
  condition_immunities?: ConditionImmunities;
  content_pack: ContentPack;
}
/**
 * Special ability or trait for a monster.
 */
export interface MonsterSpecialAbility {
  name: Name3;
  description: Description;
}
