// State management
let gameState = null;
let currentGameId = null;
let selectedCharacter = null;
let selectedScenario = null;
let sseSource = null;

// DOM elements
const characterSelection = document.getElementById('characterSelection');
const gameInterface = document.getElementById('gameInterface');
const characterList = document.getElementById('characterList');
const premise = document.getElementById('premise');
const startGameBtn = document.getElementById('startGame');
const saveGameBtn = document.getElementById('saveGame');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendMessageBtn = document.getElementById('sendMessage');
const diceDisplay = document.getElementById('diceDisplay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing...');
    
    // Check if elements exist
    const scenarioList = document.getElementById('scenarioList');
    const characterList = document.getElementById('characterList');
    
    console.log('scenarioList element:', scenarioList);
    console.log('characterList element:', characterList);
    
    if (!scenarioList) {
        console.error('ERROR: scenarioList element not found in DOM!');
    }
    if (!characterList) {
        console.error('ERROR: characterList element not found in DOM!');
    }
    
    loadCharacters();
    loadScenarios();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    startGameBtn.addEventListener('click', startGame);
    sendMessageBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
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
        });
    });
    
    saveGameBtn.addEventListener('click', saveGame);
}

// Load available scenarios
async function loadScenarios() {
    console.log('loadScenarios called');
    const scenarioList = document.getElementById('scenarioList');
    
    // Show loading indicator
    if (scenarioList) {
        scenarioList.innerHTML = '<div style="color: #888;">Loading scenarios...</div>';
    }
    
    try {
        console.log('Fetching scenarios from /api/scenarios...');
        const response = await fetch('/api/scenarios');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const scenarios = await response.json();
        console.log('Scenarios received:', scenarios);
        
        if (scenarioList) {
            scenarioList.innerHTML = '';
            
            if (scenarios && scenarios.length > 0) {
                scenarios.forEach(scenario => {
                    const card = createScenarioCard(scenario);
                    scenarioList.appendChild(card);
                });
                
                // Auto-select first scenario if available
                const firstCard = scenarioList.querySelector('.scenario-card');
                if (firstCard) {
                    firstCard.click();
                }
                console.log(`Successfully loaded ${scenarios.length} scenario(s)`);
            } else {
                scenarioList.innerHTML = '<div style="color: #666;">No scenarios available</div>';
                console.warn('No scenarios returned from API');
            }
        }
    } catch (error) {
        console.error('Failed to load scenarios:', error);
        // Display error in the UI
        const scenarioList = document.getElementById('scenarioList');
        if (scenarioList) {
            scenarioList.innerHTML = '<div style="color: red;">Failed to load scenarios: ' + error + '</div>';
        }
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
        // Clear custom premise when scenario selected
        const premise = document.getElementById('premise');
        if (premise) premise.value = '';
    });
    
    return card;
}

// Load available characters
async function loadCharacters() {
    try {
        const response = await fetch('/api/characters');
        const characters = await response.json();
        
        characterList.innerHTML = '';
        characters.forEach(char => {
            const card = createCharacterCard(char);
            characterList.appendChild(card);
        });
    } catch (error) {
        console.error('Failed to load characters:', error);
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
        startGameBtn.disabled = false;
    });
    
    return card;
}

// Start new game
async function startGame() {
    if (!selectedCharacter) return;
    
    startGameBtn.disabled = true;
    startGameBtn.textContent = 'Starting...';
    
    try {
        const response = await fetch('/api/game/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_id: selectedCharacter,
                premise: premise.value || null,
                scenario_id: selectedScenario || null
            })
        });
        
        if (!response.ok) throw new Error('Failed to start game');
        
        const data = await response.json();
        currentGameId = data.game_id;
        
        await loadGameState();
        initializeSSE();
        
        characterSelection.classList.add('hidden');
        gameInterface.classList.remove('hidden');
        
    } catch (error) {
        console.error('Failed to start game:', error);
        showError('Failed to start game. Please try again.');
        startGameBtn.disabled = false;
        startGameBtn.textContent = 'Start Adventure';
    }
}

// Load game state
async function loadGameState() {
    if (!currentGameId) return;
    
    try {
        const response = await fetch(`/api/game/${currentGameId}`);
        if (!response.ok) throw new Error('Failed to load game state');
        
        gameState = await response.json();
        updateUI();
    } catch (error) {
        console.error('Failed to load game state:', error);
        showError('Failed to load game state.');
    }
}

// Initialize Server-Sent Events
function initializeSSE() {
    if (sseSource) sseSource.close();
    
    sseSource = new EventSource(`/api/game/${currentGameId}/sse`);
    
    console.log('SSE connection established for game:', currentGameId);
    
    sseSource.addEventListener('connected', (event) => {
        console.log('Connected event received:', event.data);
    });
    
    // Handle initial narrative
    sseSource.addEventListener('initial_narrative', (event) => {
        const data = JSON.parse(event.data);
        if (data.scenario_title) {
            addMessage(`=== ${data.scenario_title} ===`, 'system');
        }
        addMessage(data.narrative, 'dm');
    });
    
    // Handle tool calls
    sseSource.addEventListener('tool_call', (event) => {
        const data = JSON.parse(event.data);
        const params = data.parameters ? JSON.stringify(data.parameters) : '';
        addMessage(`🔧 Using tool: ${data.tool_name} ${params}`, 'system');
    });
    
    // Handle scenario info
    sseSource.addEventListener('scenario_info', (event) => {
        const data = JSON.parse(event.data);
        if (data.current_scenario) {
            const header = document.querySelector('.location-time');
            if (header) {
                let scenarioDisplay = header.querySelector('.current-scenario');
                if (!scenarioDisplay) {
                    scenarioDisplay = document.createElement('span');
                    scenarioDisplay.className = 'current-scenario';
                    header.appendChild(scenarioDisplay);
                }
                scenarioDisplay.textContent = `📚 ${data.current_scenario.title}`;
            }
        }
    });
    
    sseSource.addEventListener('narrative', (event) => {
        console.log('Raw narrative event:', event);
        const data = JSON.parse(event.data);
        handleNarrative(data);
    });
    
    sseSource.addEventListener('character_update', (event) => {
        const data = JSON.parse(event.data);
        handleCharacterUpdate(data);
    });
    
    sseSource.addEventListener('dice_roll', (event) => {
        const data = JSON.parse(event.data);
        handleDiceRoll(data);
    });
    
    sseSource.addEventListener('tool_result', (event) => {
        const data = JSON.parse(event.data);
        handleToolResult(data);
    });
    
    sseSource.onerror = (error) => {
        console.error('SSE error:', error);
        reconnectSSE();
    };
}

// Reconnect SSE on error
function reconnectSSE() {
    setTimeout(() => {
        if (currentGameId) {
            initializeSSE();
        }
    }, 5000);
}

// Send message to AI DM
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !currentGameId) return;
    
    // Add player message to chat
    addMessage(message, 'player');
    messageInput.value = '';
    sendMessageBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/game/${currentGameId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        // The response will come through SSE
    } catch (error) {
        console.error('Failed to send message:', error);
        showError('Failed to send message. Please try again.');
    } finally {
        sendMessageBtn.disabled = false;
    }
}

// Handle narrative streaming
let currentDMMessage = null;
function handleNarrative(data) {
    console.log('Narrative event received:', data);
    if (data.start) {
        currentDMMessage = addMessage('', 'dm');
    } else if (data.word && currentDMMessage) {
        const p = currentDMMessage.querySelector('p');
        p.textContent += data.word;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else if (data.complete) {
        currentDMMessage = null;
    }
}

// Handle character updates
function handleCharacterUpdate(data) {
    gameState.character = data.character;
    updateCharacterSheet();
}

// Handle dice rolls
function handleDiceRoll(data) {
    showDiceRoll(data);
}

// Handle tool results
function handleToolResult(data) {
    // Display the tool result in chat
    const resultText = typeof data.result === 'object' 
        ? JSON.stringify(data.result) 
        : data.result;
    addMessage(`📊 ${data.tool_name} result: ${resultText}`, 'system');
    
    // Also handle game state updates if present
    if (data.type === 'game_state_update') {
        gameState = data.state;
        updateUI();
    }
}

// Add message to chat
function addMessage(text, type) {
    const message = document.createElement('div');
    message.className = `message ${type}`;
    const p = document.createElement('p');
    p.textContent = text;
    message.appendChild(p);
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return message;
}

// Also clear scenario selection when typing custom premise
document.addEventListener('DOMContentLoaded', () => {
    const premise = document.getElementById('premise');
    if (premise) {
        premise.addEventListener('input', () => {
            if (premise.value.trim()) {
                document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('selected'));
                selectedScenario = null;
            }
        });
    }
});

// Show dice roll animation
function showDiceRoll(rollData) {
    const display = document.getElementById('diceDisplay');
    const label = display.querySelector('.dice-label');
    const value = display.querySelector('.dice-value');
    const details = display.querySelector('.dice-details');
    
    label.textContent = rollData.type;
    value.textContent = rollData.total;
    details.textContent = rollData.details || '';
    
    display.classList.remove('hidden');
    
    setTimeout(() => {
        display.classList.add('hidden');
    }, 5000);
}

// Update entire UI
function updateUI() {
    if (!gameState) return;
    
    updateCharacterSheet();
    updateLocationTime();
    updateCombatIndicator();
}

// Update character sheet
function updateCharacterSheet() {
    if (!gameState || !gameState.character) return;
    
    const char = gameState.character;
    
    // Basic info
    document.getElementById('charName').textContent = char.name;
    document.getElementById('charRace').textContent = char.race;
    document.getElementById('charClass').textContent = `${char.class_name} ${char.level}`;
    document.getElementById('charLevel').textContent = char.level;
    
    // HP
    const current_hp = char.hit_points ? char.hit_points.current : char.hit_points_current || 0;
    const max_hp = char.hit_points ? char.hit_points.maximum : char.hit_points_maximum || 0;
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
    
    // Inventory - The backend sends currency and inventory
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
    } else {
        indicator.classList.add('hidden');
    }
}

// Save game
async function saveGame() {
    if (!currentGameId) return;
    
    saveGameBtn.disabled = true;
    saveGameBtn.textContent = 'Saving...';
    
    try {
        // Game auto-saves on server, but we can trigger a manual save
        await loadGameState();
        showNotification('Game saved successfully!');
    } catch (error) {
        console.error('Failed to save game:', error);
        showError('Failed to save game.');
    } finally {
        saveGameBtn.disabled = false;
        saveGameBtn.textContent = '💾 Save';
    }
}

// Show error message
function showError(message) {
    const errorMsg = document.createElement('div');
    errorMsg.className = 'message system';
    errorMsg.style.background = '#f44336';
    errorMsg.innerHTML = `<p>Error: ${message}</p>`;
    chatMessages.appendChild(errorMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'message system';
    notification.style.background = '#4caf50';
    notification.innerHTML = `<p>${message}</p>`;
    chatMessages.appendChild(notification);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}