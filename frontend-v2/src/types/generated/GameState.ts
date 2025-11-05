/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */
/* Generated on 2025-11-05T14:38:00.000Z */

export interface GameState {
  game_id: string;
  player: Character;
  location: Location;
  party: Party;
  combat: Combat | null;
  time: GameTime;
  conversation_history: ConversationEntry[];
  chronicle: MemoryEntry[];
  /**
   * Recent events that occurred in the game
   */
  events: GameEvent[];
  metadata: GameMetadata;
}

export interface Character {
  id: string;
  name: string;
  race: string;
  class: string;
  level: number;
  hp: number;
  max_hp: number;
  temp_hp: number;
  ac: number;
  initiative_bonus: number;
  abilities: Abilities;
  skills: Record<string, number>;
  saving_throws: Record<string, number>;
  proficiency_bonus: number;
  conditions: string[];
  inventory: InventoryItem[];
  equipment: Equipment;
  spell_slots: Record<string, SpellSlot>;
  known_spells: string[];
}

export interface Abilities {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  quantity: number;
  weight: number;
  description?: string;
}

export interface Equipment {
  weapon?: string;
  armor?: string;
  shield?: string;
}

export interface SpellSlot {
  level: number;
  total: number;
  used: number;
}

export interface Location {
  id: string;
  name: string;
  description: string;
  exits: Record<string, string>;
  npcs_present: string[];
}

export interface Party {
  members: PartyMember[];
  max_size: number;
}

export interface PartyMember {
  id: string;
  name: string;
  role: 'player' | 'companion';
  hp: number;
  max_hp: number;
  ac: number;
  level: number;
  class_name: string;
}

export interface Combat {
  is_active: boolean;
  round: number;
  turn_index: number;
  initiative_order: Initiative[];
  combatants: Combatant[];
}

export interface Initiative {
  entity_id: string;
  roll: number;
}

export interface Combatant {
  entity_id: string;
  name: string;
  type: 'player' | 'companion' | 'enemy' | 'ally' | 'neutral';
  hp: number;
  max_hp: number;
  ac: number;
  conditions: string[];
  is_conscious: boolean;
}

export interface GameTime {
  day: number;
  hour: number;
  minute: number;
}

export interface ConversationEntry {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface MemoryEntry {
  id: string;
  title: string;
  content: string;
  category: 'event' | 'npc' | 'location' | 'quest' | 'item';
  timestamp: string;
  location_id?: string;
}

export interface GameEvent {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface GameMetadata {
  created_at: string;
  last_saved: string;
  scenario_id: string;
  character_id: string;
}
