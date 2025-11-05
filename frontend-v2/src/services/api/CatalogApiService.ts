/**
 * Catalog API Service
 *
 * Handles all catalog-related API calls for browsing reference data.
 */

import { ApiService } from './ApiService.js';

export interface Character {
  id: string;
  name: string;
  race: string;
  class: string;
  level: number;
  background?: string;
  // Add more fields as needed
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  difficulty?: string;
  // Add more fields as needed
}

export interface CharactersResponse {
  characters: Character[];
}

export interface ScenariosResponse {
  scenarios: Scenario[];
}

export interface Spell {
  id: string;
  name: string;
  level: number;
  school: string;
  casting_time: string;
  range: string;
  components: string;
  duration: string;
  description: string;
  content_pack?: string;
}

export interface Item {
  id: string;
  name: string;
  type: string;
  rarity?: string;
  weight?: number;
  cost?: string;
  description: string;
  content_pack?: string;
}

export interface Monster {
  id: string;
  name: string;
  type: string;
  size: string;
  challenge_rating: string;
  armor_class: number;
  hit_points: number;
  description: string;
  content_pack?: string;
}

export interface Race {
  id: string;
  name: string;
  description: string;
  speed: number;
  size: string;
  content_pack?: string;
}

export interface Class {
  id: string;
  name: string;
  description: string;
  hit_die: number;
  primary_ability: string;
  content_pack?: string;
}

export interface Background {
  id: string;
  name: string;
  description: string;
  skill_proficiencies: string[];
  content_pack?: string;
}

export interface Feat {
  id: string;
  name: string;
  description: string;
  prerequisite?: string;
  content_pack?: string;
}

export interface ContentPack {
  id: string;
  name: string;
  description: string;
  version: string;
}

export interface SpellsResponse {
  spells: Spell[];
}

export interface ItemsResponse {
  items: Item[];
}

export interface MonstersResponse {
  monsters: Monster[];
}

export interface RacesResponse {
  races: Race[];
}

export interface ClassesResponse {
  classes: Class[];
}

export interface BackgroundsResponse {
  backgrounds: Background[];
}

export interface FeatsResponse {
  feats: Feat[];
}

export interface ContentPacksResponse {
  content_packs: ContentPack[];
}

/**
 * Service for catalog-related API operations
 */
export class CatalogApiService {
  constructor(private readonly api: ApiService) {}

  /**
   * Fetch all available characters
   */
  async getCharacters(): Promise<CharactersResponse> {
    return this.api.get<CharactersResponse>('/api/characters');
  }

  /**
   * Fetch all available scenarios
   */
  async getScenarios(): Promise<ScenariosResponse> {
    return this.api.get<ScenariosResponse>('/api/scenarios');
  }

  /**
   * Fetch spells catalog
   */
  async getSpells(): Promise<SpellsResponse> {
    return this.api.get<SpellsResponse>('/api/catalogs/spells');
  }

  /**
   * Fetch items catalog
   */
  async getItems(): Promise<ItemsResponse> {
    return this.api.get<ItemsResponse>('/api/catalogs/items');
  }

  /**
   * Fetch monsters catalog
   */
  async getMonsters(): Promise<MonstersResponse> {
    return this.api.get<MonstersResponse>('/api/catalogs/monsters');
  }

  /**
   * Fetch races catalog
   */
  async getRaces(): Promise<RacesResponse> {
    return this.api.get<RacesResponse>('/api/catalogs/races');
  }

  /**
   * Fetch classes catalog
   */
  async getClasses(): Promise<ClassesResponse> {
    return this.api.get<ClassesResponse>('/api/catalogs/classes');
  }

  /**
   * Fetch backgrounds catalog
   */
  async getBackgrounds(): Promise<BackgroundsResponse> {
    return this.api.get<BackgroundsResponse>('/api/catalogs/backgrounds');
  }

  /**
   * Fetch feats catalog
   */
  async getFeats(): Promise<FeatsResponse> {
    return this.api.get<FeatsResponse>('/api/catalogs/feats');
  }

  /**
   * Fetch content packs
   */
  async getContentPacks(): Promise<ContentPacksResponse> {
    return this.api.get<ContentPacksResponse>('/api/content-packs');
  }
}
