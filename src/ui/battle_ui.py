"""
Battle UI - Text-based tactical combat interface.
"""

from typing import Optional
from src.models.battle import BattleGrid, CombatUnit, BattlePosition, BattleTerrain
from src.systems.battle_manager import Battle, BattlePhase, BattleResult
from src.systems.battle_ai import BattleAI


class BattleUI:
    """
    Terminal-based battle interface.

    Features:
    - ASCII hex grid visualization
    - Unit stats display
    - Turn order display
    - Action menu
    - Movement and attack controls
    """

    # Terrain display symbols
    TERRAIN_SYMBOLS = {
        BattleTerrain.PLAINS: ".",
        BattleTerrain.FOREST: "T",
        BattleTerrain.HILL: "^",
        BattleTerrain.WATER: "~",
        BattleTerrain.WALL: "#",
        BattleTerrain.OBSTACLE: "X",
    }

    # ANSI color codes
    COLOR_PLAYER = "\033[94m"  # Blue
    COLOR_ENEMY = "\033[91m"   # Red
    COLOR_ALLY = "\033[92m"    # Green
    COLOR_NEUTRAL = "\033[93m"  # Yellow
    COLOR_TERRAIN = "\033[90m"  # Gray
    COLOR_HIGHLIGHT = "\033[95m"  # Magenta
    COLOR_RESET = "\033[0m"

    def __init__(self):
        """Initialize battle UI."""
        self.show_colors = True

    def display_battle_grid(
        self,
        battle: Battle,
        highlight_positions: Optional[list[BattlePosition]] = None,
        show_info: bool = True
    ) -> None:
        """
        Display battle grid.

        Args:
            battle: Battle to display
            highlight_positions: Positions to highlight (movement range, etc.)
            show_info: Whether to show battle info
        """
        grid = battle.battle_grid

        if show_info:
            self._display_battle_header(battle)

        print("\n" + "=" * 80)
        print(f"BATTLE GRID ({grid.width}×{grid.height})")
        print("=" * 80)

        # Display grid
        for y in range(grid.height):
            # Row offset for hex grid
            line = "  " if y % 2 == 1 else ""

            for x in range(grid.width):
                position = BattlePosition(x, y)
                cell = grid.get_cell(x, y)

                if not cell:
                    line += "  "
                    continue

                # Check if highlighted
                is_highlighted = (
                    highlight_positions and
                    position in highlight_positions
                )

                # Get unit at position
                unit = grid.get_unit_at_position(position)

                if unit:
                    symbol = self._get_unit_symbol(unit)
                    if self.show_colors:
                        color = self._get_unit_color(unit)
                        if is_highlighted:
                            color = self.COLOR_HIGHLIGHT
                        line += f"{color}{symbol}{self.COLOR_RESET} "
                    else:
                        line += f"{symbol} "
                else:
                    # Show terrain
                    symbol = self.TERRAIN_SYMBOLS.get(cell.terrain, ".")
                    if self.show_colors:
                        color = self.COLOR_HIGHLIGHT if is_highlighted else self.COLOR_TERRAIN
                        line += f"{color}{symbol}{self.COLOR_RESET} "
                    else:
                        line += f"{symbol} "

            print(f"{y:2d} {line}")

        # Column numbers
        print("   " + "".join(f"{x%10} " for x in range(grid.width)))
        print("=" * 80)

        if show_info:
            self._display_legend()

    def _display_battle_header(self, battle: Battle) -> None:
        """Display battle header information."""
        print("\n" + "=" * 80)
        print(f"TACTICAL BATTLE - Round {battle.round_number}")
        print("=" * 80)

        # Current turn info
        current_unit = battle.get_current_unit()
        if current_unit:
            print(f"Current Turn: {current_unit.name} ({current_unit.side})")
        else:
            print("Round Complete")

        # Phase
        print(f"Phase: {battle.phase.value.title()}")
        print()

    def _display_legend(self) -> None:
        """Display legend."""
        print("\nLEGEND:")
        print("  Units: P = Player, E = Enemy, A = Ally, N = Neutral")
        print("  Terrain: . = Plains, T = Forest, ^ = Hill, ~ = Water, # = Wall, X = Obstacle")
        print()

    def _get_unit_symbol(self, unit: CombatUnit) -> str:
        """Get display symbol for unit."""
        symbols = {
            "player": "P",
            "enemy": "E",
            "ally": "A",
            "neutral": "N",
        }
        return symbols.get(unit.side, "?")

    def _get_unit_color(self, unit: CombatUnit) -> str:
        """Get color code for unit."""
        colors = {
            "player": self.COLOR_PLAYER,
            "enemy": self.COLOR_ENEMY,
            "ally": self.COLOR_ALLY,
            "neutral": self.COLOR_NEUTRAL,
        }
        return colors.get(unit.side, self.COLOR_RESET)

    def display_unit_info(self, unit: CombatUnit, detailed: bool = True) -> None:
        """
        Display unit information.

        Args:
            unit: Unit to display
            detailed: Show detailed stats
        """
        print("\n" + "=" * 60)
        print(f"UNIT: {unit.name}")
        print("=" * 60)

        # Basic info
        print(f"Side: {unit.side.title()}")
        if unit.position:
            print(f"Position: ({unit.position.x}, {unit.position.y})")

        # HP and MP
        hp_percent = unit.get_hp_percentage()
        hp_bar = self._create_bar(hp_percent, 20)
        print(f"HP: {hp_bar} {unit.current_hp}/{unit.max_hp}")

        mp_percent = (unit.current_mp / unit.max_mp * 100) if unit.max_mp > 0 else 0
        mp_bar = self._create_bar(mp_percent, 20)
        print(f"MP: {mp_bar} {unit.current_mp}/{unit.max_mp}")

        if detailed:
            # Stats
            print("\nSTATS:")
            print(f"  Attack: {unit.get_total_attack()}")
            print(f"  Defense: {unit.get_total_defense()}")
            print(f"  Magic Attack: {unit.magic_attack}")
            print(f"  Magic Defense: {unit.magic_defense}")
            print(f"  Speed: {unit.get_total_speed()}")
            print(f"  Move Range: {unit.move_range}")

            # Element
            if unit.element:
                print(f"  Element: {unit.element.value.title()}")

            # Status effects
            if unit.status_effects:
                print("\nSTATUS EFFECTS:")
                for status in unit.status_effects:
                    duration = unit.status_durations.get(status, 0)
                    print(f"  • {status.value.title()} ({duration} turns)")

            # Flags
            print("\nACTIONS:")
            print(f"  Can Move: {'Yes' if unit.can_move() else 'No'}")
            print(f"  Can Act: {'Yes' if unit.can_act() else 'No'}")

        print("=" * 60)

    def _create_bar(self, percentage: float, width: int = 20) -> str:
        """Create a text-based progress bar."""
        filled = int(width * (percentage / 100.0))
        empty = width - filled
        return "[" + ("=" * filled) + (" " * empty) + "]"

    def display_turn_order(self, battle: Battle) -> None:
        """Display turn order."""
        print("\n" + "=" * 60)
        print("TURN ORDER")
        print("=" * 60)

        turn_order = battle.get_turn_order_display()

        for i, (name, speed, has_acted) in enumerate(turn_order):
            status = "✓" if has_acted else " "
            marker = "►" if i == battle.current_turn_index else " "
            print(f"{marker} {status} {name:20} (SPD: {speed:2d})")

        print("=" * 60)

    def display_action_menu(self, unit: CombatUnit) -> None:
        """Display action menu for unit."""
        print("\n" + "=" * 60)
        print(f"ACTIONS FOR {unit.name}")
        print("=" * 60)

        print("1. Move")
        print("2. Attack")
        print("3. Wait (End Turn)")
        print("4. View Stats")
        print("5. Cancel")
        print()

    def get_position_input(self, prompt: str = "Enter position (x y): ") -> Optional[BattlePosition]:
        """
        Get position input from user.

        Args:
            prompt: Input prompt

        Returns:
            BattlePosition or None if cancelled
        """
        try:
            user_input = input(prompt).strip()

            if not user_input or user_input.lower() == "cancel":
                return None

            parts = user_input.split()
            if len(parts) != 2:
                print("Invalid input. Use format: x y")
                return None

            x = int(parts[0])
            y = int(parts[1])

            return BattlePosition(x, y)

        except ValueError:
            print("Invalid coordinates. Must be numbers.")
            return None

    def display_battle_summary(self, battle: Battle) -> None:
        """Display battle summary."""
        print("\n" + "=" * 80)
        if battle.result == BattleResult.PLAYER_VICTORY:
            print("★ VICTORY! ★")
        elif battle.result == BattleResult.PLAYER_DEFEAT:
            print("☠ DEFEAT ☠")
        else:
            print("BATTLE RETREAT")
        print("=" * 80)

        # Count survivors
        player_units = battle.get_units_by_side("player")
        enemy_units = battle.get_units_by_side("enemy")

        print(f"\nRounds Survived: {battle.round_number}")
        print(f"Player Units Remaining: {len([u for u in player_units if u.is_alive()])}/{len(player_units)}")
        print(f"Enemy Units Defeated: {len([u for u in battle.battle_grid.units.values() if u.side == 'enemy' and not u.is_alive()])}")

        # List survivors
        if player_units:
            print("\nSURVIVORS:")
            for unit in player_units:
                if unit.is_alive():
                    hp_percent = unit.get_hp_percentage()
                    print(f"  • {unit.name} - {unit.current_hp}/{unit.max_hp} HP ({hp_percent:.0f}%)")

        print("=" * 80)


def run_battle_demo(battle: Battle) -> BattleResult:
    """
    Run interactive battle.

    Args:
        battle: Battle to run

    Returns:
        Battle result
    """
    ui = BattleUI()

    # Start battle
    battle.start_battle()

    # Create AI
    ai = BattleAI(
        battle.battle_grid,
        battle.movement_system,
        battle.combat_system
    )

    while not battle.is_battle_over():
        # Display grid
        ui.display_battle_grid(battle)

        # Get current unit
        current_unit = battle.get_current_unit()

        if not current_unit:
            # Round complete
            print("\nRound complete! Press Enter to continue...")
            input()
            battle.next_turn()
            continue

        # Display unit info
        ui.display_unit_info(current_unit, detailed=False)

        # Check if AI controlled
        if current_unit.is_ai_controlled:
            print(f"\n{current_unit.name}'s turn (AI)...")
            print("Press Enter to continue...")
            input()

            # AI takes turn
            messages = ai.take_turn(current_unit)
            for msg in messages:
                print(f"  {msg}")

            print("\nPress Enter to continue...")
            input()

        else:
            # Player turn
            ui.display_action_menu(current_unit)

            choice = input("Select action: ").strip()

            if choice == "1":
                # Move
                if current_unit.can_move():
                    # Show movement range
                    reachable = battle.movement_system.get_reachable_positions(current_unit)
                    highlight = [BattlePosition(x, y) for x, y in reachable.keys()]
                    ui.display_battle_grid(battle, highlight_positions=highlight, show_info=False)

                    pos = ui.get_position_input("Move to (x y): ")
                    if pos:
                        if battle.movement_system.move_unit(current_unit, pos):
                            print(f"✓ Moved to ({pos.x}, {pos.y})")
                        else:
                            print("✗ Cannot move there!")
                else:
                    print("Already moved this turn!")

            elif choice == "2":
                # Attack
                if current_unit.can_act():
                    targets = battle.combat_system.get_targets_in_range(current_unit, attack_range=1)

                    if targets:
                        print("\nTargets in range:")
                        for i, target in enumerate(targets, 1):
                            print(f"{i}. {target.name} ({target.current_hp}/{target.max_hp} HP)")

                        target_choice = input("Select target (number): ").strip()
                        try:
                            target_idx = int(target_choice) - 1
                            if 0 <= target_idx < len(targets):
                                target = targets[target_idx]
                                result = battle.combat_system.execute_attack(
                                    current_unit.unit_id,
                                    target.unit_id
                                )
                                if result:
                                    print(f"\n{result.message}")
                                    print(f"Damage dealt: {result.damage}")
                            else:
                                print("Invalid target!")
                        except ValueError:
                            print("Invalid input!")
                    else:
                        print("No targets in range!")
                else:
                    print("Already acted this turn!")

            elif choice == "3":
                # Wait (end turn)
                current_unit.has_moved = True
                current_unit.has_acted = True
                print("Turn ended.")

            elif choice == "4":
                # View stats
                ui.display_unit_info(current_unit)
                continue

            elif choice == "5":
                # Cancel
                continue

            else:
                print("Invalid choice!")
                continue

        # Next turn
        battle.next_turn()

    # Battle over
    ui.display_battle_summary(battle)

    return battle.result
