"""Background tasks for API, following SOLID principles."""

import logging

from app.container import container
from app.services.broadcast_service import broadcast_service
from app.services.message_service import message_service

logger = logging.getLogger(__name__)


async def process_ai_and_broadcast(game_id: str, message: str) -> None:
    """
    Background task to process AI response and broadcast events.

    Args:
        game_id: Unique game identifier
        message: Player's message/action
    """
    game_service = container.get_game_service()
    ai_service = container.get_ai_service()

    logger.info(f"Starting AI processing for game {game_id}")
    try:
        # Load game state
        game_state = game_service.load_game(game_id)
        if not game_state:
            logger.error(f"Game {game_id} not found")
            await broadcast_service.publish(game_id, "error", {"error": f"Game with ID '{game_id}' not found"})
            return

        logger.info(f"Requesting AI response for game {game_id}")
        narrative = None

        # Get the AI response (MVP uses non-streaming for simplicity)
        async for chunk in ai_service.generate_response(
            user_message=message, game_state=game_state, game_service=game_service, stream=False
        ):
            logger.debug(f"Received response: type={chunk.get('type')}")
            if chunk["type"] == "complete":
                narrative = chunk.get("narrative", "")
                break
            elif chunk["type"] == "error":
                error_msg: str = chunk.get("message", "Unknown error")  # type: ignore[assignment]
                logger.error(f"AI error for game {game_id}: {error_msg}")
                await broadcast_service.publish(game_id, "error", {"error": error_msg})
                return

        if not narrative:
            logger.error(f"Failed to get AI response for game {game_id} - narrative is empty")
            await broadcast_service.publish(game_id, "error", {"error": "AI failed to generate a response"})
            return

        logger.info(f"AI response received for game {game_id}")

        # Game state is updated by tools during AI response generation
        # Reload the final state
        updated_game_state = game_service.get_game(game_state.game_id)

        if updated_game_state:
            # Save final game state
            game_service.save_game(updated_game_state)

            # Send character and game updates
            await message_service.send_character_update(game_id, updated_game_state.character.model_dump())

            import json

            game_state_dict = json.loads(updated_game_state.model_dump_json())
            await message_service.send_game_update(game_id, game_state_dict)

            # Send detailed location update if we have scenario data
            scenario_service = container.get_scenario_service()
            if updated_game_state.scenario_id and updated_game_state.current_location_id:
                scenario = scenario_service.get_scenario(updated_game_state.scenario_id)
                if scenario:
                    location = scenario.get_location(updated_game_state.current_location_id)
                    if location:
                        # Get location state for danger level and NPCs
                        location_state = updated_game_state.get_location_state(updated_game_state.current_location_id)

                        # Format connections for frontend
                        connections = []
                        for conn in location.connections:
                            connections.append(
                                {
                                    "to_location_id": conn.to_location_id,
                                    "description": conn.description,
                                    "direction": conn.direction,
                                    "is_accessible": conn.can_traverse(),
                                    "is_visible": conn.is_visible,
                                }
                            )

                        await message_service.send_location_update(
                            game_id,
                            location.id,
                            location.name,
                            location.get_description(location_state.get_description_variant()),
                            connections,
                            location_state.danger_level.value,
                            location_state.npcs_present,
                        )

            # Send quest update
            active_quests_data = [quest.model_dump() for quest in updated_game_state.active_quests]
            await message_service.send_quest_update(game_id, active_quests_data, updated_game_state.completed_quest_ids)

            # Send act update if we have scenario data
            if updated_game_state.scenario_id and scenario:
                current_act = scenario.progression.get_current_act()
                if current_act:
                    await message_service.send_act_update(
                        game_id, current_act.id, current_act.name, scenario.progression.current_act_index
                    )

        await broadcast_service.publish(game_id, "complete", {"status": "success"})
        logger.info(f"AI processing completed successfully for game {game_id}")

    except Exception as e:
        logger.exception(f"Error in AI processing for game {game_id}: {e}")
        await broadcast_service.publish(game_id, "error", {"error": str(e), "type": type(e).__name__})
