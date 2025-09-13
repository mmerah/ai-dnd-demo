"""Content pack registry for managing modular content packages."""

import json
import logging
from pathlib import Path

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.models.content_pack import ContentPackMetadata, ContentPackSummary

logger = logging.getLogger(__name__)


class ContentPackRegistry(IContentPackRegistry):
    """Registry for discovering and managing content packs.

    Manages both SRD base content and user-created content packs,
    handling dependencies and load order resolution.
    """

    def __init__(self, path_resolver: IPathResolver):
        """Initialize the content pack registry.

        Args:
            path_resolver: Service for resolving file paths
        """
        self.path_resolver = path_resolver
        self._packs: dict[str, ContentPackMetadata] = {}
        self._pack_paths: dict[str, Path] = {}
        self._discovered = False

    def discover_packs(self) -> None:
        """Discover all available content packs."""
        if self._discovered:
            return

        # Clear existing data
        self._packs.clear()
        self._pack_paths.clear()

        # Discover SRD pack (base content)
        self._discover_srd_pack()

        # Discover user packs
        self._discover_user_packs()

        self._discovered = True
        logger.info(f"Discovered {len(self._packs)} content packs: {list(self._packs.keys())}")

    def _discover_srd_pack(self) -> None:
        """Discover the SRD base content pack."""
        data_dir = self.path_resolver.get_data_dir()
        metadata_file = data_dir / "metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata_data = json.load(f)
                metadata = ContentPackMetadata(**metadata_data)
                self._packs[metadata.id] = metadata
                self._pack_paths[metadata.id] = data_dir
                logger.debug(f"Loaded SRD pack: {metadata.id}")
            except Exception as e:
                logger.error(f"Failed to load SRD pack metadata: {e}")

    def _discover_user_packs(self) -> None:
        """Discover user-created content packs."""
        user_data_dir = self.path_resolver.get_data_dir().parent / "user-data" / "packs"

        if not user_data_dir.exists():
            logger.debug("User data packs directory does not exist")
            return

        # Scan for pack directories
        for pack_dir in user_data_dir.iterdir():
            if not pack_dir.is_dir():
                continue

            metadata_file = pack_dir / "metadata.json"
            if not metadata_file.exists():
                logger.warning(f"Pack directory {pack_dir.name} missing metadata.json")
                continue

            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata_data = json.load(f)
                metadata = ContentPackMetadata(**metadata_data)

                # Validate pack ID matches directory name
                if metadata.id != pack_dir.name:
                    logger.warning(
                        f"Pack ID mismatch: metadata says '{metadata.id}' " f"but directory is '{pack_dir.name}'"
                    )
                    continue

                self._packs[metadata.id] = metadata
                self._pack_paths[metadata.id] = pack_dir
                logger.debug(f"Loaded user pack: {metadata.id}")

            except Exception as e:
                logger.error(f"Failed to load pack {pack_dir.name}: {e}")

    def get_pack(self, pack_id: str) -> ContentPackMetadata | None:
        """Get metadata for a specific content pack."""
        if not self._discovered:
            self.discover_packs()
        return self._packs.get(pack_id)

    def list_packs(self) -> list[ContentPackSummary]:
        """List all available content packs."""
        if not self._discovered:
            self.discover_packs()

        summaries = []
        for pack in self._packs.values():
            summary = ContentPackSummary(
                id=pack.id,
                name=pack.name,
                version=pack.version,
                author=pack.author,
                description=pack.description,
                pack_type=pack.pack_type,
            )
            summaries.append(summary)

        return sorted(summaries, key=lambda s: s.name)

    def validate_dependencies(self, pack_ids: list[str]) -> tuple[bool, str]:
        """Validate that pack dependencies are satisfied."""
        if not self._discovered:
            self.discover_packs()

        # Check if all requested packs exist
        for pack_id in pack_ids:
            if pack_id not in self._packs:
                return False, f"Content pack '{pack_id}' not found"

        # Build set of all packs that will be loaded
        loaded_packs = set(pack_ids)

        # Check dependencies for each pack
        for pack_id in pack_ids:
            pack = self._packs[pack_id]
            for dep_id in pack.dependencies:
                if dep_id not in loaded_packs and dep_id not in self._packs:
                    return False, f"Pack '{pack_id}' requires missing dependency '{dep_id}'"

                # Add transitive dependencies
                if dep_id not in loaded_packs:
                    loaded_packs.add(dep_id)

        return True, ""

    def get_pack_order(self, pack_ids: list[str]) -> list[str]:
        """Get the order in which packs should be loaded."""
        if not self._discovered:
            self.discover_packs()

        # Validate all packs exist (skip scenario packs as they're virtual)
        for pack_id in pack_ids:
            if not pack_id.startswith("scenario:") and pack_id not in self._packs:
                raise ValueError(f"Content pack '{pack_id}' not found")

        # Build dependency graph including transitive dependencies
        all_packs = set(pack_ids)
        dependencies: dict[str, set[str]] = {}

        # Recursively add all dependencies
        def add_pack_with_deps(pack_id: str) -> None:
            if pack_id in dependencies:
                return

            # Skip dependency resolution for scenario packs
            if pack_id.startswith("scenario:"):
                dependencies[pack_id] = set()
                return

            pack = self._packs.get(pack_id)
            if not pack:
                return

            deps = set()
            for dep_id in pack.dependencies:
                if dep_id in self._packs:
                    deps.add(dep_id)
                    add_pack_with_deps(dep_id)
                    all_packs.add(dep_id)

            dependencies[pack_id] = deps

        for pack_id in pack_ids:
            add_pack_with_deps(pack_id)

        # Topological sort using Kahn's algorithm
        result = []
        in_degree = {pack: 0 for pack in all_packs}

        # Calculate in-degrees
        for pack in all_packs:
            for dep in dependencies.get(pack, set()):
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find all nodes with no incoming edges
        queue = [pack for pack in all_packs if in_degree[pack] == 0]

        while queue:
            # Sort for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Remove edges from current node
            for dep in dependencies.get(current, set()):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        # Check for cycles
        if len(result) != len(all_packs):
            raise ValueError("Circular dependency detected in content packs")

        # Reverse the result so dependencies come first
        result.reverse()

        # Ensure SRD always comes first if present
        if "srd" in result:
            result.remove("srd")
            result.insert(0, "srd")

        return result

    def get_pack_data_path(self, pack_id: str, data_type: str) -> Path | None:
        """Get the path to a specific data file within a content pack.

        Handles both regular content packs and scenario-specific packs.
        Scenario packs use the format "scenario:scenario-id".
        """
        if not self._discovered:
            self.discover_packs()

        # Handle scenario-specific content packs
        if pack_id.startswith("scenario:"):
            scenario_id = pack_id[9:]  # Remove "scenario:" prefix
            scenario_dir = self.path_resolver.get_data_dir() / "scenarios" / scenario_id

            # Map data types to scenario subdirectories
            if data_type == "monsters":
                monsters_dir = scenario_dir / "monsters"
                if monsters_dir.exists() and monsters_dir.is_dir():
                    # Return the directory path for scenario monsters
                    return monsters_dir
            elif data_type == "items":
                items_dir = scenario_dir / "items"
                if items_dir.exists() and items_dir.is_dir():
                    # Return the directory path for scenario items
                    return items_dir
            # TODO(MVP2): Scenarios could have other types in the future (spells, etc.)
            return None

        pack_path = self._pack_paths.get(pack_id)
        if not pack_path:
            return None

        data_file = pack_path / f"{data_type}.json"
        return data_file if data_file.exists() else None
