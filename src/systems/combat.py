"""
Combat System - Handles damage calculation, attacks, and battle actions.
"""

import random
from typing import Optional
from dataclasses import dataclass
from src.models.battle import BattleGrid, BattlePosition, CombatUnit, CombatUnitStatus
from src.data.constants import Element


@dataclass
class AttackResult:
    """Result of an attack action."""
    hit: bool
    damage: int
    critical: bool = False
    elemental_bonus: float = 1.0
    terrain_bonus: int = 0
    height_bonus: int = 0
    message: str = ""


@dataclass
class CombatAction:
    """Represents a combat action (attack, ability, item)."""
    action_type: str  # "attack", "ability", "item", "move"
    actor_id: str
    target_id: Optional[str] = None
    target_position: Optional[BattlePosition] = None
    ability_id: Optional[str] = None
    item_id: Optional[str] = None


class CombatSystem:
    """
    Handles combat calculations and battle actions.

    Includes:
    - Physical and magical damage
    - Elemental advantages
    - Critical hits
    - Terrain modifiers
    - Status effects
    """

    # Elemental advantage chart
    ELEMENT_ADVANTAGES = {
        Element.FIRE: {Element.EARTH, Element.DEATH},  # Fire beats Earth, Death
        Element.WATER: {Element.FIRE},  # Water beats Fire
        Element.EARTH: {Element.AIR},  # Earth beats Air
        Element.AIR: {Element.WATER},  # Air beats Water
        Element.LIFE: {Element.DEATH},  # Life beats Death
        Element.DEATH: {Element.LIFE},  # Death beats Life (mutual weakness)
    }

    # Base hit chance
    BASE_HIT_CHANCE = 90
    CRITICAL_HIT_CHANCE = 10

    def __init__(self, battle_grid: BattleGrid):
        """
        Initialize combat system.

        Args:
            battle_grid: Battle grid to operate on
        """
        self.grid = battle_grid

    def calculate_physical_damage(
        self,
        attacker: CombatUnit,
        defender: CombatUnit
    ) -> AttackResult:
        """
        Calculate physical attack damage.

        Args:
            attacker: Attacking unit
            defender: Defending unit

        Returns:
            AttackResult with damage and modifiers
        """
        result = AttackResult(hit=False, damage=0)

        # Check if attack hits
        hit_chance = self._calculate_hit_chance(attacker, defender)
        if random.randint(1, 100) > hit_chance:
            result.message = "Miss!"
            return result

        result.hit = True

        # Base damage calculation
        attack_power = attacker.get_total_attack()
        defense = defender.get_total_defense()

        base_damage = max(1, attack_power - defense // 2)

        # Critical hit check
        if random.randint(1, 100) <= self.CRITICAL_HIT_CHANCE:
            result.critical = True
            base_damage = int(base_damage * 1.5)

        # Elemental modifier
        if attacker.element and defender.element:
            elemental_mod = self._get_elemental_modifier(
                attacker.element,
                defender.element
            )
            result.elemental_bonus = elemental_mod
            base_damage = int(base_damage * elemental_mod)

        # Terrain defense bonus
        if defender.position:
            defender_cell = self.grid.get_cell_at_position(defender.position)
            if defender_cell:
                terrain_bonus = defender_cell.get_defense_bonus()
                result.terrain_bonus = terrain_bonus
                defense_multiplier = 1.0 - (terrain_bonus / 100.0)
                base_damage = int(base_damage * defense_multiplier)

        # Height advantage
        if attacker.position and defender.position:
            attacker_cell = self.grid.get_cell_at_position(attacker.position)
            defender_cell = self.grid.get_cell_at_position(defender.position)
            if attacker_cell and defender_cell:
                height_diff = attacker_cell.height - defender_cell.height
                if height_diff > 0:
                    # Attacker has height advantage
                    height_bonus = height_diff * 5  # 5% per height level
                    result.height_bonus = height_bonus
                    base_damage = int(base_damage * (1.0 + height_bonus / 100.0))
                elif height_diff < 0:
                    # Defender has height advantage
                    height_penalty = abs(height_diff) * 5
                    result.height_bonus = -height_penalty
                    base_damage = int(base_damage * (1.0 - height_penalty / 100.0))

        # Random variance (±10%)
        variance = random.uniform(0.9, 1.1)
        base_damage = int(base_damage * variance)

        # Minimum damage
        result.damage = max(1, base_damage)

        # Build message
        messages = []
        if result.critical:
            messages.append("Critical Hit!")
        if result.elemental_bonus > 1.0:
            messages.append("Super effective!")
        elif result.elemental_bonus < 1.0:
            messages.append("Not very effective...")
        if result.height_bonus > 0:
            messages.append("Height advantage!")

        result.message = " ".join(messages) if messages else f"{result.damage} damage!"

        return result

    def calculate_magical_damage(
        self,
        attacker: CombatUnit,
        defender: CombatUnit,
        spell_power: int = 100
    ) -> AttackResult:
        """
        Calculate magical attack damage.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            spell_power: Base power of spell

        Returns:
            AttackResult with damage and modifiers
        """
        result = AttackResult(hit=True, damage=0)  # Magic always hits

        # Base damage calculation
        magic_attack = attacker.magic_attack
        magic_defense = defender.magic_defense

        base_damage = spell_power + magic_attack - magic_defense // 2
        base_damage = max(1, base_damage)

        # Elemental modifier (stronger for magic)
        if attacker.element and defender.element:
            elemental_mod = self._get_elemental_modifier(
                attacker.element,
                defender.element
            )
            result.elemental_bonus = elemental_mod
            # Magic gets 1.5x elemental modifier
            enhanced_mod = 1.0 + (elemental_mod - 1.0) * 1.5
            base_damage = int(base_damage * enhanced_mod)

        # Random variance (±15% for magic)
        variance = random.uniform(0.85, 1.15)
        base_damage = int(base_damage * variance)

        result.damage = max(1, base_damage)

        # Build message
        messages = []
        if result.elemental_bonus > 1.0:
            messages.append("Super effective!")
        elif result.elemental_bonus < 1.0:
            messages.append("Resisted...")

        result.message = " ".join(messages) if messages else f"{result.damage} damage!"

        return result

    def _calculate_hit_chance(
        self,
        attacker: CombatUnit,
        defender: CombatUnit
    ) -> int:
        """
        Calculate chance to hit.

        Args:
            attacker: Attacking unit
            defender: Defending unit

        Returns:
            Hit chance percentage (0-100)
        """
        # Base hit chance
        hit_chance = self.BASE_HIT_CHANCE

        # Speed difference affects evasion
        speed_diff = defender.get_total_speed() - attacker.get_total_speed()
        evasion_bonus = speed_diff // 2  # Each 2 speed = 1% evasion

        hit_chance -= evasion_bonus

        # Terrain evasion
        if defender.position:
            defender_cell = self.grid.get_cell_at_position(defender.position)
            if defender_cell:
                terrain_evasion = defender_cell.get_defense_bonus() // 5
                hit_chance -= terrain_evasion

        # Status effects
        if attacker.has_status(CombatUnitStatus.BLESSED):
            hit_chance += 10
        if defender.has_status(CombatUnitStatus.BLESSED):
            hit_chance -= 10

        # Clamp to valid range
        return max(10, min(100, hit_chance))

    def _get_elemental_modifier(
        self,
        attacker_element: Element,
        defender_element: Element
    ) -> float:
        """
        Get elemental damage modifier.

        Args:
            attacker_element: Attacker's element
            defender_element: Defender's element

        Returns:
            Damage multiplier (0.5 = weak, 1.0 = neutral, 1.5 = strong)
        """
        if attacker_element == defender_element:
            return 0.5  # Same element = resistant

        # Check advantages
        if defender_element in self.ELEMENT_ADVANTAGES.get(attacker_element, set()):
            return 1.5  # Super effective

        if attacker_element in self.ELEMENT_ADVANTAGES.get(defender_element, set()):
            return 0.75  # Not very effective

        return 1.0  # Neutral

    def execute_attack(
        self,
        attacker_id: str,
        defender_id: str,
        attack_type: str = "physical"
    ) -> Optional[AttackResult]:
        """
        Execute an attack.

        Args:
            attacker_id: Attacker unit ID
            defender_id: Defender unit ID
            attack_type: "physical" or "magical"

        Returns:
            AttackResult or None if attack cannot be performed
        """
        # Get units
        attacker = self.grid.units.get(attacker_id)
        defender = self.grid.units.get(defender_id)

        if not attacker or not defender:
            return None

        # Check if attacker can act
        if not attacker.can_act():
            return None

        # Check if units are in range
        if not attacker.position or not defender.position:
            return None

        attack_range = 1  # Melee range
        distance = attacker.position.distance_to(defender.position)
        if distance > attack_range:
            return None

        # Calculate damage
        if attack_type == "physical":
            result = self.calculate_physical_damage(attacker, defender)
        else:
            result = self.calculate_magical_damage(attacker, defender)

        # Apply damage
        if result.hit:
            defender.take_damage(result.damage)

            # Check for status effects from damage
            self._apply_damage_status_effects(attacker, defender)

        # Mark attacker as having acted
        attacker.has_acted = True

        return result

    def _apply_damage_status_effects(
        self,
        attacker: CombatUnit,
        defender: CombatUnit
    ) -> None:
        """Apply status effects from attacks."""
        # Fire element can cause burning
        if attacker.element == Element.FIRE:
            if random.randint(1, 100) <= 20:  # 20% chance
                defender.add_status(CombatUnitStatus.BURNING, duration=3)

        # Death element can poison
        if attacker.element == Element.DEATH:
            if random.randint(1, 100) <= 20:
                defender.add_status(CombatUnitStatus.POISONED, duration=3)

        # Water element can slow
        if attacker.element == Element.WATER:
            if random.randint(1, 100) <= 15:
                defender.add_status(CombatUnitStatus.SLOWED, duration=2)

    def apply_status_damage(self, unit: CombatUnit) -> int:
        """
        Apply damage from status effects.

        Args:
            unit: Unit to apply status damage to

        Returns:
            Total damage dealt
        """
        total_damage = 0

        if unit.has_status(CombatUnitStatus.BURNING):
            damage = max(1, unit.max_hp // 10)  # 10% max HP
            unit.take_damage(damage)
            total_damage += damage

        if unit.has_status(CombatUnitStatus.POISONED):
            damage = max(1, unit.max_hp // 20)  # 5% max HP
            unit.take_damage(damage)
            total_damage += damage

        return total_damage

    def can_target(
        self,
        attacker: CombatUnit,
        defender: CombatUnit,
        attack_range: int = 1
    ) -> bool:
        """
        Check if attacker can target defender.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            attack_range: Attack range (default: 1 for melee)

        Returns:
            True if target is valid
        """
        if not attacker.position or not defender.position:
            return False

        # Check range
        distance = attacker.position.distance_to(defender.position)
        if distance > attack_range:
            return False

        # Can't target allies (basic implementation)
        if attacker.side == defender.side:
            return False

        # Check if defender is alive
        if not defender.is_alive():
            return False

        return True

    def get_targets_in_range(
        self,
        attacker: CombatUnit,
        attack_range: int = 1
    ) -> list[CombatUnit]:
        """
        Get all valid targets in range of attacker.

        Args:
            attacker: Attacking unit
            attack_range: Attack range

        Returns:
            List of targetable units
        """
        if not attacker.position:
            return []

        targets = []

        for unit in self.grid.units.values():
            if unit.unit_id == attacker.unit_id:
                continue

            if self.can_target(attacker, unit, attack_range):
                targets.append(unit)

        return targets

    def calculate_healing(
        self,
        healer: CombatUnit,
        target: CombatUnit,
        heal_power: int = 50
    ) -> int:
        """
        Calculate healing amount.

        Args:
            healer: Unit performing heal
            target: Unit being healed
            heal_power: Base healing power

        Returns:
            Amount healed
        """
        # Base healing
        heal_amount = heal_power + healer.magic_attack // 2

        # Life element bonus
        if healer.element == Element.LIFE:
            heal_amount = int(heal_amount * 1.3)

        # Blessed status bonus
        if healer.has_status(CombatUnitStatus.BLESSED):
            heal_amount = int(heal_amount * 1.2)

        # Random variance (±10%)
        variance = random.uniform(0.9, 1.1)
        heal_amount = int(heal_amount * variance)

        # Apply healing
        actual_healing = target.heal(heal_amount)

        return actual_healing
