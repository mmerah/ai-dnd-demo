"""Background tasks for API, following SOLID principles."""

import logging

from app.container import container

logger = logging.getLogger(__name__)


async def process_ai_and_broadcast(game_id: str, message: str) -> None:
    """
    Background task to process AI response and broadcast events.

    Args:
        game_id: Unique game identifier
        message: Player's message/action
    """
    game_service = container.game_service
    ai_service = container.ai_service
    message_service = container.message_service

    logger.info(f"Starting AI processing for game {game_id}")
    try:
        # Load game state
        game_state = game_service.load_game(game_id)
        if not game_state:
            logger.error(f"Game {game_id} not found")
            await message_service.send_error(game_id, f"Game with ID '{game_id}' not found")
            return

        logger.info(f"Requesting AI response for game {game_id}")
        narrative = None

        # Get the AI response (MVP uses non-streaming for simplicity)
        async for chunk in ai_service.generate_response(
            user_message=message,
            game_state=game_state,
            game_service=game_service,
            stream=False,
        ):
            logger.debug(f"Received response: type={chunk.type}")
            if chunk.type == "complete":
                # chunk is CompleteResponse
                from app.models.ai_response import CompleteResponse

                if isinstance(chunk, CompleteResponse):
                    narrative = chunk.narrative
                    break
            elif chunk.type == "error":
                # chunk is ErrorResponse
                from app.models.ai_response import ErrorResponse

                if isinstance(chunk, ErrorResponse):
                    error_msg: str = chunk.message
                    logger.error(f"AI error for game {game_id}: {error_msg}")
                    await message_service.send_error(game_id, error_msg)
                    return

        if not narrative:
            logger.error(f"Failed to get AI response for game {game_id} - narrative is empty")
            await message_service.send_error(game_id, "AI failed to generate a response")
            return

        logger.info(f"AI response received for game {game_id}")

        # Game state is updated by tools during AI response generation
        # Reload the final state
        updated_game_state = game_service.get_game(game_state.game_id)

        if updated_game_state:
            # Save final game state
            game_service.save_game(updated_game_state)

            # Send game state update
            await message_service.send_game_update(game_id, updated_game_state)

        # Send completion event
        await message_service.send_complete(game_id)
        logger.info(f"AI processing completed successfully for game {game_id}")

    except Exception as e:
        logger.exception(f"Error in AI processing for game {game_id}: {e}")
        await message_service.send_error(game_id, str(e), error_type=type(e).__name__)
