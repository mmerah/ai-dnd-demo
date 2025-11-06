/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Description = string;
export type ClassIndex = string;
export type SubclassIndex = string | null;
export type Level = number;
export type ClassIndex1 = string;
export type SubclassIndex1 = string | null;
export type ContentPack = string;

export interface FeatureDefinition {
  index: Index;
  name: Name;
  description: Description;
  class_index: ClassIndex;
  subclass_index?: SubclassIndex;
  level: Level;
  granted_by: FeatureGrantedBy;
  content_pack: ContentPack;
}
export interface FeatureGrantedBy {
  class_index: ClassIndex1;
  subclass_index?: SubclassIndex1;
}
