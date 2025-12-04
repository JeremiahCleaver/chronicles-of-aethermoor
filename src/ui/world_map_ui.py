"""
World Map UI - Text-based world map display and navigation.
"""

from typing import Optional
from src.models.territory import Territory
from src.models.nation import Nation


class WorldMapUI:
    """
    Terminal-based world map display.

    Features:
    - ASCII hex grid visualization
    - Territory details
    - Nation borders
    - Resource display
    - Navigation
    """

    # Biome display symbols
    BIOME_SYMBOLS = {
        "ocean": "~",
        "plains": ".",
        "forest": "T",
        "mountain": "^",
        "volcano": "V",
        "swamp": "m",
    }

    # Biome colors (ANSI color codes)
    BIOME_COLORS = {
        "ocean": "\033[94m",      # Blue
        "plains": "\033[92m",     # Green
        "forest": "\033[32m",     # Dark Green
        "mountain": "\033[90m",   # Gray
        "volcano": "\033[91m",    # Red
        "swamp": "\033[35m",      # Magenta
    }

    RESET_COLOR = "\033[0m"

    def __init__(self, width: int, height: int):
        """
        Initialize world map UI.

        Args:
            width: Map width in hexes
            height: Map height in hexes
        """
        self.width = width
        self.height = height

    def display_map(
        self,
        territories: dict[str, Territory],
        nations: Optional[dict[str, Nation]] = None,
        viewport_x: int = 0,
        viewport_y: int = 0,
        viewport_width: int = 40,
        viewport_height: int = 20,
        show_colors: bool = True
    ) -> None:
        """
        Display world map in terminal.

        Args:
            territories: Dictionary of territories
            nations: Dictionary of nations (for borders)
            viewport_x: Viewport X offset
            viewport_y: Viewport Y offset
            viewport_width: Viewport width
            viewport_height: Viewport height
            show_colors: Enable ANSI color codes
        """
        print("=" * 80)
        print(f"WORLD MAP ({self.width}×{self.height})")
        print(f"Viewport: ({viewport_x},{viewport_y}) to ({viewport_x + viewport_width},{viewport_y + viewport_height})")
        print("=" * 80)

        # Render viewport
        for y in range(viewport_y, min(viewport_y + viewport_height, self.height)):
            # Hex offset for odd rows
            line = "  " if y % 2 == 1 else ""

            for x in range(viewport_x, min(viewport_x + viewport_width, self.width)):
                territory = self._get_territory(territories, x, y)

                if territory:
                    symbol = self._get_territory_symbol(territory)
                    if show_colors:
                        color = self.BIOME_COLORS.get(territory.biome.biome_id, "")
                        line += f"{color}{symbol}{self.RESET_COLOR} "
                    else:
                        line += f"{symbol} "
                else:
                    line += "  "

            print(line)

        print("=" * 80)
        self._display_legend()

    def display_territory_info(self, territory: Territory, nation: Optional[Nation] = None) -> None:
        """
        Display detailed information about a territory.

        Args:
            territory: Territory to display
            nation: Owning nation (if any)
        """
        print("\n" + "=" * 60)
        print(f"TERRITORY: {territory.name}")
        print("=" * 60)

        # Basic info
        print(f"Location: ({territory.x}, {territory.y})")
        print(f"Biome: {territory.biome.name}")
        print(f"Element: {territory.biome.element.value if territory.biome.element else 'None'}")

        # Ownership
        if territory.owner_id:
            owner_name = nation.name if nation else territory.owner_id
            print(f"Owner: {owner_name}")
        else:
            print("Owner: Unclaimed")

        # Population and happiness
        print(f"Population: {territory.population}")
        print(f"Happiness: {territory.happiness}/100")

        # Resources
        print("\nRESOURCES:")
        if territory.resources:
            for resource, amount in territory.resources.items():
                if amount > 0:
                    print(f"  {resource.value.title()}: {amount}")
        else:
            print("  None")

        # Mana crystals
        has_mana = any(amount > 0 for amount in territory.mana_crystals.values())
        if has_mana:
            print("\nMANA CRYSTALS:")
            for element, amount in territory.mana_crystals.items():
                if amount > 0:
                    print(f"  {element.value.title()}: {amount}")

        # Buildings
        if territory.buildings:
            print("\nBUILDINGS:")
            for building in territory.buildings:
                status = "Complete" if building.is_complete() else f"{building.construction_progress}/{building.construction_required}"
                print(f"  {building.name} (Level {building.level}) - {status}")

        # Workers
        if territory.workers:
            print("\nWORKERS:")
            for worker in territory.workers:
                print(f"  {worker.job_type.title()} - {worker.skill_level} (XP: {worker.experience})")

        # Special features
        special_features = []
        if territory.has_ruins:
            special_features.append("Ancient Ruins")
        if territory.has_shrine:
            special_features.append(f"Elemental Shrine")
        if territory.special_feature:
            special_features.append(territory.special_feature)

        if special_features:
            print("\nSPECIAL FEATURES:")
            for feature in special_features:
                print(f"  • {feature}")

        # Strategic info
        print(f"\nDefense Value: {territory.get_defense_value()}")
        print(f"Movement Cost: {territory.biome.movement_cost}")

        if territory.garrison_unit_ids:
            print(f"Garrison: {len(territory.garrison_unit_ids)} units")

        print("=" * 60)

    def display_nation_overview(self, nation: Nation, territories: dict[str, Territory]) -> None:
        """
        Display overview of a nation.

        Args:
            nation: Nation to display
            territories: All territories (to calculate totals)
        """
        print("\n" + "=" * 60)
        print(f"NATION: {nation.name}")
        print("=" * 60)

        print(f"Leader: {nation.leader_name}")
        print(f"Type: {'Player Nation' if nation.is_player_nation else 'AI Nation'}")

        if nation.primary_element:
            print(f"Primary Element: {nation.primary_element.value.title()}")

        if nation.capital_territory_id:
            capital = territories.get(nation.capital_territory_id)
            if capital:
                print(f"Capital: {capital.name}")

        # Territory info
        print(f"\nTerritories: {nation.get_territory_count()}")
        print(f"Total Population: {nation.total_population}")
        print(f"Average Happiness: {nation.average_happiness}/100")

        # Resources
        print("\nNATIONAL RESOURCES:")
        for resource, amount in nation.resources.items():
            print(f"  {resource.value.title()}: {amount}")

        # Mana
        print("\nMANA RESERVES:")
        for element, amount in nation.mana_crystals.items():
            print(f"  {element.value.title()}: {amount}")

        # Military
        print(f"\nMilitary Strength: {nation.total_military_strength}")
        print(f"Generals: {len(nation.generals)}")
        print(f"Armies: {len(nation.armies)}")

        # Diplomacy
        if nation.diplomatic_relations:
            print("\nDIPLOMATIC RELATIONS:")
            for nation_id, relation in nation.diplomatic_relations.items():
                status = relation.get_relationship_status()
                print(f"  {nation_id}: {status} ({relation.relationship:+d})")

        # AI info
        if nation.is_ai and nation.ai_personality:
            print(f"\nAI Personality: {nation.ai_personality.personality_type.title()}")

        print("=" * 60)

    def display_map_statistics(self, territories: dict[str, Territory]) -> None:
        """
        Display map statistics.

        Args:
            territories: All territories
        """
        print("\n" + "=" * 60)
        print("MAP STATISTICS")
        print("=" * 60)

        # Count biomes
        biome_counts: dict[str, int] = {}
        owned_count = 0
        special_count = 0

        for territory in territories.values():
            # Biomes
            biome_id = territory.biome.biome_id
            biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1

            # Ownership
            if territory.owner_id:
                owned_count += 1

            # Special features
            if territory.has_ruins or territory.has_shrine:
                special_count += 1

        total = len(territories)
        land_count = sum(count for biome, count in biome_counts.items() if biome != "ocean")

        print(f"Total Hexes: {total}")
        print(f"Land Hexes: {land_count} ({land_count / total * 100:.1f}%)")
        print(f"Ocean Hexes: {biome_counts.get('ocean', 0)} ({biome_counts.get('ocean', 0) / total * 100:.1f}%)")

        print("\nBIOME DISTRIBUTION:")
        for biome_id, count in sorted(biome_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total * 100
            symbol = self.BIOME_SYMBOLS.get(biome_id, "?")
            print(f"  {symbol} {biome_id.title()}: {count} ({percentage:.1f}%)")

        print(f"\nOwned Territories: {owned_count}")
        print(f"Special Features: {special_count}")

        print("=" * 60)

    def display_territory_list(
        self,
        territories: dict[str, Territory],
        filter_owner: Optional[str] = None,
        filter_biome: Optional[str] = None,
        max_results: int = 20
    ) -> None:
        """
        Display list of territories with filters.

        Args:
            territories: All territories
            filter_owner: Filter by owner nation ID
            filter_biome: Filter by biome type
            max_results: Maximum results to show
        """
        print("\n" + "=" * 80)
        print("TERRITORY LIST")
        print("=" * 80)

        # Apply filters
        filtered = []
        for territory in territories.values():
            # Skip ocean by default
            if territory.biome.biome_id == "ocean":
                continue

            # Owner filter
            if filter_owner and territory.owner_id != filter_owner:
                continue

            # Biome filter
            if filter_biome and territory.biome.biome_id != filter_biome:
                continue

            filtered.append(territory)

        # Sort by name
        filtered.sort(key=lambda t: t.name)

        # Display
        count = 0
        for territory in filtered[:max_results]:
            owner = territory.owner_id if territory.owner_id else "Unclaimed"
            symbol = self.BIOME_SYMBOLS.get(territory.biome.biome_id, "?")
            print(f"{symbol} {territory.name:25} | Owner: {owner:15} | Pop: {territory.population:4} | ({territory.x},{territory.y})")
            count += 1

        if len(filtered) > max_results:
            print(f"\n... and {len(filtered) - max_results} more")

        print(f"\nShowing {count} of {len(filtered)} territories")
        print("=" * 80)

    def _get_territory(self, territories: dict[str, Territory], x: int, y: int) -> Optional[Territory]:
        """Get territory at coordinates."""
        territory_id = f"hex_{x}_{y}"
        return territories.get(territory_id)

    def _get_territory_symbol(self, territory: Territory) -> str:
        """Get display symbol for territory."""
        # Special features override
        if territory.has_shrine:
            return "S"
        if territory.has_ruins:
            return "R"

        # Owned territories show nation indicator
        if territory.owner_id:
            # Use first letter of nation ID
            return territory.owner_id[0].upper()

        # Default to biome symbol
        return self.BIOME_SYMBOLS.get(territory.biome.biome_id, "?")

    def _display_legend(self) -> None:
        """Display map legend."""
        print("\nLEGEND:")
        print("  ~ Ocean    . Plains    T Forest    ^ Mountain    V Volcano    m Swamp")
        print("  R Ruins    S Shrine    [Letter] = Owned by nation")
        print()


def display_world_map_menu(
    territories: dict[str, Territory],
    nations: dict[str, Nation],
    player_nation_id: str
) -> None:
    """
    Interactive world map menu.

    Args:
        territories: All territories
        nations: All nations
        player_nation_id: Player's nation ID
    """
    ui = WorldMapUI(width=40, height=30)

    while True:
        print("\n" + "=" * 60)
        print("WORLD MAP MENU")
        print("=" * 60)
        print("1. View World Map")
        print("2. View Your Nation")
        print("3. View Territory Details")
        print("4. Territory List")
        print("5. Map Statistics")
        print("6. Return")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            ui.display_map(territories, nations)
        elif choice == "2":
            player_nation = nations.get(player_nation_id)
            if player_nation:
                ui.display_nation_overview(player_nation, territories)
            else:
                print("Player nation not found!")
        elif choice == "3":
            x = input("Enter X coordinate: ").strip()
            y = input("Enter Y coordinate: ").strip()
            try:
                territory = territories.get(f"hex_{x}_{y}")
                if territory:
                    nation = nations.get(territory.owner_id) if territory.owner_id else None
                    ui.display_territory_info(territory, nation)
                else:
                    print("Territory not found!")
            except ValueError:
                print("Invalid coordinates!")
        elif choice == "4":
            ui.display_territory_list(territories)
        elif choice == "5":
            ui.display_map_statistics(territories)
        elif choice == "6":
            break
        else:
            print("Invalid choice!")
