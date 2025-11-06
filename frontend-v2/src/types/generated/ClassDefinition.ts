/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type HitDie = number;
export type SavingThrows = string[];
export type Proficiencies = string[];
export type SpellcastingAbility = string | null;
export type Description = string;
export type ProficiencyChoices = ClassProficiencyChoice[] | null;
export type Choose = number;
export type FromOptions = string[];
export type StartingEquipment = ClassStartingEquipment[] | null;
export type Index1 = string;
export type Quantity = number;
export type StartingEquipmentOptionsDesc = string[] | null;
export type Subclasses = string[] | null;
export type Ability = string;
export type MinimumScore = number;
export type Prerequisites = MultiClassingRequirement[];
export type Proficiencies1 = string[];
export type ProficiencyChoices1 = ClassProficiencyChoice[];
export type ContentPack = string;

export interface ClassDefinition {
  index: Index;
  name: Name;
  hit_die: HitDie;
  saving_throws: SavingThrows;
  proficiencies: Proficiencies;
  spellcasting_ability?: SpellcastingAbility;
  description: Description;
  proficiency_choices?: ProficiencyChoices;
  starting_equipment?: StartingEquipment;
  starting_equipment_options_desc?: StartingEquipmentOptionsDesc;
  subclasses?: Subclasses;
  multi_classing?: MultiClassingInfo | null;
  content_pack: ContentPack;
}
export interface ClassProficiencyChoice {
  choose: Choose;
  from_options?: FromOptions;
}
export interface ClassStartingEquipment {
  index: Index1;
  quantity: Quantity;
}
export interface MultiClassingInfo {
  prerequisites?: Prerequisites;
  proficiencies?: Proficiencies1;
  proficiency_choices?: ProficiencyChoices1;
}
export interface MultiClassingRequirement {
  ability: Ability;
  minimum_score: MinimumScore;
}
