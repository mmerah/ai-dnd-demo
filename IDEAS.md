## Current Issues [CRITICAL]

- Context building (where it happens) is a mess. It would be nice to refactor that so that it is as clear as possible to see what is going on and for developers to use. It would be fantastic that we could have a config file for it
- Context service: List of attacks/spells in combat shown for the NPC / Player (Combat agent for party, NPC agent for npc itself + party state ?)
- Spell need description
- Ally action, frontend is not "busy"
- CLAUDE.md : Update with new system once finished, tested, validated
- Put model in the .json configs instead of .env ?
- Message response of next_turn should say stop and generate a narrative, subsequence next_turn will be refused until a narrative is generated.
- system that reject duplicate next_turn until a narrative is generated ?
- Agents in combat are very unreliable. Feels like tool calling might not be it for such a system. Structured output might be the only way ? But replicating all that we have available in tools seems huge but it would be interesting to tests. Alternative would be separate a tool-calling agent. Agent only generate a narrative and the ToolCallAgent generate the tool calls for that ?

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Issues

1. Act can progress after a quest is completed. However, no active quest is activated.
2. Use and try exacto models

## Ideas

### Frontend
1. Frontend should use typescript with ban of 'any'. Or flutter ? How to use our models directly in the frontend to help type safety ? Better code architecture/modularity of the frontend. Still a "demo" frontend, no need to push too much
2. Frontend: ASCII map of the location and connection ? (frontend)

### Backend
1. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
2. Agents: that can operate on the game state: Narrative, Combat, Level-Up. The Level-Up agent would need to handle D&D 5e progression tables for each class, including: adding new spell slot levels when appropriate (e.g., Rangers get 2nd level slots at level 5), increasing existing spell slot counts, learning new spells based on class rules, updating derived stats like proficiency bonus and spell save DC, and rolling for HP increases. The current spell slot system supports dynamic addition of new levels but needs methods to manipulate slots during level-up.
3.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode. Means ability to create quests, NPCs, ... on-the-fly. Sandbox about items, spells, monsters/NPCs ? Could scenario be customized by AI during play ? Any data that does not exists could be created by an agent and linked with the save ?
4. Refinement of the dynamic memory system (metadata tags of conversation, who/when/how memory saved, who/when/how memory loaded, is there better memory that can be created ?)
5. Combat needs to be clearer who is part of what "team" (player party, neutral, enemy).
6. AgentNPC: If not in party, give the narrative agent the ability to start conversations with 1 or more NPCs. If in party, then the AgentNPC can asynchronously make suggestions to the player during narrative and during combat, when it is its turn it makes a decision (similar to when its player turn we wait for input from the frontend for player action)
7. Custom save names
8. NPCs are not known at first
9. Random encounters: Load and use random encounters from scenarios for variety
10. SSE events utility review: Audit frontend usage of SSE events and remove unused ones
11. NPC population optimization: Currently all NPCs are loaded at game start - consider lazy loading based on location
12. TODO(MVP2): Solve all those todos
13. Review completely all system prompts for the agents (narrative should only describe what is going on in engaging way, never embodies NPCs. Combat should be OK, maybe more example of full tool call turns. NPC agent system prompt + context + prompt should be reviewed)
14. Voice Generation for each agent/NPC
15. Contextual Image Generation for the location
16. Portrait Generation for the NPCs and Monsters ?
17. ToolSuggestionAgent/Heuristics use more stuff to suggest tools. Example is matching of quest elements with the prompt, or inventory with the prompt, or location with the prompt ?
