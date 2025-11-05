"""Game service interfaces."""

from app.interfaces.services.game.combat_service import ICombatService
from app.interfaces.services.game.conversation_service import IConversationService
from app.interfaces.services.game.event_manager import IEventManager
from app.interfaces.services.game.game_enrichment_service import IGameEnrichmentService
from app.interfaces.services.game.game_factory import IGameFactory
from app.interfaces.services.game.game_service import IGameService
from app.interfaces.services.game.game_state_manager import IGameStateManager
from app.interfaces.services.game.item_manager_service import IItemManagerService
from app.interfaces.services.game.location_service import ILocationService
from app.interfaces.services.game.metadata_service import IMetadataService
from app.interfaces.services.game.monster_manager_service import IMonsterManagerService
from app.interfaces.services.game.party_service import IPartyService
from app.interfaces.services.game.pre_save_sanitizer import IPreSaveSanitizer
from app.interfaces.services.game.save_manager import ISaveManager

__all__ = [
    "ICombatService",
    "IConversationService",
    "IEventManager",
    "IGameEnrichmentService",
    "IGameFactory",
    "IGameService",
    "IGameStateManager",
    "IItemManagerService",
    "ILocationService",
    "IMetadataService",
    "IMonsterManagerService",
    "IPartyService",
    "IPreSaveSanitizer",
    "ISaveManager",
]
