"""
Simplified Game State model using Python dataclasses (no external dependencies).
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from src.data.constants import Difficulty, TURNS_PER_MONTH


@dataclass
class TimeState:
    """Game time tracking."""
    current_turn: int = 1
    current_month: int = 1
    current_year: int = 1

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


@dataclass
class PlayerState:
    """Player information and settings."""
    player_name: str = "Player"
    nation_name: str = "New Nation"
    nation_id: str = "player_nation"
    primary_element: Optional[str] = None
    starting_general_class: Optional[str] = None
    difficulty: Difficulty = Difficulty.NORMAL
    iron_mode: bool = False
    achievement_points: int = 0
    unlocked_achievements: list = field(default_factory=list)
    unlocked_titles: list = field(default_factory=list)
    equipped_title: Optional[str] = None
    total_battles: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    territories_conquered: int = 0
    gold_earned: int = 0
    units_recruited: int = 0
    monsters_summoned: int = 0

    @property
    def win_rate(self) -> float:
        """Calculate battle win rate."""
        if self.total_battles == 0:
            return 0.0
        return self.battles_won / self.total_battles


@dataclass
class GameState:
    """Complete game state."""
    save_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_saved: datetime = field(default_factory=datetime.now)
    playtime_seconds: int = 0
    time: TimeState = field(default_factory=TimeState)
    player: PlayerState = field(default_factory=PlayerState)
    nations: dict = field(default_factory=dict)
    territories: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    active_quest_ids: list = field(default_factory=list)
    completed_quest_ids: list = field(default_factory=list)
    world_events: list = field(default_factory=list)
    current_battle: Optional[dict] = None
    story_flags: dict = field(default_factory=dict)
    tutorial_completed: bool = False
    armageddon_active: bool = False
    ng_plus_tier: int = 0
    carried_over_data: dict = field(default_factory=dict)

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

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        self.last_saved = datetime.now()
        return {
            "save_version": self.save_version,
            "created_at": self.created_at.isoformat(),
            "last_saved": self.last_saved.isoformat(),
            "playtime_seconds": self.playtime_seconds,
            "time": {
                "current_turn": self.time.current_turn,
                "current_month": self.time.current_month,
                "current_year": self.time.current_year,
            },
            "player": {
                "player_name": self.player.player_name,
                "nation_name": self.player.nation_name,
                "nation_id": self.player.nation_id,
                "difficulty": self.player.difficulty.value,
                "iron_mode": self.player.iron_mode,
                "total_battles": self.player.total_battles,
                "battles_won": self.player.battles_won,
                "battles_lost": self.player.battles_lost,
            },
            "nations": self.nations,
            "territories": self.territories,
            "units": self.units,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Load from dictionary."""
        state = cls()
        state.save_version = data.get("save_version", "1.0.0")
        state.created_at = datetime.fromisoformat(data["created_at"])
        state.last_saved = datetime.fromisoformat(data["last_saved"])
        state.playtime_seconds = data["playtime_seconds"]

        # Time
        time_data = data["time"]
        state.time = TimeState(
            current_turn=time_data["current_turn"],
            current_month=time_data["current_month"],
            current_year=time_data["current_year"],
        )

        # Player
        player_data = data["player"]
        state.player = PlayerState(
            player_name=player_data["player_name"],
            nation_name=player_data["nation_name"],
            nation_id=player_data["nation_id"],
            difficulty=Difficulty(player_data["difficulty"]),
            iron_mode=player_data.get("iron_mode", False),
            total_battles=player_data.get("total_battles", 0),
            battles_won=player_data.get("battles_won", 0),
            battles_lost=player_data.get("battles_lost", 0),
        )

        state.nations = data.get("nations", {})
        state.territories = data.get("territories", {})
        state.units = data.get("units", {})

        return state
