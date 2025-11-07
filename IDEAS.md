## Current Issues [CRITICAL]

- Review frontend for SOLID, KISS, DRY, clean architecture, modular with GPT-5-codex and gemini (fix with claude)
- Review frontend for "workability", no method with more than 100 lines, core behavior unit tested, no file with more than 500 lines
- Review frontend for "style": macos, minimal, modern, D&D/fantasy styling. More unified throughout the frontend (right now is inconsistent)
- Delete any unused .md, make sure frontend/README.md is good, link it to its own CLAUDE.md. Delete old frontend. Update main CLAUDE.md
- Ally action, frontend is not "busy" (thus player feels like it can send stuff)
- Put model in the .json configs instead of .env ?
- Agents in combat are very unreliable. Feels like tool calling might not be it for such a system. Structured output might be the only way ? But replicating all that we have available in tools seems huge but it would be interesting to tests. Alternative would be separate a tool-calling agent. Agent only generate a narrative + description of what it wants to do in D&D terms (roll dice -> apply dmg, validate a quest, ...) and the ToolCallAgent generate the tool calls for that ?
- Integrate claude skills superpowers (the one with a bunch of dev-stuff). Look through what others are using.
- Encounters not clearing/completing after end_combat ? Thus no memory entry for it ?

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Ideas

### Frontend
1. Frontend should use typescript with ban of 'any'. Or flutter ? How to use our models directly in the frontend to help type safety ? Better code architecture/modularity of the frontend. Still a "demo" frontend, no need to push too much
2. Right panel: Party status, character details. Combat status
3. Frontend: ASCII map of the location and connection ? (frontend)
4. Frontend: More types in the catalog browser

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
17. ToolSuggestionAgent/Heuristics use more stuff to suggest tools. Example is matching of quest elements with the prompt, or inventory with the prompt, or location with the prompt ? Or spell with the prompt (useful during combat where it might give a thorough description ---> Or is that actually more or a XXXSuggestionAgent ? Or something else ? Or entirely Contextbuilder stuff ???? List prompt-aware context builders ????)
18. More feats. The same way we extended backgrounds
19. Review how instances get their stats/characteristics/proficiencies/... (e.g. sometimes I feel like the player has WAY too many proficiencies this is weird)
20. Locations connections have a "distance/time" between them -> Automatically make time advance when moving locations !!!
