1. In system prompt: In dialogues, let the player talk back and forth with npcs. Never talk for or assume what the player wants to say
2. Double/Triple tool call streamed to the frontend should be fixed.
3. Spam backend log should be fixed:
```
2025-08-29 15:44:58,939 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:58,953 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:58,962 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:58,976 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:58,978 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:58,988 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:59,001 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:59,006 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))
2025-08-29 15:44:59,023 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=''))

2025-08-29 15:45:01,461 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=','))
2025-08-29 15:45:01,461 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' order'))
2025-08-29 15:45:01,470 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' a'))
2025-08-29 15:45:01,482 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' drink'))
2025-08-29 15:45:01,483 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' and'))
2025-08-29 15:45:01,483 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' rest'))
2025-08-29 15:45:01,483 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=','))
2025-08-29 15:45:01,499 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' head'))
2025-08-29 15:45:01,500 - app.agents.narrative_agent - DEBUG - Event details: PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' out'))
```