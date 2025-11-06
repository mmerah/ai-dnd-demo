/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Description = string;
export type Prerequisites = string | null;
export type ContentPack = string;

export interface FeatDefinition {
  index: Index;
  name: Name;
  description: Description;
  prerequisites?: Prerequisites;
  content_pack: ContentPack;
}
