"""
Game State model - represents the complete game state at any moment.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.data.constants import (
    Difficulty,
    TURNS_PER_MONTH,
    TURNS_PER_YEAR,
    SAVE_FILE_VERSION,
)


class TimeState(BaseModel):
    """Game time tracking."""
    current_turn: int = Field(default=1, ge=1)
    current_month: int = Field(default=1, ge=1, le=12)
    current_year: int = Field(default=1, ge=1)

    @property
    def season(self) -> str:
        """Get current season name."""
        if self.current_month in [12, 1, 2]:
            return "Winter"
        elif self.current_month in [3, 4, 5]:
            return "Spring"
        elif self.current_month in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"

    def advance_turn(self) -> None:
        """Move to next turn and update month/year."""
        self.current_turn += 1

        # Update month/year
        if self.current_turn % TURNS_PER_MONTH == 0:
            self.current_month += 1
            if self.current_month > 12:
                self.current_month = 1
                self.current_year += 1

    def __str__(self) -> str:
        return f"Turn {self.current_turn} | {self.season}, Year {self.current_year}"


class PlayerState(BaseModel):
    """Player information and settings."""
    player_name: str = Field(default="Player")
    nation_name: str = Field(default="New Nation")
    nation_id: str = Field(default="player_nation")

    # Starting choices
    primary_element: Optional[str] = None
    starting_general_class: Optional[str] = None

    # Settings
    difficulty: Difficulty = Field(default=Difficulty.NORMAL)
    iron_mode: bool = Field(default=False, description="Permadeath mode")

    # Progression
    achievement_points: int = Field(default=0, ge=0)
    unlocked_achievements: list[str] = Field(default_factory=list)
    unlocked_titles: list[str] = Field(default_factory=list)
    equipped_title: Optional[str] = None

    # Statistics
    total_battles: int = Field(default=0, ge=0)
    battles_won: int = Field(default=0, ge=0)
    battles_lost: int = Field(default=0, ge=0)
    territories_conquered: int = Field(default=0, ge=0)
    gold_earned: int = Field(default=0, ge=0)
    units_recruited: int = Field(default=0, ge=0)
    monsters_summoned: int = Field(default=0, ge=0)

    @property
    def win_rate(self) -> float:
        """Calculate battle win rate."""
        if self.total_battles == 0:
            return 0.0
        return self.battles_won / self.total_battles


class GameState(BaseModel):
    """
    Complete game state - everything needed to save/load a game.

    This is the root model for the entire game state. All game data
    flows through this model for saving, loading, and state management.
    """

    # Metadata
    save_version: str = Field(default=SAVE_FILE_VERSION)
    created_at: datetime = Field(default_factory=datetime.now)
    last_saved: datetime = Field(default_factory=datetime.now)
    playtime_seconds: int = Field(default=0, ge=0)

    # Core State
    time: TimeState = Field(default_factory=TimeState)
    player: PlayerState = Field(default_factory=PlayerState)

    # Game World (to be expanded in future phases)
    nations: dict[str, dict] = Field(default_factory=dict, description="All nations in the world")
    territories: dict[str, dict] = Field(default_factory=dict, description="All territories")
    units: dict[str, dict] = Field(default_factory=dict, description="All units (generals + armies)")

    # Active State
    active_quest_ids: list[str] = Field(default_factory=list)
    completed_quest_ids: list[str] = Field(default_factory=list)
    world_events: list[dict] = Field(default_factory=list)

    # Combat State (None when not in battle)
    current_battle: Optional[dict] = Field(default=None)

    # Flags and Triggers
    story_flags: dict[str, bool] = Field(default_factory=dict)
    tutorial_completed: bool = Field(default=False)
    armageddon_active: bool = Field(default=False)

    # New Game+ data
    ng_plus_tier: int = Field(default=0, ge=0)
    carried_over_data: dict = Field(default_factory=dict)

    def update_playtime(self, seconds: int) -> None:
        """Add to total playtime."""
        self.playtime_seconds += seconds

    def get_playtime_display(self) -> str:
        """Get formatted playtime string."""
        hours = self.playtime_seconds // 3600
        minutes = (self.playtime_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def is_tutorial_phase(self) -> bool:
        """Check if still in tutorial."""
        return self.time.current_turn <= 15 and not self.tutorial_completed

    def to_save_dict(self) -> dict:
        """Convert to dictionary for saving."""
        self.last_saved = datetime.now()
        return self.dict()

    @classmethod
    def from_save_dict(cls, data: dict) -> "GameState":
        """Load from save dictionary."""
        return cls(**data)

    def get_save_summary(self) -> dict:
        """Get summary information for save slot display."""
        return {
            "player_name": self.player.player_name,
            "nation_name": self.player.nation_name,
            "turn": self.time.current_turn,
            "year": self.time.current_year,
            "playtime": self.get_playtime_display(),
            "last_saved": self.last_saved.strftime("%Y-%m-%d %H:%M:%S"),
            "difficulty": self.player.difficulty.value,
            "iron_mode": self.player.iron_mode,
        }
