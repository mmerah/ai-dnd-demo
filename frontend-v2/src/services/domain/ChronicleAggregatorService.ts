/**
 * Service responsible for aggregating chronicle entries from game state.
 * Extracted from ChroniclePanel to follow Single Responsibility Principle.
 *
 * Aggregates entries from:
 * - World memories (scenario-level events)
 * - Location memories (location-specific events)
 * - NPC memories (character-specific events)
 * - Player journal entries (user-created notes)
 */

import type { GameState } from '../../types/generated/GameState.js';
import type { MemoryEntry } from '../../types/generated/MemoryEntry.js';

/**
 * Aggregated entry structure combining all chronicle entry types
 */
export interface AggregatedEntry {
  type: 'world' | 'location' | 'npc' | 'player';
  badge: string;
  timestamp: Date;
  content: string;
  tags: string[];
  locationId?: string;
  npcIds?: string[];
  npcName?: string;
  entryId?: string;
  editable: boolean;
  pinned: boolean;
}

/**
 * Options for aggregation behavior
 */
export interface AggregationOptions {
  /** Whether to include entries from all locations (true) or only current location (false) */
  showAllLocations: boolean;
  /** Current location ID (used when showAllLocations is false) */
  currentLocationId?: string;
}

/**
 * Service for aggregating chronicle entries from various game state sources
 */
export class ChronicleAggregatorService {
  /**
   * Aggregates all chronicle entries from game state
   * @param gameState - Current game state containing memories and journal entries
   * @param options - Aggregation options (location filtering)
   * @returns Array of aggregated entries from all sources
   */
  aggregateAll(gameState: GameState, options: AggregationOptions): AggregatedEntry[] {
    const entries: AggregatedEntry[] = [];

    // Aggregate from all sources
    entries.push(...this.aggregateWorldMemories(gameState));
    entries.push(...this.aggregateLocationMemories(gameState, options));
    entries.push(...this.aggregateNPCMemories(gameState, options));
    entries.push(...this.aggregatePlayerJournal(gameState));

    return entries;
  }

  /**
   * Aggregates world-level memory entries
   * @param gameState - Current game state
   * @returns Array of world memory entries
   */
  aggregateWorldMemories(gameState: GameState): AggregatedEntry[] {
    const entries: AggregatedEntry[] = [];

    if (gameState.scenario_instance?.world_memories) {
      gameState.scenario_instance.world_memories.forEach((memory: MemoryEntry) => {
        entries.push({
          type: 'world',
          badge: 'WORLD',
          timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
          content: memory.summary,
          tags: memory.tags || [],
          locationId: memory.location_id ?? undefined,
          npcIds: memory.npc_ids || [],
          editable: false,
          pinned: false,
        });
      });
    }

    return entries;
  }

  /**
   * Aggregates location-specific memory entries
   * @param gameState - Current game state
   * @param options - Aggregation options (location filtering)
   * @returns Array of location memory entries
   */
  aggregateLocationMemories(
    gameState: GameState,
    options: AggregationOptions
  ): AggregatedEntry[] {
    const entries: AggregatedEntry[] = [];

    if (gameState.scenario_instance?.location_states) {
      Object.entries(gameState.scenario_instance.location_states).forEach(([locId, locState]) => {
        // Filter by current location unless "show all" is enabled
        if (!options.showAllLocations && locId !== options.currentLocationId) {
          return;
        }

        if (locState.location_memories) {
          locState.location_memories.forEach((memory: MemoryEntry) => {
            entries.push({
              type: 'location',
              badge: 'LOCATION',
              timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
              content: memory.summary,
              tags: memory.tags || [],
              locationId: (memory.location_id ?? locId) || undefined,
              npcIds: memory.npc_ids || [],
              editable: false,
              pinned: false,
            });
          });
        }
      });
    }

    return entries;
  }

  /**
   * Aggregates NPC-specific memory entries
   * @param gameState - Current game state
   * @param options - Aggregation options (location filtering)
   * @returns Array of NPC memory entries
   */
  aggregateNPCMemories(gameState: GameState, options: AggregationOptions): AggregatedEntry[] {
    const entries: AggregatedEntry[] = [];

    if (gameState.npcs) {
      gameState.npcs.forEach((npc) => {
        // Filter by current location unless "show all" is enabled
        if (!options.showAllLocations && npc.current_location_id !== options.currentLocationId) {
          return;
        }

        if (npc.npc_memories) {
          npc.npc_memories.forEach((memory: MemoryEntry) => {
            entries.push({
              type: 'npc',
              badge: 'NPC',
              timestamp: memory.created_at ? new Date(memory.created_at) : new Date(),
              content: memory.summary,
              tags: memory.tags || [],
              locationId: memory.location_id ?? undefined,
              npcIds: memory.npc_ids || [],
              npcName: npc.sheet?.character?.name || 'Unknown NPC',
              editable: false,
              pinned: false,
            });
          });
        }
      });
    }

    return entries;
  }

  /**
   * Aggregates player journal entries
   * @param gameState - Current game state
   * @returns Array of player journal entries
   */
  aggregatePlayerJournal(gameState: GameState): AggregatedEntry[] {
    const entries: AggregatedEntry[] = [];

    if (gameState.player_journal_entries) {
      gameState.player_journal_entries.forEach((entry) => {
        entries.push({
          type: 'player',
          badge: 'PLAYER',
          timestamp: entry.created_at ? new Date(entry.created_at) : new Date(),
          content: entry.content,
          tags: entry.tags || [],
          locationId: entry.location_id ?? undefined,
          npcIds: entry.npc_ids || [],
          entryId: entry.entry_id,
          editable: true,
          pinned: entry.pinned || false,
        });
      });
    }

    return entries;
  }
}
