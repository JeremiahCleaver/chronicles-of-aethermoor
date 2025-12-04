"""
Movement System - Handles unit movement, pathfinding, and range calculation.
"""

from typing import Optional
from dataclasses import dataclass
from src.models.battle import BattleGrid, BattlePosition, CombatUnit


@dataclass
class PathNode:
    """Node in pathfinding algorithm."""
    position: BattlePosition
    g_cost: int = 0  # Cost from start
    h_cost: int = 0  # Heuristic cost to goal
    parent: Optional["PathNode"] = None

    @property
    def f_cost(self) -> int:
        """Total cost (g + h)."""
        return self.g_cost + self.h_cost

    def __eq__(self, other):
        if not isinstance(other, PathNode):
            return False
        return self.position == other.position

    def __hash__(self):
        return hash(self.position)


class MovementSystem:
    """
    Handles movement calculations and pathfinding.

    Uses A* pathfinding for hex grids with terrain costs.
    """

    def __init__(self, battle_grid: BattleGrid):
        """
        Initialize movement system.

        Args:
            battle_grid: Battle grid to operate on
        """
        self.grid = battle_grid

    def get_reachable_positions(
        self,
        unit: CombatUnit,
        max_range: Optional[int] = None
    ) -> dict[tuple[int, int], int]:
        """
        Get all positions reachable by unit within movement range.

        Args:
            unit: Unit to calculate movement for
            max_range: Override unit's move_range

        Returns:
            Dictionary mapping (x, y) to movement cost
        """
        if not unit.position:
            return {}

        if max_range is None:
            max_range = unit.move_range

        reachable: dict[tuple[int, int], int] = {}
        frontier: list[tuple[BattlePosition, int]] = [(unit.position, 0)]
        visited: set[tuple[int, int]] = set()

        while frontier:
            current_pos, current_cost = frontier.pop(0)
            current_tuple = current_pos.to_tuple()

            if current_tuple in visited:
                continue

            visited.add(current_tuple)

            # Skip if over max range
            if current_cost > max_range:
                continue

            # Add to reachable (except starting position)
            if current_pos != unit.position:
                reachable[current_tuple] = current_cost

            # Explore neighbors
            for neighbor_pos in self.grid.get_neighbors(current_pos):
                neighbor_tuple = neighbor_pos.to_tuple()

                if neighbor_tuple in visited:
                    continue

                # Check if passable
                if not self.is_position_accessible(neighbor_pos, unit):
                    continue

                # Get movement cost
                cell = self.grid.get_cell_at_position(neighbor_pos)
                if not cell:
                    continue

                move_cost = cell.get_movement_cost()
                new_cost = current_cost + move_cost

                # Check if within range
                if new_cost <= max_range:
                    # Check height difference
                    current_cell = self.grid.get_cell_at_position(current_pos)
                    if current_cell and cell:
                        height_diff = abs(cell.height - current_cell.height)
                        if height_diff > unit.jump_height:
                            continue

                    frontier.append((neighbor_pos, new_cost))

        return reachable

    def is_position_accessible(self, position: BattlePosition, unit: CombatUnit) -> bool:
        """
        Check if unit can access position.

        Args:
            position: Position to check
            unit: Unit attempting to access

        Returns:
            True if position is accessible
        """
        # Check bounds
        if not self.grid.is_valid_position(position.x, position.y):
            return False

        # Get cell
        cell = self.grid.get_cell_at_position(position)
        if not cell:
            return False

        # Check terrain passability
        if not cell.is_passable():
            return False

        # Check if occupied by another unit
        if cell.is_occupied() and cell.occupant_id != unit.unit_id:
            return False

        return True

    def find_path(
        self,
        start: BattlePosition,
        goal: BattlePosition,
        unit: CombatUnit
    ) -> Optional[list[BattlePosition]]:
        """
        Find shortest path from start to goal using A*.

        Args:
            start: Starting position
            goal: Goal position
            unit: Unit moving

        Returns:
            List of positions in path (including start and goal), or None if no path
        """
        # Check if goal is accessible
        if not self.is_position_accessible(goal, unit):
            return None

        # Initialize
        start_node = PathNode(position=start)
        goal_node = PathNode(position=goal)

        open_set: list[PathNode] = [start_node]
        closed_set: set[tuple[int, int]] = set()

        while open_set:
            # Get node with lowest f_cost
            current_node = min(open_set, key=lambda n: n.f_cost)

            # Check if reached goal
            if current_node.position == goal:
                return self._reconstruct_path(current_node)

            # Move to closed set
            open_set.remove(current_node)
            closed_set.add(current_node.position.to_tuple())

            # Explore neighbors
            for neighbor_pos in self.grid.get_neighbors(current_node.position):
                neighbor_tuple = neighbor_pos.to_tuple()

                # Skip if already evaluated
                if neighbor_tuple in closed_set:
                    continue

                # Skip if not accessible
                if not self.is_position_accessible(neighbor_pos, unit):
                    continue

                # Get movement cost
                cell = self.grid.get_cell_at_position(neighbor_pos)
                if not cell:
                    continue

                # Check height difference
                current_cell = self.grid.get_cell_at_position(current_node.position)
                if current_cell and cell:
                    height_diff = abs(cell.height - current_cell.height)
                    if height_diff > unit.jump_height:
                        continue

                # Calculate costs
                move_cost = cell.get_movement_cost()
                tentative_g = current_node.g_cost + move_cost

                # Check if neighbor already in open set
                existing_node = next(
                    (n for n in open_set if n.position == neighbor_pos),
                    None
                )

                if existing_node:
                    # Update if better path
                    if tentative_g < existing_node.g_cost:
                        existing_node.g_cost = tentative_g
                        existing_node.parent = current_node
                else:
                    # Create new node
                    neighbor_node = PathNode(
                        position=neighbor_pos,
                        g_cost=tentative_g,
                        h_cost=neighbor_pos.distance_to(goal),
                        parent=current_node
                    )
                    open_set.append(neighbor_node)

        # No path found
        return None

    def _reconstruct_path(self, node: PathNode) -> list[BattlePosition]:
        """Reconstruct path from node to start."""
        path = []
        current = node

        while current:
            path.append(current.position)
            current = current.parent

        path.reverse()
        return path

    def can_move_to(
        self,
        unit: CombatUnit,
        destination: BattlePosition,
        check_range: bool = True
    ) -> bool:
        """
        Check if unit can move to destination.

        Args:
            unit: Unit to check
            destination: Target position
            check_range: Whether to check movement range

        Returns:
            True if movement is valid
        """
        if not unit.position:
            return False

        # Check if unit can move
        if not unit.can_move():
            return False

        # Check if destination is accessible
        if not self.is_position_accessible(destination, unit):
            return False

        # Check range if required
        if check_range:
            reachable = self.get_reachable_positions(unit)
            if destination.to_tuple() not in reachable:
                return False

        # Check if path exists
        path = self.find_path(unit.position, destination, unit)
        if not path:
            return False

        return True

    def move_unit(self, unit: CombatUnit, destination: BattlePosition) -> bool:
        """
        Move unit to destination.

        Args:
            unit: Unit to move
            destination: Target position

        Returns:
            True if movement successful
        """
        # Validate movement
        if not self.can_move_to(unit, destination):
            return False

        # Move unit on grid
        if self.grid.move_unit(unit.unit_id, destination):
            unit.has_moved = True
            return True

        return False

    def get_movement_path_cost(
        self,
        path: list[BattlePosition]
    ) -> int:
        """
        Calculate total movement cost for path.

        Args:
            path: List of positions

        Returns:
            Total movement cost
        """
        total_cost = 0

        for i in range(1, len(path)):
            cell = self.grid.get_cell_at_position(path[i])
            if cell:
                total_cost += cell.get_movement_cost()

        return total_cost

    def get_positions_in_range(
        self,
        center: BattlePosition,
        min_range: int,
        max_range: int
    ) -> list[BattlePosition]:
        """
        Get all positions within min/max range of center.

        Args:
            center: Center position
            min_range: Minimum range (inclusive)
            max_range: Maximum range (inclusive)

        Returns:
            List of positions in range
        """
        positions = []

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                pos = BattlePosition(x, y)
                distance = center.distance_to(pos)

                if min_range <= distance <= max_range:
                    positions.append(pos)

        return positions

    def get_area_of_effect(
        self,
        center: BattlePosition,
        radius: int,
        shape: str = "circle"
    ) -> list[BattlePosition]:
        """
        Get positions in area of effect.

        Args:
            center: Center of effect
            radius: Radius of effect
            shape: Shape type ("circle", "line", "cone")

        Returns:
            List of positions in area
        """
        if shape == "circle":
            return self.get_positions_in_range(center, 0, radius)

        # TODO: Implement line and cone shapes for Phase 4
        return [center]

    def get_line_of_sight(
        self,
        start: BattlePosition,
        end: BattlePosition,
        max_range: Optional[int] = None
    ) -> bool:
        """
        Check if there's a clear line of sight between positions.

        Args:
            start: Starting position
            end: Ending position
            max_range: Maximum sight range

        Returns:
            True if line of sight is clear
        """
        # Check range
        distance = start.distance_to(end)
        if max_range and distance > max_range:
            return False

        # Simple implementation: check if any walls block
        # TODO: Implement proper line-of-sight algorithm for Phase 4

        return True
