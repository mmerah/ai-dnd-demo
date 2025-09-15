// State management
let gameState = null;
let currentGameId = null;
let selectedCharacter = null;
let selectedScenario = null;
let selectedContentPacks = []; // Track selected content packs
let sseSource = null;
let isProcessing = false; // Track if agent is processing

// DOM elements - cached for performance
const elements = {};

// Catalog caches (index -> display name for simple catalogs, full data for complex ones)
const catalogs = {
    classes: {},
    subclasses: {},
    alignments: {},
    magic_schools: {},
    races: {},
    race_subraces: {},
    languages: {},
    backgrounds: {},
    features: {},
    feats: {},
    skills: {},
    weapon_properties: {},
    damage_types: {},
    conditions: {},
    monsters: [],  // Full monster data
    items: [],     // Full item data
    spells: [],    // Full spell data
};

async function loadCatalogs() {
    try {
        const [classesRes, subclassesRes, alignsRes, schoolsRes, racesRes, languagesRes, backgroundsRes, featuresRes, featsRes, skillsRes, wpropsRes, dtypesRes, subracesRes, conditionsRes, traitsRes, monstersRes, itemsRes, spellsRes] = await Promise.all([
            fetch('/api/catalogs/classes'),
            fetch('/api/catalogs/subclasses'),
            fetch('/api/catalogs/alignments'),
            fetch('/api/catalogs/magic_schools'),
            fetch('/api/catalogs/races'),
            fetch('/api/catalogs/languages'),
            fetch('/api/catalogs/backgrounds'),
            fetch('/api/catalogs/features'),
            fetch('/api/catalogs/feats'),
            fetch('/api/catalogs/skills'),
            fetch('/api/catalogs/weapon_properties').catch(() => ({ ok: false })),
            fetch('/api/catalogs/damage_types').catch(() => ({ ok: false })),
            fetch('/api/catalogs/race_subraces'),
            fetch('/api/catalogs/conditions'),
            fetch('/api/catalogs/traits').catch(() => ({ ok: false })),
            fetch('/api/catalogs/monsters').catch(() => ({ ok: false })),
            fetch('/api/catalogs/items').catch(() => ({ ok: false })),
            fetch('/api/catalogs/spells').catch(() => ({ ok: false })),
        ]);

        const [classes, subclasses, alignments, schools, races, languages, backgrounds, features, feats, skills, wprops, dtypes, subraces, conditions, traits, monsters, items, spells] = await Promise.all([
            classesRes.ok ? classesRes.json() : [],
            subclassesRes.ok ? subclassesRes.json() : [],
            alignsRes.ok ? alignsRes.json() : [],
            schoolsRes.ok ? schoolsRes.json() : [],
            racesRes.ok ? racesRes.json() : [],
            languagesRes.ok ? languagesRes.json() : [],
            backgroundsRes.ok ? backgroundsRes.json() : [],
            featuresRes.ok ? featuresRes.json() : [],
            featsRes.ok ? featsRes.json() : [],
            skillsRes.ok ? skillsRes.json() : [],
            wpropsRes.ok ? wpropsRes.json() : [],
            dtypesRes.ok ? dtypesRes.json() : [],
            subracesRes.ok ? subracesRes.json() : [],
            conditionsRes.ok ? conditionsRes.json() : [],
            traitsRes.ok ? traitsRes.json() : [],
            monstersRes.ok ? monstersRes.json() : [],
            itemsRes.ok ? itemsRes.json() : [],
            spellsRes.ok ? spellsRes.json() : [],
        ]);

        catalogs.classes = Object.fromEntries(classes.map(c => [c.index, c.name]));
        catalogs.subclasses = Object.fromEntries(subclasses.map(sc => [sc.index, sc.name]));
        catalogs.alignments = Object.fromEntries(alignments.map(a => [a.index, a.name]));
        catalogs.magic_schools = Object.fromEntries(schools.map(s => [s.index, s.name]));
        catalogs.races = Object.fromEntries(races.map(r => [r.index, r.name]));
        catalogs.languages = Object.fromEntries(languages.map(l => [l.index, l.name]));
        catalogs.backgrounds = Object.fromEntries(backgrounds.map(b => [b.index, b.name]));
        catalogs.features = Object.fromEntries((features || []).map(f => [f.index, f.name]));
        catalogs.feats = Object.fromEntries((feats || []).map(f => [f.index, f.name]));
        catalogs.skills = Object.fromEntries((skills || []).map(s => [s.index, s.name]));
        catalogs.weapon_properties = Object.fromEntries((wprops || []).map(w => [w.index, w.name]));
        catalogs.damage_types = Object.fromEntries((dtypes || []).map(d => [d.index, d.name]));
        catalogs.race_subraces = Object.fromEntries((subraces || []).map(sr => [sr.index, sr.name]));
        catalogs.conditions = Object.fromEntries((conditions || []).map(c => [c.index, c.name]));
        catalogs.traits = Object.fromEntries((traits || []).map(t => [t.index, t.name]));
        
        // Store full data for complex catalogs
        catalogs.monsters = monsters || [];
        catalogs.items = items || [];
        catalogs.spells = spells || [];

        // expose globally
        window.catalogs = catalogs;
        window.catalogData = {
            classes, subclasses, alignments, schools, races, languages, backgrounds, features, feats, skills, wprops, dtypes, subraces, conditions, traits, monsters, items, spells
        };

        console.log('[CATALOGS] Loaded', { 
            classes: Object.keys(catalogs.classes).length,
            subclasses: Object.keys(catalogs.subclasses).length,
            alignments: Object.keys(catalogs.alignments).length,
            magic_schools: Object.keys(catalogs.magic_schools).length,
            races: Object.keys(catalogs.races).length,
            languages: Object.keys(catalogs.languages || {}).length,
            backgrounds: Object.keys(catalogs.backgrounds || {}).length,
            features: Object.keys(catalogs.features || {}).length,
            feats: Object.keys(catalogs.feats || {}).length,
            skills: Object.keys(catalogs.skills || {}).length,
            weapon_properties: Object.keys(catalogs.weapon_properties || {}).length,
            damage_types: Object.keys(catalogs.damage_types || {}).length,
            conditions: Object.keys(catalogs.conditions || {}).length,
            subraces: Object.keys(catalogs.race_subraces || {}).length,
            traits: Object.keys(catalogs.traits || {}).length,
            monsters: catalogs.monsters.length,
            items: catalogs.items.length,
            spells: catalogs.spells.length,
        });
    } catch (e) {
        console.warn('[CATALOGS] Failed to load one or more catalogs', e);
    }
}

// Initialize DOM element cache
function initializeElements() {
    console.log('[INIT] Caching DOM elements...');
    elements.characterSelection = document.getElementById('characterSelection');
    elements.gameInterface = document.getElementById('gameInterface');
    elements.characterList = document.getElementById('characterList');
    elements.scenarioList = document.getElementById('scenarioList');
    elements.startGameBtn = document.getElementById('startGame');
    elements.saveGameBtn = document.getElementById('saveGame');
    elements.chatMessages = document.getElementById('chatMessages');
    elements.messageInput = document.getElementById('messageInput');
    elements.sendMessageBtn = document.getElementById('sendMessage');
    elements.contentPackSection = document.getElementById('contentPackSection');
    elements.contentPackList = document.getElementById('contentPackList');
    
    // Log any missing elements
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            console.error(`[ERROR] Missing DOM element: ${key}`);
        }
    }
    console.log('[INIT] DOM elements cached successfully');
}

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[APP] Starting D&D 5e AI Dungeon Master frontend...');
    
    initializeElements();
    await loadCatalogs();
    await Promise.all([loadSavedGames(), loadCharacters(), loadScenarios(), loadContentPacks()]);
    setupEventListeners();
    // Home button to open full Catalogs screen
    const openCatalogsHomeBtn = document.getElementById('openCatalogsHome');
    if (openCatalogsHomeBtn) {
        openCatalogsHomeBtn.addEventListener('click', () => {
            window.catalogBackTarget = 'home';
            showCatalogsScreen('monsters');
        });
    }
    
    // If hash requests catalogs, open the catalogs screen
    if (window.location.hash === '#catalogs') {
        window.catalogBackTarget = 'home';
        showCatalogsScreen('monsters');
    }

    console.log('[APP] Frontend initialization complete');
});

// Event Listeners
function setupEventListeners() {
    console.log('[INIT] Setting up event listeners...');
    
    elements.startGameBtn.addEventListener('click', startGame);
    elements.sendMessageBtn.addEventListener('click', sendMessage);
    
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Collapsible sections
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.parentElement;
            section.classList.toggle('collapsed');
            console.log(`[UI] Toggled section: ${header.textContent.trim()}`);
        });
    });
    
    // Save game button
    elements.saveGameBtn.addEventListener('click', saveGame);
    
    
    console.log('[INIT] Event listeners setup complete');
}

// Load saved games
async function loadSavedGames() {
    console.log('[API] Loading saved games...');
    
    const savedGamesSection = document.getElementById('savedGamesSection');
    const savedGamesList = document.getElementById('savedGamesList');
    
    if (!savedGamesList) {
        console.error('[ERROR] savedGamesList element not found');
        return;
    }
    
    savedGamesList.innerHTML = '<div style="color: #888;">Loading saved games...</div>';
    
    try {
        const response = await fetch('/api/games');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const savedGames = await response.json();
        console.log(`[API] Loaded ${savedGames.length} saved games:`, savedGames);
        
        savedGamesList.innerHTML = '';
        
        if (savedGames && savedGames.length > 0) {
            savedGamesSection.style.display = 'block';
            
            savedGames.forEach(game => {
                const card = createSavedGameCard(game);
                savedGamesList.appendChild(card);
            });
        } else {
            savedGamesSection.style.display = 'none';
            console.log('[UI] No saved games found, hiding section');
        }
    } catch (error) {
        console.error('[ERROR] Failed to load saved games:', error);
        savedGamesList.innerHTML = `<div style="color: #666;">No saved games available</div>`;
        savedGamesSection.style.display = 'none';
    }
}

// Create saved game card element
function displayClassName(classIndex) {
    return catalogs.classes[classIndex] || (classIndex ? (classIndex.charAt(0).toUpperCase() + classIndex.slice(1)) : '');
}

function displayRaceName(raceIndex) {
    if (!raceIndex) return '';
    return catalogs.races[raceIndex] || raceIndex.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
}

function displayBackgroundName(bgIndex) {
    if (!bgIndex) return '';
    return catalogs.backgrounds[bgIndex] || bgIndex.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
}

function createSavedGameCard(game) {
    const card = document.createElement('div');
    card.className = 'saved-game-card';
    
    // Format the last saved date
    const lastPlayed = new Date(game.last_saved);
    const now = new Date();
    const timeDiff = now - lastPlayed;
    const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));
    const daysAgo = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
    
    let timeText = '';
    if (daysAgo > 0) {
        timeText = `${daysAgo} day${daysAgo > 1 ? 's' : ''} ago`;
    } else if (hoursAgo > 0) {
        timeText = `${hoursAgo} hour${hoursAgo > 1 ? 's' : ''} ago`;
    } else {
        timeText = 'Recently';
    }
    
    // Get the title to display - prefer scenario_title, fallback to character name
    const title = game.scenario_title || `${game.character.sheet?.name || 'Unknown Hero'}'s Adventure`;
    const classDisplay = displayClassName(game.character.sheet?.class_index);
    
    card.innerHTML = `
        <div class="saved-game-info">
            <h3>${title}</h3>
            <p class="character">🧝 ${game.character.sheet?.name} - Level ${game.character.state?.level} ${classDisplay}</p>
            <p class="location">📍 ${game.location}</p>
            <p class="time-ago">⏰ ${timeText}</p>
        </div>
        <div class="saved-game-actions">
            <button class="btn-continue" data-game-id="${game.game_id}">Continue</button>
        </div>
    `;
    
    // Add event listener for continue button
    const continueBtn = card.querySelector('.btn-continue');
    continueBtn.addEventListener('click', () => continueGame(game.game_id));
    
    return card;
}

// Continue a saved game
async function continueGame(gameId) {
    console.log(`[GAME] Continuing game: ${gameId}`);
    
    try {
        // First, resume the game on the backend
        const resumeResponse = await fetch(`/api/game/${gameId}/resume`, {
            method: 'POST'
        });
        
        if (!resumeResponse.ok) {
            throw new Error(`Failed to resume game: ${resumeResponse.status}`);
        }
        
        // Set the current game ID
        currentGameId = gameId;
        
        // Load the game state
        await loadGameState();
        
        // Clear chat and populate with conversation history
        elements.chatMessages.innerHTML = '';
        if (gameState && gameState.conversation_history) {
            console.log(`[GAME] Loading ${gameState.conversation_history.length} messages from history`);
            gameState.conversation_history.forEach(msg => {
                if (msg.role === 'player') {
                    addMessage(msg.content, 'player');
                } else if (msg.role === 'dm') {
                    // Check if it's a system message (auto-combat, summary, or system messages)
                    if (msg.content.startsWith('[Auto Combat:') || 
                        msg.content.startsWith('[Combat System:') || 
                        msg.content.startsWith('[Summary:') ||
                        msg.content.startsWith('[System:')) {
                        addMessage(msg.content, 'system');
                    } else {
                        addMessage(msg.content, 'dm');
                    }
                }
            });
        }
        
        // Initialize SSE connection (set flag to not show initial narrative)
        window.skipInitialNarrative = true;
        initializeSSE();
        
        // Switch to game interface
        elements.characterSelection.classList.add('hidden');
        elements.gameInterface.classList.remove('hidden');
        
        console.log('[GAME] Game resumed successfully');
        
        // Add a message indicating the game was loaded
        addMessage('Game loaded successfully. Continue your adventure!', 'system');
        
    } catch (error) {
        console.error('[ERROR] Failed to continue game:', error);
        showError('Failed to load saved game. Please try again.');
    }
}

// Load available scenarios
async function loadScenarios() {
    console.log('[API] Loading scenarios...');
    
    if (!elements.scenarioList) {
        console.error('[ERROR] scenarioList element not found');
        return;
    }
    
    elements.scenarioList.innerHTML = '<div style="color: #888;">Loading scenarios...</div>';
    
    try {
        const response = await fetch('/api/scenarios');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const scenarios = await response.json();
        console.log(`[API] Loaded ${scenarios.length} scenarios:`, scenarios);
        
        elements.scenarioList.innerHTML = '';
        
        if (scenarios && scenarios.length > 0) {
            scenarios.forEach(scenario => {
                const card = createScenarioCard(scenario);
                elements.scenarioList.appendChild(card);
            });
            
            // Auto-select first scenario
            const firstCard = elements.scenarioList.querySelector('.scenario-card');
            if (firstCard) {
                firstCard.click();
                console.log('[UI] Auto-selected first scenario');
            }
        } else {
            elements.scenarioList.innerHTML = '<div style="color: #666;">No scenarios available</div>';
        }
    } catch (error) {
        console.error('[ERROR] Failed to load scenarios:', error);
        elements.scenarioList.innerHTML = `<div style="color: red;">Failed to load scenarios: ${error.message}</div>`;
    }
}

// Create scenario card element
function createScenarioCard(scenario) {
    const card = document.createElement('div');
    card.className = 'scenario-card';
    card.dataset.scenarioId = scenario.id;
    card.innerHTML = `
        <h4>${scenario.title}</h4>
        <p>${scenario.description}</p>
    `;
    
    card.addEventListener('click', () => {
        document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedScenario = scenario.id;
        // Only enable start button if both character and scenario are selected
        elements.startGameBtn.disabled = !selectedCharacter;
        console.log(`[UI] Selected scenario: ${scenario.title} (${scenario.id})`);
    });
    
    return card;
}

// Load available content packs
async function loadContentPacks() {
    console.log('[API] Loading content packs...');
    
    if (!elements.contentPackSection || !elements.contentPackList) {
        console.warn('[WARN] Content pack elements not found, skipping');
        return;
    }
    
    try {
        const response = await fetch('/api/content-packs');
        
        if (!response.ok) {
            console.warn('[WARN] Content packs endpoint not available');
            return;
        }
        
        const data = await response.json();
        const packs = data.packs || [];
        console.log(`[API] Loaded ${packs.length} content packs:`, packs);
        
        // Filter out SRD (it's always included)
        const additionalPacks = packs.filter(pack => pack.id !== 'srd');
        
        // Always show the section, even if empty, to inform users
        elements.contentPackSection.style.display = 'block';
        elements.contentPackList.innerHTML = '';
        
        if (additionalPacks.length > 0) {
            additionalPacks.forEach(pack => {
                const packItem = document.createElement('div');
                packItem.className = 'content-pack-item';
                packItem.innerHTML = `
                    <label style="display: flex; align-items: center; margin-bottom: 0.5rem; cursor: pointer;">
                        <input type="checkbox" value="${pack.id}" style="margin-right: 0.5rem;">
                        <div>
                            <strong>${pack.name}</strong> v${pack.version}<br>
                            <small style="color: #888;">${pack.description}</small><br>
                            <small style="color: #666;">by ${pack.author}</small>
                        </div>
                    </label>
                `;
                
                const checkbox = packItem.querySelector('input[type="checkbox"]');
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        if (!selectedContentPacks.includes(pack.id)) {
                            selectedContentPacks.push(pack.id);
                        }
                    } else {
                        selectedContentPacks = selectedContentPacks.filter(id => id !== pack.id);
                    }
                    console.log('[UI] Selected content packs:', selectedContentPacks);
                });
                
                elements.contentPackList.appendChild(packItem);
            });
        } else {
            // Show a message when no additional packs are available
            elements.contentPackList.innerHTML = `
                <div style="color: #888; padding: 1rem; text-align: center;">
                    <p>No additional content packs available.</p>
                    <small>The base SRD content is always included.</small>
                </div>
            `;
        }
    } catch (error) {
        console.warn('[WARN] Failed to load content packs:', error);
        // Content packs are optional, so we don't show an error
    }
}

// Load available characters
async function loadCharacters() {
    console.log('[API] Loading characters...');
    
    try {
        const response = await fetch('/api/characters');
        const characters = await response.json();
        console.log(`[API] Loaded ${characters.length} characters:`, characters);
        
        elements.characterList.innerHTML = '';
        characters.forEach(char => {
            const card = createCharacterCard(char);
            elements.characterList.appendChild(card);
        });
    } catch (error) {
        console.error('[ERROR] Failed to load characters:', error);
        showError('Failed to load characters. Please refresh the page.');
    }
}

// Create character card element
function createCharacterCard(character) {
    const card = document.createElement('div');
    card.className = 'character-card';
    card.innerHTML = `
        <h3>${character.name}</h3>
        <p><strong>Class:</strong> ${displayClassName(character.class_index)}</p>
        <p><strong>Race:</strong> ${displayRaceName(character.race)}</p>
        <p><strong>Level:</strong> ${character.starting_level}</p>
        <p><strong>Background:</strong> ${displayBackgroundName(character.background)}</p>
    `;
    
    card.addEventListener('click', () => {
        document.querySelectorAll('.character-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedCharacter = character.id;
        // Only enable start button if both character and scenario are selected
        elements.startGameBtn.disabled = !selectedScenario;
        console.log(`[UI] Selected character: ${character.name} (${character.id})`);
    });
    
    return card;
}

// Start new game
async function startGame() {
    if (!selectedCharacter) {
        console.warn('[UI] No character selected');
        return;
    }
    
    if (!selectedScenario) {
        console.warn('[UI] No scenario selected');
        return;
    }
    
    console.log('[GAME] Starting new game...');
    console.log(`[GAME] Character: ${selectedCharacter}`);
    console.log(`[GAME] Scenario: ${selectedScenario}`);
    
    elements.startGameBtn.disabled = true;
    elements.startGameBtn.textContent = 'Starting...';
    
    try {
        const requestBody = {
            character_id: selectedCharacter,
            scenario_id: selectedScenario
        };
        
        // Add content packs if any are selected
        if (selectedContentPacks.length > 0) {
            requestBody.content_packs = selectedContentPacks;
        }
        
        console.log('[API] Sending game creation request:', requestBody);
        
        const response = await fetch('/api/game/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to start game: ${response.status}`);
        }
        
        const data = await response.json();
        currentGameId = data.game_id;
        console.log(`[GAME] Game created with ID: ${currentGameId}`);
        
        await loadGameState();
        
        // Clear chat for new game
        elements.chatMessages.innerHTML = '';
        
        // Initialize SSE (will show initial narrative for new game)
        window.skipInitialNarrative = false;
        initializeSSE();
        
        elements.characterSelection.classList.add('hidden');
        elements.gameInterface.classList.remove('hidden');
        
        console.log('[GAME] Game started successfully');
    } catch (error) {
        console.error('[ERROR] Failed to start game:', error);
        showError('Failed to start game. Please try again.');
        elements.startGameBtn.disabled = false;
        elements.startGameBtn.textContent = 'Start Adventure';
    }
}

// Load game state
async function loadGameState() {
    if (!currentGameId) {
        console.warn('[GAME] No current game ID');
        return;
    }
    
    console.log(`[API] Loading game state for: ${currentGameId}`);
    
    try {
        const response = await fetch(`/api/game/${currentGameId}`);
        if (!response.ok) {
            throw new Error(`Failed to load game state: ${response.status}`);
        }
        
        gameState = await response.json();
        console.log('[GAME] Game state loaded:', gameState);

        // Fetch spell names if there are spells
        if (gameState.character?.state?.spellcasting?.spells_known?.length > 0) {
            const spellIndexes = gameState.character.state.spellcasting.spells_known;
            try {
                const namesResponse = await fetch('/api/catalogs/resolve-names', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ game_id: currentGameId, spells: spellIndexes })
                });
                if (namesResponse.ok) {
                    const namesData = await namesResponse.json();
                    // Store the spell name mappings for use in updateSpellList
                    window.spellNameMappings = namesData.spells || {};
                }
            } catch (e) {
                console.warn('[API] Failed to fetch spell names:', e);
            }
        }
        updateUI();
    } catch (error) {
        console.error('[ERROR] Failed to load game state:', error);
        showError('Failed to load game state.');
    }
}

// Initialize Server-Sent Events
function initializeSSE() {
    if (sseSource) {
        console.log('[SSE] Closing existing connection');
        sseSource.close();
    }
    
    const sseUrl = `/api/game/${currentGameId}/sse`;
    console.log(`[SSE] Connecting to: ${sseUrl}`);
    
    sseSource = new EventSource(sseUrl);
    
    // Connection established
    sseSource.addEventListener('connected', (event) => {
        console.log('[SSE] Connection established:', event.data);
    });
    
    // Initial narrative (scenario start) - only for new games
    sseSource.addEventListener('initial_narrative', (event) => {
        console.log('[SSE] Initial narrative received');
        
        // Skip if we're resuming a game
        if (window.skipInitialNarrative) {
            console.log('[SSE] Skipping initial narrative for resumed game');
            window.skipInitialNarrative = false;
            return;
        }
        
        const data = JSON.parse(event.data);
        if (data.scenario_title) {
            addMessage(`=== ${data.scenario_title} ===`, 'system');
        }
        addMessage(data.narrative, 'dm');
    });
    
    // Tool calls - IMPORTANT: Display these in chat
    sseSource.addEventListener('tool_call', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Tool call received:', data);
        
        // Format the tool call display
        let toolMessage = `🎲 ${data.tool_name}`;
        
        // Parse parameters if they're in raw_args format
        let params = data.parameters || {};
        if (params.raw_args && typeof params.raw_args === 'string') {
            try {
                params = JSON.parse(params.raw_args);
                console.log('[SSE] Parsed raw_args:', params);
            } catch (e) {
                console.log('[SSE] Could not parse raw_args, using as-is');
            }
        }
        
        // Add parameters if present
        if (params && Object.keys(params).length > 0) {
            // Special formatting for dice rolls
            if (data.tool_name.includes('roll')) {
                if (params.ability) {
                    toolMessage += ` - ${params.ability}`;
                }
                if (params.skill) {
                    toolMessage += ` (${params.skill})`;
                }
                if (params.dc !== undefined) {
                    toolMessage += ` DC ${params.dc}`;
                }
                if (params.purpose) {
                    toolMessage += ` for ${params.purpose}`;
                }
            } else {
                // Generic parameter display for other tools
                const filteredParams = Object.entries(params)
                    .filter(([key]) => key !== 'raw_args')
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
                if (filteredParams) {
                    toolMessage += ` (${filteredParams})`;
                }
            }
        }
        
        addMessage(toolMessage, 'tool');
    });
    
    // Tool results
    sseSource.addEventListener('tool_result', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Tool result received:', data);

        // Format tool result based on type
        let resultMessage = '';

        // The result is now a Pydantic BaseModel object
        let result = data.result;

        // Level up
        if (result && result.type === 'level_up') {
            resultMessage = `⬆️ Level Up: ${result.old_level} → ${result.new_level} (HP +${result.hp_increase})`;
        } else 
        if (data.tool_name && data.tool_name.includes('roll')) {
            // Dice roll result - handle BaseModel format
            if (typeof result === 'object' && result !== null) {
                // Extract key information from the RollDiceResult model
                const total = result.total || '?';
                const rolls = result.rolls || [];
                const modifier = result.modifier || 0;
                const dice = result.dice || '';
                const rollType = result.roll_type || '';
                const ability = result.ability;
                const skill = result.skill;
                const critical = result.critical;
                
                // Build the message
                const rollsStr = rolls.length > 0 ? `[${rolls.join(', ')}]` : '';
                const modStr = modifier !== 0 ? (modifier > 0 ? `+${modifier}` : `${modifier}`) : '';
                
                resultMessage = `📊 ${rollType ? rollType.charAt(0).toUpperCase() + rollType.slice(1) : 'Dice'} Roll: ${dice}${modStr} = ${total}`;
                
                // Add the individual rolls if available
                if (rollsStr) {
                    resultMessage += ` ${rollsStr}`;
                }
                
                // Add ability/skill if specified
                if (ability) {
                    resultMessage += ` (${ability}${skill ? ' - ' + skill : ''})`;
                }
                
                // Add critical indicator
                if (critical === true) {
                    resultMessage += ' - 🎯 CRITICAL!';
                } else if (critical === false && rolls.includes(1)) {
                    resultMessage += ' - 💀 CRITICAL FAIL!';
                }
            } else {
                // Fallback for string results
                resultMessage = `📊 Result: ${result}`;
            }
        } else {
            // Generic tool result
            const resultText = typeof result === 'object' 
                ? JSON.stringify(result) 
                : result;
            resultMessage = `✓ ${data.tool_name} completed: ${resultText}`;
        }
        
        if (resultMessage) {
            addMessage(resultMessage, 'tool-result');
        }
    });
    
    // Narrative text (non-streaming for MVP)
    sseSource.addEventListener('narrative', (event) => {
        console.log('[SSE] Narrative event received');
        const data = JSON.parse(event.data);
        
        // For non-streaming, we get the complete content at once
        if (data.content) {
            console.log(`[SSE] Adding narrative: ${data.content.substring(0, 50)}...`);
            addMessage(data.content, 'dm');
        }
    });

    // Policy warnings (distinct UI treatment)
    sseSource.addEventListener('policy_warning', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Policy warning received:', data);
        const detail = [];
        if (data.tool_name) detail.push(`tool: ${data.tool_name}`);
        if (data.agent_type) detail.push(`agent: ${data.agent_type}`);
        const suffix = detail.length ? ` (${detail.join(', ')})` : '';
        addMessage(`⚠️ ${data.message}${suffix}`, 'policy-warning');
    });
    
    
    // Game state updates
    sseSource.addEventListener('game_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Game state update received');
        // Extract game_state from the wrapper
        gameState = data.game_state;
        updateUI();
        
        // Extract and update location information from game state (now in scenario_instance)
        if (gameState.scenario_instance && gameState.scenario_instance.current_location_id) {
            updateLocationFromGameState();
        }
        
        // Update quest information from game state (now in scenario_instance)
        if (gameState.scenario_instance && (gameState.scenario_instance.active_quests || gameState.scenario_instance.completed_quest_ids)) {
            updateQuestLogFromGameState();
        }
        
        // Update act information from game state (now in scenario_instance)
        if (gameState.scenario_instance && gameState.scenario_instance.current_act_id) {
            updateActFromGameState();
        }
    });
    
    // Scenario info contains full location data
    sseSource.addEventListener('scenario_info', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Scenario info received:', data);
        
        // Store scenario data globally for location information
        window.currentScenario = data.current_scenario;
        
        // Update location display with full scenario data
        if (window.currentScenario && gameState && gameState.scenario_instance && gameState.scenario_instance.current_location_id) {
            updateLocationWithScenarioData();
        }
    });
    
    // Complete event - stop loading
    sseSource.addEventListener('complete', (event) => {
        console.log('[SSE] Processing complete');
        setLoadingState(false);
    });
    
    // Error event - stop loading
    sseSource.addEventListener('error', (event) => {
        const data = JSON.parse(event.data || '{}');
        console.log('[SSE] Error received:', data);
        setLoadingState(false);
    });
    
    // Error handling
    sseSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error);
        if (sseSource.readyState === EventSource.CLOSED) {
            console.log('[SSE] Connection closed, attempting reconnect...');
            setLoadingState(false); // Reset on connection error
            reconnectSSE();
        }
    };
    
    console.log('[SSE] Event listeners configured');
}

// Reconnect SSE on error
function reconnectSSE() {
    setTimeout(() => {
        if (currentGameId) {
            console.log('[SSE] Attempting to reconnect...');
            initializeSSE();
        }
    }, 5000);
}

// Send message to AI DM
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || !currentGameId) {
        console.warn('[UI] Cannot send message: empty or no game');
        return;
    }
    
    // Prevent sending if already processing
    if (isProcessing) {
        console.warn('[UI] Cannot send message: agent is processing');
        return;
    }
    
    console.log(`[CHAT] Sending message: ${message}`);
    
    // Add player message to chat
    addMessage(message, 'player');
    elements.messageInput.value = '';
    
    // Start loading state
    setLoadingState(true);
    
    try {
        const response = await fetch(`/api/game/${currentGameId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.status}`);
        }
        
        console.log('[CHAT] Message sent successfully, awaiting SSE response');
        
        // Show auto-save indicator
        const originalText = elements.saveGameBtn.textContent;
        elements.saveGameBtn.textContent = '💾 Auto-saved';
        setTimeout(() => {
            elements.saveGameBtn.textContent = originalText;
        }, 2000);
    } catch (error) {
        console.error('[ERROR] Failed to send message:', error);
        showError('Failed to send message. Please try again.');
        setLoadingState(false); // Reset on error
    }
}

// Simple markdown parser for chat messages
function parseMarkdown(text) {
    // Convert markdown to HTML
    let html = text
        // Bold: **text** or __text__
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>')
        // Italic: *text* or _text_
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/_(.+?)_/g, '<em>$1</em>')
        // Headers: ### Header
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h4>$1</h4>')
        .replace(/^# (.+)$/gm, '<h5>$1</h5>')
        // Lists: - item or * item
        .replace(/^[*-] (.+)$/gm, '<li>$1</li>')
        // Wrap consecutive <li> in <ul>
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        // Line breaks
        .replace(/\n/g, '<br>');
    
    return html;
}

// Add message to chat
function addMessage(text, type) {
    console.log(`[CHAT] Adding ${type} message: ${text.substring(0, 50)}...`);
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    const p = document.createElement('p');
    
    // Use innerHTML for DM messages to support markdown, textContent for others
    if (type === 'dm' && text) {
        p.innerHTML = parseMarkdown(text);
    } else {
        p.textContent = text;
    }
    
    message.appendChild(p);
    elements.chatMessages.appendChild(message);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    return message;
}

// Update entire UI
function updateUI() {
    if (!gameState) {
        console.warn('[UI] No game state to update');
        return;
    }
    
    console.log('[UI] Updating UI with game state');
    updateCharacterSheet();
    updateLocationTime();
    updateCombatIndicator();
    updateActiveAgent();
}

// Update character sheet
function updateCharacterSheet() {
    if (!gameState || !gameState.character) {
        console.warn('[UI] No character data to update');
        return;
    }
    
    console.log('[UI] Updating character sheet');
    // Character data is now split between sheet (template) and state (runtime)
    const charSheet = gameState.character.sheet || gameState.character;
    const charState = gameState.character.state || gameState.character;
    
    // Basic info (from sheet)
    document.getElementById('charName').textContent = charSheet.name;
    document.getElementById('charRace').textContent = displayRaceName(charSheet.race);
    document.getElementById('charClass').textContent = `${displayClassName(charSheet.class_index)} ${charState.level || charSheet.starting_level}`;
    // Optional subrace/subclass
    const subraceEl = document.getElementById('charSubrace');
    const subraceRow = subraceEl?.parentElement;
    if (subraceEl && subraceRow) {
        if (charSheet.subrace) {
            subraceEl.textContent = (window.catalogs?.race_subraces?.[charSheet.subrace] || charSheet.subrace);
            subraceRow.style.display = '';
        } else {
            subraceEl.textContent = '';
            subraceRow.style.display = 'none';
        }
    }
    const subclassEl = document.getElementById('charSubclass');
    const subclassRow = subclassEl?.parentElement;
    if (subclassEl && subclassRow) {
        if (charSheet.subclass) {
            subclassEl.textContent = (window.catalogs?.subclasses?.[charSheet.subclass] || charSheet.subclass);
            subclassRow.style.display = '';
        } else {
            subclassEl.textContent = '';
            subclassRow.style.display = 'none';
        }
    }
    document.getElementById('charLevel').textContent = charState.level || charSheet.starting_level;
    
    // HP (from state)
    const current_hp = charState.hit_points?.current ?? 0;
    const max_hp = charState.hit_points?.maximum ?? 0;
    const hpPercent = max_hp > 0 ? (current_hp / max_hp) * 100 : 0;
    document.getElementById('hpFill').style.width = `${hpPercent}%`;
    document.getElementById('hpText').textContent = `${current_hp}/${max_hp}`;
    
    // Combat stats (from state)
    document.getElementById('charAC').textContent = charState.armor_class || 10;
    document.getElementById('charInitiative').textContent = (charState.initiative || 0) >= 0 ? `+${charState.initiative || 0}` : `${charState.initiative}`;
    document.getElementById('charSpeed').textContent = `${charState.speed || 30}ft`;

    // Attacks (from state)
    updateAttacks(charState.attacks || []);

    // Abilities (from state)
    updateAbilities(charState.abilities || charSheet.starting_abilities);
    
    // Skills (from state)
    updateSkills(charState.skills);

    // Features & Traits (from sheet)
    updateFeaturesAndTraits(charSheet);

    // Feats (from sheet)
    updateFeats(charSheet.feat_indexes);
    
    // Spellcasting (from state)
    if (charState.spellcasting) {
        updateSpellSlots(charState.spellcasting.spell_slots);
        updateSpellList(charState.spellcasting.spells_known);
    }
    
    // Equipment slots (from state)
    updateEquipmentSlots(charState.equipment_slots);

    // Inventory (from state)
    updateInventory({
        gold: charState.currency?.gold || 0,
        silver: charState.currency?.silver || 0,
        copper: charState.currency?.copper || 0,
        inventory: charState.inventory || []
    });

    // Conditions (from state)
    updateConditions(charState.conditions);
}

function updateAttacks(attacks) {
    const list = document.getElementById('attacksList');
    if (!list) return;
    list.innerHTML = '';

    if (!attacks || attacks.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'inventory-empty';
        empty.textContent = 'No attacks available';
        list.appendChild(empty);
        return;
    }

    attacks.forEach(att => {
        const row = document.createElement('div');
        row.className = 'attack-item';

        const left = document.createElement('div');
        left.className = 'attack-name';
        left.textContent = att.name || 'Unknown';

        const right = document.createElement('div');
        right.className = 'attack-meta';
        const toHitVal = (typeof att.attack_roll_bonus === 'number') ? (att.attack_roll_bonus >= 0 ? `+${att.attack_roll_bonus}` : `${att.attack_roll_bonus}`) : '';
        const dmgStr = att.damage ? `${att.damage}${att.damage_type ? ' ' + att.damage_type.toLowerCase() : ''}` : '';
        const rangeStr = att.range ? `${att.range}` : '';

        // Make it explicit for players
        const parts = [];
        if (toHitVal) parts.push(`Attack Roll ${toHitVal}`);
        if (dmgStr) parts.push(`Damage ${dmgStr}`);
        if (rangeStr) parts.push(`${rangeStr}`);
        right.textContent = parts.join(' • ');

        row.appendChild(left);
        row.appendChild(right);
        list.appendChild(row);
    });
}

// Update abilities
function updateAbilities(abilities) {
    if (!abilities) return;
    
    const abilityMap = {
        'STR': ['strScore', 'strMod'],
        'DEX': ['dexScore', 'dexMod'],
        'CON': ['conScore', 'conMod'],
        'INT': ['intScore', 'intMod'],
        'WIS': ['wisScore', 'wisMod'],
        'CHA': ['chaScore', 'chaMod']
    };
    
    for (const [ability, [scoreId, modId]] of Object.entries(abilityMap)) {
        const score = abilities[ability] || 10;
        const mod = Math.floor((score - 10) / 2);
        document.getElementById(scoreId).textContent = score;
        document.getElementById(modId).textContent = mod >= 0 ? `+${mod}` : `${mod}`;
    }
}

// Update skills
function updateSkills(skills) {
    const skillsList = document.getElementById('skillsList');
    if (!skillsList) return;
    skillsList.innerHTML = '';

    if (!skills || !Array.isArray(skills)) return;

    // New format: array of SkillValue objects with index and value
    skills.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'skill-item';
        const display = (window.catalogs?.skills && window.catalogs.skills[skill.index])
            ? window.catalogs.skills[skill.index]
            : skill.index.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
        const value = skill.value || 0;
        item.innerHTML = `<span>${display}</span><span>${value >= 0 ? '+' + value : value}</span>`;
        skillsList.appendChild(item);
    });
}

// Catalog full-screen (pagination)
let catState = { type: 'monsters', page: 1, pageSize: 50, selectedPacks: [] };
let availableContentPacks = [];

function renderCatalogsNav(activeType) {
    const nav = document.getElementById('catalogsNav');
    if (!nav) return;
    const cats = [
        ['monsters', 'Monsters'],
        ['items', 'Items'],
        ['spells', 'Spells'],
        ['races', 'Races'],
        ['race_subraces', 'Subraces'],
        ['classes', 'Classes'],
        ['subclasses', 'Subclasses'],
        ['backgrounds', 'Backgrounds'],
        ['alignments', 'Alignments'],
        ['languages', 'Languages'],
        ['magic_schools', 'Magic Schools'],
        ['skills', 'Skills'],
        ['features', 'Features'],
        ['feats', 'Feats'],
        ['traits', 'Traits'],
        ['weapon_properties', 'Weapon Properties'],
        ['damage_types', 'Damage Types'],
        ['conditions', 'Conditions'],
    ];
    nav.innerHTML = '';
    cats.forEach(([key, label]) => {
        const b = document.createElement('button');
        b.className = 'btn-small';
        b.textContent = `${label}`;
        b.dataset.type = key;
        if (key === activeType) b.classList.add('active');
        b.addEventListener('click', () => {
            catState.page = 1;
            showCatalogsScreen(key);
        });
        nav.appendChild(b);
    });
}

async function showCatalogsScreen(type = 'monsters') {
    catState.type = type;
    const home = document.getElementById('characterSelection');
    const game = document.getElementById('gameInterface');
    const screen = document.getElementById('catalogsScreen');
    if (home) home.classList.add('hidden');
    if (game) game.classList.add('hidden');
    if (screen) screen.classList.remove('hidden');
    
    // Load content packs if not loaded
    if (availableContentPacks.length === 0) {
        await loadContentPacksForCatalog();
    }
    
    renderCatalogsNav(type);
    renderPackFilter();
    renderCatalogsPage();
}

function hideCatalogsScreen() {
    const screen = document.getElementById('catalogsScreen');
    if (screen) screen.classList.add('hidden');
    // Navigate back depending on where we came from
    if (window.catalogBackTarget === 'home') {
        const home = document.getElementById('characterSelection');
        if (home) home.classList.remove('hidden');
    } else {
        const game = document.getElementById('gameInterface');
        if (game) game.classList.remove('hidden');
    }
}

async function loadContentPacksForCatalog() {
    try {
        const response = await fetch('/api/content-packs');
        if (!response.ok) return;
        
        const data = await response.json();
        availableContentPacks = data.packs || [];
        // Start with all packs selected by default
        catState.selectedPacks = availableContentPacks.map(p => p.id);
    } catch (error) {
        console.warn('[CATALOG] Failed to load content packs:', error);
        availableContentPacks = [];
    }
}

function renderPackFilter() {
    const container = document.getElementById('catalogPackCheckboxes');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (availableContentPacks.length === 0) {
        container.innerHTML = '<small style="color:#888;">No content packs available</small>';
        return;
    }
    
    availableContentPacks.forEach(pack => {
        const label = document.createElement('label');
        label.style.cssText = 'display:flex; align-items:center; cursor:pointer;';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = pack.id;
        checkbox.checked = catState.selectedPacks.includes(pack.id);
        checkbox.style.marginRight = '5px';
        
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                if (!catState.selectedPacks.includes(pack.id)) {
                    catState.selectedPacks.push(pack.id);
                }
            } else {
                catState.selectedPacks = catState.selectedPacks.filter(id => id !== pack.id);
            }
            catState.page = 1; // Reset to first page when filter changes
            renderCatalogsPage();
        });
        
        const text = document.createElement('span');
        text.textContent = pack.name;
        text.style.fontSize = '0.9rem';
        
        label.appendChild(checkbox);
        label.appendChild(text);
        container.appendChild(label);
    });
}

async function renderCatalogsPage() {
    const list = document.getElementById('catalogsContentList');
    const pageInfo = document.getElementById('catPageInfo');
    const pager = document.querySelector('#catalogsScreen .pagination');
    const { type, page, pageSize } = catState;
    if (!list || !pageInfo) return;
    list.innerHTML = '';
    
    if (type === 'monsters') {
        // Paginated catalog: fetch filtered list from API with packs
        if (pager) pager.style.display = 'flex';
        list.innerHTML = '<small style="color:#888;">Loading...</small>';
        try {
            const packsParam = (catState.selectedPacks && catState.selectedPacks.length > 0)
                ? `?packs=${encodeURIComponent(catState.selectedPacks.join(','))}`
                : '';
            const resp = await fetch(`/api/catalogs/monsters${packsParam}`);
            const monsters = resp.ok ? await resp.json() : [];
            list.innerHTML = '';
            
            const total = monsters.length;
            const start = (page - 1) * pageSize;
            const slice = monsters.slice(start, start + pageSize);
            
            slice.forEach(monster => {
                const row = document.createElement('div');
                row.className = 'catalog-row';
                row.style.cssText = 'display:flex; justify-content:space-between; align-items:center;';
                
                const text = document.createElement('span');
                text.textContent = `${monster.name} (${monster.index})`;
                
                const badge = document.createElement('span');
                badge.className = 'pack-badge';
                badge.style.cssText = 'font-size:0.75rem; padding:2px 6px; background:rgba(100,100,255,0.2); border-radius:3px; color:#88f;';
                badge.textContent = monster.content_pack || 'srd';
                
                row.appendChild(text);
                row.appendChild(badge);
                list.appendChild(row);
            });
            
            const totalPages = Math.max(1, Math.ceil(total / pageSize));
            pageInfo.textContent = `Page ${page} / ${totalPages} (${total} items)`;
            if (pager) pager.style.display = totalPages > 1 ? 'flex' : 'none';
            if (monsters.length === 0) {
                list.innerHTML = '<small style="color:#888;">No monsters for selected packs</small>';
            }
        } catch (e) {
            list.innerHTML = '<small style="color:#c66;">Failed to load monsters</small>';
        }
    } else if (type === 'items') {
        // Paginated catalog: fetch filtered list from API with packs
        if (pager) pager.style.display = 'flex';
        list.innerHTML = '<small style="color:#888;">Loading...</small>';
        try {
            const packsParam = (catState.selectedPacks && catState.selectedPacks.length > 0)
                ? `?packs=${encodeURIComponent(catState.selectedPacks.join(','))}`
                : '';
            const resp = await fetch(`/api/catalogs/items${packsParam}`);
            const items = resp.ok ? await resp.json() : [];
            list.innerHTML = '';
            
            const total = items.length;
            const start = (page - 1) * pageSize;
            const slice = items.slice(start, start + pageSize);
            
            slice.forEach(it => {
                const row = document.createElement('div');
                row.className = 'catalog-row';
                row.style.cssText = 'display:flex; justify-content:space-between; align-items:center;';
                
                const text = document.createElement('span');
                text.textContent = `${it.name} (${it.index}) — ${it.type}${it.rarity ? ' • ' + it.rarity : ''}`;
                
                const badge = document.createElement('span');
                badge.className = 'pack-badge';
                badge.style.cssText = 'font-size:0.75rem; padding:2px 6px; background:rgba(100,100,255,0.2); border-radius:3px; color:#88f;';
                badge.textContent = it.content_pack || 'srd';
                
                row.appendChild(text);
                row.appendChild(badge);
                list.appendChild(row);
            });
            
            const totalPages = Math.max(1, Math.ceil(total / pageSize));
            pageInfo.textContent = `Page ${page} / ${totalPages} (${total} items)`;
            if (pager) pager.style.display = totalPages > 1 ? 'flex' : 'none';
            if (items.length === 0) {
                list.innerHTML = '<small style="color:#888;">No items for selected packs</small>';
            }
        } catch (e) {
            list.innerHTML = '<small style="color:#c66;">Failed to load items</small>';
        }
    } else if (type === 'spells') {
        // Paginated catalog: fetch filtered list from API with packs
        if (pager) pager.style.display = 'flex';
        list.innerHTML = '<small style="color:#888;">Loading...</small>';
        try {
            const packsParam = (catState.selectedPacks && catState.selectedPacks.length > 0)
                ? `?packs=${encodeURIComponent(catState.selectedPacks.join(','))}`
                : '';
            const resp = await fetch(`/api/catalogs/spells${packsParam}`);
            const spells = resp.ok ? await resp.json() : [];
            list.innerHTML = '';
            
            const total = spells.length;
            const start = (page - 1) * pageSize;
            const slice = spells.slice(start, start + pageSize);
            
            slice.forEach(spell => {
                const row = document.createElement('div');
                row.className = 'catalog-row';
                row.style.cssText = 'display:flex; justify-content:space-between; align-items:center;';
                
                const text = document.createElement('span');
                text.textContent = `${spell.name} (${spell.index}) — Level ${spell.level}`;
                
                const badge = document.createElement('span');
                badge.className = 'pack-badge';
                badge.style.cssText = 'font-size:0.75rem; padding:2px 6px; background:rgba(100,100,255,0.2); border-radius:3px; color:#88f;';
                badge.textContent = spell.content_pack || 'srd';
                
                row.appendChild(text);
                row.appendChild(badge);
                list.appendChild(row);
            });
            
            const totalPages = Math.max(1, Math.ceil(total / pageSize));
            pageInfo.textContent = `Page ${page} / ${totalPages} (${total} items)`;
            if (pager) pager.style.display = totalPages > 1 ? 'flex' : 'none';
            if (spells.length === 0) {
                list.innerHTML = '<small style="color:#888;">No spells for selected packs</small>';
            }
        } catch (e) {
            list.innerHTML = '<small style="color:#c66;">Failed to load spells</small>';
        }
    } else {
        // Non-paginated catalogs: fetch filtered list from API with packs
        if (pager) pager.style.display = 'none';
        list.innerHTML = '<small style="color:#888;">Loading...</small>';
        try {
            const packsParam = (catState.selectedPacks && catState.selectedPacks.length > 0)
                ? `?packs=${encodeURIComponent(catState.selectedPacks.join(','))}`
                : '';
            const resp = await fetch(`/api/catalogs/${type}${packsParam}`);
            const data = resp.ok ? await resp.json() : [];
            list.innerHTML = '';
            (data || []).forEach(item => {
                const row = document.createElement('div');
                row.className = 'catalog-row';
                const name = item && item.name ? item.name : (item || '');
                const idx = item && item.index ? item.index : '';
                const text = document.createElement('span');
                text.textContent = `${name}${idx ? ' (' + idx + ')' : ''}`;

                const badge = document.createElement('span');
                badge.className = 'pack-badge';
                badge.style.cssText = 'margin-left:8px;font-size:0.75rem;padding:2px 6px;background:rgba(100,100,255,0.2);border-radius:3px;color:#88f;';
                const packId = (item && item.content_pack) ? item.content_pack : 'srd';
                badge.textContent = packId;

                row.appendChild(text);
                row.appendChild(badge);
                list.appendChild(row);
            });
            if ((data || []).length === 0) {
                list.innerHTML = '<small style="color:#888;">No entries for selected packs</small>';
            }
        } catch (e) {
            list.innerHTML = '<small style="color:#c66;">Failed to load catalog</small>';
        }
    }
}

// Catalog screen event listeners
document.addEventListener('click', (e) => {
    if (e.target && e.target.id === 'openCatalogs') {
        showCatalogsScreen('monsters');
    } else if (e.target && e.target.id === 'catBackBtn') {
        hideCatalogsScreen();
    } else if (e.target && e.target.id === 'catMonstersBtn') {
        catState.page = 1; showCatalogsScreen('monsters');
    } else if (e.target && e.target.id === 'catItemsBtn') {
        catState.page = 1; showCatalogsScreen('items');
    } else if (e.target && e.target.id === 'catPrevBtn') {
        if (catState.page > 1) { catState.page--; renderCatalogsPage(); }
    } else if (e.target && e.target.id === 'catNextBtn') {
        catState.page++; renderCatalogsPage();
    }
});

function updateFeaturesAndTraits(char) {
    const featureIndexList = document.getElementById('featureIndexList');
    const traitIndexList = document.getElementById('traitIndexList');
    const featureTextList = document.getElementById('featureTextList');
    if (featureIndexList) featureIndexList.innerHTML = '';
    if (traitIndexList) traitIndexList.innerHTML = '';
    if (featureTextList) featureTextList.innerHTML = '';

    // Index-based features (from SRD catalog)
    if (featureIndexList && Array.isArray(char.feature_indexes)) {
        if (char.feature_indexes.length > 0) {
            char.feature_indexes.forEach(idx => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = (window.catalogs?.features?.[idx] || idx);
                featureIndexList.appendChild(tag);
            });
        } else {
            featureIndexList.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem;">No class features loaded</span>';
        }
    }

    // Index-based traits (from SRD catalog)
    if (traitIndexList && Array.isArray(char.trait_indexes)) {
        if (char.trait_indexes.length > 0) {
            char.trait_indexes.forEach(idx => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = (window.catalogs?.traits?.[idx] || idx);
                traitIndexList.appendChild(tag);
            });
        } else {
            traitIndexList.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem;">No racial traits loaded</span>';
        }
    }

    // Custom features (character-specific choices)
    const customFeatures = char.custom_features;
    if (featureTextList && Array.isArray(customFeatures)) {
        if (customFeatures.length > 0) {
            customFeatures.forEach(ft => {
                const row = document.createElement('div');
                row.className = 'feature-row';
                row.innerHTML = `
                    <strong>${ft.name}</strong>
                    <div style="color: var(--text-secondary); margin-top: 0.25rem;">${ft.description || ''}</div>
                `;
                featureTextList.appendChild(row);
            });
        } else {
            featureTextList.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem;">No custom features</span>';
        }
    }
}

function updateFeats(featIndexes) {
    const featList = document.getElementById('featIndexList');
    if (!featList) return;
    featList.innerHTML = '';
    if (Array.isArray(featIndexes)) {
        featIndexes.forEach(idx => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = (window.catalogs?.feats?.[idx] || idx);
            featList.appendChild(tag);
        });
    }
}

// Update spell slots
function updateSpellSlots(spellSlots) {
    const slotsContainer = document.getElementById('spellSlots');
    slotsContainer.innerHTML = '';
    
    if (!spellSlots) {
        slotsContainer.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem;">No spell slots available</span>';
        return;
    }
    
    // Add the slots-grid container
    const slotsGrid = document.createElement('div');
    slotsGrid.className = 'slots-grid';
    
    for (const [level, slots] of Object.entries(spellSlots)) {
        // Handle different slot structures (total/current vs max/current)
        const maxSlots = slots.max || slots.total || 0;
        const currentSlots = slots.current !== undefined ? slots.current : maxSlots;
        
        const levelDiv = document.createElement('div');
        levelDiv.className = 'spell-slot-level';
        levelDiv.innerHTML = `
            <div>Level ${level}</div>
            <div style="color: var(--accent-color); font-size: 0.9rem; margin: 0.25rem 0;">
                ${currentSlots} / ${maxSlots}
            </div>
        `;
        
        const circles = document.createElement('div');
        circles.className = 'slot-circles';
        
        for (let i = 0; i < maxSlots; i++) {
            const circle = document.createElement('div');
            circle.className = `slot-circle ${i < currentSlots ? 'filled' : ''}`;
            circles.appendChild(circle);
        }
        
        levelDiv.appendChild(circles);
        slotsGrid.appendChild(levelDiv);
    }
    
    slotsContainer.appendChild(slotsGrid);
}

// Update spell list
function updateSpellList(spells) {
    const spellList = document.getElementById('spellList');
    spellList.innerHTML = '';

    if (!spells || spells.length === 0) {
        spellList.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem;">No spells known</span>';
        return;
    }

    spells.forEach(spell => {
        const spellDiv = document.createElement('div');
        spellDiv.className = 'spell-item';
        // Use spell name from mappings if available, otherwise show index
        const displayName = window.spellNameMappings?.[spell] || spell;
        spellDiv.textContent = displayName;
        spellList.appendChild(spellDiv);
    });
}

// Update equipment slots display
function updateEquipmentSlots(equipmentSlots) {
    if (!equipmentSlots) return;

    // Update each equipment slot
    const slots = [
        'head', 'neck', 'chest', 'hands', 'feet', 'waist',
        'main_hand', 'off_hand', 'ring_1', 'ring_2', 'back', 'ammunition'
    ];

    slots.forEach(slotName => {
        const slotElement = document.getElementById(`slot-${slotName}`);
        if (!slotElement) return;

        const itemIndex = equipmentSlots[slotName];

        if (itemIndex) {
            // Find the item in inventory to get its display name
            const item = gameState?.character?.state?.inventory?.find(it => it.index === itemIndex);
            const displayName = item?.name || itemIndex;

            slotElement.innerHTML = `
                <span class="equipped-item">
                    <span class="equipped-item-name">${displayName}</span>
                </span>
                <button class="unequip-btn" data-slot="${slotName}">×</button>
            `;
            // Add event listener to the unequip button
            const unequipBtn = slotElement.querySelector('.unequip-btn');
            if (unequipBtn) {
                unequipBtn.addEventListener('click', () => unequipFromSlot(slotName));
            }
        } else {
            slotElement.innerHTML = '<span class="empty-slot">Empty</span>';
        }
    });
}

// Update inventory (now simplified - no equipped section)
function updateInventory(inventory) {
    if (!inventory) return;

    // Update currency
    document.getElementById('goldAmount').textContent = inventory.gold || 0;
    document.getElementById('silverAmount').textContent = inventory.silver || 0;
    document.getElementById('copperAmount').textContent = inventory.copper || 0;

    // Update items
    const inventoryList = document.getElementById('inventoryList');
    inventoryList.innerHTML = '';

    if (!inventory.inventory) return;

    const items = inventory.inventory;

    // Get equipped items from equipment_slots
    const equipmentSlots = gameState?.character?.state?.equipment_slots || {};
    const equippedItemIndexes = new Set(Object.values(equipmentSlots).filter(Boolean));

    if (items.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'inventory-empty';
        empty.textContent = 'Inventory empty';
        inventoryList.appendChild(empty);
    } else {
        items.forEach(item => {
            const row = document.createElement('div');
            row.className = 'inventory-item';

            const left = document.createElement('div');
            left.textContent = `${item.name || item.index}`;
            left.style.fontWeight = '600';

            // Show quantity
            const right = document.createElement('div');
            right.textContent = `×${item.quantity || 1}`;

            row.appendChild(left);
            row.appendChild(right);

            // Check if item is equippable based on type
            const equippable = ['Armor', 'Weapon', 'Ammunition'].includes(item.item_type);
            const isEquipped = equippedItemIndexes.has(item.index);

            if (equippable && !isEquipped) {
                const actions = document.createElement('div');
                actions.style.marginLeft = 'auto';

                // Create slot selector dropdown
                const select = document.createElement('select');
                select.className = 'slot-select';
                select.style.marginRight = '0.5rem';

                // Add options based on item type
                select.innerHTML = '<option value="">Auto</option>';
                const validSlots = getValidSlotsForItem(item);
                validSlots.forEach(slot => {
                    const slotLabel = slot.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    select.innerHTML += `<option value="${slot}">${slotLabel}</option>`;
                });

                const btn = document.createElement('button');
                btn.className = 'btn-small';
                btn.textContent = 'Equip';
                btn.addEventListener('click', async () => {
                    await equipItem(item.index, select.value || null);
                });

                actions.appendChild(select);
                actions.appendChild(btn);
                row.appendChild(actions);
            } else if (isEquipped) {
                // Show where it's equipped
                const equippedIn = Object.entries(equipmentSlots)
                    .filter(([slot, index]) => index === item.index)
                    .map(([slot]) => slot.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
                    .join(', ');

                const status = document.createElement('div');
                status.style.marginLeft = 'auto';
                status.style.color = 'var(--accent-color)';
                status.style.fontSize = '0.9rem';
                status.textContent = `Equipped (${equippedIn})`;
                row.appendChild(status);
            }

            inventoryList.appendChild(row);
        });
    }
}

// Helper function to determine valid slots for an item
function getValidSlotsForItem(item) {
    const type = item.item_type;
    const index = item.index;

    if (type === 'Armor') {
        // Check subtype or name for armor type
        if (index.includes('shield')) {
            return ['off_hand', 'main_hand'];
        } else {
            return ['chest']; // Simplified - could check for other armor types
        }
    } else if (type === 'Weapon') {
        // Check if two-handed (simplified check)
        const name = (item.name || index).toLowerCase();
        if (name.includes('two-handed') || name.includes('longbow') || name.includes('greatsword')) {
            return ['main_hand'];
        } else {
            return ['main_hand', 'off_hand'];
        }
    } else if (type === 'Ammunition') {
        return ['ammunition'];
    }

    // Check for special items
    if (index.startsWith('ring-')) {
        return ['ring_1', 'ring_2'];
    } else if (index.startsWith('amulet-')) {
        return ['neck'];
    }

    return [];
}

// Equip item to a specific slot
async function equipItem(itemIndex, slot) {
    if (!currentGameId) return;
    try {
        const body = {
            item_index: itemIndex,
            unequip: false
        };

        if (slot) {
            body.slot = slot;
        }

        const res = await fetch(`/api/game/${currentGameId}/equip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        // Refresh state to reflect changes
        await loadGameState();
    } catch (e) {
        console.error('[ERROR] Equip failed:', e);
        showError('Failed to equip item.');
    }
}

// Unequip item from a specific slot
async function unequipFromSlot(slotName) {
    if (!currentGameId || !gameState) return;

    const equipmentSlots = gameState?.character?.state?.equipment_slots;
    if (!equipmentSlots) return;

    const itemIndex = equipmentSlots[slotName];
    if (!itemIndex) return;

    try {
        const res = await fetch(`/api/game/${currentGameId}/equip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                item_index: itemIndex,
                unequip: true
            })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        // Refresh state to reflect changes
        await loadGameState();
    } catch (e) {
        console.error('[ERROR] Unequip failed:', e);
        showError('Failed to unequip item.');
    }
}

// Update conditions
function updateConditions(conditions) {
    const section = document.getElementById('conditionsSection');
    const list = document.getElementById('conditionsList');
    
    if (!conditions || conditions.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    list.innerHTML = '';
    
    conditions.forEach(condition => {
        const tag = document.createElement('div');
        tag.className = 'condition-tag';
        tag.textContent = `${condition.name} (${condition.duration})`;
        list.appendChild(tag);
    });
}

// Update location and time
function updateLocationTime() {
    if (!gameState) return;
    
    document.getElementById('currentLocation').textContent = gameState.location || 'Unknown';
    
    if (gameState.time) {
        const timeStr = `Day ${gameState.time.day}, ${String(gameState.time.hour).padStart(2, '0')}:${String(gameState.time.minute).padStart(2, '0')}`;
        document.getElementById('gameTime').textContent = timeStr;
    }
}

// Update combat indicator and combat panel
function updateCombatIndicator() {
    const indicator = document.getElementById('combatIndicator');
    const combatSection = document.getElementById('combatSection');
    
    if (gameState && gameState.combat && gameState.combat.is_active) {
        // Show combat indicator
        indicator.classList.remove('hidden');
        
        // Show and update combat panel
        if (combatSection) {
            combatSection.style.display = 'block';
            updateCombatPanel(gameState.combat);
        }
        
        // Ensure agent is set to combat when combat is active
        // This helps sync the frontend if there's any mismatch
        if (gameState.active_agent !== 'combat') {
            console.log('[UI] Combat active but agent is not combat, expecting update soon');
        }
        
        console.log('[UI] Combat mode active');
    } else {
        // Hide combat elements
        indicator.classList.add('hidden');
        if (combatSection) {
            combatSection.style.display = 'none';
        }
        
        // Ensure agent is not combat when combat is inactive
        if (gameState.active_agent === 'combat') {
            console.log('[UI] Combat inactive but agent is still combat, expecting update soon');
        }
    }
}

// Update combat panel with current combat state
function updateCombatPanel(combat) {
    if (!combat) return;
    
    // Update round number
    const roundElement = document.getElementById('combatRound');
    if (roundElement) {
        roundElement.textContent = combat.round_number || 1;
    }
    
    // Update current turn
    const currentTurnElement = document.getElementById('currentTurn');
    const turnOrderList = document.getElementById('turnOrderList');
    
    if (!combat.participants || combat.participants.length === 0) {
        if (currentTurnElement) currentTurnElement.textContent = 'No participants';
        if (turnOrderList) turnOrderList.innerHTML = '<div class="no-participants">No participants in combat</div>';
        return;
    }
    
    // Find current turn participant
    const activeParticipants = combat.participants.filter(p => p.is_active !== false);
    const currentIndex = Math.min(combat.turn_index || 0, activeParticipants.length - 1);
    const currentParticipant = activeParticipants[currentIndex];
    
    if (currentTurnElement && currentParticipant) {
        currentTurnElement.textContent = currentParticipant.name;
    }
    
    // Build turn order list
    if (turnOrderList) {
        turnOrderList.innerHTML = '';
        
        // Sort by initiative (highest first)
        const sortedParticipants = [...combat.participants].sort((a, b) => {
            const initA = a.initiative !== null && a.initiative !== undefined ? a.initiative : -1;
            const initB = b.initiative !== null && b.initiative !== undefined ? b.initiative : -1;
            return initB - initA;
        });
        
        sortedParticipants.forEach((participant, index) => {
            if (!participant.is_active) return;
            
            const participantDiv = document.createElement('div');
            participantDiv.className = 'turn-order-item';
            
            // Check if this is the current turn
            const isCurrent = currentParticipant && 
                             participant.entity_id === currentParticipant.entity_id;
            
            if (isCurrent) {
                participantDiv.classList.add('current-turn');
            }
            
            // Build participant display
            const initiative = participant.initiative !== null && participant.initiative !== undefined 
                             ? participant.initiative : '?';
            const playerTag = participant.is_player ? ' [PLAYER]' : '';
            const turnArrow = isCurrent ? '→ ' : '';
            
            // Try to get HP info for this participant
            let hpDisplay = '';
            if (participant.entity_type === 'player' && gameState.character && gameState.character.state) {
                const hp = gameState.character.state.hit_points;
                if (hp) {
                    hpDisplay = ` <span class="participant-hp">(${hp.current}/${hp.maximum} HP)</span>`;
                }
            } else if (participant.entity_type === 'monster') {
                // Look for monster in gameState.monsters
                const monster = gameState.monsters?.find(m => m.instance_id === participant.entity_id);
                if (monster && monster.state && monster.state.hit_points) {
                    hpDisplay = ` <span class="participant-hp">(${monster.state.hit_points.current}/${monster.state.hit_points.maximum} HP)</span>`;
                }
            } else if (participant.entity_type === 'npc') {
                // Look for NPC in gameState.npcs
                const npc = gameState.npcs?.find(n => n.instance_id === participant.entity_id);
                if (npc && npc.state && npc.state.hit_points) {
                    hpDisplay = ` <span class="participant-hp">(${npc.state.hit_points.current}/${npc.state.hit_points.maximum} HP)</span>`;
                }
            }
            
            participantDiv.innerHTML = `
                <span class="turn-arrow">${turnArrow}</span>
                <span class="initiative">${initiative}</span>
                <span class="participant-name">${participant.name}${playerTag}${hpDisplay}</span>
            `;
            
            turnOrderList.appendChild(participantDiv);
        });
    }
}

// Update active agent indicator
function updateActiveAgent() {
    const agentElement = document.getElementById('activeAgent');
    const agentIndicator = document.getElementById('agentIndicator');
    
    if (!agentElement || !gameState) return;
    
    const agentType = gameState.active_agent || 'narrative';
    
    // Store previous agent for transition detection
    const previousAgent = agentElement.dataset.currentAgent || 'narrative';
    
    // Format agent name and icon for display
    let displayName = 'Narrative';
    let agentIcon = '📖';  // Default narrative icon
    
    switch (agentType) {
        case 'combat':
            displayName = 'Combat';
            agentIcon = '⚔️';
            break;
        case 'summarizer':
            displayName = 'Summarizer';
            agentIcon = '📝';
            break;
        case 'narrative':
        default:
            displayName = 'Narrative';
            agentIcon = '📖';
            break;
    }
    
    // Only update if agent has changed
    if (previousAgent !== agentType) {
        console.log(`[AGENT] Switching from ${previousAgent} to ${agentType}`);
        
        // Add transition class for animation
        if (agentIndicator) {
            agentIndicator.classList.add('agent-transitioning');
            
            // Update content after a brief delay for smooth transition
            setTimeout(() => {
                // Update the icon if there's a separate icon element
                const iconElement = agentIndicator.querySelector('.agent-icon');
                if (iconElement) {
                    iconElement.textContent = agentIcon;
                    // Update the existing span
                    const activeAgentSpan = document.getElementById('activeAgent');
                    if (activeAgentSpan) {
                        activeAgentSpan.textContent = displayName;
                        activeAgentSpan.dataset.currentAgent = agentType;
                    }
                } else {
                    // If no separate icon element, replace entire content
                    agentIndicator.innerHTML = `${agentIcon} <span id="activeAgent" data-current-agent="${agentType}">${displayName}</span>`;
                }
                
                // Update agent indicator styling based on type (moved here for sync with text)
                agentIndicator.className = 'agent-indicator';
                agentIndicator.classList.add(`agent-${agentType}`);
                
                // Remove transition class after animation
                setTimeout(() => {
                    agentIndicator.classList.remove('agent-transitioning');
                }, 300);
            }, 150);
        } else {
            // No animation, just update
            agentElement.textContent = displayName;
            agentElement.dataset.currentAgent = agentType;
            
            // Update agent indicator styling immediately
            if (agentIndicator) {
                agentIndicator.className = 'agent-indicator';
                agentIndicator.classList.add(`agent-${agentType}`);
            }
        }
    } else {
        // Agent hasn't changed, but ensure styling is correct
        if (agentIndicator) {
            // Remove existing agent classes and re-apply
            agentIndicator.className = 'agent-indicator';
            agentIndicator.classList.add(`agent-${agentType}`);
        }
    }
    
    // Ensure visibility
    if (agentIndicator) {
        agentIndicator.style.display = 'inline-block';
    }
}

// Save game
async function saveGame() {
    if (!currentGameId) {
        console.warn('[GAME] No game to save');
        return;
    }
    
    console.log(`[GAME] Saving game: ${currentGameId}`);
    
    const originalText = elements.saveGameBtn.textContent;
    elements.saveGameBtn.disabled = true;
    elements.saveGameBtn.textContent = '💾 Saving...';
    
    try {
        // Game auto-saves on server, but we can trigger a manual save
        await loadGameState();
        
        // Update save button with timestamp
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        elements.saveGameBtn.textContent = `✅ Saved at ${timeStr}`;
        
        showNotification('Game saved successfully!');
        
        // Reset button text after 3 seconds
        setTimeout(() => {
            elements.saveGameBtn.textContent = originalText;
        }, 3000);
        
    } catch (error) {
        console.error('[ERROR] Failed to save game:', error);
        showError('Failed to save game.');
        elements.saveGameBtn.textContent = originalText;
    } finally {
        elements.saveGameBtn.disabled = false;
    }
}

// Show error message
function showError(message) {
    console.error(`[ERROR] ${message}`);
    const errorMsg = document.createElement('div');
    errorMsg.className = 'message error';
    errorMsg.innerHTML = `<p>❌ Error: ${message}</p>`;
    elements.chatMessages.appendChild(errorMsg);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Show notification
function showNotification(message) {
    console.log(`[NOTIFICATION] ${message}`);
    const notification = document.createElement('div');
    notification.className = 'message success';
    notification.innerHTML = `<p>✅ ${message}</p>`;
    elements.chatMessages.appendChild(notification);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Update location information
function updateLocationInfo(locationData) {
    console.log('[UI] Updating location info:', locationData);
    
    // Update location description
    const locationDesc = document.getElementById('locationDescription');
    if (locationDesc) {
        locationDesc.textContent = locationData.description || '';
    }
    
    // Update location connections
    const connectionsContainer = document.getElementById('locationConnections');
    if (connectionsContainer) {
        connectionsContainer.innerHTML = '';
        
        if (locationData.connections && locationData.connections.length > 0) {
            locationData.connections.forEach(conn => {
                const connDiv = document.createElement('div');
                connDiv.className = `connection-item ${!conn.is_accessible ? 'blocked' : ''}`;
                
                const direction = conn.direction ? `<span class="connection-direction">[${conn.direction.toUpperCase()}]</span>` : '';
                const status = conn.is_accessible ? '' : '<span class="connection-status blocked">Blocked</span>';
                
                connDiv.innerHTML = `
                    ${direction}
                    <span class="connection-description">${conn.description}</span>
                    ${status}
                `;
                
                connectionsContainer.appendChild(connDiv);
            });
        } else {
            connectionsContainer.innerHTML = '<div style="color: #666;">No visible exits</div>';
        }
    }
        
    // Update danger level
    updateDangerLevel(locationData.danger_level);
}

// Update danger level indicator
function updateDangerLevel(dangerLevel) {
    const dangerIndicator = document.getElementById('dangerLevel');
    if (!dangerIndicator) return;
    
    // Remove existing classes
    dangerIndicator.className = 'danger-indicator';
    
    // Add appropriate class and text based on danger level
    switch (dangerLevel) {
        case 'safe':
            dangerIndicator.classList.add('danger-safe');
            dangerIndicator.textContent = '🛡️ Safe';
            break;
        case 'low':
            dangerIndicator.classList.add('danger-low');
            dangerIndicator.textContent = '⚠️ Low Danger';
            break;
        case 'moderate':
            dangerIndicator.classList.add('danger-moderate');
            dangerIndicator.textContent = '⚠️ Moderate Danger';
            break;
        case 'high':
            dangerIndicator.classList.add('danger-high');
            dangerIndicator.textContent = '⚠️ High Danger';
            break;
        case 'extreme':
            dangerIndicator.classList.add('danger-extreme');
            dangerIndicator.textContent = '☠️ EXTREME DANGER';
            break;
        case 'cleared':
            dangerIndicator.classList.add('danger-cleared');
            dangerIndicator.textContent = '✓ Cleared';
            break;
        default:
            dangerIndicator.textContent = '';
    }
}

// Extract location data from game state and update UI
function updateLocationFromGameState() {
    if (!gameState || !gameState.scenario_instance) return;
    
    // Update the current location name display
    const locationName = document.getElementById('currentLocation');
    if (locationName) {
        locationName.textContent = gameState.location || gameState.scenario_instance.current_location_id || 'Unknown';
    }
    
    // If we have location state data, update danger level
    const currentLocId = gameState.scenario_instance.current_location_id;
    if (currentLocId && gameState.scenario_instance.location_states) {
        const locationState = gameState.scenario_instance.location_states[currentLocId];
        if (locationState && locationState.danger_level) {
            updateDangerLevel(locationState.danger_level);
        }
    }
    
    // Update NPCs present - filter by current_location_id
    const npcsSection = document.getElementById('locationNPCs');
    const npcsList = document.getElementById('npcsList');
    if (npcsSection && npcsList && gameState.npcs && currentLocId) {
        // Filter NPCs that are at the current location
        const npcsAtLocation = gameState.npcs.filter(npc => 
            npc.current_location_id === currentLocId
        );
        
        if (npcsAtLocation.length > 0) {
            npcsSection.style.display = 'block';
            npcsList.innerHTML = '';
            
            npcsAtLocation.forEach(npc => {
                const npcTag = document.createElement('div');
                npcTag.className = 'npc-tag';
                // Use display name from sheet or fallback to character name
                const displayName = npc.sheet?.display_name || 
                                  npc.sheet?.character?.name || 
                                  'Unknown NPC';
                npcTag.textContent = displayName;
                npcsList.appendChild(npcTag);
            });
        } else {
            npcsSection.style.display = 'none';
        }
    }
    
    // If we have scenario data, update location with full details
    if (window.currentScenario) {
        updateLocationWithScenarioData();
    }
}

// Update location display using scenario data
function updateLocationWithScenarioData() {
    if (!window.currentScenario || !gameState || !gameState.scenario_instance) return;
    
    const currentLocId = gameState.scenario_instance.current_location_id;
    if (!currentLocId) return;
    
    // Find the current location in the scenario
    const currentLocation = window.currentScenario.locations?.find(
        loc => loc.id === currentLocId
    );
    
    if (!currentLocation) {
        console.warn('[UI] Location not found in scenario:', currentLocId);
        return;
    }
    
    console.log('[UI] Updating location with scenario data:', currentLocation);
    
    // Update location name
    const locationName = document.getElementById('currentLocation');
    if (locationName) {
        locationName.textContent = currentLocation.name || currentLocId;
    }
    
    // Update location description
    const locationDesc = document.getElementById('locationDescription');
    if (locationDesc) {
        locationDesc.textContent = currentLocation.description || '';
    }
    
    // Update location connections/exits
    const connectionsContainer = document.getElementById('locationConnections');
    if (connectionsContainer) {
        connectionsContainer.innerHTML = '';
        
        if (currentLocation.connections && currentLocation.connections.length > 0) {
            currentLocation.connections.forEach(conn => {
                const connDiv = document.createElement('div');
                connDiv.className = `connection-item ${!conn.is_accessible ? 'blocked' : ''}`;
                
                const direction = conn.direction ? `<span class="connection-direction">[${conn.direction.toUpperCase()}]</span>` : '';
                const status = conn.is_accessible !== false ? '' : '<span class="connection-status blocked">Blocked</span>';
                
                connDiv.innerHTML = `
                    ${direction}
                    <span class="connection-description">${conn.description}</span>
                    ${status}
                `;
                
                connectionsContainer.appendChild(connDiv);
            });
        } else {
            connectionsContainer.innerHTML = '<div style="color: #666;">No visible exits</div>';
        }
    }
}

// Extract quest data from game state and update UI
function updateQuestLogFromGameState() {
    if (!gameState || !gameState.scenario_instance) return;
    
    const questData = {
        active_quests: gameState.scenario_instance.active_quests || [],
        completed_quest_ids: gameState.scenario_instance.completed_quest_ids || []
    };
    
    updateQuestLog(questData);
}

// Extract act data from game state and update UI
function updateActFromGameState() {
    if (!gameState || !gameState.scenario_instance) return;
    
    const actId = gameState.scenario_instance.current_act_id;
    if (!actId) return;
    
    // Create act data object compatible with existing updateActInfo
    // Extract act number from ID if it follows pattern "act_N" 
    const actMatch = actId.match(/act[_-]?(\d+)/i);
    const actNumber = actMatch ? parseInt(actMatch[1]) : 1;
    
    const actData = {
        act_id: actId,
        act_name: `Act ${actNumber}`,
        act_index: actNumber - 1
    };
    
    updateActInfo(actData);
}

// Update quest log
function updateQuestLog(questData) {
    console.log('[UI] Updating quest log:', questData);
    
    const questLog = document.getElementById('questLog');
    const questCount = document.getElementById('questCount');
    
    if (!questLog) return;
    
    questLog.innerHTML = '';
    
    let totalQuests = 0;
    
    // Show active quests
    if (questData.active_quests && questData.active_quests.length > 0) {
        totalQuests += questData.active_quests.length;
        
        questData.active_quests.forEach(quest => {
            const questDiv = document.createElement('div');
            const isCompleted = quest.status === 'completed';
            questDiv.className = `quest-item ${isCompleted ? 'completed' : ''}`;
            
            // Calculate progress
            const completedObjectives = quest.objectives.filter(obj => obj.status === 'completed').length;
            const totalObjectives = quest.objectives.length;
            const progressPercent = totalObjectives > 0 ? Math.round((completedObjectives / totalObjectives) * 100) : 0;
            
            questDiv.innerHTML = `
                <div class="quest-header">
                    <span class="quest-name">${quest.name} ${isCompleted ? '✓' : ''}</span>
                    <span class="quest-progress">${progressPercent}%</span>
                </div>
                <div class="quest-description">${quest.description}</div>
                <div class="quest-objectives">
                    <h5>Objectives:</h5>
                    <ul class="objective-list">
                        ${quest.objectives.map(obj => `
                            <li class="objective-item ${obj.status}">
                                <span class="objective-status ${obj.status}">
                                    ${obj.status === 'completed' ? '✓' : obj.status === 'active' ? '○' : '◯'}
                                </span>
                                ${obj.description}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
            
            questLog.appendChild(questDiv);
        });
    }
    
    // Show completed quests count if any
    if (questData.completed_quest_ids && questData.completed_quest_ids.length > 0) {
        const completedDiv = document.createElement('div');
        completedDiv.className = 'completed-quests-note';
        completedDiv.innerHTML = `<em>${questData.completed_quest_ids.length} quest(s) completed</em>`;
        questLog.appendChild(completedDiv);
    }
    
    // Update quest count
    if (questCount) {
        questCount.textContent = totalQuests;
    }
    
    if (totalQuests === 0 && (!questData.completed_quest_ids || questData.completed_quest_ids.length === 0)) {
        questLog.innerHTML = '<div style="color: #666; text-align: center;">No active quests</div>';
    }
    
    // Track completed quests (no popup, just for tracking)
    window.previousQuestIds = questData.completed_quest_ids || [];
}

// Update act/chapter information
function updateActInfo(actData) {
    console.log('[UI] Updating act info:', actData);
    
    const actDisplay = document.getElementById('currentAct');
    if (actDisplay) {
        actDisplay.textContent = actData.act_name || 'Act I';
    }
}

// Loading state management
function setLoadingState(loading) {
    isProcessing = loading;
    
    // Update input controls
    elements.messageInput.disabled = loading;
    elements.sendMessageBtn.disabled = loading;
    
    // Update visual indicators
    if (loading) {
        // Add loading class to chat area
        elements.chatMessages.classList.add('loading');
        
        // Show loading message
        const loadingMsg = addMessage('', 'loading');
        loadingMsg.id = 'loadingMessage';
        updateLoadingMessage();
        
        // Add pulse to agent indicator
        const agentIndicator = document.getElementById('agentIndicator');
        if (agentIndicator) {
            agentIndicator.classList.add('agent-loading');
        }
        
        // Update button text
        elements.sendMessageBtn.textContent = 'Agent is thinking...';
        
        // Add loading class to input area
        elements.messageInput.placeholder = 'Waiting for agent response...';
    } else {
        // Remove loading class
        elements.chatMessages.classList.remove('loading');
        
        // Remove loading message
        const loadingMsg = document.getElementById('loadingMessage');
        if (loadingMsg) {
            loadingMsg.remove();
        }
        
        // Remove pulse from agent indicator
        const agentIndicator = document.getElementById('agentIndicator');
        if (agentIndicator) {
            agentIndicator.classList.remove('agent-loading');
        }
        
        // Reset button text
        elements.sendMessageBtn.textContent = 'Send';
        
        // Reset input placeholder
        elements.messageInput.placeholder = 'Type your action...';
        
        // Re-focus input for convenience
        elements.messageInput.focus();
    }
}

// Update loading message based on active agent
function updateLoadingMessage() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (!loadingMsg) return;
    
    const agentType = gameState?.active_agent || 'narrative';
    let message = '';
    
    switch (agentType) {
        case 'combat':
            message = '⚔️ Combat agent is processing the battle...';
            break;
        case 'summarizer':
            message = '📝 Summarizer agent is preparing a summary...';
            break;
        case 'narrative':
        default:
            message = '📖 The Dungeon Master is crafting your adventure...';
            break;
    }
    
    // Update the loading message content
    const msgContent = loadingMsg.querySelector('p');
    if (msgContent) {
        msgContent.innerHTML = `<span class="loading-dots">${message}</span>`;
    }
}

// Removed tooltip functions - no longer needed
