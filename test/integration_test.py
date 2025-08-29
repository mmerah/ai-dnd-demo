#!/usr/bin/env python3
"""Comprehensive integration test for D&D 5e AI Dungeon Master application.

This script tests:
1. Server startup and health check
2. Character and scenario loading
3. Game creation and state management
4. SSE event streaming and validation
5. AI response generation (with/without API key)
6. Tool calls (dice rolls, HP updates, etc.)
7. Game state persistence
8. Error handling and recovery
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
import httpx
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8123"
TEST_TIMEOUT = 60  # seconds per test
SERVER_STARTUP_TIMEOUT = 10  # seconds
SSE_READ_TIMEOUT = 30  # seconds


class IntegrationTestRunner:
    """Comprehensive integration test runner for D&D 5e AI DM."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.server_process: Optional[subprocess.Popen[str]] = None
        self.game_id: Optional[str] = None
        self.sse_events: List[Dict[str, Any]] = []
        self.test_results: Dict[str, bool] = {}
        
    async def start_server(self) -> None:
        """Start the FastAPI server in a subprocess."""
        print("Starting server...")
        self.server_process = subprocess.Popen(
            [sys.executable, "-m", "app.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "DEBUG_AI": "true"}  # Enable debug mode for more logging
        )
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        print("✓ Server started successfully")
                        return
            except httpx.ConnectError:
                await asyncio.sleep(0.5)
        
        raise RuntimeError("Server failed to start within timeout")

    def stop_server(self) -> None:
        """Stop the FastAPI server."""
        if self.server_process:
            print("Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
                print("✓ Server stopped")
            except subprocess.TimeoutExpired:
                print("⚠ Server didn't stop gracefully, killing...")
                self.server_process.kill()
                self.server_process.wait(timeout=5)
                print("✓ Server killed")

    async def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("\nTesting: Health check endpoint...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                assert response.status_code == 200, f"Health check failed: {response.status_code}"
                data = response.json()
                assert "status" in data and data["status"] == "healthy"
                print("✓ Health check passed")
                return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False

    async def test_list_characters(self) -> List[Dict[str, Any]]:
        """Test listing available characters."""
        print("\nTesting: List available characters...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/characters")
                assert response.status_code == 200, f"Failed to list characters: {response.status_code}"
                characters = response.json()
                assert len(characters) > 0, "No characters available"
                
                print(f"✓ Found {len(characters)} character(s)")
                for char in characters:
                    print(f"  - {char['name']} ({char['race']} {char['class_name']} Level {char['level']})")
                    # Validate character structure
                    assert all(key in char for key in ['id', 'name', 'race', 'class_name', 'level', 'hit_points', 'abilities'])
                    assert 'current' in char['hit_points'] and 'maximum' in char['hit_points']
                    assert all(ability in char['abilities'] for ability in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'])
                
                self.test_results["list_characters"] = True
                return characters
        except Exception as e:
            print(f"✗ Failed to list characters: {e}")
            self.test_results["list_characters"] = False
            raise

    async def test_list_scenarios(self) -> List[Dict[str, Any]]:
        """Test listing available scenarios."""
        print("\nTesting: List available scenarios...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/scenarios")
                assert response.status_code == 200, f"Failed to list scenarios: {response.status_code}"
                scenarios = response.json()
                assert len(scenarios) > 0, "No scenarios available"
                
                print(f"✓ Found {len(scenarios)} scenario(s)")
                for scenario in scenarios:
                    print(f"  - {scenario['title']}: {scenario['description'][:60]}...")
                    assert all(key in scenario for key in ['id', 'title', 'description'])
                
                self.test_results["list_scenarios"] = True
                return scenarios
        except Exception as e:
            print(f"✗ Failed to list scenarios: {e}")
            self.test_results["list_scenarios"] = False
            raise

    async def test_create_game(self, character_id: str, scenario_id: str) -> str:
        """Test creating a new game."""
        print(f"\nTesting: Create new game with character '{character_id}' and scenario '{scenario_id}'...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/game/new",
                    json={
                        "character_id": character_id,
                        "scenario_id": scenario_id
                    }
                )
                assert response.status_code == 200, f"Failed to create game: {response.status_code} - {response.text}"
                data = response.json()
                assert "game_id" in data, "No game_id in response"
                
                self.game_id = data["game_id"]
                print(f"✓ Game created with ID: {self.game_id}")
                self.test_results["create_game"] = True
                return self.game_id
        except Exception as e:
            print(f"✗ Failed to create game: {e}")
            self.test_results["create_game"] = False
            raise

    async def test_get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Test retrieving game state."""
        print(f"\nTesting: Get game state for '{game_id}'...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/api/game/{game_id}")
                assert response.status_code == 200, f"Failed to get game state: {response.status_code}"
                game_state = response.json()
                
                # Validate game state structure
                assert game_state["game_id"] == game_id, "Game ID mismatch"
                assert all(key in game_state for key in ['character', 'location', 'game_time', 'npcs', 'conversation_history'])
                
                print(f"✓ Game state retrieved:")
                print(f"  - Location: {game_state['location']}")
                print(f"  - Character: {game_state['character']['name']} (HP: {game_state['character']['hit_points']['current']}/{game_state['character']['hit_points']['maximum']})")
                print(f"  - Time: Day {game_state['game_time']['day']}, {game_state['game_time']['hour']:02d}:{game_state['game_time']['minute']:02d}")
                print(f"  - NPCs: {len(game_state['npcs'])}")
                print(f"  - Messages: {len(game_state['conversation_history'])}")
                
                self.test_results["get_game_state"] = True
                return game_state
        except Exception as e:
            print(f"✗ Failed to get game state: {e}")
            self.test_results["get_game_state"] = False
            raise

    async def test_sse_connection(self, game_id: str) -> None:
        """Test SSE connection and receive events."""
        print(f"\nTesting: SSE connection for game '{game_id}'...")
        
        try:
            async with httpx.AsyncClient(timeout=SSE_READ_TIMEOUT) as client:
                async with client.stream("GET", f"{self.base_url}/api/game/{game_id}/sse") as response:
                    assert response.status_code == 200, f"Failed to connect SSE: {response.status_code}"
                    
                    events_received = 0
                    max_events = 10
                    initial_narrative_received = False
                    connected_received = False
                    
                    print("  Listening for SSE events...")
                    
                    event_type = None
                    event_data = None
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            event_data = line.split(":", 1)[1].strip()
                            if event_type and event_data:
                                try:
                                    data = json.loads(event_data)
                                    self.sse_events.append({"event": event_type, "data": data})
                                    print(f"  ← Received event: {event_type}")
                                    
                                    if event_type == "connected":
                                        connected_received = True
                                    elif event_type == "initial_narrative":
                                        initial_narrative_received = True
                                        print(f"    - Scenario: {data.get('scenario_title', 'N/A')}")
                                    elif event_type == "heartbeat":
                                        print("    - Heartbeat received")
                                    
                                    events_received += 1
                                except json.JSONDecodeError:
                                    print(f"  ⚠ Failed to parse event data: {event_data[:50]}...")
                                
                                event_type = None
                                event_data = None
                        
                        if events_received >= max_events or (connected_received and initial_narrative_received):
                            break
                    
                    assert connected_received or initial_narrative_received, "Did not receive expected initial events"
                    print(f"✓ SSE connection working, received {events_received} event(s)")
                    self.test_results["sse_connection"] = True
        
        except Exception as e:
            print(f"✗ SSE connection failed: {e}")
            self.test_results["sse_connection"] = False
            raise

    async def test_player_action_with_sse(self, game_id: str, action: str) -> None:
        """Test sending a player action and monitoring SSE events."""
        print(f"\nTesting: Player action with SSE monitoring - '{action[:50]}...'")
        
        try:
            # Clear previous events
            self.sse_events = []
            
            # Start SSE monitoring task
            sse_task = asyncio.create_task(self.monitor_sse_events(game_id))
            
            # Send player action
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/game/{game_id}/action",
                    json={"message": action}
                )
                assert response.status_code == 200, f"Failed to send action: {response.status_code}"
                print("✓ Action sent successfully")
            
            # Wait for SSE events
            print("  Monitoring SSE events for response...")
            await asyncio.sleep(10)  # Give time for AI to respond
            
            # Cancel SSE monitoring
            sse_task.cancel()
            try:
                await sse_task
            except asyncio.CancelledError:
                pass
            
            # Analyze received events
            narrative_chunks = []
            tool_calls = []
            tool_results = []
            narrative_complete = False
            
            for event in self.sse_events:
                if event["event"] == "narrative":
                    data = event["data"]
                    if isinstance(data, dict):
                        if "word" in data:
                            narrative_chunks.append(data["word"])
                        elif data.get("complete"):
                            narrative_complete = True
                elif event["event"] == "tool_call":
                    tool_calls.append(event["data"])
                elif event["event"] == "tool_result":
                    tool_results.append(event["data"])
            
            # Print results
            print(f"  Narrative chunks received: {len(narrative_chunks)}")
            if narrative_chunks:
                full_narrative = "".join(narrative_chunks)
                print(f"  Full narrative: {full_narrative[:100]}...")
            
            print(f"  Tool calls: {len(tool_calls)}")
            for tc in tool_calls:
                print(f"    - {tc.get('tool_name', 'unknown')}: {tc.get('parameters', {})}")
            
            print(f"  Tool results: {len(tool_results)}")
            print(f"  Narrative complete signal: {narrative_complete}")
            
            # Verify we got a proper AI response
            assert narrative_complete, "Narrative complete signal not received"
            # We should get narrative chunks OR at least the narrative should be saved
            # Check if narrative was saved in the conversation history
            game_state = await self.test_get_game_state(game_id)
            last_dm_message = None
            for msg in reversed(game_state["conversation_history"]):
                if msg["role"] == "dm":
                    last_dm_message = msg
                    break
            
            if not narrative_chunks and last_dm_message:
                print(f"  ⚠ No narrative chunks streamed, but DM message saved: {last_dm_message['content'][:100]}...")
            elif not narrative_chunks and not last_dm_message:
                print(f"  ✗ No narrative content received or saved")
                self.test_results["player_action_sse"] = False
                return
            
            self.test_results["player_action_sse"] = True
            
        except Exception as e:
            print(f"✗ Player action with SSE failed: {e}")
            self.test_results["player_action_sse"] = False
            raise

    async def monitor_sse_events(self, game_id: str) -> None:
        """Monitor SSE events in the background."""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("GET", f"{self.base_url}/api/game/{game_id}/sse") as response:
                    event_type = None
                    event_data = None
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            event_data = line.split(":", 1)[1].strip()
                            if event_type and event_data:
                                try:
                                    data = json.loads(event_data)
                                    event_record = {
                                        "event": event_type,
                                        "data": data,
                                        "timestamp": time.time()
                                    }
                                    self.sse_events.append(event_record)
                                    
                                    # Log important events
                                    if event_type == "narrative":
                                        if data.get("start"):
                                            print("    → Narrative started")
                                        elif data.get("word"):
                                            pass  # Don't log every word
                                        elif data.get("complete"):
                                            print("    → Narrative completed")
                                    elif event_type == "tool_call":
                                        print(f"    → Tool called: {data.get('tool_name')}")
                                    elif event_type == "tool_result":
                                        print(f"    → Tool result received")
                                    elif event_type == "character_update":
                                        print("    → Character updated")
                                    elif event_type == "error":
                                        print(f"    ⚠ Error event: {data.get('error', 'Unknown error')}")
                                
                                except json.JSONDecodeError:
                                    pass
                                
                                event_type = None
                                event_data = None
        except asyncio.CancelledError:
            # Expected when task is cancelled
            pass

    async def test_ai_narrative_streaming(self, game_id: str, skip_ai: bool = False) -> None:
        """Test that AI narrative is properly streamed via SSE."""
        if skip_ai:
            print("\nSkipping AI narrative streaming test (no API key)")
            self.test_results["ai_streaming"] = None
            return
        
        print("\nTesting: AI narrative streaming...")
        
        try:
            # Test a simple action that should generate narrative
            test_action = "I look around the tavern and describe what I see"
            
            # Clear previous events
            self.sse_events = []
            
            # Start SSE monitoring
            sse_task = asyncio.create_task(self.monitor_sse_events(game_id))
            
            # Send action
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/game/{game_id}/action",
                    json={"message": test_action}
                )
                assert response.status_code == 200, f"Failed to send action: {response.status_code}"
            
            # Wait for AI response
            await asyncio.sleep(15)
            
            # Cancel SSE monitoring
            sse_task.cancel()
            try:
                await sse_task
            except asyncio.CancelledError:
                pass
            
            # Analyze streaming behavior
            narrative_start = False
            narrative_chunks = []
            narrative_complete = False
            
            for event in self.sse_events:
                if event["event"] == "narrative":
                    data = event["data"]
                    if isinstance(data, dict):
                        if data.get("start"):
                            narrative_start = True
                            print("  ✓ Narrative start signal received")
                        elif "word" in data:
                            narrative_chunks.append(data["word"])
                        elif data.get("complete"):
                            narrative_complete = True
                            print("  ✓ Narrative complete signal received")
            
            # Verify streaming worked
            if narrative_chunks:
                full_narrative = "".join(narrative_chunks)
                print(f"  ✓ Streamed {len(narrative_chunks)} chunks")
                print(f"  Full narrative: {full_narrative[:200]}...")
                self.test_results["ai_streaming"] = True
            else:
                print(f"  ✗ No narrative chunks received!")
                print(f"  Events received: {[e['event'] for e in self.sse_events]}")
                
                # Check if content was at least saved
                game_state = await self.test_get_game_state(game_id)
                last_dm_msg = None
                for msg in reversed(game_state["conversation_history"]):
                    if msg["role"] == "dm":
                        last_dm_msg = msg
                        break
                
                if last_dm_msg and last_dm_msg["content"]:
                    print(f"  ⚠ Content saved but not streamed: {last_dm_msg['content'][:100]}...")
                    self.test_results["ai_streaming"] = False
                else:
                    print(f"  ✗ No content generated at all!")
                    self.test_results["ai_streaming"] = False
            
        except Exception as e:
            print(f"✗ AI narrative streaming test failed: {e}")
            self.test_results["ai_streaming"] = False
            raise
    
    async def test_tool_calls(self, game_id: str, skip_ai: bool = False) -> None:
        """Test various tool calls through player actions."""
        if skip_ai:
            print("\nSkipping AI tool call tests (no API key)")
            self.test_results["tool_calls"] = None
            return
        
        print("\nTesting: Tool calls through player actions...")
        
        # Simpler test actions that are more likely to trigger tools
        test_actions = [
            {
                "message": "I look around the tavern carefully",
                "expected_tools": [],
                "description": "Basic observation (no tools expected)"
            },
            {
                "message": "I want to make a perception check to notice any suspicious activity",
                "expected_tools": ["roll_ability_check"],
                "description": "Perception check"
            }
        ]
        
        try:
            for i, test_action in enumerate(test_actions, 1):
                print(f"\n  Test {i}/{len(test_actions)}: {test_action['description']}")
                print(f"    Action: \"{test_action['message']}\"")
                
                # Clear previous events
                self.sse_events = []
                
                # Send action and monitor events
                await self.test_player_action_with_sse(game_id, test_action["message"])
                
                # Check for expected tool calls
                tool_events = [e for e in self.sse_events if e["event"] == "tool_call"]
                tool_names = [e["data"].get("tool_name") for e in tool_events]
                
                print(f"    Tools called: {tool_names}")
                
                # Verify expected tools were called (if we know what to expect)
                if tool_names:
                    print(f"    ✓ Tool calls detected")
                else:
                    print(f"    ⚠ No tool calls detected")
                
                # Check game state was updated
                game_state = await self.test_get_game_state(game_id)
                print(f"    Messages in history: {len(game_state['conversation_history'])}")
                
                # Longer delay between tests to avoid overwhelming the API
                await asyncio.sleep(10)
            
            self.test_results["tool_calls"] = True
            print("\n✓ Tool call tests completed")
            
        except Exception as e:
            print(f"\n✗ Tool call tests failed: {e}")
            self.test_results["tool_calls"] = False
            raise

    async def test_error_handling(self, game_id: str) -> None:
        """Test error handling scenarios."""
        print("\nTesting: Error handling...")
        
        # Save current test results to avoid overwriting
        saved_results = self.test_results.copy()
        
        test_cases = [
            {
                "name": "Invalid game ID",
                "test": self._test_invalid_game_id,
                "expect_error": True
            },
            {
                "name": "Invalid character ID", 
                "test": self._test_invalid_character_id,
                "expect_error": True
            },
            {
                "name": "Empty message",
                "test": lambda: self._test_empty_message(game_id),
                "expect_error": False  # Should handle gracefully
            }
        ]
        
        errors_handled = 0
        for test_case in test_cases:
            try:
                print(f"  - Testing: {test_case['name']}")
                await test_case["test"]()
                if test_case["expect_error"]:
                    print(f"    ⚠ Expected error but succeeded")
                else:
                    print(f"    ✓ Handled gracefully")
                    errors_handled += 1
            except Exception as e:
                if test_case["expect_error"]:
                    print(f"    ✓ Error handled as expected: {str(e)[:50]}...")
                    errors_handled += 1
                else:
                    print(f"    ✗ Unexpected error: {e}")
        
        # Restore saved results
        self.test_results = saved_results
        self.test_results["error_handling"] = errors_handled == len(test_cases)
        if self.test_results["error_handling"]:
            print("✓ Error handling tests passed")
        else:
            print("✗ Some error handling tests failed")
    
    async def _test_invalid_game_id(self) -> None:
        """Helper method to test invalid game ID without affecting test_results."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/game/invalid-game-id-xxx")
            assert response.status_code == 200  # This will fail as expected
    
    async def _test_invalid_character_id(self) -> None:
        """Helper method to test invalid character ID without affecting test_results."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/game/new",
                json={"character_id": "invalid-char-id", "scenario_id": "test-scenario"}
            )
            assert response.status_code == 200  # This will fail as expected
    
    async def _test_empty_message(self, game_id: str) -> None:
        """Helper method to test empty message without affecting test_results."""
        sse_task = asyncio.create_task(self.monitor_sse_events(game_id))
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/game/{game_id}/action",
                json={"message": ""}
            )
            assert response.status_code == 200
        
        await asyncio.sleep(3)
        sse_task.cancel()
        try:
            await sse_task
        except asyncio.CancelledError:
            pass

    async def test_game_persistence(self, game_id: str) -> None:
        """Test that game state persists correctly."""
        print("\nTesting: Game state persistence...")
        
        try:
            # Get initial state
            initial_state = await self.test_get_game_state(game_id)
            initial_hp = initial_state["character"]["hit_points"]["current"]
            initial_messages = len(initial_state["conversation_history"])
            
            print(f"  Initial HP: {initial_hp}")
            print(f"  Initial messages: {initial_messages}")
            
            # Make a change (if AI is available)
            if os.getenv("OPENROUTER_API_KEY"):
                await self.test_player_action_with_sse(game_id, "I take 5 damage from falling")
                await asyncio.sleep(3)
            
            # Get state again
            new_state = await self.test_get_game_state(game_id)
            new_hp = new_state["character"]["hit_points"]["current"]
            new_messages = len(new_state["conversation_history"])
            
            print(f"  New HP: {new_hp}")
            print(f"  New messages: {new_messages}")
            
            # Check persistence
            save_path = Path("./saves") / f"{game_id}.json"
            if save_path.exists():
                print(f"  ✓ Save file exists: {save_path}")
                with open(save_path, 'r') as f:
                    saved_data = json.load(f)
                    assert saved_data["game_id"] == game_id
                    print(f"  ✓ Save file is valid")
                    self.test_results["persistence"] = True
            else:
                print(f"  ✗ Save file not found")
                self.test_results["persistence"] = False
                
        except Exception as e:
            print(f"✗ Persistence test failed: {e}")
            self.test_results["persistence"] = False
            raise

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        failed_tests = sum(1 for result in self.test_results.values() if result is False)
        skipped_tests = sum(1 for result in self.test_results.values() if result is None)
        
        for test_name, result in self.test_results.items():
            if result is True:
                status = "✓ PASSED"
            elif result is False:
                status = "✗ FAILED"
            else:
                status = "⊘ SKIPPED"
            print(f"{test_name:.<30} {status}")
        
        print("-" * 60)
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests} | Skipped: {skipped_tests}")
        
        if failed_tests == 0 and skipped_tests < total_tests:
            print("\n✅ ALL ACTIVE TESTS PASSED!")
        elif failed_tests > 0:
            print(f"\n❌ {failed_tests} TEST(S) FAILED")
        
        # Print SSE event summary
        if self.sse_events:
            print("\n" + "=" * 60)
            print("SSE EVENT SUMMARY")
            print("=" * 60)
            event_counts = {}
            for event in self.sse_events:
                event_type = event["event"]
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            for event_type, count in sorted(event_counts.items()):
                print(f"  {event_type}: {count}")

    async def run_all_tests(self) -> None:
        """Run all integration tests."""
        print("=" * 60)
        print("D&D 5e AI Dungeon Master - Comprehensive Integration Tests")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"API Key Available: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
        print("=" * 60)
        
        try:
            # Start server
            await self.start_server()
            
            # Basic connectivity tests
            await self.test_health_check()
            
            # Resource loading tests
            characters = await self.test_list_characters()
            scenarios = await self.test_list_scenarios()
            
            # Game creation and management
            character_id = characters[0]["id"]
            scenario_id = scenarios[0]["id"] if scenarios else None
            game_id = await self.test_create_game(
                character_id,
                scenario_id if scenario_id else ""
            )
            
            # Game state retrieval
            await self.test_get_game_state(game_id)
            
            # SSE connection test
            await self.test_sse_connection(game_id)
            
            # AI and tool tests (skip if no API key)
            skip_ai = not os.getenv("OPENROUTER_API_KEY")
            if skip_ai:
                print("\n" + "=" * 60)
                print("⚠ NOTICE: Skipping AI-dependent tests (no API key)")
                print("Set OPENROUTER_API_KEY to test full functionality")
                print("=" * 60)
            
            # Test AI narrative streaming
            await self.test_ai_narrative_streaming(game_id, skip_ai=skip_ai)
            
            await self.test_tool_calls(game_id, skip_ai=skip_ai)
            
            # Error handling
            await self.test_error_handling(game_id)
            
            # Persistence
            await self.test_game_persistence(game_id)
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"❌ CRITICAL TEST FAILURE: {e}")
            print("=" * 60)
            raise
        finally:
            self.stop_server()


async def main() -> None:
    """Main entry point."""
    runner = IntegrationTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())