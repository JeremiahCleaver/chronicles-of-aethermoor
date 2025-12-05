"""
Monster model - represents creatures that spawn in the wilderness.

Monsters appear in uncontrolled territories, threatening nations and
providing opportunities for combat experience and loot.
"""

from dataclasses import dataclass, field
from typing import Optional
from src.data.constants import Element
import random


@dataclass
class MonsterType:
    """Definition of a monster species."""
    monster_type_id: str
    name: str
    description: str

    # Base stats
    base_hp: int
    base_attack: int
    base_defense: int
    base_magic_attack: int
    base_magic_defense: int
    base_speed: int

    # Properties
    element: Optional[Element] = None
    tier: int = 1  # 1-5, difficulty tier
    is_boss: bool = False
    is_flying: bool = False

    # Spawning
    preferred_biomes: list[str] = field(default_factory=list)
    spawn_rarity: float = 1.0  # 0.1 (rare) to 1.0 (common)
    min_turn_to_spawn: int = 1  # Monsters appear after certain turns

    # Loot
    gold_reward: tuple[int, int] = (10, 50)  # Min, max
    exp_reward: int = 50

    # Behavior
    aggression: float = 0.5  # How likely to attack nearby territories
    roaming: bool = False  # Can move between territories


# ============================================================================
# MONSTER TYPE DEFINITIONS
# ============================================================================

MONSTER_TYPES = {
    # Tier 1: Early game
    "goblin": MonsterType(
        monster_type_id="goblin",
        name="Goblin Raider",
        description="Small green creatures that attack in packs",
        base_hp=40,
        base_attack=8,
        base_defense=5,
        base_magic_attack=2,
        base_magic_defense=3,
        base_speed=12,
        tier=1,
        preferred_biomes=["forest", "plains"],
        spawn_rarity=1.0,
        gold_reward=(5, 15),
        exp_reward=25,
        aggression=0.7,
        roaming=True,
    ),

    "wolf": MonsterType(
        monster_type_id="wolf",
        name="Dire Wolf",
        description="Ferocious predators that hunt in the wilderness",
        base_hp=50,
        base_attack=12,
        base_defense=6,
        base_magic_attack=0,
        base_magic_defense=4,
        base_speed=16,
        element=Element.EARTH,
        tier=1,
        preferred_biomes=["forest", "plains"],
        spawn_rarity=0.8,
        gold_reward=(10, 25),
        exp_reward=30,
        aggression=0.6,
        roaming=True,
    ),

    "skeleton": MonsterType(
        monster_type_id="skeleton",
        name="Skeleton Warrior",
        description="Undead soldiers risen from ancient battlefields",
        base_hp=45,
        base_attack=10,
        base_defense=8,
        base_magic_attack=0,
        base_magic_defense=6,
        base_speed=8,
        element=Element.DEATH,
        tier=1,
        preferred_biomes=["swamp", "volcano"],
        spawn_rarity=0.7,
        gold_reward=(15, 30),
        exp_reward=35,
        aggression=0.5,
        roaming=False,
    ),

    # Tier 2: Mid game
    "orc": MonsterType(
        monster_type_id="orc",
        name="Orc Berserker",
        description="Brutal warriors with incredible strength",
        base_hp=80,
        base_attack=18,
        base_defense=12,
        base_magic_attack=0,
        base_magic_defense=6,
        base_speed=10,
        tier=2,
        preferred_biomes=["mountain", "plains"],
        spawn_rarity=0.6,
        min_turn_to_spawn=10,
        gold_reward=(30, 80),
        exp_reward=75,
        aggression=0.8,
        roaming=True,
    ),

    "fire_elemental": MonsterType(
        monster_type_id="fire_elemental",
        name="Fire Elemental",
        description="Living flame born from volcanic energy",
        base_hp=60,
        base_attack=8,
        base_defense=6,
        base_magic_attack=20,
        base_magic_defense=12,
        base_speed=14,
        element=Element.FIRE,
        tier=2,
        preferred_biomes=["volcano"],
        spawn_rarity=0.5,
        min_turn_to_spawn=15,
        gold_reward=(40, 100),
        exp_reward=100,
        aggression=0.7,
        roaming=False,
    ),

    "troll": MonsterType(
        monster_type_id="troll",
        name="Cave Troll",
        description="Massive creatures with regenerative abilities",
        base_hp=120,
        base_attack=16,
        base_defense=14,
        base_magic_attack=0,
        base_magic_defense=8,
        base_speed=6,
        tier=2,
        preferred_biomes=["mountain", "forest"],
        spawn_rarity=0.4,
        min_turn_to_spawn=20,
        gold_reward=(50, 120),
        exp_reward=125,
        aggression=0.5,
        roaming=False,
    ),

    # Tier 3: Late game
    "dragon_wyrmling": MonsterType(
        monster_type_id="dragon_wyrmling",
        name="Dragon Wyrmling",
        description="Young dragon, still dangerous and greedy",
        base_hp=150,
        base_attack=22,
        base_defense=18,
        base_magic_attack=24,
        base_magic_defense=16,
        base_speed=12,
        element=Element.FIRE,
        tier=3,
        is_flying=True,
        preferred_biomes=["mountain", "volcano"],
        spawn_rarity=0.2,
        min_turn_to_spawn=30,
        gold_reward=(100, 300),
        exp_reward=250,
        aggression=0.6,
        roaming=True,
    ),

    "lich": MonsterType(
        monster_type_id="lich",
        name="Ancient Lich",
        description="Undead sorcerer of immense power",
        base_hp=100,
        base_attack=10,
        base_defense=12,
        base_magic_attack=30,
        base_magic_defense=22,
        base_speed=8,
        element=Element.DEATH,
        tier=3,
        preferred_biomes=["swamp", "volcano"],
        spawn_rarity=0.15,
        min_turn_to_spawn=40,
        gold_reward=(150, 400),
        exp_reward=350,
        aggression=0.7,
        roaming=False,
    ),
}


@dataclass
class MonsterNest:
    """
    A monster nest/lair that spawns creatures.

    Nests grow over time if left unchecked, producing more
    and stronger monsters.
    """
    nest_id: str
    territory_id: str  # Where the nest is located
    monster_type_id: str  # Type of monsters spawned

    # Nest properties
    nest_level: int = 1  # 1-5, higher = more/stronger monsters
    turns_active: int = 0  # How long nest has existed
    last_spawn_turn: int = 0  # When monsters were last spawned

    # Monster population
    current_monsters: int = 1  # How many monsters currently at nest
    max_monsters: int = 5  # Maximum monsters nest can hold

    def should_spawn(self, current_turn: int, spawn_interval: int = 5) -> bool:
        """Check if nest should spawn more monsters."""
        if self.current_monsters >= self.max_monsters:
            return False

        turns_since_spawn = current_turn - self.last_spawn_turn
        return turns_since_spawn >= spawn_interval

    def spawn_monster(self, current_turn: int) -> bool:
        """
        Spawn a new monster at this nest.

        Returns:
            True if monster spawned successfully
        """
        if self.current_monsters >= self.max_monsters:
            return False

        self.current_monsters += 1
        self.last_spawn_turn = current_turn
        return True

    def grow_nest(self) -> None:
        """Increase nest level (makes it more dangerous)."""
        if self.nest_level < 5:
            self.nest_level += 1
            self.max_monsters += 2  # Can hold more monsters

    def remove_monster(self) -> None:
        """Remove a monster (e.g., when defeated)."""
        self.current_monsters = max(0, self.current_monsters - 1)

    def get_threat_level(self) -> str:
        """Get human-readable threat level."""
        if self.nest_level == 1:
            return "Minor"
        elif self.nest_level == 2:
            return "Moderate"
        elif self.nest_level == 3:
            return "Serious"
        elif self.nest_level == 4:
            return "Severe"
        else:
            return "Critical"

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "nest_id": self.nest_id,
            "territory_id": self.territory_id,
            "monster_type_id": self.monster_type_id,
            "nest_level": self.nest_level,
            "turns_active": self.turns_active,
            "last_spawn_turn": self.last_spawn_turn,
            "current_monsters": self.current_monsters,
            "max_monsters": self.max_monsters,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterNest":
        """Load from dictionary."""
        return cls(
            nest_id=data["nest_id"],
            territory_id=data["territory_id"],
            monster_type_id=data["monster_type_id"],
            nest_level=data.get("nest_level", 1),
            turns_active=data.get("turns_active", 0),
            last_spawn_turn=data.get("last_spawn_turn", 0),
            current_monsters=data.get("current_monsters", 1),
            max_monsters=data.get("max_monsters", 5),
        )


@dataclass
class MonsterParty:
    """
    A group of monsters roaming or defending territory.

    These can attack territories, defend nests, or wander the wilderness.
    """
    party_id: str
    territory_id: str  # Current location
    monster_type_id: str  # Type of monsters in party

    # Party composition
    monster_count: int = 3  # How many monsters
    party_level: int = 1  # Average level/strength

    # Behavior
    is_roaming: bool = False  # Can move between territories
    is_guarding_nest: bool = False  # Protecting a nest
    target_territory_id: Optional[str] = None  # Where party is heading

    # Stats (derived from monster type and count)
    total_strength: int = 0  # Combat power

    def calculate_strength(self) -> int:
        """Calculate total combat strength of party."""
        monster_type = MONSTER_TYPES.get(self.monster_type_id)
        if not monster_type:
            return 0

        # Base strength per monster
        base_strength = (
            monster_type.base_hp +
            monster_type.base_attack * 2 +
            monster_type.base_defense
        )

        # Multiply by count and level
        self.total_strength = base_strength * self.monster_count * self.party_level
        return self.total_strength

    def take_casualties(self, losses: int) -> bool:
        """
        Reduce monster count due to combat.

        Returns:
            True if party still exists, False if wiped out
        """
        self.monster_count = max(0, self.monster_count - losses)
        self.calculate_strength()
        return self.monster_count > 0

    def move_to_territory(self, territory_id: str) -> None:
        """Move party to a new territory."""
        self.territory_id = territory_id
        self.target_territory_id = None

    def get_monster_type(self) -> Optional[MonsterType]:
        """Get the monster type definition."""
        return MONSTER_TYPES.get(self.monster_type_id)

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "party_id": self.party_id,
            "territory_id": self.territory_id,
            "monster_type_id": self.monster_type_id,
            "monster_count": self.monster_count,
            "party_level": self.party_level,
            "is_roaming": self.is_roaming,
            "is_guarding_nest": self.is_guarding_nest,
            "target_territory_id": self.target_territory_id,
            "total_strength": self.total_strength,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterParty":
        """Load from dictionary."""
        party = cls(
            party_id=data["party_id"],
            territory_id=data["territory_id"],
            monster_type_id=data["monster_type_id"],
            monster_count=data.get("monster_count", 3),
            party_level=data.get("party_level", 1),
            is_roaming=data.get("is_roaming", False),
            is_guarding_nest=data.get("is_guarding_nest", False),
            target_territory_id=data.get("target_territory_id"),
        )
        party.total_strength = data.get("total_strength", 0)
        if party.total_strength == 0:
            party.calculate_strength()
        return party


def get_suitable_monster_types(biome_id: str, current_turn: int) -> list[MonsterType]:
    """
    Get monster types that can spawn in a given biome at current turn.

    Args:
        biome_id: Biome type (e.g., "forest", "mountain")
        current_turn: Current game turn

    Returns:
        List of suitable monster types
    """
    suitable = []

    for monster_type in MONSTER_TYPES.values():
        # Check if monster can spawn yet
        if current_turn < monster_type.min_turn_to_spawn:
            continue

        # Check if biome is preferred (or no preference)
        if not monster_type.preferred_biomes or biome_id in monster_type.preferred_biomes:
            suitable.append(monster_type)

    return suitable


def select_random_monster_type(biome_id: str, current_turn: int) -> Optional[MonsterType]:
    """
    Select a random monster type suitable for the biome.

    Respects spawn rarity weights.
    """
    suitable = get_suitable_monster_types(biome_id, current_turn)

    if not suitable:
        return None

    # Weight by rarity
    weights = [m.spawn_rarity for m in suitable]
    return random.choices(suitable, weights=weights, k=1)[0]
