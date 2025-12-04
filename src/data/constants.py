"""
Game constants and configuration values.
Based on Chronicles of Aethermoor design document.
"""

from enum import Enum, auto
from typing import Final

# ============================================================================
# ELEMENTAL SYSTEM
# ============================================================================

class Element(Enum):
    """The six elemental forces that shape the world."""
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"
    LIFE = "life"
    DEATH = "death"

# Elemental advantages (attacker -> defender = damage multiplier)
ELEMENTAL_ADVANTAGES: Final[dict[Element, list[Element]]] = {
    Element.FIRE: [Element.EARTH, Element.LIFE],      # Fire burns earth/life
    Element.WATER: [Element.FIRE, Element.DEATH],     # Water quenches fire/washes death
    Element.EARTH: [Element.AIR, Element.WATER],      # Earth grounds air/absorbs water
    Element.AIR: [Element.DEATH, Element.FIRE],       # Air disperses death/fans fire
    Element.LIFE: [Element.DEATH, Element.WATER],     # Life opposes death/grows with water
    Element.DEATH: [Element.LIFE, Element.EARTH],     # Death consumes life/decays earth
}

SUPER_EFFECTIVE_MULTIPLIER: Final[float] = 1.5
RESISTED_MULTIPLIER: Final[float] = 0.5

# ============================================================================
# GAME DIMENSIONS
# ============================================================================

# World Map
WORLD_MAP_WIDTH: Final[int] = 40
WORLD_MAP_HEIGHT: Final[int] = 30
MAX_TERRITORIES: Final[int] = WORLD_MAP_WIDTH * WORLD_MAP_HEIGHT

# Battle Grid
BATTLE_GRID_WIDTH: Final[int] = 12
BATTLE_GRID_HEIGHT: Final[int] = 18

# ============================================================================
# UNIT STATS
# ============================================================================

class UnitStat(Enum):
    """Primary unit statistics."""
    HP = "hp"           # Hit Points
    ATK = "atk"         # Physical Attack
    MAG = "mag"         # Magical Attack
    DEF = "def"         # Physical Defense
    RES = "res"         # Magical Resistance
    SPD = "spd"         # Speed (turn order)
    CRIT = "crit"       # Critical Hit Chance

# Base stat caps
MAX_LEVEL: Final[int] = 100
BASE_HP: Final[int] = 100
BASE_STAT: Final[int] = 50

# ============================================================================
# EQUIPMENT SYSTEM
# ============================================================================

class EquipmentSlot(Enum):
    """Eight body equipment slots."""
    WEAPON = "weapon"
    OFF_HAND = "off_hand"
    HEAD = "head"
    BODY = "body"
    HANDS = "hands"
    FEET = "feet"
    ACCESSORY_1 = "accessory_1"
    ACCESSORY_2 = "accessory_2"

class EquipmentTier(Enum):
    """Equipment quality tiers."""
    TIER_1 = 1  # Basic
    TIER_2 = 2  # Uncommon
    TIER_3 = 3  # Rare
    TIER_4 = 4  # Epic
    TIER_5 = 5  # Legendary

# ============================================================================
# COMBAT SYSTEM
# ============================================================================

class DamageType(Enum):
    """Types of damage."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"  # Ignores defense

class TargetType(Enum):
    """Ability targeting types."""
    SINGLE = "single"
    AOE = "aoe"
    SELF = "self"
    ALLY = "ally"
    ALL_ENEMIES = "all_enemies"
    ALL_ALLIES = "all_allies"

MAX_ARMY_SIZE: Final[int] = 8
MAX_ACTION_POINTS: Final[int] = 1  # Per unit per turn
CRITICAL_HIT_MULTIPLIER: Final[float] = 2.0
BASE_CRIT_CHANCE: Final[float] = 0.05  # 5%

# ============================================================================
# STRATEGIC LAYER
# ============================================================================

class ResourceType(Enum):
    """Strategic resources."""
    GOLD = "gold"
    FOOD = "food"
    TIMBER = "timber"
    IRON = "iron"
    LEATHER = "leather"
    HERBS = "herbs"
    GEMS = "gems"
    MITHRIL = "mithril"

class BuildingType(Enum):
    """Territory buildings."""
    BARRACKS = "barracks"
    WORKSHOP = "workshop"
    MAGE_TOWER = "mage_tower"
    SUMMONING_CIRCLE = "summoning_circle"
    MARKET = "market"
    FARM = "farm"
    MINE = "mine"
    LUMBERMILL = "lumbermill"
    TEMPLE = "temple"
    FORTRESS = "fortress"

TURNS_PER_MONTH: Final[int] = 4
MONTHS_PER_YEAR: Final[int] = 12
TURNS_PER_YEAR: Final[int] = TURNS_PER_MONTH * MONTHS_PER_YEAR

# ============================================================================
# PROGRESSION SYSTEM
# ============================================================================

class ClassTier(Enum):
    """Job class progression tiers."""
    TIER_1 = 1  # Basic
    TIER_2 = 2  # Advanced
    TIER_3 = 3  # Expert
    TIER_4 = 4  # Master
    TIER_5 = 5  # Legendary

XP_CURVE_MULTIPLIER: Final[float] = 1.2
BASE_XP_TO_LEVEL: Final[int] = 100

# ============================================================================
# DIPLOMACY
# ============================================================================

class DiplomaticRelation(Enum):
    """Relations between nations."""
    WAR = "war"
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"

RELATIONSHIP_MIN: Final[int] = -100
RELATIONSHIP_MAX: Final[int] = 100

# ============================================================================
# SAVE SYSTEM
# ============================================================================

MAX_SAVE_SLOTS: Final[int] = 10
MAX_AUTOSAVES: Final[int] = 3
SAVE_FILE_VERSION: Final[str] = "1.0.0"

# ============================================================================
# UI CONFIGURATION
# ============================================================================

class UITheme(Enum):
    """UI color themes."""
    DEFAULT = "default"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"

# Elemental colors for UI
ELEMENT_COLORS: Final[dict[Element, str]] = {
    Element.FIRE: "red",
    Element.WATER: "blue",
    Element.EARTH: "green",
    Element.AIR: "cyan",
    Element.LIFE: "yellow",
    Element.DEATH: "magenta",
}

# ============================================================================
# GAME BALANCE
# ============================================================================

# Worker productivity
WORKER_BASE_PRODUCTION: Final[int] = 10
WORKER_EXPERT_MULTIPLIER: Final[float] = 1.5
WORKER_MASTER_MULTIPLIER: Final[float] = 2.0

# Crafting
CRAFTING_BASE_SUCCESS_RATE: Final[float] = 0.8
CRAFTING_ELEMENTAL_BONUS: Final[float] = 0.2

# Monster summoning costs (mana crystals)
MONSTER_SUMMON_COSTS: Final[dict[int, int]] = {
    1: 5,   # Tier 1: 5 crystals
    2: 10,  # Tier 2: 10 crystals
    3: 20,  # Tier 3: 20 crystals
    4: 40,  # Tier 4: 40 crystals
    5: 80,  # Tier 5: 80 crystals
}

# General limits
MAX_GENERALS: Final[int] = 5
GENERAL_DEATH_LIMIT: Final[int] = 3  # Three-lives system

# ============================================================================
# DIFFICULTY SETTINGS
# ============================================================================

class Difficulty(Enum):
    """Game difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    LEGENDARY = "legendary"

AI_STAT_MULTIPLIERS: Final[dict[Difficulty, float]] = {
    Difficulty.EASY: 0.8,
    Difficulty.NORMAL: 1.0,
    Difficulty.HARD: 1.2,
    Difficulty.LEGENDARY: 1.5,
}

AI_RESOURCE_MULTIPLIERS: Final[dict[Difficulty, float]] = {
    Difficulty.EASY: 0.8,
    Difficulty.NORMAL: 1.0,
    Difficulty.HARD: 1.3,
    Difficulty.LEGENDARY: 2.0,
}
