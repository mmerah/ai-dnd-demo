# CLAUDE.md – D&D 5e AI Dungeon Master

## Mission
Ship a strongly typed, AI-assisted Dungeon Master that junior devs can extend without fear. Every change should keep the narrative agents sharp, the data validated, and the tooling green.

## Core Principles
- **SOLID first**: interfaces in `app/interfaces`, narrowly scoped classes, DI via `app/container.py`
- **Fail fast**: raise immediately, validate at startup, never swallow exceptions
- **Type safety**: Pydantic v2 everywhere, `mypy --strict` required
- **DRY & explicit**: shared logic in services, communicate via event bus, no helper duplication
- **No backwards compatibility**: replace old code fully when requirements shift
- **Ban `Any`**: forbidden by config; if unavoidable, justify and isolate
- **Tool-driven agents**: business rules in services/tools, agents only orchestrate
- **Event-sourced**: mutations via event bus + handlers for UI/save/AI sync
- **Content is data**: assets in JSON/content packs, no hardcoded lore

## Stack
- **Runtime**: Python 3.10+, FastAPI, uvicorn, Pydantic v2 + Settings, httpx, SSE via sse-starlette
- **AI**: pydantic-ai agents (Narrative/Combat/Summarizer/NPC) via OpenRouter models
- **Frontend**: Vanilla HTML/CSS/JS from `frontend/`, consumes `/api` + SSE
- **Data**: JSON repos in `data/` + user overrides in `user-data/packs`
- **Quality**: Ruff (format/lint), mypy strict, pytest/pytest-asyncio, coverage, pre-commit

## Environment
Copy `.env.example` to `.env`: `OPENROUTER_API_KEY`, `NARRATIVE_MODEL`, `COMBAT_MODEL`, `SUMMARIZER_MODEL`, `MAX_RETRIES`, `SAVE_DIRECTORY`, `PORT`, `DEBUG_AI`, `DEBUG_AGENT_CONTEXT`

## Structure

### Backend (`app/`)
```
app/
├── main.py                    # FastAPI entry with lifespan validation + SSE
├── config.py                  # Typed env loader (Pydantic Settings)
├── container.py               # Dependency injector wiring all services/repos
├── agents/
│   ├── factory.py             # Builds all agents (Narrative, Combat, NPC, etc.)
│   ├── core/
│   │   ├── base.py            # Abstract agent contract (BaseAgent)
│   │   ├── dependencies.py    # Tool dependency payload (GameState, services, etc.)
│   │   ├── prompts.py         # System prompts for each agent type
│   │   ├── types.py           # AgentType enum
│   │   └── event_stream/      # Pydantic-AI stream handlers (thinking/tools)
│   ├── narrative/             # Story progression agent
│   ├── combat/                # Tactical combat agent
│   ├── summarizer/            # Context bridge agent
│   └── npc/                   # Sub-package for NPC agents
│       ├── base.py            # Shared base class for all NPC agents
│       ├── individual_agent.py # Agent for major NPCs with persistent state
│       └── puppeteer_agent.py # Shared agent for minor, role-played NPCs
├── api/
│   ├── routes.py              # Root router composition
│   ├── dependencies.py        # FastAPI deps resolving services
│   ├── player_actions.py      # Manual actions via ActionService
│   ├── tasks.py               # Background AI task + SSE broadcast
│   ├── routers/               # game/scenarios/characters/catalogs/content_packs
│   └── schemas/               # Response DTOs
├── common/                    # exceptions.py, types.py
├── events/
│   ├── base.py                # Command/handler base classes
│   ├── event_bus.py           # Async pub/sub dispatcher
│   ├── commands/              # Payloads (broadcast/character/combat/dice/inventory/location/quest/time)
│   └── handlers/              # State mutations + SSE per command family
├── interfaces/                # Service/repo/event protocols
├── models/
│   ├── ai_response.py         # Streaming/complete/error payloads
│   ├── character.py           # Player sheet (stats/inventory/spells)
│   ├── combat.py              # Combat state (initiative/turns/conditions)
│   ├── game_state.py          # Root aggregate with history helpers
│   ├── memory.py              # Structured memory models
│   ├── instances/             # Display snapshots (player/monster/scenario)
│   └── ...                    # damage_types/spells/quests/races/traits
├── services/
│   ├── ai/
│   │   ├── ai_service.py                   # Top-level agent orchestration
│   │   ├── agent_lifecycle_service.py      # NPC agent cache/factory
│   │   ├── context_service.py              # Context composition via builders
│   │   ├── message_service.py              # SSE broadcast handler
│   │   ├── orchestrator_service.py         # Agent routing logic
│   │   ├── orchestrator/                   # agent_router/combat_loop/transitions/state_reload
│   │   ├── context_builders/               # Granular context builders (18 builders)
│   │   └── debug_logger/event_logger/message_converter/tool_call_extractor
│   ├── character/             # Sheet loading, stat compute, leveling
│   ├── common/                # DiceService/BroadcastService/ActionService/PathResolver
│   ├── data/
│   │   ├── content_pack_registry.py        # Discovers data + user packs
│   │   ├── loaders/                        # Character/scenario JSON loaders
│   │   ├── repositories/                   # Typed repos (20 entity types)
│   │   └── repository_factory.py           # Repo set per game/pack
│   └── game/
│       ├── game_factory.py                 # Initial state from scenario+character
│       ├── game_service.py                 # Create/load/save orchestration
│       ├── combat_service.py               # Turn management, damage, flow
│       ├── location_service.py             # Location transitions
│       ├── memory_service.py               # Conversation → structured memory
│       ├── message_manager/metadata_service/monster_factory
│       ├── pre_save_sanitizer/save_manager # Persistence layer
├── tools/
│   ├── decorators.py      # Wraps commands as tools with event logging
│   ├── dice_tools.py      # Dice rolling interface for agents
│   ├── combat_tools.py    # Start/advance/end combat, manage combatants
│   ├── character_tools.py # HP, conditions, spell slots, leveling
│   ├── inventory_tools.py # Currency + inventory adjustments
│   ├── location_tools.py  # Location state changes + NPC moves
│   ├── quest_tools.py     # Quest/objective progression
│   └── time_tools.py      # Rests + time advancement
└── utils/                 # ability_utils/entity_resolver/id_generator/names
```

### Data (`data/`)
```
data/
├── alignments.json        # Alignment definitions (name, description, ethos)
├── backgrounds.json       # Background traits, proficiencies, feature hooks
├── classes.json           # Class progressions, hit dice, proficiencies
├── conditions.json        # Status effect definitions and mechanics
├── damage_types.json      # Damage type catalog with descriptors
├── feats.json             # Feat details and prerequisite info
├── features.json          # Shared feature blocks reused by classes/races
├── items.json             # Generic equipment catalog (weapons, armor, gear)
├── languages.json         # Language metadata and script associations
├── magic_items.json       # Magic item list with rarity/effects
├── magic_schools.json     # Spell school definitions
├── metadata.json          # Global metadata (content versioning, ids)
├── monsters.json          # Baseline monster stat blocks
├── races.json             # Race definitions linking traits and features
├── skills.json            # Skill list with governing abilities
├── spells.json            # Spell metadata (slots, components, effects)
├── subclasses.json        # Subclass progressions tied to classes
├── subraces.json          # Subrace variants extending races.json
├── traits.json            # Trait definitions referenced by races/backgrounds
├── weapon_properties.json # Weapon property descriptions and rules
├── characters/            # Canonical playable PCs (`aldric-swiftarrow.json`)
└── scenarios/             # Scenario bundles (encounters, quests, locations)
```
### Other Directories
- `frontend/`: Static client (SSE + REST)
- `logs/`, `saves/`: Runtime output (gitignored)
- `scripts/`: SRD ingestion/migration utilities
- `tests/`: Factories, integration, unit suites
- `user-data/packs/`: Custom content mirroring `data/`
- Root: `pyproject.toml`, `requirements.txt`, `.pre-commit-config.yaml`, `.env.example`

## Runtime Flow
1. `uvicorn app.main:app --reload --port 8123` boots FastAPI, initializes Container, validates all data
2. Player action → `/api/game/{game_id}/action` → background task → GameService + AIService
3. Request → AgentOrchestrator:
   - **NPC dialogue** (@npc_name): AgentLifecycleService → IndividualMindAgent (major) or PuppeteerAgent (minor)
   - **Non-combat**: NarrativeAgent
   - **Combat active**: CombatAgent
4. Agent builds context (ContextService), processes prompt, calls tools
5. Tool → @tool_handler → Command → EventBus → Handler → mutate GameState → dispatch follow-ups
6. **Transitions**:
   - Narrative→Combat: SummarizerAgent creates context bridge
   - Combat runs NPC/monster turns until player turn/end
   - Location change: MemoryService summarizes events → MemoryEntry
7. SaveManager persists, MessageService broadcasts SSE

## Commands
- **Format**: `ruff format .`
- **Lint**: `ruff check --fix .`
- **Types**: `mypy --strict app tests`
- **Tests**: `pytest`
- **Coverage**: `coverage run -m pytest && coverage report`
- **Full**: `pre-commit run --all-files`

## APIs
- Base: `/api`
- Game: `/game/new`, `/game/{id}`, `/game/{id}/action`, `/game/{id}/sse`
- Catalogs: `/scenarios`, `/characters`, `/catalogs/*`, `/content-packs/*`
- Health: `/health`

## Dev Tips
- Read interfaces before changing services
- Extend tools/services, not agents
- Run app once to validate new data
- Use existing models for SSE payloads
- Use dice service (not `random`) for deterministic tests
- Separate content pack commits from code

## When In Doubt
Consult `app/services` + `app/tools` for canonical behavior. Run mypy and pytest locally. Delete/rewrite legacy code over patches.