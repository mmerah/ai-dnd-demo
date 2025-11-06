/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Index = string;
export type Name = string;
export type Type = string | null;
export type Script = string | null;
export type Description = string | null;
export type ContentPack = string;

export interface Language {
  index: Index;
  name: Name;
  type?: Type;
  script?: Script;
  description?: Description;
  content_pack: ContentPack;
}
