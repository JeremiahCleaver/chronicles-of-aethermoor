"""
Unit model - represents characters, monsters, and army units.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from src.data.constants import (
    Element,
    UnitStat,
    EquipmentSlot,
    ClassTier,
    MAX_LEVEL,
    BASE_HP,
    BASE_STAT,
    GENERAL_DEATH_LIMIT,
)


class UnitStats(BaseModel):
    """Unit statistics."""
    hp: int = Field(default=BASE_HP, ge=0)
    max_hp: int = Field(default=BASE_HP, gt=0)
    atk: int = Field(default=BASE_STAT, ge=0)
    mag: int = Field(default=BASE_STAT, ge=0)
    def_: int = Field(default=BASE_STAT, ge=0, alias="def")
    res: int = Field(default=BASE_STAT, ge=0)
    spd: int = Field(default=BASE_STAT, ge=0)
    crit: float = Field(default=0.05, ge=0.0, le=1.0)

    class Config:
        populate_by_name = True


class Equipment(BaseModel):
    """Equipped items."""
    weapon: Optional[str] = None
    off_hand: Optional[str] = None
    head: Optional[str] = None
    body: Optional[str] = None
    hands: Optional[str] = None
    feet: Optional[str] = None
    accessory_1: Optional[str] = None
    accessory_2: Optional[str] = None

    def get_slot(self, slot: EquipmentSlot) -> Optional[str]:
        """Get item in specified slot."""
        return getattr(self, slot.value)

    def set_slot(self, slot: EquipmentSlot, item_id: Optional[str]) -> None:
        """Equip item to specified slot."""
        setattr(self, slot.value, item_id)


class JobClass(BaseModel):
    """Job class information."""
    class_id: str = Field(..., description="Unique class identifier")
    name: str = Field(..., description="Display name")
    tier: ClassTier = Field(default=ClassTier.TIER_1)
    element: Optional[Element] = Field(default=None, description="Elemental affinity")

    # Stat modifiers from this class
    stat_bonuses: UnitStats = Field(default_factory=UnitStats)

    # Unlock requirements
    required_level: int = Field(default=1, ge=1, le=MAX_LEVEL)
    required_class: Optional[str] = Field(default=None)
    required_battles: int = Field(default=0, ge=0)


class Unit(BaseModel):
    """
    Represents a unit - character, monster, or army member.

    Units can be:
    - Player generals (named characters with progression)
    - Recruited soldiers (class-based units)
    - Summoned monsters (elemental creatures)
    - Enemy units (AI-controlled)
    """

    # Identity
    unit_id: str = Field(..., description="Unique unit identifier")
    name: str = Field(..., description="Unit display name")
    is_general: bool = Field(default=False, description="True if this is a general")
    is_monster: bool = Field(default=False, description="True if summoned monster")
    owner_id: str = Field(..., description="Nation that controls this unit")

    # Job/Class
    current_class: JobClass = Field(..., description="Current job class")
    available_classes: list[str] = Field(default_factory=list, description="Unlocked class IDs")

    # Level and Experience
    level: int = Field(default=1, ge=1, le=MAX_LEVEL)
    experience: int = Field(default=0, ge=0)
    experience_to_next: int = Field(default=100, gt=0)

    # Stats
    base_stats: UnitStats = Field(default_factory=UnitStats)
    current_stats: UnitStats = Field(default_factory=UnitStats)

    # Equipment
    equipment: Equipment = Field(default_factory=Equipment)

    # Elemental Affinity
    element: Optional[Element] = Field(default=None)
    elemental_points: dict[Element, int] = Field(
        default_factory=lambda: {elem: 0 for elem in Element}
    )

    # Combat State
    position: Optional[tuple[int, int]] = Field(default=None, description="Grid position (x, y)")
    action_points: int = Field(default=1, ge=0)
    has_acted: bool = Field(default=False)
    status_effects: list[str] = Field(default_factory=list)

    # General-specific (3-lives system)
    death_count: int = Field(default=0, ge=0, le=GENERAL_DEATH_LIMIT)
    is_permadead: bool = Field(default=False)

    # Monster-specific
    evolution_tier: int = Field(default=1, ge=1, le=5)
    evolution_progress: int = Field(default=0, ge=0)

    # Battle Statistics
    battles_fought: int = Field(default=0, ge=0)
    battles_won: int = Field(default=0, ge=0)
    kills: int = Field(default=0, ge=0)
    damage_dealt: int = Field(default=0, ge=0)
    damage_taken: int = Field(default=0, ge=0)

    @validator('current_stats', always=True)
    def calculate_current_stats(cls, v, values):
        """Recalculate current stats from base + equipment + class bonuses."""
        if 'base_stats' not in values:
            return v

        # Start with base stats
        stats = values['base_stats'].copy()

        # Add class bonuses
        if 'current_class' in values:
            class_bonuses = values['current_class'].stat_bonuses
            stats.atk += class_bonuses.atk
            stats.mag += class_bonuses.mag
            stats.def_ += class_bonuses.def_
            stats.res += class_bonuses.res
            stats.spd += class_bonuses.spd
            stats.max_hp += class_bonuses.max_hp
            stats.crit += class_bonuses.crit

        # TODO: Add equipment bonuses when equipment system is implemented

        # Ensure HP doesn't exceed max_hp
        stats.hp = min(stats.hp, stats.max_hp)

        return stats

    def gain_experience(self, amount: int) -> bool:
        """
        Add experience points. Returns True if leveled up.
        """
        self.experience += amount

        if self.experience >= self.experience_to_next:
            self.level_up()
            return True

        return False

    def level_up(self) -> None:
        """Increase level and improve stats."""
        if self.level >= MAX_LEVEL:
            return

        self.level += 1
        self.experience -= self.experience_to_next

        # Calculate next level XP requirement (exponential curve)
        from src.data.constants import XP_CURVE_MULTIPLIER, BASE_XP_TO_LEVEL
        self.experience_to_next = int(BASE_XP_TO_LEVEL * (self.level ** XP_CURVE_MULTIPLIER))

        # Increase base stats (simplified growth)
        self.base_stats.max_hp += 5
        self.base_stats.hp = self.base_stats.max_hp
        self.base_stats.atk += 2
        self.base_stats.mag += 2
        self.base_stats.def_ += 1
        self.base_stats.res += 1
        self.base_stats.spd += 1

        # Recalculate current stats
        self.current_stats = self.calculate_current_stats(
            self.current_stats,
            self.dict()
        )

    def take_damage(self, amount: int) -> int:
        """
        Apply damage to unit. Returns actual damage dealt.
        """
        actual_damage = max(0, amount)
        self.current_stats.hp = max(0, self.current_stats.hp - actual_damage)
        self.damage_taken += actual_damage

        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal unit. Returns actual HP restored.
        """
        old_hp = self.current_stats.hp
        self.current_stats.hp = min(
            self.current_stats.max_hp,
            self.current_stats.hp + amount
        )
        return self.current_stats.hp - old_hp

    def is_alive(self) -> bool:
        """Check if unit is alive."""
        return self.current_stats.hp > 0 and not self.is_permadead

    def die(self) -> None:
        """Handle unit death."""
        self.current_stats.hp = 0

        if self.is_general:
            self.death_count += 1
            if self.death_count >= GENERAL_DEATH_LIMIT:
                self.is_permadead = True

    def reset_for_battle(self) -> None:
        """Reset unit state for new battle."""
        self.position = None
        self.action_points = 1
        self.has_acted = False
        self.status_effects.clear()

    def can_act(self) -> bool:
        """Check if unit can perform actions."""
        return (
            self.is_alive() and
            self.action_points > 0 and
            not self.has_acted and
            'stunned' not in self.status_effects
        )
