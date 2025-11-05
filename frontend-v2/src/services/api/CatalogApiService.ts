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
  async getSpells(): Promise<unknown> {
    return this.api.get('/api/catalogs/spells');
  }

  /**
   * Fetch items catalog
   */
  async getItems(): Promise<unknown> {
    return this.api.get('/api/catalogs/items');
  }

  /**
   * Fetch monsters catalog
   */
  async getMonsters(): Promise<unknown> {
    return this.api.get('/api/catalogs/monsters');
  }

  /**
   * Fetch content packs
   */
  async getContentPacks(): Promise<unknown> {
    return this.api.get('/api/content-packs');
  }
}
