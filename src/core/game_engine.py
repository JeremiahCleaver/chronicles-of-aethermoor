"""
Game Engine - Core game loop and state management.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from src.models.game_state_simple import GameState
from src.core.save_system import SaveSystem


class GameEngine:
    """
    Main game engine that manages game state and coordinates all systems.

    The engine is responsible for:
    - Game state management
    - Turn progression
    - Save/load coordination
    - System initialization
    """

    def __init__(self, save_directory: Optional[Path] = None):
        """
        Initialize game engine.

        Args:
            save_directory: Path to save game directory (default: ./saves)
        """
        # Save system
        if save_directory is None:
            save_directory = Path("./saves")
        self.save_system = SaveSystem(save_directory)

        # Game state
        self.state: Optional[GameState] = None
        self.is_running = False
        self.last_update_time: Optional[datetime] = None

    def new_game(
        self,
        player_name: str = "Player",
        nation_name: str = "New Nation",
        difficulty: str = "normal"
    ) -> bool:
        """
        Start a new game.

        Args:
            player_name: Player's name
            nation_name: Nation name
            difficulty: Difficulty level

        Returns:
            True if game started successfully
        """
        from src.data.constants import Difficulty

        # Create new game state
        self.state = GameState()
        self.state.player.player_name = player_name
        self.state.player.nation_name = nation_name

        # Set difficulty
        try:
            self.state.player.difficulty = Difficulty(difficulty)
        except ValueError:
            self.state.player.difficulty = Difficulty.NORMAL

        # Initialize player starting resources
        self._initialize_player_nation()

        # Mark game as running
        self.is_running = True
        self.last_update_time = datetime.now()

        return True

    def load_game(self, slot: int, slot_type: str = "manual") -> bool:
        """
        Load game from save slot.

        Args:
            slot: Save slot number
            slot_type: Type of save slot

        Returns:
            True if load successful
        """
        loaded_state = self.save_system.load_game(slot, slot_type)

        if loaded_state is None:
            return False

        self.state = loaded_state
        self.is_running = True
        self.last_update_time = datetime.now()

        return True

    def save_game(self, slot: int, slot_type: str = "manual") -> bool:
        """
        Save current game to slot.

        Args:
            slot: Save slot number
            slot_type: Type of save slot

        Returns:
            True if save successful
        """
        if self.state is None:
            return False

        # Update playtime before saving
        self._update_playtime()

        return self.save_system.save_game(self.state, slot, slot_type)

    def autosave(self) -> bool:
        """Create autosave of current game."""
        if self.state is None:
            return False

        self._update_playtime()
        return self.save_system.autosave(self.state)

    def quicksave(self) -> bool:
        """Create quicksave of current game."""
        if self.state is None:
            return False

        self._update_playtime()
        return self.save_system.quicksave(self.state)

    def advance_turn(self) -> None:
        """
        Advance to next turn.

        This is called at the end of each turn and triggers:
        - Time progression
        - Resource generation
        - AI turns
        - Event processing
        - Autosave (if configured)
        """
        if self.state is None:
            return

        # Update playtime
        self._update_playtime()

        # Advance time
        self.state.time.advance_turn()

        # Process turn
        self._process_turn()

        # Autosave every 5 turns
        if self.state.time.current_turn % 5 == 0:
            self.autosave()

        print(f"Turn advanced to: {self.state.time}")

    def _process_turn(self) -> None:
        """Process turn actions for all nations and territories."""
        if self.state is None:
            return

        from src.models.territory import Territory
        from src.models.nation import Nation
        from src.data.constants import ResourceType, Element

        # Load territories
        territories: dict[str, Territory] = {}
        for territory_id, territory_data in self.state.territories.items():
            territories[territory_id] = Territory.from_dict(territory_data)

        # Load nations
        nations: dict[str, Nation] = {}
        for nation_id, nation_data in self.state.nations.items():
            nations[nation_id] = Nation.from_dict(nation_data)

        # Generate resources for each nation
        for nation in nations.values():
            turn_resources: dict[ResourceType, int] = {}
            turn_mana: dict[Element, int] = {}

            # Collect from all controlled territories
            for territory_id in nation.controlled_territories:
                territory = territories.get(territory_id)
                if territory:
                    # Generate resources
                    generated = territory.generate_resources()
                    for resource, amount in generated.items():
                        turn_resources[resource] = turn_resources.get(resource, 0) + amount

                    # Generate mana
                    mana_generated = territory.generate_mana()
                    for element, amount in mana_generated.items():
                        turn_mana[element] = turn_mana.get(element, 0) + amount

            # Add to nation stockpile
            nation.add_resources(turn_resources)
            nation.add_mana(turn_mana)

            # Update population statistics
            nation.update_population(self.state.territories)

        # Save updated territories back
        self.state.territories = {
            territory_id: territory.to_dict()
            for territory_id, territory in territories.items()
        }

        # Save updated nations back
        self.state.nations = {
            nation_id: nation.to_dict()
            for nation_id, nation in nations.items()
        }

    def get_current_state(self) -> Optional[GameState]:
        """Get current game state (read-only)."""
        return self.state

    def is_game_active(self) -> bool:
        """Check if game is currently active."""
        return self.is_running and self.state is not None

    def end_game(self) -> None:
        """End current game session."""
        self.is_running = False

        # Final autosave
        if self.state is not None:
            self.autosave()

    def _initialize_player_nation(self) -> None:
        """Initialize player's starting nation."""
        if self.state is None:
            return

        from src.models.nation import Nation
        from src.systems.world_map import WorldMapGenerator
        from src.data.constants import ResourceType, Element

        # Generate world map
        print("Generating world map...")
        map_generator = WorldMapGenerator(seed=None)  # Random seed
        territories = map_generator.generate_map(num_continents=3)

        # Get starting positions for nations
        num_ai_nations = 3  # Player + 3 AI
        starting_positions = map_generator.get_starting_positions(num_ai_nations + 1)

        if not starting_positions:
            print("Warning: No suitable starting positions found!")
            return

        # Create player nation
        player_nation = Nation(
            nation_id=self.state.player.nation_id,
            name=self.state.player.nation_name,
            leader_name=self.state.player.player_name,
            is_player_nation=True,
            is_ai=False,
        )

        # Give starting resources
        player_nation.resources = {
            ResourceType.GOLD: 5000,
            ResourceType.FOOD: 500,
            ResourceType.TIMBER: 200,
            ResourceType.IRON: 100,
            ResourceType.LEATHER: 50,
            ResourceType.HERBS: 50,
            ResourceType.GEMS: 10,
            ResourceType.MITHRIL: 5,
        }

        player_nation.mana_crystals = {
            Element.FIRE: 10,
            Element.WATER: 10,
            Element.EARTH: 10,
            Element.AIR: 10,
            Element.LIFE: 10,
            Element.DEATH: 10,
        }

        # Assign starting territory
        start_x, start_y = starting_positions[0]
        start_territory_id = f"hex_{start_x}_{start_y}"
        start_territory = territories.get(start_territory_id)

        if start_territory:
            start_territory.owner_id = player_nation.nation_id
            start_territory.name = f"{self.state.player.nation_name} Capital"
            start_territory.population = 1000
            start_territory.happiness = 75
            player_nation.add_territory(start_territory_id)

            # Add starting buildings
            from src.data.constants import BuildingType
            farm = start_territory.add_building(BuildingType.FARM)
            farm.construction_progress = 100  # Complete
            barracks = start_territory.add_building(BuildingType.BARRACKS)
            barracks.construction_progress = 100

            # Add starting workers
            start_territory.add_worker("farmer")
            start_territory.add_worker("farmer")
            start_territory.add_worker("miner")

        # Store player nation
        self.state.nations[player_nation.nation_id] = player_nation.to_dict()

        # Create AI nations
        ai_names = ["Silvermoon Empire", "Crimson Dominion", "Verdant Alliance"]
        ai_leaders = ["Emperor Aldric", "Warlord Kael", "Archdruid Elara"]
        ai_elements = [Element.WATER, Element.FIRE, Element.EARTH]

        for i in range(min(num_ai_nations, len(starting_positions) - 1)):
            from src.models.nation import AIPersonality

            ai_nation = Nation(
                nation_id=f"ai_nation_{i+1}",
                name=ai_names[i],
                leader_name=ai_leaders[i],
                primary_element=ai_elements[i],
                is_player_nation=False,
                is_ai=True,
            )

            # AI starting resources (less than player)
            ai_nation.resources = {
                ResourceType.GOLD: 3000,
                ResourceType.FOOD: 300,
                ResourceType.TIMBER: 150,
                ResourceType.IRON: 75,
                ResourceType.LEATHER: 30,
                ResourceType.HERBS: 30,
                ResourceType.GEMS: 5,
                ResourceType.MITHRIL: 2,
            }

            ai_nation.mana_crystals = {elem: 5 for elem in Element}

            # Assign AI personality
            personalities = [
                AIPersonality.create_aggressive(),
                AIPersonality.create_expansionist(),
                AIPersonality.create_balanced(),
            ]
            ai_nation.ai_personality = personalities[i % len(personalities)]

            # Assign starting territory
            ai_start_x, ai_start_y = starting_positions[i + 1]
            ai_territory_id = f"hex_{ai_start_x}_{ai_start_y}"
            ai_territory = territories.get(ai_territory_id)

            if ai_territory:
                ai_territory.owner_id = ai_nation.nation_id
                ai_territory.name = f"{ai_nation.name} Capital"
                ai_territory.population = 800
                ai_territory.happiness = 60
                ai_nation.add_territory(ai_territory_id)

                # Add buildings
                farm = ai_territory.add_building(BuildingType.FARM)
                farm.construction_progress = 100

            # Set up diplomacy (neutral with all)
            from src.models.nation import DiplomaticRelation
            ai_nation.set_relationship(
                player_nation.nation_id,
                DiplomaticRelation(nation_id=player_nation.nation_id, relationship=0)
            )

            self.state.nations[ai_nation.nation_id] = ai_nation.to_dict()

        # Save territories to game state
        self.state.territories = {
            territory_id: territory.to_dict()
            for territory_id, territory in territories.items()
        }

        print(f"World created with {len(territories)} territories")
        print(f"Player starts at ({start_x}, {start_y})")
        print(f"Created {num_ai_nations} AI nations")

    def _update_playtime(self) -> None:
        """Update total playtime."""
        if self.state is None or self.last_update_time is None:
            return

        now = datetime.now()
        elapsed = (now - self.last_update_time).total_seconds()
        self.state.update_playtime(int(elapsed))
        self.last_update_time = now

    def get_game_info(self) -> dict:
        """Get summary information about current game."""
        if self.state is None:
            return {}

        return {
            "active": self.is_game_active(),
            "player_name": self.state.player.player_name,
            "nation_name": self.state.player.nation_name,
            "turn": self.state.time.current_turn,
            "time_display": str(self.state.time),
            "playtime": self.state.get_playtime_display(),
            "difficulty": self.state.player.difficulty.value,
            "win_rate": f"{self.state.player.win_rate * 100:.1f}%",
        }
