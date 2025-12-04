"""
Nation model - represents player and AI nations in the game world.
"""

from dataclasses import dataclass, field
from typing import Optional
from src.data.constants import Element, ResourceType


@dataclass
class DiplomaticRelation:
    """Diplomatic relationship between two nations."""
    nation_id: str
    relationship: int = 0  # -100 (war) to +100 (alliance)

    # Diplomatic states
    at_war: bool = False
    has_trade_agreement: bool = False
    has_non_aggression_pact: bool = False
    has_alliance: bool = False

    # History tracking
    turns_at_current_state: int = 0
    last_interaction_turn: int = 0

    def get_relationship_status(self) -> str:
        """Get diplomatic status as a string."""
        if self.at_war:
            return "At War"
        elif self.has_alliance:
            return "Allied"
        elif self.has_non_aggression_pact:
            return "Non-Aggression Pact"
        elif self.has_trade_agreement:
            return "Trade Agreement"
        elif self.relationship >= 75:
            return "Friendly"
        elif self.relationship >= 25:
            return "Cordial"
        elif self.relationship >= -25:
            return "Neutral"
        elif self.relationship >= -75:
            return "Unfriendly"
        else:
            return "Hostile"

    def improve_relations(self, amount: int) -> None:
        """Improve relationship value."""
        if not self.at_war:
            self.relationship = min(100, self.relationship + amount)

    def worsen_relations(self, amount: int) -> None:
        """Worsen relationship value."""
        self.relationship = max(-100, self.relationship - amount)


@dataclass
class AIPersonality:
    """AI personality traits that affect behavior."""
    personality_type: str  # "aggressive", "diplomatic", "expansionist", "defensive", "balanced"

    # Behavioral weights (0.0 to 1.0)
    aggression: float = 0.5  # Likelihood to attack
    expansion_desire: float = 0.5  # Desire to conquer territory
    diplomacy_preference: float = 0.5  # Preference for diplomatic solutions
    economic_focus: float = 0.5  # Focus on economic development
    military_focus: float = 0.5  # Focus on military buildup

    # Strategic preferences
    preferred_element: Optional[Element] = None
    prefers_magic: bool = False
    prefers_melee: bool = False
    prefers_ranged: bool = False

    @classmethod
    def create_aggressive(cls) -> "AIPersonality":
        """Create aggressive AI personality."""
        return cls(
            personality_type="aggressive",
            aggression=0.8,
            expansion_desire=0.7,
            diplomacy_preference=0.2,
            military_focus=0.8,
            economic_focus=0.4,
        )

    @classmethod
    def create_diplomatic(cls) -> "AIPersonality":
        """Create diplomatic AI personality."""
        return cls(
            personality_type="diplomatic",
            aggression=0.2,
            expansion_desire=0.3,
            diplomacy_preference=0.9,
            military_focus=0.4,
            economic_focus=0.6,
        )

    @classmethod
    def create_expansionist(cls) -> "AIPersonality":
        """Create expansionist AI personality."""
        return cls(
            personality_type="expansionist",
            aggression=0.6,
            expansion_desire=0.9,
            diplomacy_preference=0.4,
            military_focus=0.6,
            economic_focus=0.7,
        )

    @classmethod
    def create_defensive(cls) -> "AIPersonality":
        """Create defensive AI personality."""
        return cls(
            personality_type="defensive",
            aggression=0.3,
            expansion_desire=0.2,
            diplomacy_preference=0.6,
            military_focus=0.7,
            economic_focus=0.5,
        )

    @classmethod
    def create_balanced(cls) -> "AIPersonality":
        """Create balanced AI personality."""
        return cls(
            personality_type="balanced",
            aggression=0.5,
            expansion_desire=0.5,
            diplomacy_preference=0.5,
            military_focus=0.5,
            economic_focus=0.5,
        )


@dataclass
class Nation:
    """
    Represents a nation in the game world.

    Each nation has:
    - Identity and leadership
    - Controlled territories
    - Resources and economy
    - Military forces
    - Diplomatic relations
    - AI behavior (if AI-controlled)
    """

    # Identity
    nation_id: str
    name: str
    leader_name: str = "Unknown Leader"

    # Elemental affinity (affects magic and nation bonuses)
    primary_element: Optional[Element] = None
    secondary_element: Optional[Element] = None

    # Territory control
    controlled_territories: list[str] = field(default_factory=list)  # Territory IDs
    capital_territory_id: Optional[str] = None

    # Economy - National stockpiles
    resources: dict[ResourceType, int] = field(default_factory=lambda: {
        ResourceType.GOLD: 0,
        ResourceType.FOOD: 0,
        ResourceType.TIMBER: 0,
        ResourceType.IRON: 0,
        ResourceType.LEATHER: 0,
        ResourceType.HERBS: 0,
        ResourceType.GEMS: 0,
        ResourceType.MITHRIL: 0,
    })

    # Mana reserves
    mana_crystals: dict[Element, int] = field(default_factory=lambda: {
        elem: 0 for elem in Element
    })

    # Military
    generals: list[str] = field(default_factory=list)  # Unit IDs of general-rank commanders
    armies: list[str] = field(default_factory=list)  # Army group IDs
    total_military_strength: int = 0  # Calculated strength

    # Diplomacy
    diplomatic_relations: dict[str, DiplomaticRelation] = field(default_factory=dict)

    # Control flags
    is_player_nation: bool = False
    is_ai: bool = True
    is_active: bool = True  # False if eliminated

    # AI settings
    ai_personality: Optional[AIPersonality] = None

    # Statistics
    total_population: int = 0
    average_happiness: int = 50  # 0-100
    treasury_per_turn: int = 0  # Net income/expense

    # Special features
    has_special_victory: bool = False
    special_abilities: list[str] = field(default_factory=list)

    def get_territory_count(self) -> int:
        """Get number of controlled territories."""
        return len(self.controlled_territories)

    def add_territory(self, territory_id: str) -> None:
        """Add a territory to nation control."""
        if territory_id not in self.controlled_territories:
            self.controlled_territories.append(territory_id)

            # Set as capital if first territory
            if self.capital_territory_id is None:
                self.capital_territory_id = territory_id

    def remove_territory(self, territory_id: str) -> None:
        """Remove a territory from nation control."""
        if territory_id in self.controlled_territories:
            self.controlled_territories.remove(territory_id)

            # If capital was lost, reassign
            if territory_id == self.capital_territory_id:
                if self.controlled_territories:
                    self.capital_territory_id = self.controlled_territories[0]
                else:
                    self.capital_territory_id = None
                    self.is_active = False  # Nation eliminated

    def has_resources(self, required: dict[ResourceType, int]) -> bool:
        """Check if nation has required resources."""
        for resource, amount in required.items():
            if self.resources.get(resource, 0) < amount:
                return False
        return True

    def consume_resources(self, costs: dict[ResourceType, int]) -> bool:
        """
        Consume resources if available.

        Returns:
            True if resources consumed successfully
        """
        if not self.has_resources(costs):
            return False

        for resource, amount in costs.items():
            self.resources[resource] -= amount

        return True

    def add_resources(self, gained: dict[ResourceType, int]) -> None:
        """Add resources to national stockpile."""
        for resource, amount in gained.items():
            self.resources[resource] = self.resources.get(resource, 0) + amount

    def has_mana(self, required: dict[Element, int]) -> bool:
        """Check if nation has required mana crystals."""
        for element, amount in required.items():
            if self.mana_crystals.get(element, 0) < amount:
                return False
        return True

    def consume_mana(self, costs: dict[Element, int]) -> bool:
        """
        Consume mana crystals if available.

        Returns:
            True if mana consumed successfully
        """
        if not self.has_mana(costs):
            return False

        for element, amount in costs.items():
            self.mana_crystals[element] -= amount

        return True

    def add_mana(self, gained: dict[Element, int]) -> None:
        """Add mana crystals to national reserves."""
        for element, amount in gained.items():
            self.mana_crystals[element] = self.mana_crystals.get(element, 0) + amount

    def get_relationship(self, nation_id: str) -> Optional[DiplomaticRelation]:
        """Get diplomatic relationship with another nation."""
        return self.diplomatic_relations.get(nation_id)

    def set_relationship(self, nation_id: str, relation: DiplomaticRelation) -> None:
        """Set diplomatic relationship with another nation."""
        self.diplomatic_relations[nation_id] = relation

    def is_at_war_with(self, nation_id: str) -> bool:
        """Check if at war with another nation."""
        relation = self.get_relationship(nation_id)
        return relation is not None and relation.at_war

    def is_allied_with(self, nation_id: str) -> bool:
        """Check if allied with another nation."""
        relation = self.get_relationship(nation_id)
        return relation is not None and relation.has_alliance

    def declare_war(self, nation_id: str) -> None:
        """Declare war on another nation."""
        relation = self.get_relationship(nation_id)
        if relation is None:
            relation = DiplomaticRelation(nation_id=nation_id)

        relation.at_war = True
        relation.has_alliance = False
        relation.has_non_aggression_pact = False
        relation.relationship = -100
        self.set_relationship(nation_id, relation)

    def make_peace(self, nation_id: str) -> None:
        """Make peace with another nation."""
        relation = self.get_relationship(nation_id)
        if relation:
            relation.at_war = False
            relation.relationship = max(relation.relationship, -50)

    def form_alliance(self, nation_id: str) -> None:
        """Form alliance with another nation."""
        relation = self.get_relationship(nation_id)
        if relation is None:
            relation = DiplomaticRelation(nation_id=nation_id)

        if not relation.at_war:
            relation.has_alliance = True
            relation.relationship = max(relation.relationship, 75)
            self.set_relationship(nation_id, relation)

    def calculate_military_strength(self, all_units: dict) -> int:
        """
        Calculate total military strength.

        Args:
            all_units: Dictionary of all units in game

        Returns:
            Total military strength value
        """
        strength = 0

        for general_id in self.generals:
            if general_id in all_units:
                unit = all_units[general_id]
                # Simple strength calculation based on stats
                strength += unit.get("power", 10) * 10

        self.total_military_strength = strength
        return strength

    def update_population(self, territories: dict) -> None:
        """
        Update total population from controlled territories.

        Args:
            territories: Dictionary of all territories
        """
        total = 0
        happiness_sum = 0
        count = 0

        for territory_id in self.controlled_territories:
            if territory_id in territories:
                territory = territories[territory_id]
                total += territory.get("population", 0)
                happiness_sum += territory.get("happiness", 50)
                count += 1

        self.total_population = total
        self.average_happiness = happiness_sum // count if count > 0 else 50

    def is_eliminated(self) -> bool:
        """Check if nation has been eliminated."""
        return not self.is_active or len(self.controlled_territories) == 0

    def get_nation_summary(self) -> dict:
        """Get summary of nation status."""
        return {
            "name": self.name,
            "leader": self.leader_name,
            "territories": self.get_territory_count(),
            "population": self.total_population,
            "happiness": self.average_happiness,
            "military_strength": self.total_military_strength,
            "gold": self.resources.get(ResourceType.GOLD, 0),
            "is_player": self.is_player_nation,
            "is_active": self.is_active,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "nation_id": self.nation_id,
            "name": self.name,
            "leader_name": self.leader_name,
            "primary_element": self.primary_element.value if self.primary_element else None,
            "secondary_element": self.secondary_element.value if self.secondary_element else None,
            "controlled_territories": self.controlled_territories,
            "capital_territory_id": self.capital_territory_id,
            "resources": {k.value: v for k, v in self.resources.items()},
            "mana_crystals": {k.value: v for k, v in self.mana_crystals.items()},
            "generals": self.generals,
            "armies": self.armies,
            "total_military_strength": self.total_military_strength,
            "diplomatic_relations": {
                nation_id: {
                    "nation_id": rel.nation_id,
                    "relationship": rel.relationship,
                    "at_war": rel.at_war,
                    "has_trade_agreement": rel.has_trade_agreement,
                    "has_non_aggression_pact": rel.has_non_aggression_pact,
                    "has_alliance": rel.has_alliance,
                }
                for nation_id, rel in self.diplomatic_relations.items()
            },
            "is_player_nation": self.is_player_nation,
            "is_ai": self.is_ai,
            "is_active": self.is_active,
            "ai_personality": self.ai_personality.personality_type if self.ai_personality else None,
            "total_population": self.total_population,
            "average_happiness": self.average_happiness,
            "special_abilities": self.special_abilities,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Nation":
        """Load from dictionary."""
        nation = cls(
            nation_id=data["nation_id"],
            name=data["name"],
            leader_name=data.get("leader_name", "Unknown Leader"),
            primary_element=Element(data["primary_element"]) if data.get("primary_element") else None,
            secondary_element=Element(data["secondary_element"]) if data.get("secondary_element") else None,
            controlled_territories=data.get("controlled_territories", []),
            capital_territory_id=data.get("capital_territory_id"),
            generals=data.get("generals", []),
            armies=data.get("armies", []),
            total_military_strength=data.get("total_military_strength", 0),
            is_player_nation=data.get("is_player_nation", False),
            is_ai=data.get("is_ai", True),
            is_active=data.get("is_active", True),
            total_population=data.get("total_population", 0),
            average_happiness=data.get("average_happiness", 50),
            special_abilities=data.get("special_abilities", []),
        )

        # Load resources
        if "resources" in data:
            nation.resources = {
                ResourceType(k): v for k, v in data["resources"].items()
            }

        # Load mana
        if "mana_crystals" in data:
            nation.mana_crystals = {
                Element(k): v for k, v in data["mana_crystals"].items()
            }

        # Load diplomatic relations
        if "diplomatic_relations" in data:
            for nation_id, rel_data in data["diplomatic_relations"].items():
                relation = DiplomaticRelation(
                    nation_id=rel_data["nation_id"],
                    relationship=rel_data.get("relationship", 0),
                    at_war=rel_data.get("at_war", False),
                    has_trade_agreement=rel_data.get("has_trade_agreement", False),
                    has_non_aggression_pact=rel_data.get("has_non_aggression_pact", False),
                    has_alliance=rel_data.get("has_alliance", False),
                )
                nation.diplomatic_relations[nation_id] = relation

        # Load AI personality
        if data.get("ai_personality"):
            personality_type = data["ai_personality"]
            if personality_type == "aggressive":
                nation.ai_personality = AIPersonality.create_aggressive()
            elif personality_type == "diplomatic":
                nation.ai_personality = AIPersonality.create_diplomatic()
            elif personality_type == "expansionist":
                nation.ai_personality = AIPersonality.create_expansionist()
            elif personality_type == "defensive":
                nation.ai_personality = AIPersonality.create_defensive()
            else:
                nation.ai_personality = AIPersonality.create_balanced()

        return nation
