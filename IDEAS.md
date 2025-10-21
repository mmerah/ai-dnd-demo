## Current Issues [CRITICAL]

- Context Builders: current state builder make no sense. Builders need to understand what/who/how things are called. current state builder need to add party information, renamed probably to party overview builder or something. Then need to think: NPC agents use that context builder but while for party npc it make sense, for non-party npcs it make no sense to have that in the context. How to solve such issues ? Need to review context builders 1 by 1, make them more token efficient, clear data, associate with the relevant agents as well. The background context builder is also affected (and could be renamed background_builder like others no?). Need to see in all context builder if they manually take the character (would it then make sense to make them configurable with either returning context for the party, or for an npc instance ? Then we have the differentiation ?)

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Issues

1. PartyState should contain the character instance. Removes character instance from the game state. That removes combat service ensure player in combat and any such occurance throughout the code where now we would interact directly with the party.
2. Read docs/FUTURE-AGENTS.md. We might need very early an agent that can improve tool usage. Basically a tool usage suggestor ? Or something of that nature. One example is if I interact with an NPC using @npc-name then, tool calling is very inconsistent. Need a more general tool call verifier ?

## Ideas

### Frontend
1. Frontend should use typescript with ban of 'any'. Or flutter ? How to use our models directly in the frontend to help type safety ?
2. Frontend: ASCII map of the location and connection ? (frontend)
3. Character Sheet on the side of game view should be a level deeper. Basically leave general game information on side (location, quests, combat element when active, ...) and have a party screen with summarized cards for each member of the party. When you click on a member then you get his details as we do get right now (stats, skills, inventory, spells, ...)

### Backend
1. Refine the concept of the dynamic memory system. NPCs, Locations have memory ? How/When to store memory ? How/When to load memory ?
2. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
3. Agents: that can operate on the game state: Narrative, Combat, Level-Up. The Level-Up agent would need to handle D&D 5e progression tables for each class, including: adding new spell slot levels when appropriate (e.g., Rangers get 2nd level slots at level 5), increasing existing spell slot counts, learning new spells based on class rules, updating derived stats like proficiency bonus and spell save DC, and rolling for HP increases. The current spell slot system supports dynamic addition of new levels but needs methods to manipulate slots during level-up.
4. Agents: Not on the game state, technically on the conversation history ?: Summarizer is special because it can happen in the background -> But that means we need to add metadata for each conversation history message (location ? NPC interaction with ?). This links to a memory system. NPC have memory, location have memory, ...
5.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode. Means ability to create quests, NPCs, ... on-the-fly. Sandbox about items, spells, monsters/NPCs ? Could scenario be customized by AI during play ? Any data that does not exists could be created by an agent and linked with the save ?
6. Combat needs to be clearer who is part of what "team" (player party, neutral, enemy).
7.  Ability to play with a party of NPCs. Combat system also needs to be able to support NPCs in the player's party or out the player's party. AgentNPC: If not in party, give the narrative agent the ability to start conversations with 1 or more NPCs. If in party, then the AgentNPC can asynchronously make suggestions to the player during narrative and during combat, when it is its turn it makes a decision (similar to when its player turn we wait for input from the frontend for player action)
8. Custom save names
9. NPCs are not known at first
10. Random encounters: Load and use random encounters from scenarios for variety
11. SSE events utility review: Audit frontend usage of SSE events and remove unused ones
12. NPC population optimization: Currently all NPCs are loaded at game start - consider lazy loading based on location
13. TODO(MVP2): Solve all those todos
14. Review completely all system prompts for the agents (narrative should only describe what is going on in engaging way, never embodies NPCs. Combat should be OK, maybe more example of full tool call turns. NPC agent system prompt + context + prompt should be reviewed)