"""
Unit Recruitment System - recruit units from territories and manage armies.

This system:
- Recruits tactical combat units from territories
- Manages unit progression and experience
- Converts strategic units to tactical battle units
- Handles unit equipment and loadouts
"""

from typing import Optional
from dataclasses import dataclass
from src.models.territory import Territory
from src.models.nation import Nation
from src.models.battle import BattleUnit
from src.data.constants import Element, ResourceType, BuildingType
import random


@dataclass
class UnitClass:
    """Definition of a recruitable unit class."""
    class_id: str
    name: str
    description: str

    # Requirements
    required_building: Optional[BuildingType] = None
    required_biome: Optional[str] = None  # If unit is biome-specific

    # Recruitment cost
    gold_cost: int = 100
    food_cost: int = 50
    resource_cost: dict[ResourceType, int] = None
    mana_cost: dict[Element, int] = None

    # Base stats for tactical combat
    base_hp: int = 100
    base_attack: int = 10
    base_defense: int = 10
    base_magic_attack: int = 5
    base_magic_defense: int = 5
    base_speed: int = 10
    base_move_range: int = 3

    # Properties
    element: Optional[Element] = None
    can_use_magic: bool = False
    is_flying: bool = False
    is_cavalry: bool = False

    def __post_init__(self):
        if self.resource_cost is None:
            self.resource_cost = {}
        if self.mana_cost is None:
            self.mana_cost = {}


# ============================================================================
# RECRUITABLE UNIT CLASSES
# ============================================================================

UNIT_CLASSES = {
    # Basic Infantry
    "militia": UnitClass(
        class_id="militia",
        name="Militia",
        description="Basic infantry, cheap and expendable",
        gold_cost=50,
        food_cost=25,
        base_hp=80,
        base_attack=8,
        base_defense=8,
        base_speed=10,
        base_move_range=3,
    ),

    "swordsman": UnitClass(
        class_id="swordsman",
        name="Swordsman",
        description="Trained infantry with sword and shield",
        required_building=BuildingType.BARRACKS,
        gold_cost=100,
        food_cost=50,
        resource_cost={ResourceType.IRON: 20},
        base_hp=100,
        base_attack=12,
        base_defense=12,
        base_speed=10,
        base_move_range=3,
    ),

    "knight": UnitClass(
        class_id="knight",
        name="Knight",
        description="Heavily armored cavalry",
        required_building=BuildingType.BARRACKS,
        gold_cost=250,
        food_cost=75,
        resource_cost={ResourceType.IRON: 50, ResourceType.LEATHER: 25},
        base_hp=120,
        base_attack=15,
        base_defense=16,
        base_speed=8,
        base_move_range=4,
        is_cavalry=True,
        element=Element.EARTH,
    ),

    # Ranged Units
    "archer": UnitClass(
        class_id="archer",
        name="Archer",
        description="Ranged attacker with bow",
        required_building=BuildingType.BARRACKS,
        gold_cost=120,
        food_cost=40,
        resource_cost={ResourceType.TIMBER: 30},
        base_hp=70,
        base_attack=14,
        base_defense=6,
        base_speed=12,
        base_move_range=3,
        element=Element.AIR,
    ),

    "crossbowman": UnitClass(
        class_id="crossbowman",
        name="Crossbowman",
        description="Heavy ranged unit with powerful crossbow",
        required_building=BuildingType.WORKSHOP,
        gold_cost=180,
        food_cost=50,
        resource_cost={ResourceType.IRON: 30, ResourceType.TIMBER: 20},
        base_hp=85,
        base_attack=18,
        base_defense=8,
        base_speed=10,
        base_move_range=3,
    ),

    # Magic Users
    "mage": UnitClass(
        class_id="mage",
        name="Battle Mage",
        description="Elemental spellcaster",
        required_building=BuildingType.MAGE_TOWER,
        gold_cost=200,
        food_cost=30,
        mana_cost={Element.FIRE: 5, Element.WATER: 5},
        base_hp=60,
        base_attack=5,
        base_defense=5,
        base_magic_attack=20,
        base_magic_defense=12,
        base_speed=8,
        base_move_range=3,
        element=Element.FIRE,
        can_use_magic=True,
    ),

    "cleric": UnitClass(
        class_id="cleric",
        name="Cleric",
        description="Holy healer and support caster",
        required_building=BuildingType.TEMPLE,
        gold_cost=180,
        food_cost=30,
        mana_cost={Element.LIFE: 10},
        base_hp=70,
        base_attack=6,
        base_defense=8,
        base_magic_attack=15,
        base_magic_defense=15,
        base_speed=9,
        base_move_range=3,
        element=Element.LIFE,
        can_use_magic=True,
    ),

    "necromancer": UnitClass(
        class_id="necromancer",
        name="Necromancer",
        description="Death magic specialist",
        required_building=BuildingType.SUMMONING_CIRCLE,
        gold_cost=250,
        food_cost=20,
        mana_cost={Element.DEATH: 15},
        base_hp=65,
        base_attack=4,
        base_defense=6,
        base_magic_attack=22,
        base_magic_defense=14,
        base_speed=7,
        base_move_range=3,
        element=Element.DEATH,
        can_use_magic=True,
    ),

    # Biome-Specific Units
    "forest_ranger": UnitClass(
        class_id="forest_ranger",
        name="Forest Ranger",
        description="Expert tracker and archer from forests",
        required_building=BuildingType.BARRACKS,
        required_biome="forest",
        gold_cost=150,
        food_cost=40,
        resource_cost={ResourceType.TIMBER: 20},
        base_hp=85,
        base_attack=16,
        base_defense=8,
        base_speed=14,
        base_move_range=4,
        element=Element.EARTH,
    ),

    "mountain_dwarf": UnitClass(
        class_id="mountain_dwarf",
        name="Mountain Dwarf",
        description="Hardy warrior from mountain holds",
        required_building=BuildingType.BARRACKS,
        required_biome="mountain",
        gold_cost=200,
        food_cost=60,
        resource_cost={ResourceType.IRON: 40},
        base_hp=130,
        base_attack=16,
        base_defense=18,
        base_speed=6,
        base_move_range=2,
        element=Element.EARTH,
    ),

    "storm_knight": UnitClass(
        class_id="storm_knight",
        name="Storm Knight",
        description="Thunder-wielding warrior",
        required_building=BuildingType.MAGE_TOWER,
        gold_cost=280,
        food_cost=60,
        mana_cost={Element.AIR: 10},
        base_hp=110,
        base_attack=14,
        base_defense=14,
        base_magic_attack=16,
        base_magic_defense=12,
        base_speed=12,
        base_move_range=4,
        element=Element.AIR,
        can_use_magic=True,
    ),
}


class RecruitmentSystem:
    """
    Manages unit recruitment and army composition.
    """

    def __init__(self):
        """Initialize recruitment system."""
        self.recruited_units: dict[str, dict] = {}  # unit_id -> unit data
        self.next_unit_id = 0

    def get_available_units(
        self,
        territory: Territory,
        nation: Nation,
    ) -> list[UnitClass]:
        """
        Get list of unit classes that can be recruited in this territory.

        Args:
            territory: Territory to recruit from
            nation: Nation doing the recruiting

        Returns:
            List of available unit classes
        """
        available = []

        for unit_class in UNIT_CLASSES.values():
            # Check building requirement
            if unit_class.required_building:
                if not territory.has_building(unit_class.required_building):
                    continue

            # Check biome requirement
            if unit_class.required_biome:
                if territory.biome.biome_id != unit_class.required_biome:
                    continue

            available.append(unit_class)

        return available

    def can_afford_unit(
        self,
        nation: Nation,
        unit_class: UnitClass,
    ) -> bool:
        """Check if nation can afford to recruit this unit."""
        # Check gold and food
        if nation.resources.get(ResourceType.GOLD, 0) < unit_class.gold_cost:
            return False
        if nation.resources.get(ResourceType.FOOD, 0) < unit_class.food_cost:
            return False

        # Check other resources
        for resource, amount in unit_class.resource_cost.items():
            if nation.resources.get(resource, 0) < amount:
                return False

        # Check mana
        for element, amount in unit_class.mana_cost.items():
            if nation.mana_crystals.get(element, 0) < amount:
                return False

        return True

    def recruit_unit(
        self,
        nation: Nation,
        territory: Territory,
        unit_class_id: str,
        unit_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Recruit a new unit.

        Args:
            nation: Nation recruiting the unit
            territory: Territory to recruit from
            unit_class_id: ID of unit class to recruit
            unit_name: Optional custom name for unit

        Returns:
            Unit ID if successful, None if failed
        """
        unit_class = UNIT_CLASSES.get(unit_class_id)
        if not unit_class:
            return None

        # Check if can afford
        if not self.can_afford_unit(nation, unit_class):
            return None

        # Check if available in territory
        available = self.get_available_units(territory, nation)
        if unit_class not in available:
            return None

        # Consume resources
        nation.resources[ResourceType.GOLD] -= unit_class.gold_cost
        nation.resources[ResourceType.FOOD] -= unit_class.food_cost

        for resource, amount in unit_class.resource_cost.items():
            nation.resources[resource] -= amount

        for element, amount in unit_class.mana_cost.items():
            nation.mana_crystals[element] -= amount

        # Create unit
        unit_id = f"unit_{nation.nation_id}_{self.next_unit_id}"
        self.next_unit_id += 1

        unit_data = {
            "unit_id": unit_id,
            "class_id": unit_class_id,
            "name": unit_name or unit_class.name,
            "owner_nation_id": nation.nation_id,
            "recruited_at_territory": territory.territory_id,
            "level": 1,
            "experience": 0,
            "equipment": {},  # Will add equipment system later
        }

        self.recruited_units[unit_id] = unit_data

        # Add to nation's generals/units
        nation.generals.append(unit_id)
        nation.units_recruited += 1

        # Update military strength
        strength = self._calculate_unit_strength(unit_class)
        nation.total_military_strength += strength

        return unit_id

    def create_battle_unit(
        self,
        unit_id: str,
        position: tuple[int, int],
        is_ai_controlled: bool = False,
    ) -> Optional[BattleUnit]:
        """
        Convert a strategic unit to a tactical battle unit.

        Args:
            unit_id: Strategic unit ID
            position: Starting position on battle grid
            is_ai_controlled: Whether unit is controlled by AI

        Returns:
            BattleUnit for tactical combat
        """
        unit_data = self.recruited_units.get(unit_id)
        if not unit_data:
            return None

        unit_class = UNIT_CLASSES.get(unit_data["class_id"])
        if not unit_class:
            return None

        # Apply level scaling
        level = unit_data.get("level", 1)
        stat_bonus = (level - 1) * 5  # +5 per level

        battle_unit = BattleUnit(
            unit_id=unit_id,
            name=unit_data["name"],
            position=position,
            max_hp=unit_class.base_hp + stat_bonus,
            current_hp=unit_class.base_hp + stat_bonus,
            attack=unit_class.base_attack + stat_bonus,
            defense=unit_class.base_defense + stat_bonus // 2,
            magic_attack=unit_class.base_magic_attack + stat_bonus,
            magic_defense=unit_class.base_magic_defense + stat_bonus // 2,
            speed=unit_class.base_speed,
            move_range=unit_class.base_move_range,
            element=unit_class.element,
            is_ai_controlled=is_ai_controlled,
        )

        return battle_unit

    def gain_experience(
        self,
        unit_id: str,
        exp_amount: int,
    ) -> bool:
        """
        Give experience to a unit, potentially leveling up.

        Returns:
            True if unit leveled up
        """
        unit_data = self.recruited_units.get(unit_id)
        if not unit_data:
            return False

        unit_data["experience"] += exp_amount

        # Check for level up (100 exp per level)
        exp_for_next_level = unit_data["level"] * 100
        leveled_up = False

        while unit_data["experience"] >= exp_for_next_level:
            unit_data["level"] += 1
            unit_data["experience"] -= exp_for_next_level
            exp_for_next_level = unit_data["level"] * 100
            leveled_up = True

        return leveled_up

    def _calculate_unit_strength(self, unit_class: UnitClass) -> int:
        """Calculate strategic military strength value for a unit."""
        return (
            unit_class.base_hp +
            unit_class.base_attack * 3 +
            unit_class.base_defense * 2 +
            unit_class.base_magic_attack * 2
        )

    def get_unit_info(self, unit_id: str) -> Optional[dict]:
        """Get information about a recruited unit."""
        unit_data = self.recruited_units.get(unit_id)
        if not unit_data:
            return None

        unit_class = UNIT_CLASSES.get(unit_data["class_id"])
        if not unit_class:
            return None

        return {
            "unit_id": unit_id,
            "name": unit_data["name"],
            "class": unit_class.name,
            "level": unit_data["level"],
            "experience": unit_data["experience"],
            "owner": unit_data["owner_nation_id"],
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "recruited_units": self.recruited_units,
            "next_unit_id": self.next_unit_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecruitmentSystem":
        """Load from dictionary."""
        system = cls()
        system.recruited_units = data.get("recruited_units", {})
        system.next_unit_id = data.get("next_unit_id", 0)
        return system
