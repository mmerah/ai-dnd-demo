/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Id = string;
export type Name = string;
export type Version = string;
export type Author = string;
export type Description = string;
/**
 * Types of content packs.
 *
 * SRD: Base content in data/
 * Custom: User-generated in user-data/
 * Scenario: Scenario-specific in data/scenarios/<id>/...
 * Sandbox: AI-Generated content during a game
 */
export type ContentPackType = 'srd' | 'custom' | 'scenario' | 'sandbox';
export type Packs = ContentPackSummary[];
export type Total = number;

export interface ContentPackListResponse {
  packs: Packs;
  total: Total;
}
/**
 * Summary information for a content pack.
 */
export interface ContentPackSummary {
  id: Id;
  name: Name;
  version: Version;
  author: Author;
  description: Description;
  pack_type: ContentPackType;
}
