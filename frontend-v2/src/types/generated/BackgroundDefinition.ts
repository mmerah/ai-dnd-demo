/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Description = string;
export type Name1 = string;
export type Description1 = string;
/**
 * Skill indexes granted by this background (e.g., ['insight', 'religion'])
 */
export type SkillProficiencies = string[];
/**
 * Tool proficiency indexes granted (e.g., ['thieves-tools'])
 */
export type ToolProficiencies = string[];
/**
 * Number of languages the character can choose
 */
export type LanguageCount = number;
/**
 * Summary of starting equipment provided
 */
export type StartingEquipmentDescription = string | null;
/**
 * 8 personality trait options (player chooses 2)
 */
export type PersonalityTraitOptions = string[];
export type Text = string;
export type Alignments = string[];
/**
 * 6 ideal options with alignment associations (player chooses 1)
 */
export type IdealOptions = BackgroundOption[];
/**
 * 6 bond options (player chooses 1)
 */
export type BondOptions = string[];
/**
 * 6 flaw options (player chooses 1)
 */
export type FlawOptions = string[];
export type ContentPack = string;

/**
 * D&D 5e character background definition.
 */
export interface BackgroundDefinition {
  index: Index;
  name: Name;
  description: Description;
  feature?: BackgroundFeature | null;
  skill_proficiencies?: SkillProficiencies;
  tool_proficiencies?: ToolProficiencies;
  language_count?: LanguageCount;
  starting_equipment_description?: StartingEquipmentDescription;
  personality_trait_options?: PersonalityTraitOptions;
  ideal_options?: IdealOptions;
  bond_options?: BondOptions;
  flaw_options?: FlawOptions;
  content_pack: ContentPack;
}
/**
 * Background-specific feature or ability.
 */
export interface BackgroundFeature {
  name: Name1;
  description: Description1;
}
/**
 * A personality option (ideal) with optional alignment associations.
 */
export interface BackgroundOption {
  text: Text;
  alignments?: Alignments;
}
