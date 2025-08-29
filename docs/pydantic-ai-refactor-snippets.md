# Pydantic-AI Refactor Snippets for AIService

This document contains comprehensive code snippets from pydantic-ai documentation for refactoring the AIService with SOLID principles and modern pydantic-ai patterns.

## Table of Contents
1. [OpenRouter Provider Setup](#openrouter-provider-setup)
2. [Custom System Prompts](#custom-system-prompts)
3. [Tool Registration](#tool-registration)
4. [Model Settings and Parallel Tool Calls](#model-settings-and-parallel-tool-calls)
5. [Event Stream Handlers](#event-stream-handlers)
6. [Thinking Parts](#thinking-parts)
7. [Message History](#message-history)
8. [Streaming Output](#streaming-output)
9. [SOLID Principles and Multiple Agents](#solid-principles-and-multiple-agents)

## OpenRouter Provider Setup

### Basic OpenRouter Configuration
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

model = OpenAIChatModel(
    'anthropic/claude-3.5-sonnet',
    provider=OpenRouterProvider(api_key='your-openrouter-api-key'),
)
agent = Agent(model)
```

### OpenAI-Compatible Model with Custom Base URL
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>.com', 
        api_key='your-api-key'
    ),
)
agent = Agent(model)
```

### Custom Model Profile with Strict Tool Definitions
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles import InlineDefsJsonSchemaTransformer
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>.com', 
        api_key='your-api-key'
    ),
    profile=OpenAIModelProfile(
        json_schema_transformer=InlineDefsJsonSchemaTransformer,
        openai_supports_strict_tool_definition=False
    )
)
agent = Agent(model)
```

### Environment Variable Configuration
```bash
export OPENROUTER_API_KEY='your-openrouter-api-key'
```

## Custom System Prompts

### Static and Dynamic System Prompts
```python
from datetime import date
from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,
    system_prompt="Use the customer's name while replying to them.",  # Static prompt
)

@agent.system_prompt  # Dynamic prompt
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."

@agent.system_prompt
def add_the_date() -> str:
    return f'The date is {date.today()}.'

result = agent.run_sync('What is the date?', deps='Frank')
```

### Instructions (Similar to System Prompts)
```python
from datetime import date
from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,
    instructions="Use the customer's name while replying to them.",
)

@agent.instructions
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."
```

### System Prompt with Dependencies
```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

    async def system_prompt_factory(self) -> str:
        response = await self.http_client.get('https://example.com')
        response.raise_for_status()
        return f'Prompt: {response.text}'

joke_agent = Agent('openai:gpt-4o', deps_type=MyDeps)

@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    return await ctx.deps.system_prompt_factory()
```

## Tool Registration

### Basic Tool Registration
```python
import random
from pydantic_ai import Agent, RunContext

agent = Agent(
    'google-gla:gemini-1.5-flash',
    deps_type=str,
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
)

@agent.tool_plain  # Tool without context
def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))

@agent.tool  # Tool with context
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps

dice_result = agent.run_sync('My guess is 4', deps='Anne')
```

### Advanced Tool Registration with Schema
```python
from pydantic_ai import Agent, Tool
from pydantic_ai.models.test import TestModel

def foobar(**kwargs) -> str:
    return kwargs['a'] + kwargs['b']

tool = Tool.from_schema(
    function=foobar,
    name='sum',
    description='Sum two numbers.',
    json_schema={
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'the first number', 'type': 'integer'},
            'b': {'description': 'the second number', 'type': 'integer'},
        },
        'required': ['a', 'b'],
        'type': 'object',
    },
    takes_ctx=False,
)

test_model = TestModel()
agent = Agent(test_model, tools=[tool])
```

### Dynamic Tool Preparation
```python
from typing import Union
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition

agent = Agent('test')

async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> Union[ToolDefinition, None]:
    if ctx.deps == 42:
        return tool_def

@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'

result = agent.run_sync('testing...', deps=41)  # Tool not available
result = agent.run_sync('testing...', deps=42)  # Tool available
```

### Tool Return with Multi-Modal Content
```python
import time
from pydantic_ai import Agent
from pydantic_ai.messages import ToolReturn, BinaryContent

agent = Agent('openai:gpt-4o')

@agent.tool_plain
def click_and_capture(x: int, y: int) -> ToolReturn:
    """Click at coordinates and show before/after screenshots."""
    before_screenshot = capture_screen()
    perform_click(x, y)
    time.sleep(0.5)
    after_screenshot = capture_screen()

    return ToolReturn(
        return_value=f"Successfully clicked at ({x}, {y})",
        content=[
            f"Clicked at coordinates ({x}, {y}). Here's the comparison:",
            "Before:",
            BinaryContent(data=before_screenshot, media_type="image/png"),
            "After:",
            BinaryContent(data=after_screenshot, media_type="image/png"),
            "Please analyze the changes and suggest next steps."
        ],
        metadata={
            "coordinates": {"x": x, "y": y},
            "action_type": "click_and_capture",
            "timestamp": time.time()
        }
    )
```

### Toolsets
```python
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

def temperature_celsius(city: str) -> float:
    return 21.0

def temperature_fahrenheit(city: str) -> float:
    return 69.8

weather_toolset = FunctionToolset(tools=[temperature_celsius, temperature_fahrenheit])

@weather_toolset.tool
def conditions(ctx: RunContext, city: str) -> str:
    if ctx.run_step % 2 == 0:
        return "It's sunny"
    else:
        return "It's raining"

agent = Agent(test_model, toolsets=[weather_toolset])
```

## Model Settings and Parallel Tool Calls

### Basic Model Settings
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.settings import ModelSettings

# Model-level defaults
model = OpenAIChatModel(
    'gpt-4o',
    settings=ModelSettings(temperature=0.8, max_tokens=500)
)

# Agent-level defaults (overrides model defaults)
agent = Agent(model, model_settings=ModelSettings(temperature=0.5))

# Run-time overrides (highest priority)
result = agent.run_sync(
    'What is the capital of Italy?',
    model_settings=ModelSettings(temperature=0.0)
)
```

### Parallel Tool Calls Configuration
```python
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.tools import ToolDefinition

# When making direct model requests with tools
model_request_parameters = ModelRequestParameters(
    function_tools=[
        ToolDefinition(
            name='tool_name',
            description='Tool description',
            parameters_json_schema={'type': 'object', 'properties': {}},
        )
    ],
    allow_text_output=True,
    parallel_tool_calls=True  # Enable parallel tool execution
)
```

### Dynamic Tool Strictness for OpenAI
```python
from dataclasses import replace
from typing import Union
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.models.test import TestModel

async def turn_on_strict_if_openai(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    if ctx.model.system == 'openai':
        return [replace(tool_def, strict=True) for tool_def in tool_defs]
    return tool_defs

test_model = TestModel()
agent = Agent(test_model, prepare_tools=turn_on_strict_if_openai)

@agent.tool_plain
def echo(message: str) -> str:
    return message
```

## Event Stream Handlers

### Comprehensive Event Stream Handler
```python
import asyncio
from collections.abc import AsyncIterable
from datetime import date
from pydantic_ai import Agent
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.tools import RunContext

weather_agent = Agent(
    'openai:gpt-4o',
    system_prompt='Providing a weather forecast at the locations the user provides.',
)

@weather_agent.tool
async def weather_forecast(
    ctx: RunContext,
    location: str,
    forecast_date: date,
) -> str:
    return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'

output_messages: list[str] = []

async def event_stream_handler(
    ctx: RunContext,
    event_stream: AsyncIterable[AgentStreamEvent],
):
    async for event in event_stream:
        if isinstance(event, PartStartEvent):
            output_messages.append(f'[Request] Starting part {event.index}: {event.part!r}')
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, TextPartDelta):
                output_messages.append(f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}')
            elif isinstance(event.delta, ThinkingPartDelta):
                output_messages.append(f'[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}')
            elif isinstance(event.delta, ToolCallPartDelta):
                output_messages.append(f'[Request] Part {event.index} args delta: {event.delta.args_delta}')
        elif isinstance(event, FunctionToolCallEvent):
            output_messages.append(
                f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
            )
        elif isinstance(event, FunctionToolResultEvent):
            output_messages.append(f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}')
        elif isinstance(event, FinalResultEvent):
            output_messages.append(f'[Result] The model starting producing a final result (tool_name={event.tool_name})')

async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'
    
    # Stream with event handler
    async with weather_agent.run_stream(user_prompt, event_stream_handler=event_stream_handler) as run:
        async for output in run.stream_text():
            output_messages.append(f'[Output] {output}')
```

## Thinking Parts

### OpenAI Thinking Configuration
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('o3-mini')
settings = OpenAIResponsesModelSettings(
    openai_reasoning_effort='low',
    openai_reasoning_summary='detailed',
)
agent = Agent(model, model_settings=settings)
```

### Anthropic Thinking Configuration
```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-3-7-sonnet-latest')
settings = AnthropicModelSettings(
    anthropic_thinking={'type': 'enabled', 'budget_tokens': 1024},
)
agent = Agent(model, model_settings=settings)
```

### Google Model Thinking Configuration
```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model = GoogleModel('gemini-2.5-pro-preview-03-25')
settings = GoogleModelSettings(google_thinking_config={'include_thoughts': True})
agent = Agent(model, model_settings=settings)
```

## Message History

### Basic Message History Usage
```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

# First run
result1 = agent.run_sync('Tell me a joke.')
print(result1.output)

# Second run with history
result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)

# Access all messages
print(result2.all_messages())
```

### History Processors
```python
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the last 5 messages to manage token usage."""
    return messages[-5:] if len(messages) > 5 else messages

agent = Agent('openai:gpt-4o', history_processors=[keep_recent_messages])
```

### Context-Aware History Processor
```python
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.tools import RunContext

def context_aware_processor(
    ctx: RunContext[None],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Access current usage
    current_tokens = ctx.usage.total_tokens
    
    # Filter messages based on context
    if current_tokens > 1000:
        return messages[-3:]  # Keep only recent messages when token usage is high
    return messages

agent = Agent('openai:gpt-4o', history_processors=[context_aware_processor])
```

### Serializing Messages for Persistence
```python
from pydantic_core import to_jsonable_python, to_json
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()

# Convert to JSON-compatible Python objects
as_python_objects = to_jsonable_python(history_step_1)
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

# Or directly to JSON
as_json_objects = to_json(history_step_1)
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_json(as_json_objects)
```

## Streaming Output

### Basic Text Streaming
```python
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-1.5-flash')

async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text():
            print(message)  # Full accumulated text
```

### Delta Streaming
```python
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-1.5-flash')

async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):
            print(message)  # Only new text delta
```

### Structured Output Streaming
```python
from datetime import date
from typing_extensions import TypedDict, NotRequired
from pydantic_ai import Agent

class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]

agent = Agent(
    'openai:gpt-4o',
    output_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)

async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream_output():
            print(profile)  # Partial structured output
```

### Streaming with Validation
```python
from datetime import date
from pydantic import ValidationError
from typing_extensions import TypedDict
from pydantic_ai import Agent

class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str

agent = Agent('openai:gpt-4o', output_type=UserProfile)

async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990'
    async with agent.run_stream(user_input) as result:
        async for message, last in result.stream_responses(debounce_by=0.01):
            try:
                profile = await result.validate_response_output(
                    message,
                    allow_partial=not last,
                )
            except ValidationError:
                continue
            print(profile)
```

## SOLID Principles and Multiple Agents

### Agent Delegation Pattern
```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

@dataclass
class ClientAndKey:
    http_client: httpx.AsyncClient
    api_key: str

# Selection Agent
joke_selection_agent = Agent(
    'openai:gpt-4o',
    deps_type=ClientAndKey,
    system_prompt=(
        'Use the `joke_factory` tool to generate some jokes on the given subject, '
        'then choose the best. You must return just a single joke.'
    ),
)

# Generation Agent
joke_generation_agent = Agent(
    'gemini-1.5-flash',
    deps_type=ClientAndKey,
    output_type=list[str],
    system_prompt=(
        'Use the "get_jokes" tool to get some jokes on the given subject, '
        'then extract each joke into a list.'
    ),
)

@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[ClientAndKey], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        deps=ctx.deps,
        usage=ctx.usage,
    )
    return r.output

@joke_generation_agent.tool
async def get_jokes(ctx: RunContext[ClientAndKey], count: int) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com',
        params={'count': count},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text

async def main():
    async with httpx.AsyncClient() as client:
        deps = ClientAndKey(client, 'foobar')
        result = await joke_selection_agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        print(result.usage())
```

### Multiple Output Types
```python
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput

class Fruit(BaseModel):
    name: str
    color: str

class Vehicle(BaseModel):
    name: str
    wheels: int

agent = Agent(
    'openai:gpt-4o',
    output_type=[
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ],
)

result = agent.run_sync('What is a banana?')
print(repr(result.output))  # Fruit(name='banana', color='yellow')
```

### Agent Factory Pattern for Multiple Specialized Agents
```python
from enum import Enum
from typing import Protocol
from pydantic_ai import Agent
from dataclasses import dataclass

class AgentType(Enum):
    NARRATIVE = "narrative"
    COMBAT = "combat"
    SUMMARIZER = "summarizer"

class BaseAgent(Protocol):
    """Protocol for all specialized agents"""
    async def process(self, context: dict) -> str:
        ...

@dataclass
class NarrativeAgent:
    agent: Agent
    
    async def process(self, context: dict) -> str:
        result = await self.agent.run(
            context.get('prompt'),
            deps=context.get('deps')
        )
        return result.output

@dataclass
class CombatAgent:
    agent: Agent
    
    async def process(self, context: dict) -> str:
        # Specialized combat logic
        result = await self.agent.run(
            context.get('prompt'),
            deps=context.get('deps')
        )
        return result.output

class AgentFactory:
    """Factory for creating specialized agents"""
    
    @staticmethod
    def create_agent(agent_type: AgentType, model: str = 'openai:gpt-4o') -> BaseAgent:
        if agent_type == AgentType.NARRATIVE:
            agent = Agent(
                model,
                system_prompt="You are a narrative DM for D&D 5e...",
            )
            return NarrativeAgent(agent)
        elif agent_type == AgentType.COMBAT:
            agent = Agent(
                model,
                system_prompt="You handle combat encounters in D&D 5e...",
            )
            return CombatAgent(agent)
        elif agent_type == AgentType.SUMMARIZER:
            agent = Agent(
                model,
                system_prompt="You summarize game sessions...",
            )
            return NarrativeAgent(agent)  # Reuse NarrativeAgent for summarizer
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

# Usage
narrative_agent = AgentFactory.create_agent(AgentType.NARRATIVE)
combat_agent = AgentFactory.create_agent(AgentType.COMBAT)
```

## Complete Agent Setup Example

```python
from dataclasses import dataclass
from typing import Optional
import httpx
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.messages import ModelMessage

# Dependencies
@dataclass
class AgentDependencies:
    game_id: str
    http_client: httpx.AsyncClient
    api_key: str

# Output type
class AgentOutput(BaseModel):
    narrative: str
    tool_calls: list[str]
    metadata: dict

# Model setup
model = OpenAIChatModel(
    'openai/gpt-oss-120b',
    provider=OpenRouterProvider(api_key='your-openrouter-api-key'),
)

# Agent configuration
agent = Agent(
    model,
    deps_type=AgentDependencies,
    output_type=AgentOutput,
    system_prompt="You are an AI Dungeon Master for D&D 5e...",
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=1000,
    )
)

# Dynamic system prompt
@agent.system_prompt
async def add_game_context(ctx: RunContext[AgentDependencies]) -> str:
    # Fetch game state from API
    response = await ctx.deps.http_client.get(
        f'https://api.example.com/games/{ctx.deps.game_id}',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    game_state = response.json()
    return f"Current game state: {game_state}"

# Tools
@agent.tool
async def roll_dice(ctx: RunContext[AgentDependencies], dice_notation: str) -> str:
    """Roll dice in standard notation (e.g., '2d6+3')"""
    # Implementation here
    return "Rolled: 15"

@agent.tool_plain
def calculate_damage(base_damage: int, modifiers: list[int]) -> int:
    """Calculate total damage with modifiers"""
    return base_damage + sum(modifiers)

# History processor
async def limit_history(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only recent messages to manage context"""
    return messages[-10:] if len(messages) > 10 else messages

agent._history_processors = [limit_history]

# Usage
async def main():
    async with httpx.AsyncClient() as client:
        deps = AgentDependencies(
            game_id="game-123",
            http_client=client,
            api_key="api-key"
        )
        
        # Regular run
        result = await agent.run("The player attacks the goblin", deps=deps)
        print(result.output)
        
        # Streaming run
        async with agent.run_stream("Describe the tavern", deps=deps) as stream:
            async for text in stream.stream_text(delta=True):
                print(text, end="")
```

## Key Patterns for Refactoring

1. **Dependency Injection**: Use dataclasses for dependencies, pass them through RunContext
2. **Tool Organization**: Group tools by domain (dice_tools, character_tools, etc.)
3. **Model Configuration**: Use ModelSettings for fine-tuning, provider-specific settings
4. **Event Handling**: Implement event_stream_handler for logging and monitoring
5. **Message History**: Use history processors for token management
6. **Streaming**: Support both full and delta streaming for real-time responses
7. **Multiple Agents**: Use factory pattern or delegation for specialized agents
8. **Error Handling**: Use ModelRetry for recoverable errors
9. **Persistence**: Serialize messages for saving/loading conversations
10. **Testing**: Use TestModel and FunctionModel for unit testing

## Notes for Implementation

- Always use type hints and Pydantic models for validation
- Implement proper error handling with try/except blocks
- Use async/await throughout for better performance
- Keep agents focused on single responsibilities (SOLID)
- Use toolsets to organize related tools
- Implement proper logging with event handlers
- Support both sync and async execution where appropriate
- Use environment variables for sensitive configuration
- Implement proper message history management for context
- Consider token usage and implement appropriate limits