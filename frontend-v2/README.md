# AI D&D Frontend v2.0

TypeScript-based frontend following SOLID principles, clean architecture, and DRY patterns.

## Features

- **Type Safety**: TypeScript with strict mode, zero `any` types
- **Generated Types**: Auto-generated from backend Pydantic models
- **Clean Architecture**: Layered design with dependency injection
- **Three-Panel Layout**: Location/Chronicle | Chat | Party/Combat/Character
- **Observable State**: Reactive state management pattern
- **Component-Based**: Lifecycle-aware components with automatic cleanup

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8123

### Installation

```bash
npm install
```

### Development

```bash
# Generate types from backend (backend must be running)
npm run generate:types

# Start dev server with hot reload
npm run dev

# Type check only
npm run type-check
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── types/
│   ├── generated/          # Auto-generated from backend (DO NOT EDIT)
│   ├── api.ts              # API request/response contracts
│   ├── sse.ts              # SSE event types
│   └── ui.ts               # UI-specific types
├── models/                 # Data models with validation
├── services/               # Business logic & external communication
│   ├── api/                # HTTP API services
│   ├── sse/                # SSE connection & event handlers
│   └── state/              # State management (Observable pattern)
├── components/             # UI components
│   ├── base/               # Component base class
│   ├── chat/               # Chat panel components
│   ├── character/          # Character sheet components
│   ├── party/              # Party management components
│   ├── combat/             # Combat status components
│   ├── location/           # Location info components
│   ├── chronicle/          # Chronicle/journal components
│   └── catalog/            # Catalog browser components
├── screens/                # Screen controllers
├── utils/                  # Pure utility functions
├── config.ts               # App configuration
├── container.ts            # Dependency injection container
└── main.ts                 # Application bootstrap
```

## Type Generation

Types are automatically generated from the backend Pydantic models to ensure type safety across the stack:

1. Backend exports JSON schemas via `/api/schemas`
2. `npm run generate:types` fetches schemas and converts to TypeScript
3. Generated types in `src/types/generated/` (DO NOT EDIT)
4. Import types from `@/types/generated`

**Generated types match backend models exactly** - any breaking changes are caught at compile time.

## Architecture Principles

### SOLID

- **Single Responsibility**: One class/function = one purpose
- **Open/Closed**: Extend via composition, not modification
- **Liskov Substitution**: Polymorphic components via base class
- **Interface Segregation**: Focused service interfaces
- **Dependency Inversion**: Depend on abstractions, inject dependencies

### DRY

- Shared logic in services
- Reusable components
- No code duplication

### Clean Architecture

```
UI Layer (Components)
    ↓
Controller Layer (Screens)
    ↓
Service Layer (API, SSE, State)
    ↓
Domain Layer (Models, Types)
```

### Fail Fast

- Validate at boundaries
- Explicit error handling
- No silent failures
- Type safety prevents runtime errors

## Code Quality Standards

- **No `any` types** - Use `unknown` with type guards
- **Max file size** - 200 lines (exceptions for generated types)
- **Strict TypeScript** - All strict checks enabled
- **Pure functions** - No side effects in utilities
- **Lifecycle cleanup** - Event listeners cleaned up automatically
- **Test coverage** - >80% for services and utilities

## Testing

```bash
# Run tests
npm run test

# Run tests with UI
npm run test:ui
```

## License

Private
