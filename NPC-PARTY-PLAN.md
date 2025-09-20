# NPC Party System — Implementation Plan (Revised)

Aligns with CLAUDE.md: SOLID first, DRY, and fail-fast. Extends the app to support first-class NPC parties with major NPCs that follow the player, and with a player-confirmation flow for party NPC turns in combat.

Decisions applied
- Party size: 4 (configurable later).
- Eligible members: Major NPCs only (NPCSheet.importance == 'major').
- Follow rules: Party members always auto-follow the player between locations.
- Join/Leave flow: Natural-language; agents invoke tools.
- Consent: Agents request consent through dialogue; tools perform the change once consent is clear.
- Combat: On an allied NPC turn, the NPC agent proposes an action (suggestion). The system waits for the player to accept or choose another action. This preserves NPC agency and player control.

## Sequencing
- Do after the NPC Agent Extension (AGENT-EXTENSION-PLAN.md). We rely on: MessageRole.NPC, NPC_DIALOGUE SSE, dialogue_session state, AgentLifecycleService, NPC persona builders, and policy/guardrails.

## Goals
- Create a robust PartyState and PartyService to manage membership, capacity, and syncing.
- Ensure party members auto-follow the player between locations.
- Represent party NPCs as ALLIES in combat and stop auto-play for their turns.
- Add an NPC combat suggestion flow: NPC agent proposes, player confirms or overrides.
- Update UI to show party members and present suggestions in combat.

## Scope and Non‑Goals
- Scope: party membership, follow mechanics, combat factions, suggestion+confirmation flow, UI to display party and suggestions.
- Non‑Goals (now): formation/marching order, party role bonuses, deep consent enforcement beyond prompts, minor NPC party membership, pet/summon systems.

## Data Model
1) app/models/party.py (new)
   - class PartyState:
     - member_ids: list[str] = []  (NPCInstance.instance_id)
     - max_size: int = 4  (constant default; future setting)

2) app/models/game_state.py
   - Add: party: PartyState = Field(default_factory=PartyState)

3) app/models/combat.py
   - Add enum CombatFaction: PLAYER | ALLY | ENEMY | NEUTRAL
   - Extend CombatParticipant with: faction: CombatFaction (defaulted in service)

Fail-fast notes
- Exact types via Pydantic. Validate max_size >= 1.

## Interfaces & Services
1) app/interfaces/services/game_party.py (new)
   - IPartyService
     - add_member(game_state: GameState, npc_id: str) -> None
     - remove_member(game_state: GameState, npc_id: str) -> None
     - is_member(game_state: GameState, npc_id: str) -> bool
     - list_members(game_state: GameState) -> list[NPCInstance]
     - on_player_moved(game_state: GameState, to_location_id: str) -> list[BaseCommand]
       - Generate MoveNPCCommand follow-ups for all members not already at destination.
     - eligible_to_join(game_state: GameState, npc_id: str) -> bool  (major-only check)

2) app/services/game/party_service.py (new)
   - Enforce constraints: major-only, capacity=4, no duplicates, npc_id must exist.
   - DRY: uses LocationService via generated MoveNPCCommand; no direct movement.

3) app/interfaces/services/combat_suggestion.py (new)
   - ICombatSuggestionService
     - build_suggestion(game_state: GameState, npc_id: str) -> CombatSuggestion
       - Uses NPC agent (IndividualMindAgent) to propose action(s) without executing tools.

4) app/services/game/combat_suggestion_service.py (new)
   - Builds a compact structured suggestion for an allied NPC’s turn.
   - Pulls persona + combat context via ContextService builders (NPCPersona + Combat builders).
   - Produces a pydantic model CombatSuggestion with:
     - suggestion_id: str (for acceptance)
     - npc_id, npc_name
     - summary: str (1–2 lines)
     - proposed_actions: list[ProposedAction] where ProposedAction = { tool_name: str, arguments: dict[str, JSONSerializable] }
   - Fail-fast: if agent fails to produce a structured plan, fall back to a short textual summary and treat acceptance as a no-op (player must issue manual instruction).

## Events & Commands
1) app/events/commands/party_commands.py (new)
   - AddPartyMemberCommand(npc_id: str)
   - RemovePartyMemberCommand(npc_id: str)

2) app/events/handlers/party_handler.py (new)
   - Validates and applies add/remove via PartyService.
   - BroadcastGameUpdate on change.

3) Container wiring
   - container.party_service (cached_property)
   - event_bus.register_handler("party", PartyHandler(self.party_service))

4) Handler integrations
   - LocationHandler(ChangeLocationCommand): append follow-up MoveNPCCommand’s from PartyService.on_player_moved after successful player move.
   - CombatHandler(StartCombat/StartEncounter): add party members at current location as participants (faction=ALLY), skip duplicates.

## Tools & Guardrails
1) app/tools/party_tools.py (new)
   - add_party_member(npc_id: str) → AddPartyMemberCommand
   - remove_party_member(npc_id: str) → RemovePartyMemberCommand
   - Policy:
     - Narrative agent uses add/remove based on dialogue consent.
     - NPC agent can call self_join/self_leave in a later phase; initially blocked.
     - During combat, add/remove are blocked (tool decorator policy).

2) Consent model
   - Keep consent in prompts/agent reasoning; server enforces major-only + capacity.
   - If needed later, we can verify consent via dialogue_session state or a transient flag.

## Combat Integration (Suggestion + Confirmation)
1) Factions
   - CombatService.add_participant infers faction:
     - CharacterInstance → PLAYER
     - NPCInstance in PartyState.member_ids → ALLY
     - MonsterInstance → ENEMY
     - Else → NEUTRAL
   - should_auto_end_combat considers only ENEMY participants as enemies.

2) Stop auto-play for allied NPC turns
   - Adjust ICombatService.should_auto_continue to return False when current turn is faction == ALLY.
   - Keeps existing behavior for ENEMY NPCs/Monsters.

3) Suggestion generation
   - Orchestrator: when combat is active and current turn is ALLY NPC, obtain NPC agent via AgentLifecycleService and call CombatSuggestionService.build_suggestion.
   - Broadcast suggestion via SSE (see SSE section) and do NOT run the combat agent automatically.

4) Player confirmation path
   - Accept suggestion:
     - API executes proposed_actions sequentially via ActionService (tool_name + arguments), then issues NextTurnCommand.
     - On errors, fail-fast and broadcast error; do not advance turn.
   - Manual override:
     - Player sends a chat instruction; orchestrator routes to CombatAgent which executes tools and calls NextTurn.

## SSE & API
1) app/models/sse_events.py
   - Add SSEEventType.COMBAT_SUGGESTION
   - CombatSuggestionData: { suggestion_id, npc_id, npc_name, summary, proposed_actions }

2) app/services/ai/message_service.py
   - send_combat_suggestion(game_id: str, suggestion: CombatSuggestion)

3) API endpoints
   - POST /api/game/{game_id}/combat/suggestions/{suggestion_id}/accept
     - Body optional; executes proposed_actions in order, persists and broadcasts GAME_UPDATE, remains fail-fast.
   - POST /api/game/{game_id}/combat/suggestions/{suggestion_id}/reject (optional)
     - No-op server-side; the player can provide manual instruction via chat.

## Frontend
1) Party panel
   - Add “Party” section (left column) showing member names, HP/AC, conditions.
   - Data sourced from GameState.npcs filtered by GameState.party.member_ids.

2) Combat suggestions UI
   - In Combat section, render COMBAT_SUGGESTION with npc avatar/name, summary, and buttons:
     - “Use suggestion” → accept API
     - “Edit as message” → prefill chat input with a short instruction derived from the summary
   - If rejected or edited, the next chat message routes to CombatAgent for manual execution.

## Persistence
- PartyState included in GameState metadata via SaveManager (no layout changes required).
- Suggestions are transient (no persistence); tool executions remain in GameEvents and conversation history.

## Failure Handling
- PartyService.add_member: raises on non‑major, capacity reached, dup, or unknown id.
- Movement follow-ups only generated after a successful ChangeLocationCommand; invalid locations fail earlier in LocationService.
- Suggestion acceptance: if any proposed action fails, stop and surface error; do not advance turn.

## Testing
- Unit
  - PartyService: add/remove validations, list_members, on_player_moved follow-ups.
  - CombatService: faction inference, should_auto_end_combat ignores ALLY, should_auto_continue returns False for ALLY turns.
  - CombatSuggestionService: returns structured suggestion (mock NPC agent); fallback on failure.
- Integration
  - LocationHandler: change location enqueues MoveNPCCommand’s for all party members.
  - Combat start: party ALLY participants added; no duplicates.
  - Orchestrator: on ALLY turn, emits COMBAT_SUGGESTION and does not auto-run.
  - API: accept suggestion executes tools in sequence and advances turn.
  - Frontend: party panel renders; suggestion UI shows and buttons wire to endpoints.

## Step-by-Step Implementation
1) Models
   - Add app/models/party.py
   - Add party: PartyState to app/models/game_state.py
   - Add CombatFaction enum + participant.faction to app/models/combat.py

2) Services & Interfaces
   - Add IPartyService and PartyService with validations and follow-up generation.
   - Add ICombatSuggestionService and CombatSuggestionService (agent-backed, structured output).

3) Event Bus
   - Add Party commands and PartyHandler.
   - Wire handler and service in container.
   - Integrate PartyService with LocationHandler and CombatHandler as described.

4) Tools & Policy
   - Add party_tools.py; wire via NarrativeAgent tool list.
   - Extend tool decorator policy to block party changes during combat and to block NPC agents from add/remove initially.

5) Orchestrator & Combat
   - Update ICombatService.should_auto_continue for ALLY turns.
   - Add orchestrator hook to produce suggestions for ALLY turns using CombatSuggestionService + NPC agent.
   - Broadcast COMBAT_SUGGESTION via MessageService.

6) SSE & API
   - Add COMBAT_SUGGESTION event + send_combat_suggestion.
   - Add accept (and optional reject) endpoints.

7) Frontend
   - Render party list in left panel.
   - Render combat suggestion panel with Accept/Edit controls.

8) Tests & Docs
   - Add tests above; update README and docs with party behavior and combat suggestion flow.

## Notes on SOLID/DRY/Fail‑Fast
- SOLID: new capabilities behind IPartyService and ICombatSuggestionService; orchestrator composes services; handlers remain thin.
- DRY: movement via LocationService commands; no duplicated persistence; shared MessageService for new SSE type.
- Fail‑Fast: strict validations on membership actions, explicit policy gating for tools, immediate error surfacing on suggestion acceptance failures.

