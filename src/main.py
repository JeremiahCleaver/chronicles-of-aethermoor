"""
Chronicles of Aethermoor - Main Entry Point

A text-based tactical JRPG.
"""

import sys
import argparse
from pathlib import Path

from src.core.game_engine import GameEngine


def print_banner():
    """Print game title banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           CHRONICLES OF AETHERMOOR                            ║
║                                                               ║
║     A Text-Based Tactical JRPG                                ║
║     Version 0.3.0 - Phase 3 Development Build                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main_menu(engine: GameEngine) -> None:
    """Display main menu and handle user input."""
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("\n1. New Game")
        print("2. Load Game")
        print("3. Settings")
        print("4. Credits")
        print("5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

        if choice == "1":
            new_game_menu(engine)
        elif choice == "2":
            load_game_menu(engine)
        elif choice == "3":
            print("\n[Settings menu - Not yet implemented]")
        elif choice == "4":
            show_credits()
        elif choice == "5":
            print("\nThanks for playing!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please select 1-5.")


def new_game_menu(engine: GameEngine) -> None:
    """New game setup menu."""
    print("\n" + "="*60)
    print("NEW GAME")
    print("="*60)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "Player"

    # Get nation name
    nation_name = input("Enter your nation's name: ").strip()
    if not nation_name:
        nation_name = "New Nation"

    # Select difficulty
    print("\nSelect Difficulty:")
    print("1. Easy - For newcomers")
    print("2. Normal - Balanced challenge (Recommended)")
    print("3. Hard - For JRPG veterans")
    print("4. Legendary - Ultimate challenge")

    difficulty_map = {
        "1": "easy",
        "2": "normal",
        "3": "hard",
        "4": "legendary",
    }

    diff_choice = input("\nDifficulty (1-4): ").strip()
    difficulty = difficulty_map.get(diff_choice, "normal")

    # Start game
    if engine.new_game(player_name, nation_name, difficulty):
        print(f"\n✓ New game started!")
        print(f"  Player: {player_name}")
        print(f"  Nation: {nation_name}")
        print(f"  Difficulty: {difficulty.upper()}")

        # Enter game loop
        game_loop(engine)
    else:
        print("\n✗ Failed to start new game.")


def load_game_menu(engine: GameEngine) -> None:
    """Load game menu."""
    print("\n" + "="*60)
    print("LOAD GAME")
    print("="*60)

    # List available saves
    saves = engine.save_system.list_saves("manual")

    if not saves:
        print("\nNo saved games found.")
        input("\nPress Enter to continue...")
        return

    print("\nAvailable Saves:")
    print()
    for i, save_info in enumerate(saves, 1):
        print(f"{i}. {save_info['nation_name']} - Turn {save_info['turn']}")
        print(f"   Player: {save_info['player_name']}")
        print(f"   Saved: {save_info['saved_at'].strftime('%Y-%m-%d %H:%M')}")
        print()

    choice = input(f"Select save (1-{len(saves)}) or 0 to cancel: ").strip()

    try:
        slot = int(choice)
        if slot == 0:
            return
        if 1 <= slot <= len(saves):
            save_info = saves[slot - 1]
            if engine.load_game(save_info['slot'], "manual"):
                print(f"\n✓ Game loaded successfully!")
                game_loop(engine)
            else:
                print(f"\n✗ Failed to load game.")
    except ValueError:
        print("\nInvalid input.")


def game_loop(engine: GameEngine) -> None:
    """Main game loop."""
    while engine.is_game_active():
        state = engine.get_current_state()
        if state is None:
            break

        print("\n" + "="*60)
        print(f"TURN {state.time.current_turn} | {state.time.season}, Year {state.time.current_year}")
        print("="*60)
        print(f"Nation: {state.player.nation_name}")
        print(f"Playtime: {state.get_playtime_display()}")
        print()

        print("1. View Status")
        print("2. View World Map")
        print("3. Start Battle (Demo)")
        print("4. Advance Turn")
        print("5. Save Game")
        print("6. Return to Main Menu")

        choice = input("\nSelect action (1-6): ").strip()

        if choice == "1":
            show_status(engine)
        elif choice == "2":
            show_world_map(engine)
        elif choice == "3":
            start_battle_demo()
        elif choice == "4":
            engine.advance_turn()
            print(f"\n✓ Turn advanced to {state.time.current_turn + 1}")
        elif choice == "5":
            save_game_submenu(engine)
        elif choice == "6":
            print("\nReturning to main menu...")
            engine.end_game()
            break
        else:
            print("\nInvalid choice.")


def start_battle_demo() -> None:
    """Start a tactical battle demo."""
    from src.models.battle import CombatUnit, BattlePosition
    from src.systems.battle_manager import BattleGenerator
    from src.ui.battle_ui import run_battle_demo
    from src.data.constants import Element

    print("\n" + "=" * 60)
    print("TACTICAL BATTLE - DEMO")
    print("=" * 60)
    print("\nPreparing battle...")

    # Create player units
    player_units = [
        CombatUnit(
            unit_id="player_1",
            name="Knight",
            side="player",
            max_hp=120,
            current_hp=120,
            max_mp=30,
            current_mp=30,
            attack=15,
            defense=12,
            magic_attack=8,
            magic_defense=10,
            speed=10,
            move_range=3,
            element=Element.EARTH,
        ),
        CombatUnit(
            unit_id="player_2",
            name="Archer",
            side="player",
            max_hp=80,
            current_hp=80,
            max_mp=20,
            current_mp=20,
            attack=18,
            defense=8,
            magic_attack=6,
            magic_defense=8,
            speed=14,
            move_range=4,
            element=Element.AIR,
        ),
        CombatUnit(
            unit_id="player_3",
            name="Mage",
            side="player",
            max_hp=60,
            current_hp=60,
            max_mp=80,
            current_mp=80,
            attack=6,
            defense=6,
            magic_attack=20,
            magic_defense=15,
            speed=8,
            move_range=3,
            element=Element.FIRE,
        ),
    ]

    # Generate battle
    battle = BattleGenerator.generate_random_battle(
        player_units=player_units,
        enemy_count=3,
        terrain_variety=True
    )

    print("Battle ready!")
    print(f"Player units: {len(player_units)}")
    print(f"Enemy units: {len([u for u in battle.battle_grid.units.values() if u.side == 'enemy'])}")
    print()
    input("Press Enter to begin battle...")

    # Run battle
    result = run_battle_demo(battle)

    print(f"\nBattle complete! Result: {result.value}")
    input("\nPress Enter to continue...")


def show_world_map(engine: GameEngine) -> None:
    """Display world map interface."""
    from src.ui.world_map_ui import display_world_map_menu
    from src.models.territory import Territory
    from src.models.nation import Nation

    state = engine.get_current_state()
    if state is None:
        return

    # Load territories and nations
    territories: dict[str, Territory] = {}
    for territory_id, territory_data in state.territories.items():
        territories[territory_id] = Territory.from_dict(territory_data)

    nations: dict[str, Nation] = {}
    for nation_id, nation_data in state.nations.items():
        nations[nation_id] = Nation.from_dict(nation_data)

    # Show world map menu
    display_world_map_menu(territories, nations, state.player.nation_id)


def show_status(engine: GameEngine) -> None:
    """Display current game status."""
    info = engine.get_game_info()

    print("\n" + "="*60)
    print("GAME STATUS")
    print("="*60)
    print(f"Player: {info['player_name']}")
    print(f"Nation: {info['nation_name']}")
    print(f"Turn: {info['turn']} ({info['time_display']})")
    print(f"Playtime: {info['playtime']}")
    print(f"Difficulty: {info['difficulty'].upper()}")
    print(f"Battle Win Rate: {info['win_rate']}")

    input("\nPress Enter to continue...")


def save_game_submenu(engine: GameEngine) -> None:
    """Save game submenu."""
    print("\n" + "="*60)
    print("SAVE GAME")
    print("="*60)
    print("\n1. Save to Slot 1")
    print("2. Save to Slot 2")
    print("3. Save to Slot 3")
    print("4. Quicksave")
    print("5. Cancel")

    choice = input("\nSelect (1-5): ").strip()

    if choice in ["1", "2", "3"]:
        slot = int(choice) - 1
        if engine.save_game(slot, "manual"):
            print(f"\n✓ Game saved to Slot {choice}!")
        else:
            print("\n✗ Failed to save game.")
    elif choice == "4":
        if engine.quicksave():
            print("\n✓ Quicksave created!")
        else:
            print("\n✗ Failed to create quicksave.")

    input("\nPress Enter to continue...")


def show_credits():
    """Display game credits."""
    print("\n" + "="*60)
    print("CREDITS")
    print("="*60)
    print()
    print("Chronicles of Aethermoor")
    print("A Text-Based Tactical JRPG")
    print()
    print("Inspired by:")
    print("  - Final Fantasy Tactics")
    print("  - Brigandine: Legend of Forsena")
    print("  - Age of Wonders")
    print("  - Final Fantasy VI")
    print()
    print("Phase 1 Development Build")
    print("2025")

    input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Chronicles of Aethermoor - A Text-Based Tactical JRPG"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=Path("./saves"),
        help="Save game directory"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Initialize game engine
    engine = GameEngine(save_directory=args.save_dir)

    # Show main menu
    try:
        main_menu(engine)
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
