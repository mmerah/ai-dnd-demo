"""Service for managing scenarios."""

import json
from pathlib import Path
from typing import Optional, List, Dict
from app.models.scenario import Scenario


class ScenarioService:
    """Service for loading and managing scenarios."""
    
    def __init__(self, data_directory: Optional[Path] = None):
        """
        Initialize scenario service.
        
        Args:
            data_directory: Path to data directory containing scenarios
        """
        if data_directory is None:
            # Default to app/data directory
            data_directory = Path(__file__).parent.parent / "data"
        self.data_directory = data_directory
        self._scenarios: Dict[str, Scenario] = {}
        self._load_all_scenarios()
    
    def _load_all_scenarios(self) -> None:
        """Load all available scenarios from data directory."""
        # Load the main scenario.json
        scenario_path = self.data_directory / "scenario.json"
        if scenario_path.exists():
            scenario = self.load_scenario_from_file(scenario_path)
            if scenario:
                self._scenarios[scenario.id] = scenario
        
        # Also check for a scenarios directory with multiple scenarios
        scenarios_dir = self.data_directory / "scenarios"
        if scenarios_dir.exists() and scenarios_dir.is_dir():
            for scenario_file in scenarios_dir.glob("*.json"):
                scenario = self.load_scenario_from_file(scenario_file)
                if scenario:
                    self._scenarios[scenario.id] = scenario
    
    def load_scenario_from_file(self, file_path: Path) -> Optional[Scenario]:
        """
        Load a scenario from a JSON file.
        
        Args:
            file_path: Path to scenario JSON file
            
        Returns:
            Loaded Scenario object or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add ID based on filename if not present
            if 'id' not in data:
                data['id'] = file_path.stem
            
            return Scenario(**data)
        except Exception as e:
            print(f"Failed to load scenario from {file_path}: {e}")
            return None
    
    def get_scenario(self, scenario_id: str = "scenario") -> Optional[Scenario]:
        """
        Get a scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to retrieve
            
        Returns:
            Scenario object or None if not found
        """
        return self._scenarios.get(scenario_id)
    
    def get_default_scenario(self) -> Optional[Scenario]:
        """
        Get the default scenario.
        
        Returns:
            Default scenario or first available scenario
        """
        # Try to get the main scenario.json first
        if "scenario" in self._scenarios:
            return self._scenarios["scenario"]
        
        # Otherwise return the first available scenario
        if self._scenarios:
            return next(iter(self._scenarios.values()))
        
        return None
    
    def list_scenarios(self) -> List[Dict[str, str]]:
        """
        List all available scenarios.
        
        Returns:
            List of scenario summaries
        """
        scenarios = []
        for scenario_id, scenario in self._scenarios.items():
            scenarios.append({
                "id": scenario_id,
                "title": scenario.title,
                "description": scenario.description
            })
        return scenarios
    
    def get_scenario_context_for_ai(self, scenario: Scenario, current_location_id: str) -> str:
        """
        Generate scenario context for AI.
        
        Args:
            scenario: The scenario object
            current_location_id: Current location ID
            
        Returns:
            Context string for AI
        """
        context_parts = []
        
        # Add scenario overview
        context_parts.append(f"Scenario: {scenario.title}")
        context_parts.append(f"Description: {scenario.description}")
        
        # Add current location details
        location = scenario.get_location(current_location_id)
        if location:
            context_parts.append(f"\nCurrent Location: {location.name}")
            context_parts.append(f"Description: {location.description}")
            
            if location.npcs:
                npc_list = ", ".join([npc.name for npc in location.npcs])
                context_parts.append(f"NPCs present: {npc_list}")
            
            if location.environmental_features:
                context_parts.append(f"Environmental features: {', '.join(location.environmental_features)}")
            
            if location.connections:
                connected_locations = []
                for conn_id in location.connections:
                    conn_loc = scenario.get_location(conn_id)
                    if conn_loc:
                        connected_locations.append(conn_loc.name)
                if connected_locations:
                    context_parts.append(f"Connected locations: {', '.join(connected_locations)}")
        
        # Add current act/progression info
        for act_name, act in [("Act 1", scenario.progression.act1), 
                               ("Act 2", scenario.progression.act2),
                               ("Act 3", scenario.progression.act3),
                               ("Act 4", scenario.progression.act4)]:
            if act and current_location_id in act.locations:
                context_parts.append(f"\nCurrent Act: {act_name} - {act.name}")
                context_parts.append(f"Act Objectives: {', '.join(act.objectives)}")
                break
        
        return "\n".join(context_parts)