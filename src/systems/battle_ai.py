"""
Battle AI - Controls AI-controlled units in tactical combat.
"""

from typing import Optional
from src.models.battle import BattleGrid, CombatUnit, BattlePosition
from src.systems.movement import MovementSystem
from src.systems.combat import CombatSystem, CombatAction


class BattleAI:
    """
    AI controller for tactical combat.

    Implements basic tactics:
    - Target selection (weakest enemy, nearest threat)
    - Movement (approach enemies, maintain range)
    - Action priority (attack > heal > move)
    """

    def __init__(
        self,
        battle_grid: BattleGrid,
        movement_system: MovementSystem,
        combat_system: CombatSystem
    ):
        """
        Initialize battle AI.

        Args:
            battle_grid: Battle grid
            movement_system: Movement system
            combat_system: Combat system
        """
        self.grid = battle_grid
        self.movement = movement_system
        self.combat = combat_system

    def take_turn(self, unit: CombatUnit) -> list[str]:
        """
        Execute AI turn for unit.

        Args:
            unit: Unit to control

        Returns:
            List of action messages
        """
        messages = []

        if not unit.is_ai_controlled:
            return messages

        # Phase 1: Attack if enemies in range
        if unit.can_act():
            attack_msg = self._try_attack(unit)
            if attack_msg:
                messages.append(attack_msg)
                return messages  # End turn after attacking

        # Phase 2: Move toward enemies
        if unit.can_move():
            move_msg = self._try_move_toward_enemies(unit)
            if move_msg:
                messages.append(move_msg)

        # Phase 3: Attack again if now in range
        if unit.can_act():
            attack_msg = self._try_attack(unit)
            if attack_msg:
                messages.append(attack_msg)

        # End turn
        unit.has_acted = True
        unit.has_moved = True

        return messages

    def _try_attack(self, unit: CombatUnit) -> Optional[str]:
        """
        Try to attack an enemy.

        Args:
            unit: Attacking unit

        Returns:
            Action message or None
        """
        # Get targets in range
        targets = self.combat.get_targets_in_range(unit, attack_range=1)

        if not targets:
            return None

        # Select target (prioritize weakest)
        target = self._select_target(unit, targets)

        if not target:
            return None

        # Execute attack
        result = self.combat.execute_attack(
            unit.unit_id,
            target.unit_id,
            attack_type="physical"
        )

        if result and result.hit:
            msg = f"{unit.name} attacks {target.name} for {result.damage} damage!"
            if result.critical:
                msg += " Critical hit!"
            if not target.is_alive():
                msg += f" {target.name} is defeated!"
            return msg

        return f"{unit.name} attacks {target.name} but misses!"

    def _try_move_toward_enemies(self, unit: CombatUnit) -> Optional[str]:
        """
        Try to move toward nearest enemy.

        Args:
            unit: Moving unit

        Returns:
            Action message or None
        """
        if not unit.position:
            return None

        # Find nearest enemy
        nearest_enemy = self._find_nearest_enemy(unit)

        if not nearest_enemy or not nearest_enemy.position:
            return None

        # Get reachable positions
        reachable = self.movement.get_reachable_positions(unit)

        if not reachable:
            return None

        # Find position closest to enemy
        best_position = None
        best_distance = float('inf')

        for pos_tuple, cost in reachable.items():
            pos = BattlePosition(pos_tuple[0], pos_tuple[1])
            distance = pos.distance_to(nearest_enemy.position)

            if distance < best_distance:
                best_distance = distance
                best_position = pos

        if best_position:
            # Move to position
            if self.movement.move_unit(unit, best_position):
                return f"{unit.name} moves toward {nearest_enemy.name}"

        return None

    def _select_target(
        self,
        attacker: CombatUnit,
        targets: list[CombatUnit]
    ) -> Optional[CombatUnit]:
        """
        Select best target from list.

        Strategy: Target weakest enemy (lowest HP percentage).

        Args:
            attacker: Attacking unit
            targets: List of potential targets

        Returns:
            Selected target or None
        """
        if not targets:
            return None

        # Prioritize weakest (by HP percentage)
        weakest = min(targets, key=lambda t: t.get_hp_percentage())

        return weakest

    def _find_nearest_enemy(self, unit: CombatUnit) -> Optional[CombatUnit]:
        """
        Find nearest enemy unit.

        Args:
            unit: Reference unit

        Returns:
            Nearest enemy or None
        """
        if not unit.position:
            return None

        enemies = [
            u for u in self.grid.units.values()
            if u.side != unit.side and u.is_alive() and u.position
        ]

        if not enemies:
            return None

        # Find nearest
        nearest = min(
            enemies,
            key=lambda e: unit.position.distance_to(e.position) if e.position else float('inf')
        )

        return nearest

    def _find_nearest_ally(self, unit: CombatUnit) -> Optional[CombatUnit]:
        """
        Find nearest ally unit.

        Args:
            unit: Reference unit

        Returns:
            Nearest ally or None
        """
        if not unit.position:
            return None

        allies = [
            u for u in self.grid.units.values()
            if u.side == unit.side and u.unit_id != unit.unit_id and u.is_alive() and u.position
        ]

        if not allies:
            return None

        # Find nearest
        nearest = min(
            allies,
            key=lambda a: unit.position.distance_to(a.position) if a.position else float('inf')
        )

        return nearest

    def evaluate_position(
        self,
        unit: CombatUnit,
        position: BattlePosition
    ) -> float:
        """
        Evaluate how good a position is for a unit.

        Args:
            unit: Unit to evaluate for
            position: Position to evaluate

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Terrain bonuses
        cell = self.grid.get_cell_at_position(position)
        if cell:
            score += cell.get_defense_bonus() / 10.0
            score += cell.height * 5.0

        # Distance to enemies (prefer closer)
        nearest_enemy = self._find_nearest_enemy(unit)
        if nearest_enemy and nearest_enemy.position:
            distance = position.distance_to(nearest_enemy.position)
            # Prefer distance of 1-2 (melee range)
            if distance == 1:
                score += 50.0
            elif distance == 2:
                score += 30.0
            elif distance <= 4:
                score += 10.0

        # Distance to allies (slight preference for staying grouped)
        nearest_ally = self._find_nearest_ally(unit)
        if nearest_ally and nearest_ally.position:
            distance = position.distance_to(nearest_ally.position)
            if 2 <= distance <= 4:
                score += 5.0

        return score


class TacticalAI(BattleAI):
    """
    Enhanced AI with more sophisticated tactics.

    Features:
    - Flanking attempts
    - Focus fire on low HP targets
    - Defensive positioning
    - Ability usage (future)
    """

    def __init__(
        self,
        battle_grid: BattleGrid,
        movement_system: MovementSystem,
        combat_system: CombatSystem,
        aggression: float = 0.7
    ):
        """
        Initialize tactical AI.

        Args:
            battle_grid: Battle grid
            movement_system: Movement system
            combat_system: Combat system
            aggression: Aggression level (0.0 = defensive, 1.0 = aggressive)
        """
        super().__init__(battle_grid, movement_system, combat_system)
        self.aggression = aggression

    def _try_move_toward_enemies(self, unit: CombatUnit) -> Optional[str]:
        """Enhanced movement with tactical positioning."""
        if not unit.position:
            return None

        # Find nearest enemy
        nearest_enemy = self._find_nearest_enemy(unit)

        if not nearest_enemy or not nearest_enemy.position:
            return None

        # Get reachable positions
        reachable = self.movement.get_reachable_positions(unit)

        if not reachable:
            return None

        # Evaluate all reachable positions
        best_position = None
        best_score = float('-inf')

        for pos_tuple, cost in reachable.items():
            pos = BattlePosition(pos_tuple[0], pos_tuple[1])

            # Calculate score
            score = self.evaluate_position(unit, pos)

            # Adjust for aggression
            distance_to_enemy = pos.distance_to(nearest_enemy.position)
            if self.aggression > 0.5:
                # Aggressive: prefer closer positions
                score -= distance_to_enemy * 10
            else:
                # Defensive: prefer safe positions
                score += distance_to_enemy * 5

            if score > best_score:
                best_score = score
                best_position = pos

        if best_position:
            # Move to position
            if self.movement.move_unit(unit, best_position):
                return f"{unit.name} moves tactically"

        return None

    def _select_target(
        self,
        attacker: CombatUnit,
        targets: list[CombatUnit]
    ) -> Optional[CombatUnit]:
        """Enhanced target selection with focus fire."""
        if not targets:
            return None

        # Score each target
        best_target = None
        best_score = float('-inf')

        for target in targets:
            score = 0.0

            # Prioritize low HP targets (finish them off)
            hp_percent = target.get_hp_percentage()
            if hp_percent < 30:
                score += 100
            elif hp_percent < 60:
                score += 50

            # Prioritize high-threat targets (high attack)
            score += target.get_total_attack() * 2

            # Slightly prefer closer targets
            if attacker.position and target.position:
                distance = attacker.position.distance_to(target.position)
                score -= distance * 5

            if score > best_score:
                best_score = score
                best_target = target

        return best_target
