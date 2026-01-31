from dataclasses import dataclass
from typing import Optional, List

@dataclass
class GameState:
    """Represents the current state of the game."""
    player_x: float = 0.0
    player_y: float = 0.0
    player_vx: float = 0.0
    player_vy: float = 0.0
    player_grounded: bool = False
    stars_collected: int = 0
    total_stars: int = 0
    goal_x: float = 0.0
    goal_y: float = 0.0
    level_width: float = 800.0
    is_dead: bool = False
    level_complete: bool = False
    platforms: List[dict] = None
    hazards: List[dict] = None
    collectibles: List[dict] = None
    raycasts: List[float] = None
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = []
        if self.hazards is None:
            self.hazards = []
        if self.collectibles is None:
            self.collectibles = []
        if self.raycasts is None:
            self.raycasts = []
