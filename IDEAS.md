# MVP 1

Full D&D 5e functionality with scenario management, character management, functional combat, quest, inventory with only the Narrative agent

## Ideas

1. Save/Load game handling in the frontend. If it is correct in the backend
2. Scenario: Does not seem to be completely passed as context to the AI. Location handling, NPCs, ... A scenario need a LOT more data as it references monsters, items, NPCs. This means we need to expand the content in app/data/ considerably. Then make a scenario reference the content of data. Then if scenario is passed correctly with its references as context to the AI (depending on location, location has connection to other locations, refers events/quests/monsters/checks/npcs/items/...). Need tools let AI handle all that stuff.
3. Linked the database of stuff in app/data/ to the inventory/spells. Same to the frontend
4. Frontend upgrades: Location information, current scenario, quest logs, more info on spells/items, 

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Ideas

1. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
2. Agents: that can operate on the game state: Narrative, Combat, Level-Up
3. Agents: Not on the game state, technically on the conversation history ?: Summarizer is special because it can happen in the background -> But that means we need to add metadata for each conversation history message (location ? NPC interaction with ?). This links to a memory system. NPC have memory, location have memory, ...
4.  Characters template ? Scenario Template ? Separated from instances ? Same as ai-gamemaster. Save is a lot more complicated than it seems. Probably need a folder/subfolder to put in memory, and specificities
5.  Frontend: ASCII map of the location and connection ? (frontend)
6.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode.
