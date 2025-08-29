# CLAUDE.md - D&D 5e AI Dungeon Master Project Specification

## Project Overview
A proof-of-concept web application that provides an AI-powered Dungeon Master for D&D 5e gameplay. Players select a pre-generated character and interact with an AI DM through a chat interface, with automatic character sheet updates and dice roll visualizations.

## Technical Stack
- **Backend**: Python with FastAPI
- **Type System**: Strict typing with Pydantic (no `Any` types allowed)
- **AI Integration**: PydanticAI library with native tool system
- **Model**: `openai/gpt-oss-120b` via OpenRouter (OpenAI-compatible API)
- **Frontend**: Vanilla JavaScript, HTML, CSS (served via FastAPI)
- **Data Storage**: JSON files for game saves and data
- **Communication**: Server-Sent Events (SSE) for streaming AI responses

## Core Architecture Principles
- **SOLID principles** enforced throughout (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- **Fail Fast**: No silent failures, errors should be immediately raised
- **Type Safety**: Strict Pydantic models for all data structures
- **Domain Separation**: Tools organized by functional domain
- **Native Integration**: Uses PydanticAI's native tool system

## Project Structure
```
dungeon-master-5e/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # Pydantic models
│   │   ├── character.py     # CharacterSheet model
│   │   ├── npc.py          # NPCSheet model
│   │   ├── game_state.py   # GameState and related models
│   │   └── ai_response.py  # Display models for frontend
│   ├── services/
│   │   ├── ai_service.py    # PydanticAI integration & agent setup
│   │   ├── game_service.py  # Game state management & persistence
│   │   └── dice_service.py  # Dice rolling mechanics
│   ├── tools/               # Domain-specific tool implementations
│   │   ├── dice_tools.py    # Dice rolls and combat mechanics
│   │   ├── character_tools.py # HP, conditions, spells
│   │   ├── inventory_tools.py # Items and currency
│   │   └── time_tools.py    # Rest and time advancement
│   ├── api/                 
│   │   └── routes.py        # FastAPI endpoints
│   └── data/               
│       ├── spells.json      # 5-10 ranger-appropriate spells
│       ├── items.json       # 10-15 basic items
│       ├── monsters.json    # 5-8 low CR monsters
│       └── characters.json  # Pre-generated ranger character
├── frontend/
│   ├── index.html           # Split-screen interface
│   ├── style.css           # Responsive styling
│   └── app.js              # SSE handling, UI updates
├── saves/                   # JSON game save files
├── .env                     # Configuration
├── requirements.txt         # Python dependencies
└── README.md               # Setup instructions
```

## Key Architecture Components

### AI Service with Native Tools
The AI service uses PydanticAI's native tool registration system:
- Tools are defined as async functions in domain-specific modules
- Each tool has comprehensive docstrings with examples
- Tools are registered with `@agent.tool` decorator
- The AI agent returns natural text responses while tools execute transparently

### Tool Organization (SOLID Principles)
Tools are organized by domain following Single Responsibility Principle:

**dice_tools.py**: Combat and dice mechanics
- `roll_ability_check` - Ability and skill checks
- `roll_saving_throw` - Saving throws
- `roll_attack` - Attack rolls
- `roll_damage` - Damage rolls  
- `roll_initiative` - Initiative for combat

**character_tools.py**: Character state management
- `update_hp` - Damage and healing
- `add_condition` - Apply status effects
- `remove_condition` - Clear status effects
- `update_spell_slots` - Spell slot tracking

**inventory_tools.py**: Inventory management
- `modify_currency` - Gold/silver/copper transactions
- `add_item` - Add items to inventory
- `remove_item` - Remove/use items

**time_tools.py**: Time and rest mechanics
- `short_rest` - 1 hour rest with HP recovery
- `long_rest` - 8 hour rest with full recovery
- `advance_time` - Time progression

### Data Models

#### Character Sheet (Simplified)
Essential fields only:
- Basic: name, race, class, level, alignment, background
- Stats: HP (current/max), AC, abilities (STR/DEX/CON/INT/WIS/CHA)
- Combat: initiative, speed, attacks, proficiency bonus
- Skills: proficiencies, saving throws
- Spellcasting: spell list, spell slots (current/max)
- Inventory: equipment, currency

#### NPC/Monster Sheet (Minimal)
```python
class NPCSheet(BaseModel):
    name: str
    hp: int
    max_hp: int
    ac: int
    attacks: List[Attack]
    challenge_rating: float
```

#### Game State
```python
class GameState(BaseModel):
    game_id: str  # Human-readable (e.g., "ranger-adventure-001")
    character: CharacterSheet
    npcs: List[NPCSheet]
    location: str
    time: GameTime  # Day, hour, minute
    combat: Optional[CombatState]
    quest_flags: Dict[str, Any]
    conversation_history: List[Message]
```

## AI Integration Details

### PydanticAI Native Tool System
- Tools are registered directly on the Agent using `agent.tool()`
- Each tool receives `RunContext[AgentDependencies]` as first parameter
- Tool execution is handled internally by PydanticAI
- No manual queue processing or validation needed
- Tools can access game state through context dependencies

### OpenRouter Configuration
- Model: `openai/gpt-oss-120b`
- Uses OpenAI-compatible API at custom base URL
- API key from `.env` file
- Max retries: 3
- Natural language responses without structured format

### System Prompt
Focuses on:
1. D&D 5e rules and mechanics
2. Narrative style (second person, atmospheric)
3. Natural tool usage for game mechanics
4. Combat flow and turn management
5. Authority on rules interpretation

### Response Flow
1. User sends message via POST `/game/{game_id}/action`
2. AI generates response with PydanticAI agent
3. Tools execute transparently during response generation
4. Narrative streams word-by-word via SSE
5. Character sheet updates broadcast automatically
6. Game state auto-saved to JSON

## Frontend Specifications

### Layout
- Split screen: Character sheet (left), Chat (right)
- Collapsible sections in character sheet
- Combat mode indicator
- Location and time display
- Dice roll visualizations

### Real-time Updates
- SSE connection for streaming narrative
- Character sheet updates on state changes
- Dice roll displays with modifiers shown
- Visual indicators for HP changes, conditions

## API Endpoints
```
POST /game/new              # Create new game
    Body: {character_id: str, premise: str}
    Response: {game_id: str}

GET  /game/{game_id}        # Get full game state
    Response: Complete GameState

POST /game/{game_id}/action # Player action
    Body: {message: str}
    Response: SSE stream of AI response

GET  /game/{game_id}/sse    # SSE endpoint for updates

GET  /characters            # List available characters
    Response: List of character summaries
```

## Initial Content

### Pre-generated Character
- **Name**: Aldric Swiftarrow
- **Class**: Ranger, Level 3
- **Race**: Wood Elf
- **Stats**: STR 13, DEX 16, CON 14, INT 12, WIS 15, CHA 10

### Demo Scenario
Classic progression: Tavern → Forest Path → Goblin Cave → Boss Fight
- Multiple locations for variety
- Skill checks and combat encounters
- NPCs for roleplay opportunities

### Data Files
- **spells.json**: Cure Wounds, Hunter's Mark, Entangle, Fog Cloud, Goodberry
- **items.json**: Healing Potion, Rope, Torch, Rations, weapons, armor
- **monsters.json**: Goblin, Wolf, Hobgoblin, Owlbear, Goblin Boss

## Environment Configuration (.env)
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b
MAX_RETRIES=3
SAVE_DIRECTORY=./saves
PORT=8123
DEBUG_AI=false
```

## Implementation Notes

1. **No Testing in MVP**: Focus on functional implementation first
2. **Auto-save**: Every action triggers a save to JSON
3. **Single Client**: No concurrency handling needed
4. **Error Handling**: Fail fast, no silent failures
5. **AI Authority**: AI decides all narrative outcomes
6. **Native Tools**: Uses PydanticAI's built-in tool system
7. **Context Management**: Full game state provided with each interaction
8. **CORS**: Configure as needed for local development

## Success Criteria
- Player can start a new game with the ranger character
- AI DM provides engaging narrative responses
- Dice rolls are calculated and displayed correctly
- Character sheet updates automatically
- Combat flows naturally with initiative
- Game state persists across sessions
- Tools execute transparently during AI responses
- Full D&D 5e experience within scope limitations

## Architecture Benefits
- **Clean Separation**: Tools organized by domain responsibility
- **Native Integration**: Leverages PydanticAI's strengths
- **Natural Responses**: AI speaks naturally without JSON constraints
- **Maintainable**: Each tool module handles one domain
- **Extensible**: Easy to add new tools or domains
- **Type Safe**: Full Pydantic validation throughout

## Reminder Notes

- Avoid backward compatibility. Always do the complete change and remove previous stuff
- Avoid the use of 'Any'. If it appears anywhere, analyze the code to figure out what it could be replaced with. If it is unavoidable, explain why with a comment
- At every step: Read all related code and explore all execution paths. Ultrathink to decide the best way to move forward.