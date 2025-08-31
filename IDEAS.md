# MVP 1

Full D&D 5e functionality with scenario management, character management, functional combat, quest, inventory with only the Narrative agent

## Ideas

1. data/ and saves/ need better organization to avoid thousand lines files. Scenarios should be put in data/scenarios/. Then a folder with the name of the scenario. Same for characters instead of having all characters in 1 json file. For items, spells, monsters it is fine. saves/ also need somehow to be cut correctly. A save has a name which is a folder. Then it should be separated into the character of the save, then separation into things that make sense ? (think about it, if we want a memory system in the future that might make sense)
2. Review all fail fast (no fallback !)
3. Constructors should not have | None stuff.
4. Review all # type: ignore and replace them with best possible fix
5. Complete the D&D foundation: Subraces, Subclasses are missing. Ideally look in something like https://github.com/5e-bits/5e-database for reference. That means all 27 type of stuff need to be in with correct format. Conditions, attack types, ability-scores, alignments, backgrounds, ... all become database content. DataService would become much bigger as well.
6. Review scenarios, acts, quests, location, npcs (game state does seem to properly populate the npcs of the area for example), and how game state and tools handle every possible case
7. Handle all the TODO comments in the code
8. ContextService should just be the GameState + current Scenario ? Maybe a curated version but that would make ContextService MUCH easier to handle and scale
9.  Vulture, verify no TYPE_CHECKING, verify unused (including methods)
10. Cleanup logger calls to minimum
11. Review manually the code
12. Re-organize the code ? (cut routes, review models, services all dependency inversion, ...), interfaces for services structured the same as app/services/...

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Ideas

1. Frontend should use typescript with ban of 'any'. Or flutter ? How to use our models directly in the frontend to help type safety ?
2. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
3. Agents: that can operate on the game state: Narrative, Combat, Level-Up. The Level-Up agent would need to handle D&D 5e progression tables for each class, including: adding new spell slot levels when appropriate (e.g., Rangers get 2nd level slots at level 5), increasing existing spell slot counts, learning new spells based on class rules, updating derived stats like proficiency bonus and spell save DC, and rolling for HP increases. The current spell slot system supports dynamic addition of new levels but needs methods to manipulate slots during level-up.
4. Agents: Not on the game state, technically on the conversation history ?: Summarizer is special because it can happen in the background -> But that means we need to add metadata for each conversation history message (location ? NPC interaction with ?). This links to a memory system. NPC have memory, location have memory, ...
5.  Characters template ? Scenario Template ? Separated from instances ? Same as ai-gamemaster. Save is a lot more complicated than it seems. Probably need a folder/subfolder to put in memory, and specificities
6.  Frontend: ASCII map of the location and connection ? (frontend)
7.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode. Means ability to create quests, NPCs, ... on-the-fly
8.  Ability to play with a party of NPCs
9.  Custom save names
