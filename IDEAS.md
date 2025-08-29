1. Any and circular dependencies are really destroying the type-safe architecture. We could also enforce SOLID principles better. Notably, dependency inversion might help a lot. Things NEED to be analyzed and reorganized properly so that Any disappear (outside of for JSON results) and no circular dependency exists. All the import in the middle of the files should then disappear !
2. Notably thanks to more SOLID principles, dependency inversion, we need to achieve much better type safety and type hinting. We have numerous places in the code where Any is used but offer no type hinting
3. To be fixed:
```
(venv) toto@toto-VM:~/repos/ai-dnd-demo$ mypy --strict app
app/agents/narrative_agent.py:133: error: Item "dict[str, Any]" of "str | dict[str, Any] | None" has no attribute "strip"  [union-attr]
app/agents/narrative_agent.py:133: error: Item "None" of "str | dict[str, Any] | None" has no attribute "strip"  [union-attr]
app/agents/narrative_agent.py:139: error: Statement is unreachable  [unreachable]
Found 3 errors in 1 file (checked 50 source files)
(venv) toto@toto-VM:~/repos/ai-dnd-demo$ ruff check --fix
app/agents/narrative_agent.py:154:17: SIM102 Use a single `if` statement instead of nested `if` statements
    |
152 |               elif isinstance(event, PartDeltaEvent):
153 |                   # Receiving delta updates
154 |                   if isinstance(event.delta, ThinkingPartDelta):
    |  _________________^
155 | |                     if event.delta.content_delta:
    | |_________________________________________________^ SIM102
156 |                           self.event_logger.log_thinking(event.delta.content_delta)
    |
    = help: Combine `if` statements using `and`

app/agents/narrative_agent.py:193:21: SIM108 Use ternary operator `result_content = str(result.content) if hasattr(result, "content") else str(result)` instead of `if`-`else`-block
    |
191 |                   if hasattr(event, "result"):
192 |                       result = event.result
193 |                       if hasattr(result, "content"):
    |  _____________________^
194 | |                         result_content = str(result.content)
195 | |                     else:
196 | |                         result_content = str(result)
    | |____________________________________________________^ SIM108
197 |   
198 |                   if result_content:
    |
    = help: Replace `if`-`else`-block with `result_content = str(result.content) if hasattr(result, "content") else str(result)`

app/agents/narrative_agent.py:257:17: B007 Loop control variable `tool_name` not used within loop body
    |
256 |             # Extract commands from tool results
257 |             for tool_name, params, result_data in self.captured_events:
    |                 ^^^^^^^^^ B007
258 |                 if result_data and isinstance(result_data, dict) and "commands" in result_data:
259 |                     commands = result_data.get("commands", [])
    |
    = help: Rename unused `tool_name` to `_tool_name`

app/agents/narrative_agent.py:257:28: B007 Loop control variable `params` not used within loop body
    |
256 |             # Extract commands from tool results
257 |             for tool_name, params, result_data in self.captured_events:
    |                            ^^^^^^ B007
258 |                 if result_data and isinstance(result_data, dict) and "commands" in result_data:
259 |                     commands = result_data.get("commands", [])
    |
    = help: Rename unused `params` to `_params`

app/agents/narrative_agent.py:279:25: SIM102 Use a single `if` statement instead of nested `if` statements
    |
277 |                   if isinstance(msg, ModelResponse):
278 |                       for part in msg.parts:
279 |                           if isinstance(part, ToolCallPart):
    |  _________________________^
280 | |                             if isinstance(part.args, dict):
    | |___________________________________________________________^ SIM102
281 |                                   tool_calls.append(
282 |                                       ToolCallEvent(
    |
    = help: Combine `if` statements using `and`

app/events/base.py:35:7: B024 `BaseEvent` is an abstract base class, but it has no abstract methods or properties
   |
34 | @dataclass
35 | class BaseEvent(ABC):
   |       ^^^^^^^^^ B024
36 |     """Base class for events that are broadcast to frontend."""
   |

app/events/handlers/broadcast_handler.py:77:16: UP038 Use `X | Y` in `isinstance` call instead of `(X, Y)`
   |
75 |       def can_handle(self, command: BaseCommand) -> bool:
76 |           """Check if this handler can process the given command."""
77 |           return isinstance(
   |  ________________^
78 | |             command,
79 | |             (
80 | |                 BroadcastNarrativeCommand,
81 | |                 BroadcastToolCallCommand,
82 | |                 BroadcastToolResultCommand,
83 | |                 BroadcastGameUpdateCommand,
84 | |                 BroadcastCharacterUpdateCommand,
85 | |             ),
86 | |         )
   | |_________^ UP038
   |
   = help: Convert to `X | Y`

app/events/handlers/character_handler.py:171:16: UP038 Use `X | Y` in `isinstance` call instead of `(X, Y)`
    |
169 |       def can_handle(self, command: BaseCommand) -> bool:
170 |           """Check if this handler can process the given command."""
171 |           return isinstance(
    |  ________________^
172 | |             command, (UpdateHPCommand, AddConditionCommand, RemoveConditionCommand, UpdateSpellSlotsCommand)
173 | |         )
    | |_________^ UP038
    |
    = help: Convert to `X | Y`

app/events/handlers/inventory_handler.py:133:16: UP038 Use `X | Y` in `isinstance` call instead of `(X, Y)`
    |
131 |     def can_handle(self, command: BaseCommand) -> bool:
132 |         """Check if this handler can process the given command."""
133 |         return isinstance(command, (ModifyCurrencyCommand, AddItemCommand, RemoveItemCommand))
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ UP038
    |
    = help: Convert to `X | Y`

app/events/handlers/time_handler.py:72:21: B007 Loop control variable `slot_key` not used within loop body
   |
70 |             # Restore all spell slots
71 |             if character.spellcasting:
72 |                 for slot_key, slot in character.spellcasting.spell_slots.items():
   |                     ^^^^^^^^ B007
73 |                     slot.current = slot.total
   |
   = help: Rename unused `slot_key` to `_slot_key`

app/events/handlers/time_handler.py:136:16: UP038 Use `X | Y` in `isinstance` call instead of `(X, Y)`
    |
134 |     def can_handle(self, command: BaseCommand) -> bool:
135 |         """Check if this handler can process the given command."""
136 |         return isinstance(command, (ShortRestCommand, LongRestCommand, AdvanceTimeCommand))
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ UP038
    |
    = help: Convert to `X | Y`

app/services/ai_service.py:36:14: UP007 Use `X | Y` for type annotations
   |
36 | AIResponse = Union[NarrativeChunkResponse, CompleteResponse, ErrorResponse]
   |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ UP007
   |
   = help: Convert to `X | Y`

Found 12 errors.
No fixes available (8 hidden fixes can be enabled with the `--unsafe-fixes` option).
```