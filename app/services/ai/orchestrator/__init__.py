"""Modular helpers for the AgentOrchestrator.

Package contains small, focused modules that the orchestrator composes:
- agent_router: select active agent type from GameState
- transitions: handle agent transition summaries and broadcasts
- combat_loop: auto-continue loop for NPC/monster turns
- system_broadcasts: helpers for standard system/auto messages
- state_reload: utility to reload in-memory state from GameService
"""
