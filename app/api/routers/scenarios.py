"""Scenario catalog endpoints."""

from fastapi import APIRouter, HTTPException

from app.container import container
from app.models.scenario import ScenarioSheet

router = APIRouter()


@router.get("/scenarios")
async def list_available_scenarios() -> list[ScenarioSheet]:
    """
    List all available scenarios.

    Returns:
        List of scenario summaries

    Raises:
        HTTPException: If scenarios cannot be loaded
    """
    scenario_service = container.scenario_service
    try:
        return scenario_service.list_scenarios()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenarios: {e!s}") from e


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> ScenarioSheet:
    """
    Get a specific scenario by ID.

    Args:
        scenario_id: Unique scenario identifier

    Returns:
        Scenario data

    Raises:
        HTTPException: If scenario not found
    """
    scenario_service = container.scenario_service
    try:
        scenario = scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario with ID '{scenario_id}' not found")
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {e!s}") from e
