// State management
let gameState = null;
let currentGameId = null;
let selectedCharacter = null;
let selectedScenario = null;
let sseSource = null;

// DOM elements - cached for performance
const elements = {};

// Initialize DOM element cache
function initializeElements() {
    console.log('[INIT] Caching DOM elements...');
    elements.characterSelection = document.getElementById('characterSelection');
    elements.gameInterface = document.getElementById('gameInterface');
    elements.characterList = document.getElementById('characterList');
    elements.scenarioList = document.getElementById('scenarioList');
    elements.premise = document.getElementById('premise');
    elements.startGameBtn = document.getElementById('startGame');
    elements.saveGameBtn = document.getElementById('saveGame');
    elements.chatMessages = document.getElementById('chatMessages');
    elements.messageInput = document.getElementById('messageInput');
    elements.sendMessageBtn = document.getElementById('sendMessage');
    
    // Log any missing elements
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            console.error(`[ERROR] Missing DOM element: ${key}`);
        }
    }
    console.log('[INIT] DOM elements cached successfully');
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('[APP] Starting D&D 5e AI Dungeon Master frontend...');
    
    initializeElements();
    loadSavedGames();
    loadCharacters();
    loadScenarios();
    setupEventListeners();
    
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
    
    // Custom premise input clears scenario selection
    elements.premise.addEventListener('input', () => {
        if (elements.premise.value.trim()) {
            document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('selected'));
            selectedScenario = null;
            console.log('[UI] Custom premise entered, cleared scenario selection');
        }
    });
    
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
    const title = game.scenario_title || `${game.character.name}'s Adventure`;
    
    card.innerHTML = `
        <div class="saved-game-info">
            <h3>${title}</h3>
            <p class="character">🧝 ${game.character.name} - Level ${game.character.level} ${game.character.class_name}</p>
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
                    addMessage(msg.content, 'dm');
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
        elements.premise.value = ''; // Clear custom premise
        console.log(`[UI] Selected scenario: ${scenario.title} (${scenario.id})`);
    });
    
    return card;
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
        <p><strong>Class:</strong> ${character.class_name}</p>
        <p><strong>Race:</strong> ${character.race}</p>
        <p><strong>Level:</strong> ${character.level}</p>
        <p><strong>Background:</strong> ${character.background}</p>
    `;
    
    card.addEventListener('click', () => {
        document.querySelectorAll('.character-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedCharacter = character.id;
        elements.startGameBtn.disabled = false;
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
    
    console.log('[GAME] Starting new game...');
    console.log(`[GAME] Character: ${selectedCharacter}`);
    console.log(`[GAME] Scenario: ${selectedScenario || 'custom'}`);
    console.log(`[GAME] Custom premise: ${elements.premise.value || 'none'}`);
    
    elements.startGameBtn.disabled = true;
    elements.startGameBtn.textContent = 'Starting...';
    
    try {
        const requestBody = {
            character_id: selectedCharacter,
            premise: elements.premise.value || null,
            scenario_id: selectedScenario || null
        };
        
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
                if (params.target && params.target !== 'player') {
                    toolMessage += ` for ${params.target}`;
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
        
        // Try to parse the result if it's a string representation of an object
        let result = data.result;
        if (typeof result === 'string' && result.startsWith('{')) {
            try {
                // Use eval carefully - only for dict-like strings from Python
                result = eval('(' + result + ')');
                console.log('[SSE] Parsed tool result:', result);
            } catch (e) {
                console.log('[SSE] Could not parse result, using as string');
            }
        }
        
        if (data.tool_name && data.tool_name.includes('roll')) {
            // Dice roll result - handle both object and string formats
            if (typeof result === 'object' && result !== null) {
                // Extract key information
                const roll = result.roll || result.total || '?';
                const naturalRoll = result.natural_roll;
                const modifier = result.modifier;
                const success = result.success;
                const critSuccess = result.critical_success;
                const critFail = result.critical_failure;
                
                // Build the message
                resultMessage = `📊 Rolled: ${roll}`;
                
                // Add natural roll and modifier if available
                if (naturalRoll !== undefined && modifier !== undefined) {
                    const modStr = modifier >= 0 ? `+${modifier}` : `${modifier}`;
                    resultMessage = `📊 Rolled: ${roll} (${naturalRoll}${modStr})`;
                }
                
                // Add success/failure
                if (success !== undefined) {
                    if (critSuccess) {
                        resultMessage += ' - 🎯 CRITICAL SUCCESS!';
                    } else if (critFail) {
                        resultMessage += ' - 💀 CRITICAL FAILURE!';
                    } else if (success) {
                        resultMessage += ' - ✅ Success';
                    } else {
                        resultMessage += ' - ❌ Failure';
                    }
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
    
    // Character updates
    sseSource.addEventListener('character_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Character update received:', data);
        gameState.character = data.character;
        updateCharacterSheet();
    });
    
    
    // Game state updates
    sseSource.addEventListener('game_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Game state update received');
        // Extract game_state from the wrapper
        gameState = data.game_state;
        updateUI();
    });
    
    // Location updates
    sseSource.addEventListener('location_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Location update received:', data);
        updateLocationInfo(data);
    });
    
    // Quest updates
    sseSource.addEventListener('quest_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Quest update received:', data);
        updateQuestLog(data);
    });
    
    // Act updates
    sseSource.addEventListener('act_update', (event) => {
        const data = JSON.parse(event.data);
        console.log('[SSE] Act update received:', data);
        updateActInfo(data);
    });
    
    // Error handling
    sseSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error);
        if (sseSource.readyState === EventSource.CLOSED) {
            console.log('[SSE] Connection closed, attempting reconnect...');
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
    
    console.log(`[CHAT] Sending message: ${message}`);
    
    // Add player message to chat
    addMessage(message, 'player');
    elements.messageInput.value = '';
    elements.sendMessageBtn.disabled = true;
    
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
    } finally {
        elements.sendMessageBtn.disabled = false;
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
}

// Update character sheet
function updateCharacterSheet() {
    if (!gameState || !gameState.character) {
        console.warn('[UI] No character data to update');
        return;
    }
    
    console.log('[UI] Updating character sheet');
    const char = gameState.character;
    
    // Basic info
    document.getElementById('charName').textContent = char.name;
    document.getElementById('charRace').textContent = char.race;
    document.getElementById('charClass').textContent = `${char.class_name} ${char.level}`;
    document.getElementById('charLevel').textContent = char.level;
    
    // HP
    const current_hp = char.hit_points?.current ?? char.hit_points_current ?? 0;
    const max_hp = char.hit_points?.maximum ?? char.hit_points_maximum ?? 0;
    const hpPercent = max_hp > 0 ? (current_hp / max_hp) * 100 : 0;
    document.getElementById('hpFill').style.width = `${hpPercent}%`;
    document.getElementById('hpText').textContent = `${current_hp}/${max_hp}`;
    
    // Combat stats
    document.getElementById('charAC').textContent = char.armor_class;
    document.getElementById('charInitiative').textContent = char.initiative >= 0 ? `+${char.initiative}` : `${char.initiative}`;
    document.getElementById('charSpeed').textContent = `${char.speed}ft`;
    
    // Abilities
    updateAbilities(char.abilities);
    
    // Skills
    updateSkills(char.skills);
    
    // Spellcasting
    if (char.spellcasting) {
        updateSpellSlots(char.spellcasting.spell_slots);
        updateSpellList(char.spellcasting.spells_known);
    }
    
    // Inventory
    updateInventory({
        gold: char.currency?.gold || 0,
        silver: char.currency?.silver || 0,
        copper: char.currency?.copper || 0,
        inventory: char.inventory || []
    });
    
    // Conditions
    updateConditions(char.conditions);
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
    skillsList.innerHTML = '';
    
    if (!skills) return;
    
    for (const [skill, proficient] of Object.entries(skills)) {
        const item = document.createElement('div');
        item.className = `skill-item ${proficient ? 'proficient' : ''}`;
        item.innerHTML = `
            <span>${skill}</span>
            <span>${proficient ? '✓' : ''}</span>
        `;
        skillsList.appendChild(item);
    }
}

// Update spell slots
function updateSpellSlots(spellSlots) {
    const slotsContainer = document.getElementById('spellSlots');
    slotsContainer.innerHTML = '';
    
    if (!spellSlots) return;
    
    for (const [level, slots] of Object.entries(spellSlots)) {
        const levelDiv = document.createElement('div');
        levelDiv.className = 'spell-slot-level';
        levelDiv.innerHTML = `<div>Level ${level}</div>`;
        
        const circles = document.createElement('div');
        circles.className = 'slot-circles';
        
        for (let i = 0; i < slots.max; i++) {
            const circle = document.createElement('div');
            circle.className = `slot-circle ${i < slots.current ? 'filled' : ''}`;
            circles.appendChild(circle);
        }
        
        levelDiv.appendChild(circles);
        slotsContainer.appendChild(levelDiv);
    }
}

// Update spell list
function updateSpellList(spells) {
    const spellList = document.getElementById('spellList');
    spellList.innerHTML = '';
    
    if (!spells || spells.length === 0) return;
    
    spells.forEach(spell => {
        const spellDiv = document.createElement('div');
        spellDiv.className = 'spell-item';
        spellDiv.textContent = spell;
        spellDiv.style.position = 'relative';
        spellDiv.style.cursor = 'pointer';
        
        // Add hover event for tooltip
        let tooltipTimeout;
        spellDiv.addEventListener('mouseenter', () => {
            tooltipTimeout = setTimeout(() => {
                if (!spellDiv.querySelector('.spell-tooltip')) {
                    showSpellTooltip(spell, spellDiv);
                }
            }, 500); // Delay to avoid too many requests
        });
        
        spellDiv.addEventListener('mouseleave', () => {
            clearTimeout(tooltipTimeout);
            const tooltip = spellDiv.querySelector('.spell-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
        
        spellList.appendChild(spellDiv);
    });
}

// Update inventory
function updateInventory(inventory) {
    if (!inventory) return;
    
    // Update currency
    document.getElementById('goldAmount').textContent = inventory.gold || 0;
    document.getElementById('silverAmount').textContent = inventory.silver || 0;
    document.getElementById('copperAmount').textContent = inventory.copper || 0;
    
    // Update items
    const inventoryList = document.getElementById('inventoryList');
    inventoryList.innerHTML = '';
    
    if (inventory.inventory) {
        inventory.inventory.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'inventory-item';
            const equipped = item.equipped ? ' (equipped)' : '';
            itemDiv.innerHTML = `
                <span>${item.name}${equipped}</span>
                <span>×${item.quantity || 1}</span>
            `;
            
            // Add hover event for tooltip
            let tooltipTimeout;
            itemDiv.addEventListener('mouseenter', () => {
                tooltipTimeout = setTimeout(() => {
                    if (!itemDiv.querySelector('.item-tooltip')) {
                        showItemTooltip(item.name, itemDiv);
                    }
                }, 500); // Delay to avoid too many requests
            });
            
            itemDiv.addEventListener('mouseleave', () => {
                clearTimeout(tooltipTimeout);
                const tooltip = itemDiv.querySelector('.item-tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
            });
            
            inventoryList.appendChild(itemDiv);
        });
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

// Update combat indicator
function updateCombatIndicator() {
    const indicator = document.getElementById('combatIndicator');
    if (gameState && gameState.combat && gameState.combat.active) {
        indicator.classList.remove('hidden');
        console.log('[UI] Combat mode active');
    } else {
        indicator.classList.add('hidden');
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
    
    // Update NPCs present
    const npcsSection = document.getElementById('locationNPCs');
    const npcsList = document.getElementById('npcsList');
    if (npcsSection && npcsList) {
        if (locationData.npcs_present && locationData.npcs_present.length > 0) {
            npcsSection.style.display = 'block';
            npcsList.innerHTML = '';
            
            locationData.npcs_present.forEach(npc => {
                const npcTag = document.createElement('div');
                npcTag.className = 'npc-tag';
                npcTag.textContent = npc;
                npcsList.appendChild(npcTag);
            });
        } else {
            npcsSection.style.display = 'none';
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


// Fetch and display item tooltip
async function showItemTooltip(itemName, element) {
    try {
        const response = await fetch(`/api/items/${encodeURIComponent(itemName)}`);
        if (!response.ok) return;
        
        const itemData = await response.json();
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'item-tooltip';
        
        const rarityClass = `rarity-${itemData.rarity.toLowerCase().replace(' ', '-')}`;
        
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <span class="tooltip-name">${itemData.name}</span>
                <span class="tooltip-rarity ${rarityClass}">${itemData.rarity}</span>
            </div>
            <div class="tooltip-type">${itemData.type}</div>
            <div class="tooltip-description">${itemData.description}</div>
            <div class="tooltip-stats">
                ${itemData.damage ? `<div class="tooltip-stat"><span>Damage:</span><span>${itemData.damage} ${itemData.damage_type || ''}</span></div>` : ''}
                ${itemData.armor_class ? `<div class="tooltip-stat"><span>AC:</span><span>${itemData.armor_class}</span></div>` : ''}
                ${itemData.weight ? `<div class="tooltip-stat"><span>Weight:</span><span>${itemData.weight} lbs</span></div>` : ''}
                ${itemData.value ? `<div class="tooltip-stat"><span>Value:</span><span>${itemData.value} gp</span></div>` : ''}
            </div>
        `;
        
        element.appendChild(tooltip);
    } catch (error) {
        console.error('[ERROR] Failed to fetch item tooltip:', error);
    }
}

// Fetch and display spell tooltip
async function showSpellTooltip(spellName, element) {
    try {
        const response = await fetch(`/api/spells/${encodeURIComponent(spellName)}`);
        if (!response.ok) return;
        
        const spellData = await response.json();
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'spell-tooltip';
        
        const levelText = spellData.level === 0 ? 'Cantrip' : `Level ${spellData.level}`;
        
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <span class="tooltip-name">${spellData.name}</span>
                <span class="tooltip-type">${levelText} - ${spellData.school}</span>
            </div>
            <div class="tooltip-description">${spellData.description}</div>
            <div class="tooltip-stats">
                <div class="tooltip-stat"><span>Casting Time:</span><span>${spellData.casting_time}</span></div>
                <div class="tooltip-stat"><span>Range:</span><span>${spellData.range}</span></div>
                <div class="tooltip-stat"><span>Duration:</span><span>${spellData.duration}</span></div>
                <div class="tooltip-stat"><span>Components:</span><span>${spellData.components}</span></div>
                ${spellData.concentration ? '<div class="tooltip-stat"><span>Concentration:</span><span>Yes</span></div>' : ''}
            </div>
        `;
        
        element.appendChild(tooltip);
    } catch (error) {
        console.error('[ERROR] Failed to fetch spell tooltip:', error);
    }
}