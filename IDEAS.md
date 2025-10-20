## Current Issues [CRITICAL]

- Frontend: Added party member but new member does not show in the party list
- Frontend: Select party member in the list but no details is loaded for npc members
- Frontend: combat suggestion shows "Undefined's turn" as title with empty content. Using combat/suggestion/accept then I get 422 Unprocessable Entity.
- NPC agent in combat called with no context
- If I pick something else for ally turn, then I feel like the combat agent is rolling for the player character which is wrong. I did that, had a roll dice call tool and then another suggestion box appeared which should not be the case normally
- Upon starting the fight, NPC ally was first and the AI agent just called roll dice tool to attack instead of doing a combat suggestion. I think we need to make sure that the system prompt tells the AI exactly what to do in combat (which is suggestions)
- In an ideal world, in combat: [Move to NPC Ally turn] -> [Combat Agent is waiting for a prompt] -> [NPC Agent prompted to get a suggestion] -> [suggestion shown to UI] -> [Player accept or refuse the suggestion] -> [action: suggestion or player override is given as a prompt to the combat agent] -> [combat agent does the necessary tool calls, if next_turn is not called then we have the usual prompt to tell it to call next_turn ?]

- equip does not work with party member. Used the button on the shield of party member. Tool called with 'shortsword' as if it used the off hand of the player character. Generally, tools are not made for party use I think
- quest completed -> act did not progress automatically -> quest log empty

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Issues

1. If I interact with an NPC using @npc-name then, certain tools are not called (like party, quest). Or at least, progression through quests/acts is very inconsistent. Need a progression agent ? or more general tool verifier ?????
2. PartyState should contain the character instance. Removes character instance from the game state. That removes combat service ensure player in combat and any such occurance throughout the code where now we would interact directly with the party.
3. Read docs/FUTURE-AGENTS.md. We might need very early an agent that can improve tool usage. Basically a tool usage suggestor ? Or something of that nature.
4. data/backgrounds.json SRD only has acolyte as an example. Not enough at all !

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