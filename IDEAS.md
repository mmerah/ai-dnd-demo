# MVP 1

Full D&D 5e functionality with scenario management, character management, functional combat, quest, inventory with only the Narrative agent

## Ideas

1. Character need a character_service.py similar to scenario_service.py (with validate_scenario_references equivalent) instead of being loaded from characters.json directly in routes
2. Frontend upgrades needed:
   - Display current location name and available connections/exits
   - Show quest log with active quests and objectives progress
   - Item/spell tooltips pulling descriptions from database
   - Location danger level indicator
   - Act/chapter display
   - Enhanced inventory with item descriptions on hover
   - Quest completion notifications 
3. data/ and saves/ need better organization to avoid thousand lines files. Scenarios should be put in data/scenarios/. Then a folder with the name of the scenario. Same for characters instead of having all characters in 1 json file. For items, spells, monsters it is fine. saves/ also need somehow to be cut correctly. A save has a name which is a folder. Then it should be separated into the character of the save, then separation into things that make sense
4. Characters should be loaded through the IDataService as well, same as spells, items, monsters. Scenarios as well ?
5. Complete the D&D foundation: Subraces, Subclasses are missing. Ideally look in something like https://github.com/5e-bits/5e-database for reference.
6. Handle all the TODO comments in the code
7. Cleanup logger calls to minimum
8. Review manually the code

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Ideas

1. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
2. Agents: that can operate on the game state: Narrative, Combat, Level-Up. The Level-Up agent would need to handle D&D 5e progression tables for each class, including: adding new spell slot levels when appropriate (e.g., Rangers get 2nd level slots at level 5), increasing existing spell slot counts, learning new spells based on class rules, updating derived stats like proficiency bonus and spell save DC, and rolling for HP increases. The current spell slot system supports dynamic addition of new levels but needs methods to manipulate slots during level-up.
3. Agents: Not on the game state, technically on the conversation history ?: Summarizer is special because it can happen in the background -> But that means we need to add metadata for each conversation history message (location ? NPC interaction with ?). This links to a memory system. NPC have memory, location have memory, ...
4.  Characters template ? Scenario Template ? Separated from instances ? Same as ai-gamemaster. Save is a lot more complicated than it seems. Probably need a folder/subfolder to put in memory, and specificities
5.  Frontend: ASCII map of the location and connection ? (frontend)
6.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode.
