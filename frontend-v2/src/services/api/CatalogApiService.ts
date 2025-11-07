/**
 * Catalog API Service
 *
 * Handles all catalog-related API calls for browsing reference data.
 * All types are auto-generated from backend Pydantic models.
 */

import { ApiService } from './ApiService.js';
import type { CharacterSheet } from '../../types/generated/CharacterSheet.js';
import type { ScenarioSheet } from '../../types/generated/ScenarioSheet.js';
import type { SpellDefinition } from '../../types/generated/SpellDefinition.js';
import type { ItemDefinition } from '../../types/generated/ItemDefinition.js';
import type { MonsterSheet } from '../../types/generated/MonsterSheet.js';
import type { RaceDefinition } from '../../types/generated/RaceDefinition.js';
import type { SubraceDefinition } from '../../types/generated/SubraceDefinition.js';
import type { ClassDefinition } from '../../types/generated/ClassDefinition.js';
import type { SubclassDefinition } from '../../types/generated/SubclassDefinition.js';
import type { BackgroundDefinition } from '../../types/generated/BackgroundDefinition.js';
import type { FeatDefinition } from '../../types/generated/FeatDefinition.js';
import type { FeatureDefinition } from '../../types/generated/FeatureDefinition.js';
import type { TraitDefinition } from '../../types/generated/TraitDefinition.js';
import type { Skill } from '../../types/generated/Skill.js';
import type { Condition } from '../../types/generated/Condition.js';
import type { Language } from '../../types/generated/Language.js';
import type { DamageType } from '../../types/generated/DamageType.js';
import type { MagicSchool } from '../../types/generated/MagicSchool.js';
import type { WeaponProperty } from '../../types/generated/WeaponProperty.js';
import type { Alignment } from '../../types/generated/Alignment.js';
import type { ResolveNamesRequest } from '../../types/generated/ResolveNamesRequest.js';
import type { ResolveNamesResponse } from '../../types/generated/ResolveNamesResponse.js';
import type { ContentPackListResponse } from '../../types/generated/ContentPackListResponse.js';

/**
 * Service for catalog-related API operations
 */
export class CatalogApiService {
  constructor(private readonly api: ApiService) {}

  /**
   * Fetch all available characters
   * Backend returns list[CharacterSheet] directly
   */
  async getCharacters(): Promise<CharacterSheet[]> {
    return this.api.get<CharacterSheet[]>('/api/characters');
  }

  /**
   * Fetch all available scenarios
   * Backend returns list[ScenarioSheet] directly
   */
  async getScenarios(): Promise<ScenarioSheet[]> {
    return this.api.get<ScenarioSheet[]>('/api/scenarios');
  }

  /**
   * Fetch spells catalog
   */
  async getSpells(): Promise<SpellDefinition[]> {
    return this.api.get<SpellDefinition[]>('/api/catalogs/spells');
  }

  /**
   * Fetch items catalog
   */
  async getItems(): Promise<ItemDefinition[]> {
    return this.api.get<ItemDefinition[]>('/api/catalogs/items');
  }

  /**
   * Fetch monsters catalog
   */
  async getMonsters(): Promise<MonsterSheet[]> {
    return this.api.get<MonsterSheet[]>('/api/catalogs/monsters');
  }

  /**
   * Fetch races catalog
   */
  async getRaces(): Promise<RaceDefinition[]> {
    return this.api.get<RaceDefinition[]>('/api/catalogs/races');
  }

  /**
   * Fetch subraces catalog
   */
  async getSubraces(): Promise<SubraceDefinition[]> {
    return this.api.get<SubraceDefinition[]>('/api/catalogs/race_subraces');
  }

  /**
   * Fetch classes catalog
   */
  async getClasses(): Promise<ClassDefinition[]> {
    return this.api.get<ClassDefinition[]>('/api/catalogs/classes');
  }

  /**
   * Fetch subclasses catalog
   */
  async getSubclasses(): Promise<SubclassDefinition[]> {
    return this.api.get<SubclassDefinition[]>('/api/catalogs/subclasses');
  }

  /**
   * Fetch backgrounds catalog
   */
  async getBackgrounds(): Promise<BackgroundDefinition[]> {
    return this.api.get<BackgroundDefinition[]>('/api/catalogs/backgrounds');
  }

  /**
   * Fetch feats catalog
   */
  async getFeats(): Promise<FeatDefinition[]> {
    return this.api.get<FeatDefinition[]>('/api/catalogs/feats');
  }

  /**
   * Fetch features catalog
   */
  async getFeatures(): Promise<FeatureDefinition[]> {
    return this.api.get<FeatureDefinition[]>('/api/catalogs/features');
  }

  /**
   * Fetch traits catalog
   */
  async getTraits(): Promise<TraitDefinition[]> {
    return this.api.get<TraitDefinition[]>('/api/catalogs/traits');
  }

  /**
   * Fetch skills catalog
   */
  async getSkills(): Promise<Skill[]> {
    return this.api.get<Skill[]>('/api/catalogs/skills');
  }

  /**
   * Fetch conditions catalog
   */
  async getConditions(): Promise<Condition[]> {
    return this.api.get<Condition[]>('/api/catalogs/conditions');
  }

  /**
   * Fetch languages catalog
   */
  async getLanguages(): Promise<Language[]> {
    return this.api.get<Language[]>('/api/catalogs/languages');
  }

  /**
   * Fetch damage types catalog
   */
  async getDamageTypes(): Promise<DamageType[]> {
    return this.api.get<DamageType[]>('/api/catalogs/damage_types');
  }

  /**
   * Fetch magic schools catalog
   */
  async getMagicSchools(): Promise<MagicSchool[]> {
    return this.api.get<MagicSchool[]>('/api/catalogs/magic_schools');
  }

  /**
   * Fetch weapon properties catalog
   */
  async getWeaponProperties(): Promise<WeaponProperty[]> {
    return this.api.get<WeaponProperty[]>('/api/catalogs/weapon_properties');
  }

  /**
   * Fetch alignments catalog
   */
  async getAlignments(): Promise<Alignment[]> {
    return this.api.get<Alignment[]>('/api/catalogs/alignments');
  }

  /**
   * Resolve display names for catalog indexes
   * Useful for converting indexes to human-readable names
   */
  async resolveNames(request: ResolveNamesRequest): Promise<ResolveNamesResponse> {
    return this.api.post<ResolveNamesResponse, ResolveNamesRequest>(
      '/api/catalogs/resolve-names',
      request
    );
  }

  /**
   * Fetch content packs list
   * Returns list of available content packs with metadata
   */
  async getContentPacks(): Promise<ContentPackListResponse> {
    return this.api.get<ContentPackListResponse>('/api/content-packs');
  }
}
