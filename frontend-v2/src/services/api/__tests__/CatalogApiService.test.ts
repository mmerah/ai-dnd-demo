import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CatalogApiService } from '../CatalogApiService';
import { ApiService } from '../ApiService';

// Mock ApiService
vi.mock('../ApiService');

describe('CatalogApiService', () => {
  let catalogApiService: CatalogApiService;
  let mockApiService: ApiService;

  beforeEach(() => {
    mockApiService = {
      get: vi.fn(),
    } as unknown as ApiService;

    catalogApiService = new CatalogApiService(mockApiService);
  });

  describe('getCharacters', () => {
    it('should fetch characters list', async () => {
      const mockResponse = {
        characters: [
          {
            id: 'char-1',
            name: 'Aldric Swiftarrow',
            race: 'Elf',
            class: 'Ranger',
            level: 5,
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getCharacters();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/characters');
      expect(result).toEqual(mockResponse);
      expect(result.characters).toHaveLength(1);
    });

    it('should handle empty characters list', async () => {
      const mockResponse = { characters: [] };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getCharacters();

      expect(result.characters).toHaveLength(0);
    });
  });

  describe('getScenarios', () => {
    it('should fetch scenarios list', async () => {
      const mockResponse = {
        scenarios: [
          {
            id: 'scenario-1',
            name: 'The Lost Mine',
            description: 'A classic adventure',
            difficulty: 'medium',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getScenarios();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/scenarios');
      expect(result).toEqual(mockResponse);
      expect(result.scenarios).toHaveLength(1);
    });
  });

  describe('getSpells', () => {
    it('should fetch spells catalog', async () => {
      const mockResponse = {
        spells: [
          {
            id: 'spell-1',
            name: 'Fireball',
            level: 3,
            school: 'Evocation',
            casting_time: '1 action',
            range: '150 feet',
            components: 'V, S, M',
            duration: 'Instantaneous',
            description: 'A bright streak...',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getSpells();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/spells');
      expect(result).toEqual(mockResponse);
      expect(result.spells[0]?.level).toBe(3);
    });

    it('should handle spells with no content pack', async () => {
      const mockResponse = {
        spells: [
          {
            id: 'spell-1',
            name: 'Magic Missile',
            level: 1,
            school: 'Evocation',
            casting_time: '1 action',
            range: '120 feet',
            components: 'V, S',
            duration: 'Instantaneous',
            description: 'You create three...',
            // No content_pack field
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getSpells();

      expect(result.spells[0]?.content_pack).toBeUndefined();
    });
  });

  describe('getItems', () => {
    it('should fetch items catalog', async () => {
      const mockResponse = {
        items: [
          {
            id: 'item-1',
            name: 'Longsword',
            type: 'weapon',
            rarity: 'common',
            weight: 3,
            cost: '15 gp',
            description: 'A versatile blade',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getItems();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/items');
      expect(result).toEqual(mockResponse);
      expect(result.items[0].type).toBe('weapon');
    });
  });

  describe('getMonsters', () => {
    it('should fetch monsters catalog', async () => {
      const mockResponse = {
        monsters: [
          {
            id: 'monster-1',
            name: 'Goblin',
            type: 'humanoid',
            size: 'Small',
            challenge_rating: '1/4',
            armor_class: 15,
            hit_points: 7,
            description: 'Small, green humanoid',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getMonsters();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/monsters');
      expect(result).toEqual(mockResponse);
      expect(result.monsters[0].challenge_rating).toBe('1/4');
    });
  });

  describe('getRaces', () => {
    it('should fetch races catalog', async () => {
      const mockResponse = {
        races: [
          {
            id: 'race-1',
            name: 'Elf',
            description: 'Graceful and long-lived',
            speed: 30,
            size: 'Medium',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getRaces();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/races');
      expect(result).toEqual(mockResponse);
      expect(result.races[0].speed).toBe(30);
    });
  });

  describe('getClasses', () => {
    it('should fetch classes catalog', async () => {
      const mockResponse = {
        classes: [
          {
            id: 'class-1',
            name: 'Fighter',
            description: 'Master of weapons',
            hit_die: 10,
            primary_ability: 'Strength',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getClasses();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/classes');
      expect(result).toEqual(mockResponse);
      expect(result.classes[0].hit_die).toBe(10);
    });
  });

  describe('getBackgrounds', () => {
    it('should fetch backgrounds catalog', async () => {
      const mockResponse = {
        backgrounds: [
          {
            id: 'bg-1',
            name: 'Soldier',
            description: 'Trained for war',
            skill_proficiencies: ['Athletics', 'Intimidation'],
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getBackgrounds();

      expect(mockApiService.get).toHaveBeenCalledWith(
        '/api/catalogs/backgrounds'
      );
      expect(result).toEqual(mockResponse);
      expect(result.backgrounds[0].skill_proficiencies).toHaveLength(2);
    });
  });

  describe('getFeats', () => {
    it('should fetch feats catalog', async () => {
      const mockResponse = {
        feats: [
          {
            id: 'feat-1',
            name: 'Alert',
            description: 'Always on the lookout',
            prerequisite: 'None',
            content_pack: 'core',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getFeats();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/feats');
      expect(result).toEqual(mockResponse);
      expect(result.feats[0].prerequisite).toBe('None');
    });

    it('should handle feats without prerequisites', async () => {
      const mockResponse = {
        feats: [
          {
            id: 'feat-1',
            name: 'Alert',
            description: 'Always on the lookout',
            content_pack: 'core',
            // No prerequisite field
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getFeats();

      expect(result.feats[0].prerequisite).toBeUndefined();
    });
  });

  describe('getContentPacks', () => {
    it('should fetch content packs list', async () => {
      const mockResponse = {
        content_packs: [
          {
            id: 'core',
            name: 'Core Rules',
            description: 'The base D&D 5e content',
            version: '1.0.0',
          },
          {
            id: 'expansion-1',
            name: 'Expansion Pack',
            description: 'Additional content',
            version: '1.0.0',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getContentPacks();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/content-packs');
      expect(result).toEqual(mockResponse);
      expect(result.content_packs).toHaveLength(2);
    });
  });

  describe('error handling', () => {
    it('should propagate API errors', async () => {
      const error = new Error('Fetch failed');
      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(catalogApiService.getSpells()).rejects.toThrow(
        'Fetch failed'
      );
    });

    it('should handle network errors across all methods', async () => {
      const error = new Error('Network error');

      // Test that each method properly propagates errors
      const methods = [
        'getCharacters',
        'getScenarios',
        'getSpells',
        'getItems',
        'getMonsters',
        'getRaces',
        'getClasses',
        'getBackgrounds',
        'getFeats',
        'getContentPacks',
      ];

      for (const methodName of methods) {
        (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
          error
        );

        await expect(
          (catalogApiService as any)[methodName]()
        ).rejects.toThrow('Network error');
      }
    });
  });

  describe('content pack filtering', () => {
    it('should fetch items from different content packs', async () => {
      const mockResponse = {
        items: [
          {
            id: 'item-1',
            name: 'Core Item',
            type: 'weapon',
            description: 'From core',
            content_pack: 'core',
          },
          {
            id: 'item-2',
            name: 'Expansion Item',
            type: 'armor',
            description: 'From expansion',
            content_pack: 'expansion-1',
          },
        ],
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getItems();

      expect(result.items).toHaveLength(2);
      expect(result.items[0].content_pack).toBe('core');
      expect(result.items[1].content_pack).toBe('expansion-1');
    });
  });
});
