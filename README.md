# D&D 5e AI Dungeon Master

A proof-of-concept web application that provides an AI-powered Dungeon Master for D&D 5e gameplay. Players interact with an AI DM through a chat interface with automatic character sheet updates and dice roll visualizations.

## Features

- AI-powered Dungeon Master using OpenRouter API
- Pre-generated ranger character (Aldric Swiftarrow)
- Real-time character sheet updates
- Automated dice rolling with visual feedback
- Server-Sent Events for streaming narrative
- Combat system with initiative tracking
- Spell slot management
- Inventory system
- Save/load game functionality

## Prerequisites

- Python 3.9 or higher
- OpenRouter API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-agent-demo
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_api_key_here
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8123
```

2. Open your browser and navigate to:
```
http://localhost:8123
```

3. Select the pre-generated character and begin your adventure!

## Project Structure

```
├── app/                    # Backend application
│   ├── models/            # Pydantic data models
│   ├── services/          # Business logic services
│   ├── tools/             # D&D game tools
│   ├── api/               # API routes
│   └── data/              # Static game data (spells, items, etc.)
├── frontend/              # Web interface
├── saves/                 # Game save files
└── requirements.txt       # Python dependencies
```

## API Endpoints

- `POST /game/new` - Create a new game
- `GET /game/{game_id}` - Get game state
- `POST /game/{game_id}/action` - Send player action
- `GET /game/{game_id}/sse` - SSE stream for updates
- `GET /characters` - List available characters

## Development

This is an MVP implementation focusing on core functionality. Key architectural principles:
- Strict typing with Pydantic models
- SOLID principles
- Fail-fast error handling
- Sequential tool processing

## Technologies

- **Backend**: FastAPI, Python
- **AI**: PydanticAI with OpenRouter (GPT-OSS-120B model)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Communication**: Server-Sent Events (SSE)
- **Data Storage**: JSON files

## License

This project is a proof-of-concept for educational purposes.