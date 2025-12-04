"""
Territory model - represents land hexes on the world map.
"""

from dataclasses import dataclass, field
from typing import Optional
from src.data.constants import Element, BuildingType, ResourceType


@dataclass
class BiomeType:
    """Biome types with their characteristics."""
    biome_id: str
    name: str
    element: Optional[Element]
    base_resources: dict[ResourceType, int]
    movement_cost: int = 1
    defense_bonus: int = 0
    description: str = ""


# Predefined biome types
BIOMES = {
    "plains": BiomeType(
        biome_id="plains",
        name="Plains",
        element=None,
        base_resources={
            ResourceType.FOOD: 20,
            ResourceType.GOLD: 10,
        },
        movement_cost=1,
        defense_bonus=0,
        description="Fertile grasslands"
    ),
    "forest": BiomeType(
        biome_id="forest",
        name="Forest",
        element=Element.EARTH,
        base_resources={
            ResourceType.TIMBER: 30,
            ResourceType.FOOD: 15,
            ResourceType.HERBS: 10,
        },
        movement_cost=2,
        defense_bonus=10,
        description="Dense woodland"
    ),
    "mountain": BiomeType(
        biome_id="mountain",
        name="Mountain",
        element=Element.EARTH,
        base_resources={
            ResourceType.IRON: 25,
            ResourceType.GEMS: 15,
            ResourceType.MITHRIL: 5,
        },
        movement_cost=3,
        defense_bonus=20,
        description="Rocky peaks"
    ),
    "volcano": BiomeType(
        biome_id="volcano",
        name="Volcanic Wastes",
        element=Element.FIRE,
        base_resources={
            ResourceType.IRON: 20,
            ResourceType.GEMS: 20,
        },
        movement_cost=2,
        defense_bonus=5,
        description="Scorched volcanic terrain"
    ),
    "ocean": BiomeType(
        biome_id="ocean",
        name="Ocean",
        element=Element.WATER,
        base_resources={
            ResourceType.FOOD: 25,
        },
        movement_cost=2,
        defense_bonus=0,
        description="Deep waters"
    ),
    "swamp": BiomeType(
        biome_id="swamp",
        name="Swamp",
        element=Element.DEATH,
        base_resources={
            ResourceType.HERBS: 20,
        },
        movement_cost=3,
        defense_bonus=15,
        description="Murky wetlands"
    ),
}


@dataclass
class Building:
    """Building in a territory."""
    building_id: str
    building_type: BuildingType
    name: str
    level: int = 1
    construction_progress: int = 0
    construction_required: int = 100

    def is_complete(self) -> bool:
        """Check if building construction is complete."""
        return self.construction_progress >= self.construction_required


@dataclass
class Worker:
    """Worker assigned to a territory."""
    worker_id: str
    job_type: str
    experience: int = 0
    efficiency: float = 1.0

    @property
    def skill_level(self) -> str:
        """Get skill level based on experience."""
        if self.experience < 100:
            return "Basic"
        elif self.experience < 500:
            return "Expert"
        else:
            return "Master"

    @property
    def efficiency_multiplier(self) -> float:
        """Get production multiplier based on skill."""
        if self.experience < 100:
            return 1.0
        elif self.experience < 500:
            return 1.5
        else:
            return 2.0


@dataclass
class Territory:
    """
    Represents a territory (hex) on the world map.

    Each territory has:
    - Location (x, y coordinates)
    - Biome type
    - Owner nation
    - Buildings
    - Workers
    - Resources
    - Strategic value
    """

    # Identity
    territory_id: str
    name: str
    x: int  # Hex coordinate X
    y: int  # Hex coordinate Y

    # Terrain
    biome: BiomeType = field(default_factory=lambda: BIOMES["plains"])

    # Ownership
    owner_id: Optional[str] = None  # Nation ID that controls this territory

    # Infrastructure
    buildings: list[Building] = field(default_factory=list)
    workers: list[Worker] = field(default_factory=list)

    # Resources (stockpiles in this territory)
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

    # Mana crystals (if territory has elemental affinity)
    mana_crystals: dict[Element, int] = field(default_factory=lambda: {
        elem: 0 for elem in Element
    })

    # Military
    garrison_unit_ids: list[str] = field(default_factory=list)
    fortification_level: int = 0

    # Strategic data
    population: int = 100
    happiness: int = 50  # 0-100

    # Special features
    has_ruins: bool = False
    has_shrine: bool = False
    special_feature: Optional[str] = None

    def get_hex_coords(self) -> tuple[int, int]:
        """Get hexagonal coordinates."""
        return (self.x, self.y)

    def get_neighbors(self, world_width: int, world_height: int) -> list[tuple[int, int]]:
        """
        Get neighboring hex coordinates.

        Hex grid has 6 neighbors in directions:
        - Even row: NW, NE, E, SE, SW, W
        - Odd row: NW, NE, E, SE, SW, W (different offsets)
        """
        neighbors = []

        # Hex neighbor offsets (even row)
        if self.y % 2 == 0:
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
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < world_width and 0 <= ny < world_height:
                neighbors.append((nx, ny))

        return neighbors

    def add_building(self, building_type: BuildingType) -> Building:
        """Add a new building to this territory."""
        building = Building(
            building_id=f"{self.territory_id}_{building_type.value}_{len(self.buildings)}",
            building_type=building_type,
            name=building_type.value.replace('_', ' ').title(),
        )
        self.buildings.append(building)
        return building

    def has_building(self, building_type: BuildingType) -> bool:
        """Check if territory has a specific building type."""
        return any(
            b.building_type == building_type and b.is_complete()
            for b in self.buildings
        )

    def get_building(self, building_type: BuildingType) -> Optional[Building]:
        """Get first completed building of specified type."""
        for building in self.buildings:
            if building.building_type == building_type and building.is_complete():
                return building
        return None

    def add_worker(self, job_type: str) -> Worker:
        """Add a worker to this territory."""
        worker = Worker(
            worker_id=f"{self.territory_id}_worker_{len(self.workers)}",
            job_type=job_type,
        )
        self.workers.append(worker)
        return worker

    def generate_resources(self) -> dict[ResourceType, int]:
        """
        Generate resources based on biome, buildings, and workers.

        Returns:
            Dictionary of resources generated this turn
        """
        generated = {}

        # Base resources from biome
        for resource, amount in self.biome.base_resources.items():
            generated[resource] = amount

        # Worker bonuses
        for worker in self.workers:
            if worker.job_type == "farmer" and ResourceType.FOOD in generated:
                generated[ResourceType.FOOD] += int(10 * worker.efficiency_multiplier)
            elif worker.job_type == "miner" and ResourceType.IRON in generated:
                generated[ResourceType.IRON] += int(10 * worker.efficiency_multiplier)
            elif worker.job_type == "lumberjack" and ResourceType.TIMBER in generated:
                generated[ResourceType.TIMBER] += int(10 * worker.efficiency_multiplier)

        # Building bonuses
        if self.has_building(BuildingType.FARM):
            generated[ResourceType.FOOD] = generated.get(ResourceType.FOOD, 0) + 20
        if self.has_building(BuildingType.MINE):
            generated[ResourceType.IRON] = generated.get(ResourceType.IRON, 0) + 15
        if self.has_building(BuildingType.LUMBERMILL):
            generated[ResourceType.TIMBER] = generated.get(ResourceType.TIMBER, 0) + 15
        if self.has_building(BuildingType.MARKET):
            generated[ResourceType.GOLD] = generated.get(ResourceType.GOLD, 0) + 50

        # Add to stockpiles
        for resource, amount in generated.items():
            self.resources[resource] = self.resources.get(resource, 0) + amount

        return generated

    def generate_mana(self) -> dict[Element, int]:
        """Generate mana crystals if territory has elemental affinity."""
        generated = {}

        if self.biome.element:
            # Base generation
            amount = 1

            # Temple bonus
            if self.has_building(BuildingType.TEMPLE):
                amount += 1

            # Mage tower bonus
            if self.has_building(BuildingType.MAGE_TOWER):
                amount += 1

            # Crystallizer workers
            for worker in self.workers:
                if worker.job_type == "crystallizer":
                    amount += int(2 * worker.efficiency_multiplier)

            generated[self.biome.element] = amount
            self.mana_crystals[self.biome.element] += amount

        return generated

    def get_defense_value(self) -> int:
        """Calculate total defensive value of territory."""
        defense = self.biome.defense_bonus

        # Fortification
        defense += self.fortification_level * 10

        # Buildings
        if self.has_building(BuildingType.FORTRESS):
            defense += 50
        if self.has_building(BuildingType.BARRACKS):
            defense += 20

        return defense

    def is_owned(self) -> bool:
        """Check if territory is owned by any nation."""
        return self.owner_id is not None

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "territory_id": self.territory_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "biome": self.biome.biome_id,
            "owner_id": self.owner_id,
            "buildings": [
                {
                    "building_id": b.building_id,
                    "type": b.building_type.value,
                    "level": b.level,
                    "progress": b.construction_progress,
                }
                for b in self.buildings
            ],
            "workers": [
                {
                    "worker_id": w.worker_id,
                    "job_type": w.job_type,
                    "experience": w.experience,
                }
                for w in self.workers
            ],
            "resources": {k.value: v for k, v in self.resources.items()},
            "mana_crystals": {k.value: v for k, v in self.mana_crystals.items()},
            "garrison": self.garrison_unit_ids,
            "population": self.population,
            "happiness": self.happiness,
            "special_feature": self.special_feature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Territory":
        """Load from dictionary."""
        territory = cls(
            territory_id=data["territory_id"],
            name=data["name"],
            x=data["x"],
            y=data["y"],
            biome=BIOMES.get(data["biome"], BIOMES["plains"]),
            owner_id=data.get("owner_id"),
            population=data.get("population", 100),
            happiness=data.get("happiness", 50),
            special_feature=data.get("special_feature"),
        )

        # Load buildings
        for b_data in data.get("buildings", []):
            building = Building(
                building_id=b_data["building_id"],
                building_type=BuildingType(b_data["type"]),
                name=b_data["type"].replace('_', ' ').title(),
                level=b_data.get("level", 1),
                construction_progress=b_data.get("progress", 100),
            )
            territory.buildings.append(building)

        # Load workers
        for w_data in data.get("workers", []):
            worker = Worker(
                worker_id=w_data["worker_id"],
                job_type=w_data["job_type"],
                experience=w_data.get("experience", 0),
            )
            territory.workers.append(worker)

        # Load resources
        if "resources" in data:
            territory.resources = {
                ResourceType(k): v for k, v in data["resources"].items()
            }

        return territory
