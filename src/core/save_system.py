"""
Save/Load System - handles game state persistence.

Implements the hybrid JSON + compression format described in the design doc.
"""

import json
import zlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.models.game_state_simple import GameState
from src.data.constants import MAX_SAVE_SLOTS, MAX_AUTOSAVES


class SaveSystem:
    """
    Manages saving and loading game state.

    Features:
    - 10 manual save slots
    - 3 rotating autosaves
    - 1 quicksave slot
    - 1 checkpoint slot
    - JSON + zlib compression
    - Backup system
    """

    def __init__(self, save_directory: Path):
        self.save_dir = Path(save_directory)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Save slot directories
        self.manual_dir = self.save_dir / "manual"
        self.auto_dir = self.save_dir / "auto"
        self.quick_dir = self.save_dir / "quick"
        self.checkpoint_dir = self.save_dir / "checkpoint"

        # Create directories
        for directory in [self.manual_dir, self.auto_dir, self.quick_dir, self.checkpoint_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_game(
        self,
        game_state: GameState,
        slot: int,
        slot_type: str = "manual"
    ) -> bool:
        """
        Save game to specified slot.

        Args:
            game_state: Current game state
            slot: Slot number (0-9 for manual, 0-2 for auto)
            slot_type: "manual", "auto", "quick", or "checkpoint"

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Get save path
            save_path = self._get_save_path(slot, slot_type)

            # Create backup if file exists
            if save_path.exists():
                backup_path = save_path.with_suffix('.bak')
                save_path.rename(backup_path)

            # Convert game state to dictionary
            save_data = game_state.to_dict()

            # Add metadata
            save_data['_metadata'] = {
                'slot': slot,
                'slot_type': slot_type,
                'saved_at': datetime.now().isoformat(),
            }

            # Convert to JSON
            json_data = json.dumps(save_data, indent=2)

            # Compress
            compressed_data = zlib.compress(json_data.encode('utf-8'), level=9)

            # Write to file
            with open(save_path, 'wb') as f:
                f.write(compressed_data)

            # Remove backup on successful save
            backup_path = save_path.with_suffix('.bak')
            if backup_path.exists():
                backup_path.unlink()

            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            # Restore backup if save failed
            backup_path = save_path.with_suffix('.bak')
            if backup_path.exists():
                backup_path.rename(save_path)
            return False

    def load_game(self, slot: int, slot_type: str = "manual") -> Optional[GameState]:
        """
        Load game from specified slot.

        Args:
            slot: Slot number
            slot_type: "manual", "auto", "quick", or "checkpoint"

        Returns:
            GameState if load successful, None otherwise
        """
        try:
            save_path = self._get_save_path(slot, slot_type)

            if not save_path.exists():
                return None

            # Read compressed data
            with open(save_path, 'rb') as f:
                compressed_data = f.read()

            # Decompress
            json_data = zlib.decompress(compressed_data).decode('utf-8')

            # Parse JSON
            save_data = json.loads(json_data)

            # Remove metadata
            save_data.pop('_metadata', None)

            # Create GameState
            game_state = GameState.from_dict(save_data)

            return game_state

        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def autosave(self, game_state: GameState) -> bool:
        """
        Create rotating autosave.

        Autosaves rotate: auto_0 -> auto_1 -> auto_2 -> auto_0
        """
        # Find next autosave slot
        next_slot = 0
        for i in range(MAX_AUTOSAVES):
            path = self._get_save_path(i, "auto")
            if not path.exists():
                next_slot = i
                break
            # Use oldest autosave
            if i == MAX_AUTOSAVES - 1:
                # Find oldest
                oldest_time = datetime.max
                oldest_slot = 0
                for j in range(MAX_AUTOSAVES):
                    save_info = self.get_save_info(j, "auto")
                    if save_info and save_info['saved_at'] < oldest_time:
                        oldest_time = save_info['saved_at']
                        oldest_slot = j
                next_slot = oldest_slot

        return self.save_game(game_state, next_slot, "auto")

    def quicksave(self, game_state: GameState) -> bool:
        """Create quicksave (single slot, overwritten each time)."""
        return self.save_game(game_state, 0, "quick")

    def save_checkpoint(self, game_state: GameState) -> bool:
        """Save checkpoint (important story moments)."""
        return self.save_game(game_state, 0, "checkpoint")

    def get_save_info(self, slot: int, slot_type: str = "manual") -> Optional[dict]:
        """
        Get information about a save without fully loading it.

        Returns:
            Dictionary with save metadata, or None if slot empty
        """
        try:
            save_path = self._get_save_path(slot, slot_type)

            if not save_path.exists():
                return None

            # Read compressed data
            with open(save_path, 'rb') as f:
                compressed_data = f.read()

            # Decompress
            json_data = zlib.decompress(compressed_data).decode('utf-8')

            # Parse JSON
            save_data = json.loads(json_data)

            # Extract summary info
            return {
                'slot': slot,
                'slot_type': slot_type,
                'player_name': save_data['player']['player_name'],
                'nation_name': save_data['player']['nation_name'],
                'turn': save_data['time']['current_turn'],
                'year': save_data['time']['current_year'],
                'playtime_seconds': save_data['playtime_seconds'],
                'saved_at': datetime.fromisoformat(save_data['_metadata']['saved_at']),
                'difficulty': save_data['player']['difficulty'],
                'iron_mode': save_data['player'].get('iron_mode', False),
            }

        except Exception as e:
            print(f"Error reading save info: {e}")
            return None

    def list_saves(self, slot_type: str = "manual") -> list[dict]:
        """
        List all saves of specified type.

        Returns:
            List of save info dictionaries
        """
        saves = []
        max_slots = MAX_SAVE_SLOTS if slot_type == "manual" else MAX_AUTOSAVES

        for slot in range(max_slots):
            info = self.get_save_info(slot, slot_type)
            if info:
                saves.append(info)

        return saves

    def delete_save(self, slot: int, slot_type: str = "manual") -> bool:
        """Delete a save file."""
        try:
            save_path = self._get_save_path(slot, slot_type)
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False

    def _get_save_path(self, slot: int, slot_type: str) -> Path:
        """Get file path for specified save slot."""
        if slot_type == "manual":
            directory = self.manual_dir
            filename = f"save_{slot:02d}.sav"
        elif slot_type == "auto":
            directory = self.auto_dir
            filename = f"autosave_{slot}.sav"
        elif slot_type == "quick":
            directory = self.quick_dir
            filename = "quicksave.sav"
        elif slot_type == "checkpoint":
            directory = self.checkpoint_dir
            filename = "checkpoint.sav"
        else:
            raise ValueError(f"Invalid slot_type: {slot_type}")

        return directory / filename

    def get_save_size(self, slot: int, slot_type: str = "manual") -> int:
        """Get file size of save in bytes."""
        save_path = self._get_save_path(slot, slot_type)
        if save_path.exists():
            return save_path.stat().st_size
        return 0

    def export_save(self, slot: int, slot_type: str, export_path: Path) -> bool:
        """Export save to external location."""
        try:
            save_path = self._get_save_path(slot, slot_type)
            if save_path.exists():
                import shutil
                shutil.copy2(save_path, export_path)
                return True
            return False
        except Exception as e:
            print(f"Error exporting save: {e}")
            return False

    def import_save(self, import_path: Path, slot: int, slot_type: str = "manual") -> bool:
        """Import save from external location."""
        try:
            save_path = self._get_save_path(slot, slot_type)

            # Validate it's a valid save file
            with open(import_path, 'rb') as f:
                compressed_data = f.read()
            json_data = zlib.decompress(compressed_data).decode('utf-8')
            save_data = json.loads(json_data)

            # Verify it has required fields
            if 'player' not in save_data or 'time' not in save_data:
                return False

            # Copy to save location
            import shutil
            shutil.copy2(import_path, save_path)
            return True

        except Exception as e:
            print(f"Error importing save: {e}")
            return False
