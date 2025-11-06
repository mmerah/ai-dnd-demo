/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Id = string;
export type DisplayName = string;
export type Role = string;
export type Description = string;
export type InitialLocationId = string;
/**
 * Classification for NPC routing importance.
 */
export type NPCImportance = 'major' | 'minor';
export type InitialDialogueHints = string[];
export type InitialAttitude = string | null;
export type InitialNotes = string[];
export type Id1 = string;
export type Name = string;
export type Race = string;
export type ClassIndex = string;
export type Subclass = string | null;
export type Subrace = string | null;
export type ContentPacks = string[];
export type StartingLevel = number;
export type Background = string;
export type Alignment = string;
export type StartingExperiencePoints = number;
export type Str = number;
export type Dex = number;
export type Con = number;
export type Int = number;
export type Wis = number;
export type Cha = number;
export type Name1 = string;
export type Description1 = string;
export type CustomFeatures = CustomFeature[];
export type FeatureIndexes = string[];
export type TraitIndexes = string[];
export type FeatIndexes = string[];
export type StartingSkillIndexes = string[];
/**
 * Spellcasting ability scores.
 */
export type SpellcastingAbility = 'Intelligence' | 'Wisdom' | 'Charisma' | 'INT' | 'WIS' | 'CHA';
export type SpellSaveDc = number | null;
export type SpellAttackBonus = number | null;
export type SpellsKnown = string[];
export type Level = number;
export type Total = number;
export type Current = number;
export type SpellsPrepared = string[];
export type RitualSpells = string[];
export type Index = string;
export type Name2 = string | null;
/**
 * Types of items in the game.
 */
export type ItemType = 'Weapon' | 'Armor' | 'Potion' | 'Ammunition' | 'Adventuring Gear' | 'Equipment Pack';
export type Quantity = number;
export type StartingInventory = InventoryItem[];
export type Copper = number;
export type Silver = number;
export type Electrum = number;
export type Gold = number;
export type Platinum = number;
export type Traits = string[];
export type Ideals = string[];
export type Bonds = string[];
export type Flaws = string[];
export type Backstory = string;
export type Languages = string[];

/**
 * NPC wrapper embedding a full CharacterSheet plus scenario metadata (template-only).
 */
export interface NPCSheet {
  id: Id;
  display_name: DisplayName;
  role: Role;
  description: Description;
  initial_location_id: InitialLocationId;
  importance?: NPCImportance;
  initial_dialogue_hints?: InitialDialogueHints;
  initial_attitude?: InitialAttitude;
  initial_notes?: InitialNotes;
  character: CharacterSheet;
}
/**
 * Character template for pre-game selection.
 *
 * Contains base identity and choices only. All dynamic/derived fields
 * live on CharacterInstance at runtime.
 */
export interface CharacterSheet {
  id: Id1;
  name: Name;
  race: Race;
  class_index: ClassIndex;
  subclass?: Subclass;
  subrace?: Subrace;
  content_packs?: ContentPacks;
  starting_level?: StartingLevel;
  background: Background;
  alignment: Alignment;
  starting_experience_points?: StartingExperiencePoints;
  starting_abilities: Abilities;
  custom_features?: CustomFeatures;
  feature_indexes?: FeatureIndexes;
  trait_indexes?: TraitIndexes;
  feat_indexes?: FeatIndexes;
  starting_skill_indexes?: StartingSkillIndexes;
  starting_spellcasting?: Spellcasting | null;
  starting_inventory?: StartingInventory;
  starting_currency: Currency;
  personality: Personality;
  backstory: Backstory;
  languages: Languages;
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
/**
 * Character feature or trait.
 */
export interface CustomFeature {
  name: Name1;
  description: Description1;
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
  level: Level;
  total: Total;
  current: Current;
}
/**
 * Item instance in inventory.
 */
export interface InventoryItem {
  index: Index;
  name?: Name2;
  item_type?: ItemType | null;
  quantity?: Quantity;
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
 * Character personality traits for roleplay.
 */
export interface Personality {
  traits?: Traits;
  ideals?: Ideals;
  bonds?: Bonds;
  flaws?: Flaws;
}
