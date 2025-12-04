"""
World Map Generator - Creates procedurally generated hex-based world maps.
"""

import random
from typing import Optional
from src.models.territory import Territory, BIOMES, BiomeType
from src.data.constants import WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT, Element


class WorldMapGenerator:
    """
    Generates procedurally generated world maps.

    Features:
    - 40×30 hex grid
    - Multiple biome types
    - Terrain clustering (realistic biome placement)
    - Special features (ruins, shrines)
    - Strategic starting positions
    """

    def __init__(self, width: int = WORLD_MAP_WIDTH, height: int = WORLD_MAP_HEIGHT, seed: Optional[int] = None):
        """
        Initialize world map generator.

        Args:
            width: Map width in hexes (default: 40)
            height: Map height in hexes (default: 30)
            seed: Random seed for reproducible maps
        """
        self.width = width
        self.height = height
        self.seed = seed

        if seed is not None:
            random.seed(seed)

        # Storage for generated territories
        self.territories: dict[str, Territory] = {}

    def generate_map(self, num_continents: int = 3) -> dict[str, Territory]:
        """
        Generate complete world map.

        Args:
            num_continents: Number of major landmasses

        Returns:
            Dictionary of territories keyed by territory_id
        """
        print(f"Generating {self.width}×{self.height} hex world map...")

        # Step 1: Create base ocean map
        self._create_base_map()

        # Step 2: Generate continents
        self._generate_continents(num_continents)

        # Step 3: Add biome variety
        self._diversify_biomes()

        # Step 4: Smooth terrain transitions
        self._smooth_terrain()

        # Step 5: Add special features
        self._add_special_features()

        print(f"Generated {len(self.territories)} territories")
        return self.territories

    def _create_base_map(self) -> None:
        """Create base map filled with ocean."""
        for y in range(self.height):
            for x in range(self.width):
                territory_id = f"hex_{x}_{y}"
                name = f"Ocean {x},{y}"

                territory = Territory(
                    territory_id=territory_id,
                    name=name,
                    x=x,
                    y=y,
                    biome=BIOMES["ocean"],
                )

                self.territories[territory_id] = territory

    def _generate_continents(self, num_continents: int) -> None:
        """
        Generate continents using terrain growth algorithm.

        Args:
            num_continents: Number of major landmasses to create
        """
        # Place continent seeds
        continent_centers = []
        for i in range(num_continents):
            # Spread continents across map
            x = random.randint(self.width // 4, 3 * self.width // 4)
            y = random.randint(self.height // 4, 3 * self.height // 4)
            continent_centers.append((x, y))

            # Mark as plains (land)
            territory = self._get_territory(x, y)
            if territory:
                territory.biome = BIOMES["plains"]
                territory.name = f"Plains {x},{y}"

        # Grow continents outward
        for center_x, center_y in continent_centers:
            continent_size = random.randint(80, 150)  # Size in hexes
            self._grow_landmass(center_x, center_y, continent_size)

    def _grow_landmass(self, start_x: int, start_y: int, target_size: int) -> None:
        """
        Grow landmass from starting point using flood-fill growth.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            target_size: Target number of land hexes
        """
        # List of land tiles to potentially expand from
        frontier = [(start_x, start_y)]
        land_count = 1

        while land_count < target_size and frontier:
            # Pick random frontier tile
            current = random.choice(frontier)
            cx, cy = current

            # Get neighbors
            neighbors = self._get_hex_neighbors(cx, cy)

            for nx, ny in neighbors:
                territory = self._get_territory(nx, ny)
                if territory and territory.biome.biome_id == "ocean":
                    # Probability decreases with distance from center
                    distance = abs(nx - start_x) + abs(ny - start_y)
                    probability = max(0.3, 1.0 - (distance / 20.0))

                    if random.random() < probability:
                        # Convert to land
                        territory.biome = BIOMES["plains"]
                        territory.name = f"Plains {nx},{ny}"
                        frontier.append((nx, ny))
                        land_count += 1

                        if land_count >= target_size:
                            break

            # Remove exhausted frontier
            if random.random() < 0.3:  # 30% chance to remove from frontier
                frontier.remove(current)

    def _diversify_biomes(self) -> None:
        """Add biome variety to land territories."""
        # Convert some plains to other biomes
        for territory in self.territories.values():
            if territory.biome.biome_id == "plains":
                # Randomly assign biomes with weighted probabilities
                rand = random.random()

                if rand < 0.10:  # 10% mountains
                    territory.biome = BIOMES["mountain"]
                    territory.name = f"Mountain {territory.x},{territory.y}"
                elif rand < 0.25:  # 15% forests
                    territory.biome = BIOMES["forest"]
                    territory.name = f"Forest {territory.x},{territory.y}"
                elif rand < 0.30:  # 5% swamps
                    territory.biome = BIOMES["swamp"]
                    territory.name = f"Swamp {territory.x},{territory.y}"
                elif rand < 0.33:  # 3% volcanic
                    territory.biome = BIOMES["volcano"]
                    territory.name = f"Volcanic Wastes {territory.x},{territory.y}"
                # Rest remain plains (67%)

    def _smooth_terrain(self) -> None:
        """Smooth terrain by clustering similar biomes together."""
        # Multiple smoothing passes
        for _ in range(2):
            changes = []

            for territory in self.territories.values():
                # Skip ocean
                if territory.biome.biome_id == "ocean":
                    continue

                # Count neighbor biomes
                neighbors = self._get_hex_neighbors(territory.x, territory.y)
                biome_counts: dict[str, int] = {}

                for nx, ny in neighbors:
                    neighbor = self._get_territory(nx, ny)
                    if neighbor and neighbor.biome.biome_id != "ocean":
                        biome_id = neighbor.biome.biome_id
                        biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1

                # If surrounded by different biome, consider changing
                if biome_counts:
                    most_common_biome = max(biome_counts, key=biome_counts.get)
                    if biome_counts[most_common_biome] >= 4:
                        # Strong majority - change to match
                        if random.random() < 0.6:  # 60% chance
                            changes.append((territory, most_common_biome))

            # Apply changes
            for territory, new_biome_id in changes:
                territory.biome = BIOMES[new_biome_id]
                territory.name = f"{territory.biome.name} {territory.x},{territory.y}"

    def _add_special_features(self) -> None:
        """Add special features like ruins and shrines to territories."""
        land_territories = [
            t for t in self.territories.values()
            if t.biome.biome_id != "ocean"
        ]

        if not land_territories:
            return

        # Add ruins (5% of land tiles)
        num_ruins = max(1, len(land_territories) // 20)
        ruin_territories = random.sample(land_territories, min(num_ruins, len(land_territories)))
        for territory in ruin_territories:
            territory.has_ruins = True
            territory.special_feature = "ancient_ruins"

        # Add elemental shrines (one per element on suitable biomes)
        element_biomes = {
            Element.FIRE: ["volcano"],
            Element.WATER: ["ocean"],
            Element.EARTH: ["mountain", "forest"],
            Element.AIR: ["plains"],
            Element.LIFE: ["forest", "plains"],
            Element.DEATH: ["swamp"],
        }

        for element, biome_types in element_biomes.items():
            # Find suitable locations
            suitable = [
                t for t in land_territories
                if t.biome.biome_id in biome_types and not t.has_shrine
            ]

            if suitable:
                shrine_territory = random.choice(suitable)
                shrine_territory.has_shrine = True
                shrine_territory.special_feature = f"shrine_{element.value}"

    def _get_territory(self, x: int, y: int) -> Optional[Territory]:
        """Get territory at coordinates."""
        territory_id = f"hex_{x}_{y}"
        return self.territories.get(territory_id)

    def _get_hex_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Get neighboring hex coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of (x, y) neighbor coordinates
        """
        neighbors = []

        # Hex neighbor offsets (even row)
        if y % 2 == 0:
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
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))

        return neighbors

    def get_starting_positions(self, num_positions: int) -> list[tuple[int, int]]:
        """
        Get strategic starting positions for nations.

        Args:
            num_positions: Number of starting positions needed

        Returns:
            List of (x, y) coordinates for starting positions
        """
        # Filter to good starting locations
        good_starts = []

        for territory in self.territories.values():
            # Plains or forest near water are best starts
            if territory.biome.biome_id in ["plains", "forest"]:
                # Check if near ocean (for trade access)
                neighbors = self._get_hex_neighbors(territory.x, territory.y)
                near_water = any(
                    self._get_territory(nx, ny).biome.biome_id == "ocean"
                    for nx, ny in neighbors
                    if self._get_territory(nx, ny)
                )

                if near_water or random.random() < 0.3:  # Prefer coastal, but allow inland
                    good_starts.append((territory.x, territory.y))

        # Select starting positions spread across map
        if len(good_starts) < num_positions:
            return good_starts

        # Try to maximize distance between starts
        selected = []
        remaining = good_starts.copy()

        # Pick first randomly
        first = random.choice(remaining)
        selected.append(first)
        remaining.remove(first)

        # Pick rest to maximize minimum distance
        while len(selected) < num_positions and remaining:
            best_candidate = None
            best_min_distance = 0

            for candidate in remaining:
                # Calculate minimum distance to any selected position
                min_dist = min(
                    abs(candidate[0] - s[0]) + abs(candidate[1] - s[1])
                    for s in selected
                )

                if min_dist > best_min_distance:
                    best_min_distance = min_dist
                    best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break

        return selected

    def get_map_statistics(self) -> dict:
        """Get statistics about generated map."""
        biome_counts: dict[str, int] = {}
        special_counts = {
            "ruins": 0,
            "shrines": 0,
        }

        for territory in self.territories.values():
            # Count biomes
            biome_id = territory.biome.biome_id
            biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1

            # Count special features
            if territory.has_ruins:
                special_counts["ruins"] += 1
            if territory.has_shrine:
                special_counts["shrines"] += 1

        land_count = sum(
            count for biome_id, count in biome_counts.items()
            if biome_id != "ocean"
        )

        return {
            "total_hexes": len(self.territories),
            "land_hexes": land_count,
            "ocean_hexes": biome_counts.get("ocean", 0),
            "biome_distribution": biome_counts,
            "special_features": special_counts,
            "land_percentage": (land_count / len(self.territories)) * 100,
        }

    def save_map_to_dict(self) -> dict:
        """Save map data to dictionary for game state."""
        return {
            territory_id: territory.to_dict()
            for territory_id, territory in self.territories.items()
        }

    @classmethod
    def load_map_from_dict(cls, data: dict, width: int = WORLD_MAP_WIDTH, height: int = WORLD_MAP_HEIGHT) -> "WorldMapGenerator":
        """Load map from dictionary."""
        generator = cls(width=width, height=height)

        for territory_id, territory_data in data.items():
            territory = Territory.from_dict(territory_data)
            generator.territories[territory_id] = territory

        return generator
