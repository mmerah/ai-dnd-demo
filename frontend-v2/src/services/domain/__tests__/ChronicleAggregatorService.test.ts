import { describe, it, expect } from 'vitest';
import { ChronicleAggregatorService } from '../ChronicleAggregatorService';
import type { GameState } from '../../../types/generated/GameState';

describe('ChronicleAggregatorService', () => {
  const service = new ChronicleAggregatorService();

  describe('aggregateWorldMemories', () => {
    it('should aggregate world memories from game state', () => {
      const gameState = {
        scenario_instance: {
          world_memories: [
            {
              summary: 'The ancient dragon awoke',
              created_at: '2024-01-01T12:00:00Z',
              tags: ['dragon', 'awakening'],
              location_id: 'loc-1',
              npc_ids: ['npc-1'],
            },
            {
              summary: 'A dark prophecy was spoken',
              created_at: '2024-01-02T12:00:00Z',
              tags: ['prophecy'],
              location_id: null,
              npc_ids: [],
            },
          ],
        },
      } as unknown as GameState;

      const entries = service.aggregateWorldMemories(gameState);

      expect(entries).toHaveLength(2);
      expect(entries[0]).toMatchObject({
        type: 'world',
        badge: 'WORLD',
        content: 'The ancient dragon awoke',
        tags: ['dragon', 'awakening'],
        locationId: 'loc-1',
        npcIds: ['npc-1'],
        editable: false,
        pinned: false,
      });
      expect(entries[0].timestamp).toBeInstanceOf(Date);
      expect(entries[1]).toMatchObject({
        type: 'world',
        badge: 'WORLD',
        content: 'A dark prophecy was spoken',
        tags: ['prophecy'],
        npcIds: [],
        editable: false,
        pinned: false,
      });
    });

    it('should return empty array if no world memories exist', () => {
      const gameState = {
        scenario_instance: {
          world_memories: [],
        },
      } as unknown as GameState;

      const entries = service.aggregateWorldMemories(gameState);

      expect(entries).toEqual([]);
    });

    it('should return empty array if scenario_instance is missing', () => {
      const gameState = {} as unknown as GameState;

      const entries = service.aggregateWorldMemories(gameState);

      expect(entries).toEqual([]);
    });

    it('should handle missing created_at with current date', () => {
      const gameState = {
        scenario_instance: {
          world_memories: [
            {
              summary: 'Memory without timestamp',
              tags: [],
              location_id: null,
              npc_ids: [],
            },
          ],
        },
      } as unknown as GameState;

      const entries = service.aggregateWorldMemories(gameState);

      expect(entries[0].timestamp).toBeInstanceOf(Date);
    });
  });

  describe('aggregateLocationMemories', () => {
    it('should aggregate location memories from all locations when showAllLocations is true', () => {
      const gameState = {
        scenario_instance: {
          current_location_id: 'loc-1',
          location_states: {
            'loc-1': {
              location_memories: [
                {
                  summary: 'You entered the tavern',
                  created_at: '2024-01-01T12:00:00Z',
                  tags: ['arrival'],
                  location_id: 'loc-1',
                  npc_ids: [],
                },
              ],
            },
            'loc-2': {
              location_memories: [
                {
                  summary: 'The forest was dark',
                  created_at: '2024-01-02T12:00:00Z',
                  tags: ['exploration'],
                  location_id: 'loc-2',
                  npc_ids: [],
                },
              ],
            },
          },
        },
      } as unknown as GameState;

      const entries = service.aggregateLocationMemories(gameState, {
        showAllLocations: true,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(2);
      expect(entries[0].content).toBe('You entered the tavern');
      expect(entries[1].content).toBe('The forest was dark');
    });

    it('should filter to current location when showAllLocations is false', () => {
      const gameState = {
        scenario_instance: {
          current_location_id: 'loc-1',
          location_states: {
            'loc-1': {
              location_memories: [
                {
                  summary: 'You entered the tavern',
                  created_at: '2024-01-01T12:00:00Z',
                  tags: ['arrival'],
                  location_id: 'loc-1',
                  npc_ids: [],
                },
              ],
            },
            'loc-2': {
              location_memories: [
                {
                  summary: 'The forest was dark',
                  created_at: '2024-01-02T12:00:00Z',
                  tags: ['exploration'],
                  location_id: 'loc-2',
                  npc_ids: [],
                },
              ],
            },
          },
        },
      } as unknown as GameState;

      const entries = service.aggregateLocationMemories(gameState, {
        showAllLocations: false,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(1);
      expect(entries[0].content).toBe('You entered the tavern');
      expect(entries[0].locationId).toBe('loc-1');
    });

    it('should return empty array if no location states exist', () => {
      const gameState = {
        scenario_instance: {
          location_states: {},
        },
      } as unknown as GameState;

      const entries = service.aggregateLocationMemories(gameState, {
        showAllLocations: true,
      });

      expect(entries).toEqual([]);
    });

    it('should use location ID from state if memory location_id is null', () => {
      const gameState = {
        scenario_instance: {
          location_states: {
            'loc-1': {
              location_memories: [
                {
                  summary: 'Event happened here',
                  created_at: '2024-01-01T12:00:00Z',
                  tags: [],
                  location_id: null,
                  npc_ids: [],
                },
              ],
            },
          },
        },
      } as unknown as GameState;

      const entries = service.aggregateLocationMemories(gameState, {
        showAllLocations: true,
      });

      expect(entries[0].locationId).toBe('loc-1');
    });
  });

  describe('aggregateNPCMemories', () => {
    it('should aggregate NPC memories from all NPCs when showAllLocations is true', () => {
      const gameState = {
        npcs: [
          {
            current_location_id: 'loc-1',
            sheet: {
              character: {
                name: 'Gandalf',
              },
            },
            npc_memories: [
              {
                summary: 'The wizard arrived',
                created_at: '2024-01-01T12:00:00Z',
                tags: ['arrival'],
                location_id: 'loc-1',
                npc_ids: ['npc-1'],
              },
            ],
          },
          {
            current_location_id: 'loc-2',
            sheet: {
              character: {
                name: 'Aragorn',
              },
            },
            npc_memories: [
              {
                summary: 'The ranger scouted ahead',
                created_at: '2024-01-02T12:00:00Z',
                tags: ['scouting'],
                location_id: 'loc-2',
                npc_ids: ['npc-2'],
              },
            ],
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregateNPCMemories(gameState, {
        showAllLocations: true,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(2);
      expect(entries[0]).toMatchObject({
        type: 'npc',
        badge: 'NPC',
        content: 'The wizard arrived',
        npcName: 'Gandalf',
      });
      expect(entries[1]).toMatchObject({
        type: 'npc',
        badge: 'NPC',
        content: 'The ranger scouted ahead',
        npcName: 'Aragorn',
      });
    });

    it('should filter to current location when showAllLocations is false', () => {
      const gameState = {
        npcs: [
          {
            current_location_id: 'loc-1',
            sheet: {
              character: {
                name: 'Gandalf',
              },
            },
            npc_memories: [
              {
                summary: 'The wizard arrived',
                created_at: '2024-01-01T12:00:00Z',
                tags: [],
                location_id: 'loc-1',
                npc_ids: [],
              },
            ],
          },
          {
            current_location_id: 'loc-2',
            sheet: {
              character: {
                name: 'Aragorn',
              },
            },
            npc_memories: [
              {
                summary: 'The ranger scouted ahead',
                created_at: '2024-01-02T12:00:00Z',
                tags: [],
                location_id: 'loc-2',
                npc_ids: [],
              },
            ],
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregateNPCMemories(gameState, {
        showAllLocations: false,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(1);
      expect(entries[0].npcName).toBe('Gandalf');
    });

    it('should handle NPC with no name', () => {
      const gameState = {
        npcs: [
          {
            current_location_id: 'loc-1',
            sheet: {
              character: {},
            },
            npc_memories: [
              {
                summary: 'Something happened',
                created_at: '2024-01-01T12:00:00Z',
                tags: [],
                location_id: 'loc-1',
                npc_ids: [],
              },
            ],
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregateNPCMemories(gameState, {
        showAllLocations: true,
      });

      expect(entries[0].npcName).toBe('Unknown NPC');
    });

    it('should return empty array if no NPCs exist', () => {
      const gameState = {
        npcs: [],
      } as unknown as GameState;

      const entries = service.aggregateNPCMemories(gameState, {
        showAllLocations: true,
      });

      expect(entries).toEqual([]);
    });
  });

  describe('aggregatePlayerJournal', () => {
    it('should aggregate player journal entries', () => {
      const gameState = {
        player_journal_entries: [
          {
            entry_id: 'entry-1',
            content: 'We defeated the goblins today',
            created_at: '2024-01-01T12:00:00Z',
            tags: ['combat', 'victory'],
            location_id: 'loc-1',
            npc_ids: ['npc-1'],
            pinned: true,
          },
          {
            entry_id: 'entry-2',
            content: 'Found a mysterious map',
            created_at: '2024-01-02T12:00:00Z',
            tags: ['treasure'],
            location_id: null,
            npc_ids: [],
            pinned: false,
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregatePlayerJournal(gameState);

      expect(entries).toHaveLength(2);
      expect(entries[0]).toMatchObject({
        type: 'player',
        badge: 'PLAYER',
        content: 'We defeated the goblins today',
        entryId: 'entry-1',
        editable: true,
        pinned: true,
      });
      expect(entries[1]).toMatchObject({
        type: 'player',
        badge: 'PLAYER',
        content: 'Found a mysterious map',
        entryId: 'entry-2',
        editable: true,
        pinned: false,
      });
    });

    it('should return empty array if no journal entries exist', () => {
      const gameState = {
        player_journal_entries: [],
      } as unknown as GameState;

      const entries = service.aggregatePlayerJournal(gameState);

      expect(entries).toEqual([]);
    });

    it('should handle missing pinned field', () => {
      const gameState = {
        player_journal_entries: [
          {
            entry_id: 'entry-1',
            content: 'Test entry',
            created_at: '2024-01-01T12:00:00Z',
            tags: [],
            location_id: null,
            npc_ids: [],
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregatePlayerJournal(gameState);

      expect(entries[0].pinned).toBe(false);
    });
  });

  describe('aggregateAll', () => {
    it('should combine all entry types', () => {
      const gameState = {
        scenario_instance: {
          current_location_id: 'loc-1',
          world_memories: [
            {
              summary: 'World event',
              created_at: '2024-01-01T12:00:00Z',
              tags: [],
              location_id: null,
              npc_ids: [],
            },
          ],
          location_states: {
            'loc-1': {
              location_memories: [
                {
                  summary: 'Location event',
                  created_at: '2024-01-02T12:00:00Z',
                  tags: [],
                  location_id: 'loc-1',
                  npc_ids: [],
                },
              ],
            },
          },
        },
        npcs: [
          {
            current_location_id: 'loc-1',
            sheet: {
              character: {
                name: 'Test NPC',
              },
            },
            npc_memories: [
              {
                summary: 'NPC event',
                created_at: '2024-01-03T12:00:00Z',
                tags: [],
                location_id: 'loc-1',
                npc_ids: [],
              },
            ],
          },
        ],
        player_journal_entries: [
          {
            entry_id: 'entry-1',
            content: 'Player note',
            created_at: '2024-01-04T12:00:00Z',
            tags: [],
            location_id: null,
            npc_ids: [],
            pinned: false,
          },
        ],
      } as unknown as GameState;

      const entries = service.aggregateAll(gameState, {
        showAllLocations: true,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(4);
      expect(entries.map((e) => e.type)).toEqual(['world', 'location', 'npc', 'player']);
      expect(entries.map((e) => e.content)).toEqual([
        'World event',
        'Location event',
        'NPC event',
        'Player note',
      ]);
    });

    it('should respect location filtering across all entry types', () => {
      const gameState = {
        scenario_instance: {
          current_location_id: 'loc-1',
          world_memories: [],
          location_states: {
            'loc-1': {
              location_memories: [
                {
                  summary: 'Current location',
                  created_at: '2024-01-01T12:00:00Z',
                  tags: [],
                  location_id: 'loc-1',
                  npc_ids: [],
                },
              ],
            },
            'loc-2': {
              location_memories: [
                {
                  summary: 'Other location',
                  created_at: '2024-01-02T12:00:00Z',
                  tags: [],
                  location_id: 'loc-2',
                  npc_ids: [],
                },
              ],
            },
          },
        },
        npcs: [
          {
            current_location_id: 'loc-1',
            sheet: { character: { name: 'Here' } },
            npc_memories: [
              {
                summary: 'NPC here',
                created_at: '2024-01-03T12:00:00Z',
                tags: [],
                location_id: 'loc-1',
                npc_ids: [],
              },
            ],
          },
          {
            current_location_id: 'loc-2',
            sheet: { character: { name: 'There' } },
            npc_memories: [
              {
                summary: 'NPC there',
                created_at: '2024-01-04T12:00:00Z',
                tags: [],
                location_id: 'loc-2',
                npc_ids: [],
              },
            ],
          },
        ],
        player_journal_entries: [],
      } as unknown as GameState;

      const entries = service.aggregateAll(gameState, {
        showAllLocations: false,
        currentLocationId: 'loc-1',
      });

      expect(entries).toHaveLength(2);
      expect(entries.map((e) => e.content)).toEqual(['Current location', 'NPC here']);
    });

    it('should return empty array for empty game state', () => {
      const gameState = {} as unknown as GameState;

      const entries = service.aggregateAll(gameState, {
        showAllLocations: true,
      });

      expect(entries).toEqual([]);
    });
  });
});
