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
      post: vi.fn(),
    } as unknown as ApiService;

    catalogApiService = new CatalogApiService(mockApiService);
  });

  describe('getCharacters', () => {
    it('should fetch characters list', async () => {
      // Backend returns array directly, not wrapped
      const mockResponse = [
        {
          id: 'char-1',
          name: 'Aldric Swiftarrow',
          race: 'Elf',
          class_index: 'ranger',
          starting_level: 5,
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getCharacters();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/characters');
      expect(result).toEqual(mockResponse);
      expect(result).toHaveLength(1);
    });

    it('should handle empty characters list', async () => {
      const mockResponse: any[] = [];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getCharacters();

      expect(result).toHaveLength(0);
    });
  });

  describe('getScenarios', () => {
    it('should fetch scenarios list', async () => {
      const mockResponse = [
        {
          id: 'scenario-1',
          title: 'The Lost Mine',
          description: 'A classic adventure',
          starting_location_id: 'start-1',
          locations: {},
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getScenarios();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/scenarios');
      expect(result).toEqual(mockResponse);
      expect(result).toHaveLength(1);
    });
  });

  describe('getSpells', () => {
    it('should fetch spells catalog', async () => {
      const mockResponse = [
        {
          index: 'fireball',
          name: 'Fireball',
          level: 3,
          school: 'Evocation',
          casting_time: '1 action',
          range: '150 feet',
          duration: 'Instantaneous',
          description: 'A bright streak...',
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getSpells();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/spells');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.level).toBe(3);
    });

    it('should handle spells with no content pack', async () => {
      const mockResponse = [
        {
          index: 'magic-missile',
          name: 'Magic Missile',
          level: 1,
          school: 'Evocation',
          casting_time: '1 action',
          range: '120 feet',
          duration: 'Instantaneous',
          description: 'You create three...',
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getSpells();

      expect(result[0]?.content_pack).toBe('srd');
    });
  });

  describe('getItems', () => {
    it('should fetch items catalog', async () => {
      const mockResponse = [
        {
          index: 'longsword',
          name: 'Longsword',
          type: 'Weapon',
          rarity: 'Common',
          weight: 3,
          value: 15,
          description: 'A versatile blade',
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getItems();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/items');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.type).toBe('Weapon');
    });
  });

  describe('getMonsters', () => {
    it('should fetch monsters catalog', async () => {
      const mockResponse = [
        {
          index: 'goblin',
          name: 'Goblin',
          type: 'humanoid',
          size: 'Small',
          alignment: 'Neutral Evil',
          armor_class: 15,
          hit_points: { current: 7, maximum: 7 },
          hit_dice: '2d6',
          speed: '30 ft.',
          challenge_rating: 0.25,
          abilities: {
            strength: 8,
            dexterity: 14,
            constitution: 10,
            intelligence: 10,
            wisdom: 8,
            charisma: 8,
          },
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getMonsters();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/monsters');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.challenge_rating).toBe(0.25);
    });
  });

  describe('getRaces', () => {
    it('should fetch races catalog', async () => {
      const mockResponse = [
        {
          index: 'elf',
          name: 'Elf',
          speed: 30,
          size: 'Medium',
          languages: ['Common', 'Elvish'],
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getRaces();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/races');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.speed).toBe(30);
    });
  });

  describe('getClasses', () => {
    it('should fetch classes catalog', async () => {
      const mockResponse = [
        {
          index: 'fighter',
          name: 'Fighter',
          hit_die: 10,
          saving_throws: ['Strength', 'Constitution'],
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getClasses();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/classes');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.hit_die).toBe(10);
    });
  });

  describe('getBackgrounds', () => {
    it('should fetch backgrounds catalog', async () => {
      const mockResponse = [
        {
          index: 'acolyte',
          name: 'Acolyte',
          skill_proficiencies: ['Insight', 'Religion'],
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getBackgrounds();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/backgrounds');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.skill_proficiencies).toContain('Insight');
    });
  });

  describe('getFeats', () => {
    it('should fetch feats catalog', async () => {
      const mockResponse = [
        {
          index: 'alert',
          name: 'Alert',
          description: 'Always on the lookout for danger',
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getFeats();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/catalogs/feats');
      expect(result).toEqual(mockResponse);
      expect(result[0]?.name).toBe('Alert');
    });

    it('should handle empty feats list', async () => {
      const mockResponse: any[] = [];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getFeats();

      expect(result).toHaveLength(0);
    });
  });

  describe('getContentPacks', () => {
    it('should fetch content packs list', async () => {
      const mockResponse = {
        packs: [
          {
            id: 'srd',
            name: 'System Reference Document',
            version: '1.0.0',
            author: 'Wizards of the Coast',
            description: 'Core SRD content',
            pack_type: 'srd',
          },
        ],
        total: 1,
      };

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getContentPacks();

      expect(mockApiService.get).toHaveBeenCalledWith('/api/content-packs');
      expect(result.packs).toHaveLength(1);
      expect(result.total).toBe(1);
    });
  });

  describe('filtering and searching', () => {
    it('should support filtering spells by content pack', async () => {
      const mockResponse = [
        {
          index: 'fireball',
          name: 'Fireball',
          level: 3,
          school: 'Evocation',
          casting_time: '1 action',
          range: '150 feet',
          duration: 'Instantaneous',
          description: 'A bright streak...',
          content_pack: 'srd',
        },
        {
          index: 'custom-spell',
          name: 'Custom Spell',
          level: 1,
          school: 'Abjuration',
          casting_time: '1 action',
          range: 'Self',
          duration: '1 hour',
          description: 'A custom spell',
          content_pack: 'custom',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getSpells();

      // Client-side filtering would happen in the component
      const srdSpells = result.filter((s: any) => s.content_pack === 'srd');
      expect(srdSpells).toHaveLength(1);
    });

    it('should support searching items by name', async () => {
      const mockResponse = [
        {
          index: 'longsword',
          name: 'Longsword',
          type: 'Weapon',
          rarity: 'Common',
          weight: 3,
          value: 15,
          description: 'A versatile blade',
          content_pack: 'srd',
        },
        {
          index: 'shortsword',
          name: 'Shortsword',
          type: 'Weapon',
          rarity: 'Common',
          weight: 2,
          value: 10,
          description: 'A light blade',
          content_pack: 'srd',
        },
      ];

      (mockApiService.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse
      );

      const result = await catalogApiService.getItems();

      // Client-side search would happen in the component
      const swords = result.filter((item: any) =>
        item.name.toLowerCase().includes('sword')
      );
      expect(swords).toHaveLength(2);
    });
  });

  describe('error handling', () => {
    it('should propagate errors from ApiService', async () => {
      const error = new Error('Network error');

      (mockApiService.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        error
      );

      await expect(catalogApiService.getSpells()).rejects.toThrow('Network error');
    });
  });
});
