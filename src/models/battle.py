"""
Battle model - represents tactical combat encounters on hex grids.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from src.data.constants import Element, BATTLE_GRID_WIDTH, BATTLE_GRID_HEIGHT


class BattleTerrain(Enum):
    """Terrain types on battle grid."""
    PLAINS = "plains"
    FOREST = "forest"
    HILL = "hill"
    WATER = "water"
    WALL = "wall"
    OBSTACLE = "obstacle"


class CombatUnitStatus(Enum):
    """Status conditions affecting combat units."""
    NORMAL = "normal"
    POISONED = "poisoned"
    BURNING = "burning"
    FROZEN = "frozen"
    PARALYZED = "paralyzed"
    CHARMED = "charmed"
    SLEEPING = "sleeping"
    STUNNED = "stunned"
    BLESSED = "blessed"
    HASTED = "hasted"
    SLOWED = "slowed"


@dataclass
class BattlePosition:
    """Position on battle grid."""
    x: int
    y: int

    def __eq__(self, other):
        if not isinstance(other, BattlePosition):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def distance_to(self, other: "BattlePosition") -> int:
        """Calculate hex distance to another position."""
        # Hex distance calculation
        dx = self.x - other.x
        dy = self.y - other.y

        # Convert to axial coordinates for distance
        if (self.y % 2 == 0 and other.y % 2 == 1) or (self.y % 2 == 1 and other.y % 2 == 0):
            # Different row parities
            return abs(dx) + abs(dy) + max(0, abs(dx) - abs(dy)) // 2
        else:
            return abs(dx) + abs(dy)

    def to_tuple(self) -> tuple[int, int]:
        """Convert to tuple."""
        return (self.x, self.y)


@dataclass
class BattleGridCell:
    """Single cell on battle grid."""
    position: BattlePosition
    terrain: BattleTerrain = BattleTerrain.PLAINS
    height: int = 0  # Elevation for height advantage
    occupant_id: Optional[str] = None  # Unit ID if occupied

    def is_passable(self) -> bool:
        """Check if cell can be moved through."""
        if self.terrain in [BattleTerrain.WALL, BattleTerrain.OBSTACLE]:
            return False
        return True

    def is_occupied(self) -> bool:
        """Check if cell is occupied by a unit."""
        return self.occupant_id is not None

    def get_movement_cost(self) -> int:
        """Get movement cost for entering this cell."""
        costs = {
            BattleTerrain.PLAINS: 1,
            BattleTerrain.FOREST: 2,
            BattleTerrain.HILL: 2,
            BattleTerrain.WATER: 3,
            BattleTerrain.WALL: 99,
            BattleTerrain.OBSTACLE: 99,
        }
        return costs.get(self.terrain, 1)

    def get_defense_bonus(self) -> int:
        """Get defensive bonus from terrain."""
        bonuses = {
            BattleTerrain.PLAINS: 0,
            BattleTerrain.FOREST: 15,
            BattleTerrain.HILL: 20,
            BattleTerrain.WATER: 5,
            BattleTerrain.WALL: 50,
            BattleTerrain.OBSTACLE: 10,
        }
        return bonuses.get(self.terrain, 0)


@dataclass
class CombatUnit:
    """
    Unit in tactical combat.

    This is a specialized combat instance of a unit,
    separate from the general Unit model.
    """

    # Identity
    unit_id: str
    name: str
    side: str  # "player", "enemy", "ally", "neutral"

    # Position
    position: Optional[BattlePosition] = None
    facing: int = 0  # Direction unit is facing (0-5 for hex)

    # Core Stats
    max_hp: int = 100
    current_hp: int = 100
    max_mp: int = 50
    current_mp: int = 50

    # Combat Stats
    attack: int = 10
    defense: int = 10
    magic_attack: int = 10
    magic_defense: int = 10
    speed: int = 10

    # Movement
    move_range: int = 3
    jump_height: int = 1
    has_moved: bool = False
    has_acted: bool = False

    # Elemental Affinity
    element: Optional[Element] = None

    # Status
    status_effects: list[CombatUnitStatus] = field(default_factory=list)
    status_durations: dict[CombatUnitStatus, int] = field(default_factory=dict)

    # Equipment Effects
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0

    # Abilities
    abilities: list[str] = field(default_factory=list)  # Ability IDs

    # AI Control
    is_ai_controlled: bool = False

    def is_alive(self) -> bool:
        """Check if unit is alive."""
        return self.current_hp > 0

    def is_ready(self) -> bool:
        """Check if unit can act this turn."""
        if not self.is_alive():
            return False
        if self.has_status(CombatUnitStatus.STUNNED):
            return False
        if self.has_status(CombatUnitStatus.SLEEPING):
            return False
        if self.has_status(CombatUnitStatus.PARALYZED):
            return False
        return True

    def can_move(self) -> bool:
        """Check if unit can move."""
        return self.is_ready() and not self.has_moved

    def can_act(self) -> bool:
        """Check if unit can take action."""
        return self.is_ready() and not self.has_acted

    def has_status(self, status: CombatUnitStatus) -> bool:
        """Check if unit has specific status effect."""
        return status in self.status_effects

    def add_status(self, status: CombatUnitStatus, duration: int = 3) -> None:
        """Add status effect."""
        if status not in self.status_effects:
            self.status_effects.append(status)
        self.status_durations[status] = duration

    def remove_status(self, status: CombatUnitStatus) -> None:
        """Remove status effect."""
        if status in self.status_effects:
            self.status_effects.remove(status)
        if status in self.status_durations:
            del self.status_durations[status]

    def update_status_effects(self) -> None:
        """Update status effect durations."""
        to_remove = []
        for status, duration in self.status_durations.items():
            self.status_durations[status] = duration - 1
            if self.status_durations[status] <= 0:
                to_remove.append(status)

        for status in to_remove:
            self.remove_status(status)

    def take_damage(self, damage: int) -> int:
        """
        Take damage and return actual damage dealt.

        Returns:
            Actual damage dealt after reductions
        """
        actual_damage = max(1, damage)  # Minimum 1 damage
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal unit and return actual healing.

        Returns:
            Actual HP restored
        """
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp

    def consume_mp(self, amount: int) -> bool:
        """
        Consume MP for abilities.

        Returns:
            True if MP was available and consumed
        """
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False

    def restore_mp(self, amount: int) -> int:
        """
        Restore MP and return actual amount restored.

        Returns:
            Actual MP restored
        """
        old_mp = self.current_mp
        self.current_mp = min(self.max_mp, self.current_mp + amount)
        return self.current_mp - old_mp

    def get_total_attack(self) -> int:
        """Get total attack including bonuses."""
        total = self.attack + self.attack_bonus
        if self.has_status(CombatUnitStatus.BLESSED):
            total = int(total * 1.2)
        return total

    def get_total_defense(self) -> int:
        """Get total defense including bonuses."""
        total = self.defense + self.defense_bonus
        if self.has_status(CombatUnitStatus.BLESSED):
            total = int(total * 1.2)
        return total

    def get_total_speed(self) -> int:
        """Get total speed including status effects."""
        total = self.speed + self.speed_bonus
        if self.has_status(CombatUnitStatus.HASTED):
            total = int(total * 1.5)
        if self.has_status(CombatUnitStatus.SLOWED):
            total = int(total * 0.5)
        return total

    def reset_turn_flags(self) -> None:
        """Reset movement and action flags for new turn."""
        self.has_moved = False
        self.has_acted = False

    def get_hp_percentage(self) -> float:
        """Get HP as percentage."""
        if self.max_hp == 0:
            return 0.0
        return (self.current_hp / self.max_hp) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "unit_id": self.unit_id,
            "name": self.name,
            "side": self.side,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
            } if self.position else None,
            "facing": self.facing,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "max_mp": self.max_mp,
            "current_mp": self.current_mp,
            "attack": self.attack,
            "defense": self.defense,
            "magic_attack": self.magic_attack,
            "magic_defense": self.magic_defense,
            "speed": self.speed,
            "move_range": self.move_range,
            "jump_height": self.jump_height,
            "has_moved": self.has_moved,
            "has_acted": self.has_acted,
            "element": self.element.value if self.element else None,
            "status_effects": [s.value for s in self.status_effects],
            "status_durations": {s.value: d for s, d in self.status_durations.items()},
            "abilities": self.abilities,
            "is_ai_controlled": self.is_ai_controlled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CombatUnit":
        """Load from dictionary."""
        unit = cls(
            unit_id=data["unit_id"],
            name=data["name"],
            side=data["side"],
            facing=data.get("facing", 0),
            max_hp=data.get("max_hp", 100),
            current_hp=data.get("current_hp", 100),
            max_mp=data.get("max_mp", 50),
            current_mp=data.get("current_mp", 50),
            attack=data.get("attack", 10),
            defense=data.get("defense", 10),
            magic_attack=data.get("magic_attack", 10),
            magic_defense=data.get("magic_defense", 10),
            speed=data.get("speed", 10),
            move_range=data.get("move_range", 3),
            jump_height=data.get("jump_height", 1),
            has_moved=data.get("has_moved", False),
            has_acted=data.get("has_acted", False),
            abilities=data.get("abilities", []),
            is_ai_controlled=data.get("is_ai_controlled", False),
        )

        # Load position
        if data.get("position"):
            unit.position = BattlePosition(
                x=data["position"]["x"],
                y=data["position"]["y"],
            )

        # Load element
        if data.get("element"):
            unit.element = Element(data["element"])

        # Load status effects
        if data.get("status_effects"):
            unit.status_effects = [CombatUnitStatus(s) for s in data["status_effects"]]

        if data.get("status_durations"):
            unit.status_durations = {
                CombatUnitStatus(s): d
                for s, d in data["status_durations"].items()
            }

        return unit


@dataclass
class BattleGrid:
    """
    Tactical battle grid (12×18 hexes).

    Manages terrain, unit positions, and battlefield state.
    """

    width: int = BATTLE_GRID_WIDTH
    height: int = BATTLE_GRID_HEIGHT

    # Grid cells
    cells: dict[tuple[int, int], BattleGridCell] = field(default_factory=dict)

    # Units on battlefield
    units: dict[str, CombatUnit] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize grid cells."""
        if not self.cells:
            for y in range(self.height):
                for x in range(self.width):
                    pos = BattlePosition(x, y)
                    self.cells[(x, y)] = BattleGridCell(position=pos)

    def get_cell(self, x: int, y: int) -> Optional[BattleGridCell]:
        """Get cell at position."""
        return self.cells.get((x, y))

    def get_cell_at_position(self, position: BattlePosition) -> Optional[BattleGridCell]:
        """Get cell at BattlePosition."""
        return self.get_cell(position.x, position.y)

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_position_passable(self, position: BattlePosition) -> bool:
        """Check if position can be moved to."""
        if not self.is_valid_position(position.x, position.y):
            return False

        cell = self.get_cell_at_position(position)
        if not cell:
            return False

        return cell.is_passable() and not cell.is_occupied()

    def add_unit(self, unit: CombatUnit, position: BattlePosition) -> bool:
        """
        Add unit to battlefield at position.

        Returns:
            True if unit was added successfully
        """
        if not self.is_valid_position(position.x, position.y):
            return False

        cell = self.get_cell_at_position(position)
        if not cell or cell.is_occupied():
            return False

        # Place unit
        unit.position = position
        self.units[unit.unit_id] = unit
        cell.occupant_id = unit.unit_id

        return True

    def remove_unit(self, unit_id: str) -> bool:
        """
        Remove unit from battlefield.

        Returns:
            True if unit was removed
        """
        unit = self.units.get(unit_id)
        if not unit or not unit.position:
            return False

        # Clear cell
        cell = self.get_cell_at_position(unit.position)
        if cell:
            cell.occupant_id = None

        # Remove unit
        del self.units[unit_id]
        return True

    def move_unit(self, unit_id: str, new_position: BattlePosition) -> bool:
        """
        Move unit to new position.

        Returns:
            True if unit was moved successfully
        """
        unit = self.units.get(unit_id)
        if not unit or not unit.position:
            return False

        # Check if new position is valid
        if not self.is_position_passable(new_position):
            return False

        # Clear old cell
        old_cell = self.get_cell_at_position(unit.position)
        if old_cell:
            old_cell.occupant_id = None

        # Occupy new cell
        new_cell = self.get_cell_at_position(new_position)
        if new_cell:
            new_cell.occupant_id = unit_id

        # Update unit position
        unit.position = new_position

        return True

    def get_neighbors(self, position: BattlePosition) -> list[BattlePosition]:
        """Get neighboring positions (hex grid)."""
        neighbors = []
        x, y = position.x, position.y

        # Hex neighbor offsets
        if y % 2 == 0:  # Even row
            offsets = [
                (-1, -1),  # NW
                (0, -1),   # NE
                (1, 0),    # E
                (0, 1),    # SE
                (-1, 1),   # SW
                (-1, 0),   # W
            ]
        else:  # Odd row
            offsets = [
                (0, -1),   # NW
                (1, -1),   # NE
                (1, 0),    # E
                (1, 1),    # SE
                (0, 1),    # SW
                (-1, 0),   # W
            ]

        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append(BattlePosition(nx, ny))

        return neighbors

    def get_units_in_range(self, position: BattlePosition, range_distance: int) -> list[CombatUnit]:
        """Get all units within range of position."""
        units_in_range = []

        for unit in self.units.values():
            if unit.position and position.distance_to(unit.position) <= range_distance:
                units_in_range.append(unit)

        return units_in_range

    def get_unit_at_position(self, position: BattlePosition) -> Optional[CombatUnit]:
        """Get unit at specific position."""
        cell = self.get_cell_at_position(position)
        if cell and cell.occupant_id:
            return self.units.get(cell.occupant_id)
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "width": self.width,
            "height": self.height,
            "cells": {
                f"{x},{y}": {
                    "terrain": cell.terrain.value,
                    "height": cell.height,
                }
                for (x, y), cell in self.cells.items()
                if cell.terrain != BattleTerrain.PLAINS or cell.height != 0
            },
            "units": {
                unit_id: unit.to_dict()
                for unit_id, unit in self.units.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BattleGrid":
        """Load from dictionary."""
        grid = cls(width=data["width"], height=data["height"])

        # Load cells
        for cell_key, cell_data in data.get("cells", {}).items():
            x, y = map(int, cell_key.split(","))
            cell = grid.get_cell(x, y)
            if cell:
                cell.terrain = BattleTerrain(cell_data["terrain"])
                cell.height = cell_data.get("height", 0)

        # Load units
        for unit_id, unit_data in data.get("units", {}).items():
            unit = CombatUnit.from_dict(unit_data)
            if unit.position:
                grid.add_unit(unit, unit.position)

        return grid
