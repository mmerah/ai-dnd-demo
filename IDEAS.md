# MVP 1

Full D&D 5e functionality with scenario management, character management, functional combat, quest, inventory with only the Narrative agent

## Ideas

1. Review all fail fast (no fallback !)
2. Constructors should not have | None stuff.
3. Analyze all hasattr and similar pattern
4. Review all # type: ignore and replace them with best possible fix
5. Complete the D&D foundation: Subraces, Subclasses are missing. Ideally look in something like https://github.com/5e-bits/5e-database for reference. That means all 27 type of stuff need to be in with correct format. Conditions, attack types, ability-scores, alignments, backgrounds, ... all become database content. DataService would become much bigger as well.
6. Review scenarios, acts, quests, location, npcs (game state does seem to properly populate the npcs of the area for example), and how game state and tools handle every possible case. Review the models to ensure no duplicates and clean/clear models. Avoid having optional stuff
7. Handle all the TODO comments in the code
8. ContextService should just be the GameState + current Scenario ? Maybe a curated version but that would make ContextService MUCH easier to handle and scale
9.  Vulture, verify no TYPE_CHECKING, verify unused (including methods)
10. Cleanup logger calls to minimum
11. Review manually the code
12. Re-organize the code ? (cut routes, review models, services all dependency inversion, ...), interfaces for services structured the same as app/services/...
13. Update CLAUDE.md
14. Content pack management ? data/ contain scenarios, characters, SRD monsters/items/spells/classes/conditions/backgrounds/... But users can create new content packs ? Sandbox content pack gives AI ability to create on-the-fly, users can create custom packs, scenario are by default SRD. You can create sandbox, with SRD+custom_pack+sandbox, ... ?
15. Add pre-commit
16. Add unit-tests ? Or rather in MVP2 for faster iteration for now ?

# MVP 2

Refine functionality of MVP 1. Integrate the multi-agent system and the dynamic memory system

## Ideas

1. Frontend should use typescript with ban of 'any'. Or flutter ? How to use our models directly in the frontend to help type safety ?
2. Creator Agents: CharacterCreator and ScenarioCreator. Character is easy, needs 1 tool to populate a CharacterSheet, would just need to pose a series of questions and have all possibilities of races/subraces/classes/subclasses/spells/... in its system prompt. At the end it would call the tool. Scenario is more complicated, it requires creating monsters, npcs, quests, items, locations and fill it all out correctly
3. Agents: that can operate on the game state: Narrative, Combat, Level-Up. The Level-Up agent would need to handle D&D 5e progression tables for each class, including: adding new spell slot levels when appropriate (e.g., Rangers get 2nd level slots at level 5), increasing existing spell slot counts, learning new spells based on class rules, updating derived stats like proficiency bonus and spell save DC, and rolling for HP increases. The current spell slot system supports dynamic addition of new levels but needs methods to manipulate slots during level-up.
4. Agents: Not on the game state, technically on the conversation history ?: Summarizer is special because it can happen in the background -> But that means we need to add metadata for each conversation history message (location ? NPC interaction with ?). This links to a memory system. NPC have memory, location have memory, ...
5.  Characters template ? Scenario Template ? Separated from instances ? Same as ai-gamemaster. Save is a lot more complicated than it seems. Probably need a folder/subfolder to put in memory, and specificities
6.  Frontend: ASCII map of the location and connection ? (frontend)
7.  Scenario: If wandering outside of the defined scenario, should enter some sandbox mode. Means ability to create quests, NPCs, ... on-the-fly. Sandbox about items, spells, monsters/NPCs ? Could scenario be customized by AI during play ? Any data that does not exists could be created by an agent and linked with the save ?
8.  Ability to play with a party of NPCs
9.  Custom save names
