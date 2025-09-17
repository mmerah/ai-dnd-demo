# CLAUDE.md – D&D 5e AI Dungeon Master

## Mission
Ship a strongly typed, AI-assisted Dungeon Master that junior devs can extend without fear. Every change should keep the narrative agents sharp, the data validated, and the tooling green.

## Core Principles
- **SOLID first**: drive behavior through interfaces in `app/interfaces`, keep classes narrowly scoped, inject dependencies via `app/container.py`.
- **Fail fast**: raise immediately, validate data at startup (`app/main.py` lifespan preloads/validates assets), never swallow exceptions.
- **Type safety**: Pydantic v2 models everywhere, `mypy --strict` is non-negotiable, prefer `Protocol`/`TypedDict` over structural duck typing.
- **DRY & explicit flow**: common logic lives in services (`app/services`), share via event bus or dedicated services, not helper duplication.
- **No backwards compatibility promises**: when requirements shift, replace old code fully and cleanly.
- **Ban `Any`**: config forbids it; if unavoidable, justify in-code with context and isolate usage.
- **Tool-driven agents**: business rules live in services and tool functions, agents orchestrate behavior only.
- **Event-sourced side effects**: game state mutations go through the event bus + handlers so UI, saves, and AI stay in sync.
- **Content is data**: game assets live in JSON/content packs, never hard-code lore in services.

## Stack
- **Runtime**: Python 3.10+, FastAPI, uvicorn, Pydantic v2, Pydantic Settings, httpx, SSE via `sse-starlette`.
- **AI**: pydantic-ai agents (Narrative, Combat, Summarizer) using OpenRouter GPT-OSS models with tool calling.
- **Frontend**: Vanilla HTML/CSS/JS served from `frontend/`, consumes `/api` + SSE stream.
- **Data**: JSON repositories in `data/` plus user overrides in `user-data/packs`.
- **Quality**: Ruff (format + lint), mypy strict, pytest + pytest-asyncio, coverage, pre-commit.

## Environment & Secrets
- Copy `.env.example` to `.env` and fill: `OPENROUTER_API_KEY`, `NARRATIVE_MODEL`, `COMBAT_MODEL`, `SUMMARIZER_MODEL`, `MAX_RETRIES`, `SAVE_DIRECTORY`, `PORT`, `DEBUG_AI`, `DEBUG_AGENT_CONTEXT`.
- Save directory is auto-created; set `DEBUG_AI=true` only when tracing errors (enables traceback payloads).

## Project Structure

### Backend (`app/`)
```
app/
├── main.py                    # FastAPI entrypoint with lifespan validation + SSE static hosting
├── config.py                  # Strongly typed env loader (Pydantic Settings)
├── container.py               # Cached dependency injector wiring every service/repo
├── agents/
│   ├── factory.py             # Builds agents, fetches OpenRouter models, registers tools
│   ├── core/
│   │   ├── base.py            # Abstract agent contract
│   │   ├── dependencies.py    # Tool dependency payload (GameState, repos, bus)
│   │   ├── prompts.py         # System prompts per agent type
│   │   └── event_stream/      # Handler framework for thinking/tool events
│   ├── narrative/agent.py     # Narrative agent orchestrating story tools
│   ├── combat/agent.py        # Combat agent handling initiative + combat-only tools
│   └── summarizer/agent.py    # Context bridge between narrative/combat flows
├── api/
│   ├── routes.py              # Root `/api` router composition
│   ├── dependencies.py        # FastAPI dependencies resolving services/game state
│   ├── player_actions.py      # Executes manual player actions through ActionService
│   ├── tasks.py               # Background task to run AI + broadcast responses
│   ├── routers/               # `game.py`, `scenarios.py`, `characters.py`, `catalogs.py`, `content_packs.py`
│   └── schemas/               # Pydantic response DTOs (content pack metadata, etc.)
├── common/                    # Shared exceptions + narrow helper types
├── events/
│   ├── base.py                # Command/handler base classes and mixins
│   ├── event_bus.py           # Async pub/sub dispatcher
│   ├── commands/              # Broadcast, character, combat, dice, inventory, location, quest, time payloads
│   └── handlers/              # Mutate game state + push SSE per command family
├── interfaces/                # Protocols for services, repositories, event bus
├── models/
│   ├── ai_response.py         # Streaming/complete/error payloads from agents
│   ├── character.py           # Player sheet (stats, inventory, spell slots)
│   ├── combat.py              # Combat state (initiative, turns, conditions)
│   ├── game_state.py          # Root aggregate with helpers for history slicing
│   ├── instances/             # Display-facing snapshots (player, monster, scenario)
│   └── ...                    # Damage types, spells, quests, races, traits, etc.
├── services/
│   ├── ai/
│   │   ├── ai_service.py      # Public generate_response API
│   │   ├── context_service.py # Structured prompts per agent
│   │   ├── context_builders/  # Structured prompts per agent
│   │   ├── orchestrator/      # Agent routing, combat loop, transitions
│   │   ├── message_service.py # SSE emitter
│   │   └── logging tools      # Debug/event logging, tool call extraction
│   ├── character/             # Sheet loading, derived stat computation, leveling
│   ├── common/                # DiceService, BroadcastService, ActionService, PathResolver
│   ├── data/
│   │   ├── content_pack_registry.py # Discovers `data/` + `user-data/` packs
│   │   ├── loaders/           # JSON loaders for characters + scenarios
│   │   ├── repositories/      # Typed repositories (items, spells, monsters, etc.)
│   │   └── repository_factory.py # Picks repo set per game/content pack
│   └── game/
│       ├── game_factory.py       # Builds initial state from scenario + character
│       ├── game_service.py       # Create/load/save orchestrator
│       ├── combat_service.py     # Turn management + damage application
│       ├── location_service.py   # Location transitions + lookups
│       ├── message_manager.py    # SSE payload assembly
│       ├── metadata_service.py   # Display name enrichment
│       ├── monster_factory.py    # Encounter monster instantiation
│       ├── pre_save_sanitizer.py # Strip volatile fields before persistence
│       └── save_manager.py       # Filesystem persistence adapter
├── tools/
│   ├── decorators.py      # Wraps commands as tools with event logging
│   ├── dice_tools.py      # Dice rolling interface for agents
│   ├── combat_tools.py    # Start/advance/end combat, manage combatants
│   ├── character_tools.py # HP, conditions, spell slots, leveling
│   ├── inventory_tools.py # Currency + inventory adjustments
│   ├── location_tools.py  # Location state changes + NPC moves
│   ├── quest_tools.py     # Quest/objective progression
│   └── time_tools.py      # Rests + time advancement
└── utils/                 # Ability math, entity resolution, deterministic id + name helpers
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

### Other Top-Level Directories
- `frontend/`: static client consuming SSE + REST.
- `logs/`: runtime log output (gitignored).
- `saves/`: JSON save files written per game id (gitignored).
- `scripts/`: SRD ingestion/migration utilities (alignments, spells, monsters, etc.).
- `tests/`: factories, integration flows, and unit suites.
- `user-data/`: custom content packs mirroring `data/` structure (`packs/custom-example`).
- Root configs: `pyproject.toml`, `requirements.txt`, `.pre-commit-config.yaml`, `.env.example`.

## Runtime Flow
1. `uvicorn app.main:app --reload --port 8123` boots FastAPI, loads env, builds the container, validates data repositories.
2. Requests hit `/api/...` routers which delegate to services resolved via the container.
3. Agents (`app/services/ai`) orchestrate Narrative/Combat/Summarizer flows, call tool functions, emit events.
4. Event bus dispatches commands to handlers (broadcast, character, combat, inventory, quest, time) which mutate state and notify SSE clients.
5. Game state is persisted through `SaveManager`, enriched via repositories, and streamed to the frontend.

## Data & Content Packs
- Core assets live in `data/*.json`; keep them normalized and validated via repositories.
- Custom packs belong in `user-data/packs/<pack-id>/` mirroring `data/` file names; discovered via `ContentPackRegistry`.
- Use scripts in `scripts/` (e.g., `migrate_spells_from_srd.py`, `ingest_srd_to_internal.py`) for bulk imports—always stage output to `user-data` first.

## Development Workflow
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `pre-commit install`
4. Export OpenRouter key before running commands.
5. Run the app: `uvicorn app.main:app --reload --port 8123`
6. Watch logs in `logs/` or console; SSE/UI is served at `http://localhost:8123` (static) + `/api/...` (JSON).

## Quality Gates & Commands
- Format: `ruff format .`
- Lint: `ruff check --fix .`
- Types: `mypy --strict app tests`
- Tests: `pytest` (or `pytest tests/unit`, `pytest tests/integration`)
- Coverage: `coverage run -m pytest && coverage report`
- Full sweep: `pre-commit run --all-files`
- Regenerate requirements lockstep by editing pins here (no automation yet).

## Tips for New Contributors
- Read related interfaces before changing a service; implementations live alongside their protocol.
- Favor extending tool modules or service methods over embedding logic in agents.
- When adding data, run the app once to trigger startup validation—failures surface immediately.
- Keep SSE payloads small: reuse models in `app/api/schemas` and `app/models/instances`.
- Tests expect deterministic dice—use the dice service helpers instead of `random`.
- Commit generated content packs separately so reviews stay focused on code.

## Reference APIs
- Base path: `/api`
- Game lifecycle: `/game/new`, `/game/{game_id}`, `/game/{game_id}/action`, `/game/{game_id}/sse`
- Catalog endpoints: `/scenarios`, `/characters`, `/catalogs/*`, `/content-packs/*`
- Health: `/health`

## When In Doubt
Consult `app/services` + `app/tools` for the canonical behavior, run mypy and pytest locally, and prefer deleting or rewriting legacy code over layering patches.
