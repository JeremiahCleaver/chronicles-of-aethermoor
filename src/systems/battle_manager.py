"""
Battle Manager - Orchestrates tactical battles and turn order.
"""

from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from src.models.battle import BattleGrid, CombatUnit, BattlePosition, BattleTerrain
from src.systems.movement import MovementSystem
from src.systems.combat import CombatSystem


class BattlePhase(Enum):
    """Phases of battle."""
    SETUP = "setup"
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"


class BattleResult(Enum):
    """Battle outcome."""
    ONGOING = "ongoing"
    PLAYER_VICTORY = "player_victory"
    PLAYER_DEFEAT = "player_defeat"
    RETREAT = "retreat"


@dataclass
class TurnOrderEntry:
    """Entry in turn order queue."""
    unit_id: str
    speed: int
    has_acted: bool = False


@dataclass
class Battle:
    """
    Represents a tactical battle encounter.

    Manages:
    - Battle grid and units
    - Turn order
    - Victory/defeat conditions
    - Battle flow
    """

    battle_id: str
    battle_grid: BattleGrid = field(default_factory=BattleGrid)

    # Systems
    movement_system: Optional[MovementSystem] = None
    combat_system: Optional[CombatSystem] = None

    # Turn management
    turn_order: list[TurnOrderEntry] = field(default_factory=list)
    current_turn_index: int = 0
    round_number: int = 1

    # Battle state
    phase: BattlePhase = BattlePhase.SETUP
    result: BattleResult = BattleResult.ONGOING

    # Victory conditions
    defeat_all_enemies: bool = True
    protect_unit_id: Optional[str] = None
    survive_rounds: Optional[int] = None

    def __post_init__(self):
        """Initialize systems."""
        if self.movement_system is None:
            self.movement_system = MovementSystem(self.battle_grid)
        if self.combat_system is None:
            self.combat_system = CombatSystem(self.battle_grid)

    def add_unit(
        self,
        unit: CombatUnit,
        position: BattlePosition
    ) -> bool:
        """
        Add unit to battle.

        Args:
            unit: Unit to add
            position: Starting position

        Returns:
            True if unit was added successfully
        """
        if self.battle_grid.add_unit(unit, position):
            # Add to turn order
            self._add_to_turn_order(unit)
            return True
        return False

    def start_battle(self) -> None:
        """Start the battle."""
        # Generate turn order
        self._generate_turn_order()

        # Set phase
        first_unit = self.get_current_unit()
        if first_unit:
            self.phase = (
                BattlePhase.PLAYER_TURN
                if first_unit.side == "player"
                else BattlePhase.ENEMY_TURN
            )
        else:
            self.phase = BattlePhase.PLAYER_TURN

    def _add_to_turn_order(self, unit: CombatUnit) -> None:
        """Add unit to turn order."""
        entry = TurnOrderEntry(
            unit_id=unit.unit_id,
            speed=unit.get_total_speed()
        )
        self.turn_order.append(entry)

    def _generate_turn_order(self) -> None:
        """Generate turn order based on unit speed."""
        # Clear existing
        self.turn_order.clear()

        # Add all units
        for unit in self.battle_grid.units.values():
            self._add_to_turn_order(unit)

        # Sort by speed (highest first)
        self.turn_order.sort(key=lambda e: e.speed, reverse=True)

        # Reset index
        self.current_turn_index = 0

    def get_current_unit(self) -> Optional[CombatUnit]:
        """Get unit whose turn it is."""
        if not self.turn_order:
            return None

        if self.current_turn_index >= len(self.turn_order):
            return None

        entry = self.turn_order[self.current_turn_index]
        return self.battle_grid.units.get(entry.unit_id)

    def next_turn(self) -> Optional[CombatUnit]:
        """
        Advance to next unit's turn.

        Returns:
            Next unit, or None if round complete
        """
        # Mark current entry as acted
        if self.current_turn_index < len(self.turn_order):
            self.turn_order[self.current_turn_index].has_acted = True

        # Advance index
        self.current_turn_index += 1

        # Check if round is complete
        if self.current_turn_index >= len(self.turn_order):
            self._end_round()
            return None

        # Get next unit
        next_unit = self.get_current_unit()

        # Update phase
        if next_unit:
            self.phase = (
                BattlePhase.PLAYER_TURN
                if next_unit.side == "player"
                else BattlePhase.ENEMY_TURN
            )

        return next_unit

    def _end_round(self) -> None:
        """End current round and start new one."""
        # Process end-of-round effects
        for unit in self.battle_grid.units.values():
            # Update status effects
            unit.update_status_effects()

            # Apply status damage
            if self.combat_system:
                self.combat_system.apply_status_damage(unit)

            # Reset turn flags
            unit.reset_turn_flags()

        # Start new round
        self.round_number += 1
        self.current_turn_index = 0

        # Reset turn order flags
        for entry in self.turn_order:
            entry.has_acted = False

        # Remove defeated units
        self._remove_defeated_units()

        # Check victory conditions
        self._check_victory_conditions()

    def _remove_defeated_units(self) -> None:
        """Remove defeated units from battle."""
        defeated = [
            unit_id for unit_id, unit in self.battle_grid.units.items()
            if not unit.is_alive()
        ]

        for unit_id in defeated:
            self.battle_grid.remove_unit(unit_id)
            # Remove from turn order
            self.turn_order = [
                entry for entry in self.turn_order
                if entry.unit_id != unit_id
            ]

    def _check_victory_conditions(self) -> None:
        """Check if battle is won or lost."""
        # Count units by side
        player_units = [
            u for u in self.battle_grid.units.values()
            if u.side == "player" and u.is_alive()
        ]
        enemy_units = [
            u for u in self.battle_grid.units.values()
            if u.side == "enemy" and u.is_alive()
        ]

        # Check defeat (no player units)
        if not player_units:
            self.result = BattleResult.PLAYER_DEFEAT
            self.phase = BattlePhase.DEFEAT
            return

        # Check victory (no enemy units)
        if self.defeat_all_enemies and not enemy_units:
            self.result = BattleResult.PLAYER_VICTORY
            self.phase = BattlePhase.VICTORY
            return

        # Check protected unit
        if self.protect_unit_id:
            protected_unit = self.battle_grid.units.get(self.protect_unit_id)
            if not protected_unit or not protected_unit.is_alive():
                self.result = BattleResult.PLAYER_DEFEAT
                self.phase = BattlePhase.DEFEAT
                return

        # Check survival rounds
        if self.survive_rounds and self.round_number > self.survive_rounds:
            self.result = BattleResult.PLAYER_VICTORY
            self.phase = BattlePhase.VICTORY
            return

    def is_battle_over(self) -> bool:
        """Check if battle has ended."""
        return self.phase in [BattlePhase.VICTORY, BattlePhase.DEFEAT]

    def get_units_by_side(self, side: str) -> list[CombatUnit]:
        """Get all units on a side."""
        return [
            unit for unit in self.battle_grid.units.values()
            if unit.side == side
        ]

    def get_turn_order_display(self) -> list[tuple[str, int, bool]]:
        """
        Get turn order for display.

        Returns:
            List of (unit_name, speed, has_acted) tuples
        """
        display = []

        for entry in self.turn_order:
            unit = self.battle_grid.units.get(entry.unit_id)
            if unit:
                display.append((unit.name, entry.speed, entry.has_acted))

        return display

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "battle_id": self.battle_id,
            "battle_grid": self.battle_grid.to_dict(),
            "turn_order": [
                {
                    "unit_id": entry.unit_id,
                    "speed": entry.speed,
                    "has_acted": entry.has_acted,
                }
                for entry in self.turn_order
            ],
            "current_turn_index": self.current_turn_index,
            "round_number": self.round_number,
            "phase": self.phase.value,
            "result": self.result.value,
            "defeat_all_enemies": self.defeat_all_enemies,
            "protect_unit_id": self.protect_unit_id,
            "survive_rounds": self.survive_rounds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Battle":
        """Load from dictionary."""
        battle = cls(
            battle_id=data["battle_id"],
            battle_grid=BattleGrid.from_dict(data["battle_grid"]),
            current_turn_index=data.get("current_turn_index", 0),
            round_number=data.get("round_number", 1),
            phase=BattlePhase(data.get("phase", "setup")),
            result=BattleResult(data.get("result", "ongoing")),
            defeat_all_enemies=data.get("defeat_all_enemies", True),
            protect_unit_id=data.get("protect_unit_id"),
            survive_rounds=data.get("survive_rounds"),
        )

        # Load turn order
        for entry_data in data.get("turn_order", []):
            entry = TurnOrderEntry(
                unit_id=entry_data["unit_id"],
                speed=entry_data["speed"],
                has_acted=entry_data.get("has_acted", False),
            )
            battle.turn_order.append(entry)

        # Initialize systems
        battle.movement_system = MovementSystem(battle.battle_grid)
        battle.combat_system = CombatSystem(battle.battle_grid)

        return battle


class BattleGenerator:
    """Generates battle scenarios."""

    @staticmethod
    def generate_random_battle(
        player_units: list[CombatUnit],
        enemy_count: int = 3,
        terrain_variety: bool = True
    ) -> Battle:
        """
        Generate a random battle.

        Args:
            player_units: Player's units
            enemy_count: Number of enemy units
            terrain_variety: Whether to add varied terrain

        Returns:
            Generated battle
        """
        battle = Battle(battle_id="random_battle")

        # Add terrain variety
        if terrain_variety:
            BattleGenerator._add_random_terrain(battle.battle_grid)

        # Place player units (left side)
        player_positions = [
            BattlePosition(2, y)
            for y in range(2, min(2 + len(player_units), battle.battle_grid.height - 2))
        ]

        for unit, position in zip(player_units, player_positions):
            battle.add_unit(unit, position)

        # Create and place enemy units (right side)
        enemy_positions = [
            BattlePosition(battle.battle_grid.width - 3, y)
            for y in range(2, min(2 + enemy_count, battle.battle_grid.height - 2))
        ]

        for i, position in enumerate(enemy_positions):
            enemy = CombatUnit(
                unit_id=f"enemy_{i}",
                name=f"Enemy {i+1}",
                side="enemy",
                is_ai_controlled=True,
                max_hp=80,
                current_hp=80,
                attack=12,
                defense=8,
                speed=8 + i,
            )
            battle.add_unit(enemy, position)

        return battle

    @staticmethod
    def _add_random_terrain(grid: BattleGrid) -> None:
        """Add random terrain features to grid."""
        import random

        # Add some forests
        for _ in range(random.randint(3, 6)):
            x = random.randint(3, grid.width - 4)
            y = random.randint(2, grid.height - 3)
            cell = grid.get_cell(x, y)
            if cell:
                cell.terrain = BattleTerrain.FOREST

        # Add some hills
        for _ in range(random.randint(2, 4)):
            x = random.randint(3, grid.width - 4)
            y = random.randint(2, grid.height - 3)
            cell = grid.get_cell(x, y)
            if cell:
                cell.terrain = BattleTerrain.HILL
                cell.height = random.randint(1, 2)

        # Add some obstacles
        for _ in range(random.randint(1, 3)):
            x = random.randint(4, grid.width - 5)
            y = random.randint(3, grid.height - 4)
            cell = grid.get_cell(x, y)
            if cell:
                cell.terrain = BattleTerrain.OBSTACLE
