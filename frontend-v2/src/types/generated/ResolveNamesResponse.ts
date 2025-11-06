/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

/**
 * Response model for resolved catalog names.
 */
export interface ResolveNamesResponse {
  items?: Items;
  spells?: Spells;
  monsters?: Monsters;
  classes?: Classes;
  races?: Races;
  alignments?: Alignments;
  backgrounds?: Backgrounds;
  feats?: Feats;
  features?: Features;
  traits?: Traits;
  skills?: Skills;
  conditions?: Conditions;
  languages?: Languages;
  damage_types?: DamageTypes;
  magic_schools?: MagicSchools;
  subclasses?: Subclasses;
  subraces?: Subraces;
  weapon_properties?: WeaponProperties;
}
/**
 * Item index to name mapping
 */
export interface Items {
  [k: string]: string;
}
/**
 * Spell index to name mapping
 */
export interface Spells {
  [k: string]: string;
}
/**
 * Monster index to name mapping
 */
export interface Monsters {
  [k: string]: string;
}
/**
 * Class index to name mapping
 */
export interface Classes {
  [k: string]: string;
}
/**
 * Race index to name mapping
 */
export interface Races {
  [k: string]: string;
}
/**
 * Alignment Index to name mapping
 */
export interface Alignments {
  [k: string]: string;
}
/**
 * Background index to name mapping
 */
export interface Backgrounds {
  [k: string]: string;
}
/**
 * Feat index to name mapping
 */
export interface Feats {
  [k: string]: string;
}
/**
 * Feature index to name mapping
 */
export interface Features {
  [k: string]: string;
}
/**
 * Trait index to name mapping
 */
export interface Traits {
  [k: string]: string;
}
/**
 * Skill index to name mapping
 */
export interface Skills {
  [k: string]: string;
}
/**
 * Condition index to name mapping
 */
export interface Conditions {
  [k: string]: string;
}
/**
 * Language index to name mapping
 */
export interface Languages {
  [k: string]: string;
}
/**
 * Damage Types index to name mapping
 */
export interface DamageTypes {
  [k: string]: string;
}
/**
 * Magic Schools index to name mapping
 */
export interface MagicSchools {
  [k: string]: string;
}
/**
 * Subclasses index to name mapping
 */
export interface Subclasses {
  [k: string]: string;
}
/**
 * Subraces index to name mapping
 */
export interface Subraces {
  [k: string]: string;
}
/**
 * Weapon Properties index to name mapping
 */
export interface WeaponProperties {
  [k: string]: string;
}
