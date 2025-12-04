"""
Basic tests for Phase 1 systems.
"""

import pytest
from pathlib import Path
from src.models.game_state import GameState, TimeState, PlayerState
from src.models.unit import Unit, UnitStats, JobClass
from src.core.game_engine import GameEngine
from src.core.save_system import SaveSystem
from src.data.constants import Element, ClassTier, Difficulty


class TestGameState:
    """Test game state models."""

    def test_time_state_creation(self):
        """Test time state initialization."""
        time = TimeState()
        assert time.current_turn == 1
        assert time.current_month == 1
        assert time.current_year == 1
        assert time.season == "Winter"

    def test_time_advance(self):
        """Test turn advancement."""
        time = TimeState()
        time.advance_turn()
        assert time.current_turn == 2

    def test_player_state_creation(self):
        """Test player state initialization."""
        player = PlayerState()
        assert player.player_name == "Player"
        assert player.difficulty == Difficulty.NORMAL
        assert player.total_battles == 0

    def test_game_state_creation(self):
        """Test complete game state creation."""
        state = GameState()
        assert state.time.current_turn == 1
        assert state.player.player_name == "Player"
        assert not state.tutorial_completed


class TestUnit:
    """Test unit models."""

    def test_unit_creation(self):
        """Test basic unit creation."""
        job_class = JobClass(
            class_id="warrior",
            name="Warrior",
            tier=ClassTier.TIER_1
        )

        unit = Unit(
            unit_id="unit_001",
            name="Test Warrior",
            owner_id="player",
            current_class=job_class
        )

        assert unit.name == "Test Warrior"
        assert unit.level == 1
        assert unit.is_alive()

    def test_unit_damage(self):
        """Test unit taking damage."""
        job_class = JobClass(class_id="warrior", name="Warrior")
        unit = Unit(
            unit_id="unit_001",
            name="Test Unit",
            owner_id="player",
            current_class=job_class
        )

        initial_hp = unit.current_stats.hp
        damage = unit.take_damage(20)
        assert damage == 20
        assert unit.current_stats.hp == initial_hp - 20

    def test_unit_healing(self):
        """Test unit healing."""
        job_class = JobClass(class_id="warrior", name="Warrior")
        unit = Unit(
            unit_id="unit_001",
            name="Test Unit",
            owner_id="player",
            current_class=job_class
        )

        unit.take_damage(50)
        healed = unit.heal(30)
        assert healed == 30

    def test_unit_level_up(self):
        """Test unit leveling up."""
        job_class = JobClass(class_id="warrior", name="Warrior")
        unit = Unit(
            unit_id="unit_001",
            name="Test Unit",
            owner_id="player",
            current_class=job_class
        )

        initial_level = unit.level
        unit.gain_experience(150)
        assert unit.level == initial_level + 1


class TestSaveSystem:
    """Test save/load system."""

    def test_save_system_creation(self, tmp_path):
        """Test save system initialization."""
        save_system = SaveSystem(tmp_path)
        assert save_system.save_dir.exists()

    def test_save_and_load(self, tmp_path):
        """Test saving and loading game state."""
        save_system = SaveSystem(tmp_path)
        state = GameState()
        state.player.player_name = "TestPlayer"
        state.player.nation_name = "TestNation"

        # Save
        success = save_system.save_game(state, 0, "manual")
        assert success

        # Load
        loaded_state = save_system.load_game(0, "manual")
        assert loaded_state is not None
        assert loaded_state.player.player_name == "TestPlayer"
        assert loaded_state.player.nation_name == "TestNation"

    def test_autosave(self, tmp_path):
        """Test autosave functionality."""
        save_system = SaveSystem(tmp_path)
        state = GameState()

        success = save_system.autosave(state)
        assert success

        saves = save_system.list_saves("auto")
        assert len(saves) == 1

    def test_quicksave(self, tmp_path):
        """Test quicksave functionality."""
        save_system = SaveSystem(tmp_path)
        state = GameState()

        success = save_system.quicksave(state)
        assert success


class TestGameEngine:
    """Test game engine."""

    def test_engine_creation(self, tmp_path):
        """Test engine initialization."""
        engine = GameEngine(tmp_path)
        assert engine.save_system is not None
        assert not engine.is_game_active()

    def test_new_game(self, tmp_path):
        """Test starting new game."""
        engine = GameEngine(tmp_path)
        success = engine.new_game("TestPlayer", "TestNation", "normal")

        assert success
        assert engine.is_game_active()
        assert engine.state is not None
        assert engine.state.player.player_name == "TestPlayer"

    def test_save_and_load_game(self, tmp_path):
        """Test saving and loading through engine."""
        engine = GameEngine(tmp_path)
        engine.new_game("TestPlayer", "TestNation")

        # Save
        success = engine.save_game(0, "manual")
        assert success

        # Create new engine and load
        engine2 = GameEngine(tmp_path)
        success = engine2.load_game(0, "manual")
        assert success
        assert engine2.state.player.player_name == "TestPlayer"

    def test_turn_advancement(self, tmp_path):
        """Test advancing turns."""
        engine = GameEngine(tmp_path)
        engine.new_game("TestPlayer", "TestNation")

        initial_turn = engine.state.time.current_turn
        engine.advance_turn()
        assert engine.state.time.current_turn == initial_turn + 1


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory for tests."""
    return tmp_path_factory.mktemp("test_saves")
