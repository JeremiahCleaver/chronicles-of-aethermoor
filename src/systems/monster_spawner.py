"""
Monster Spawning System - manages monster nests and roaming parties.

This system:
- Creates monster nests in wilderness territories
- Spawns monsters at nests over time
- Creates roaming monster parties
- Manages monster movement and threats
"""

from typing import Optional
import random
from src.models.monster import (
    MonsterNest,
    MonsterParty,
    MonsterType,
    MONSTER_TYPES,
    select_random_monster_type,
)
from src.models.territory import Territory


class MonsterSpawner:
    """
    Manages monster spawning and behavior across the world.
    """

    def __init__(self):
        """Initialize monster spawner."""
        self.nests: dict[str, MonsterNest] = {}  # nest_id -> MonsterNest
        self.monster_parties: dict[str, MonsterParty] = {}  # party_id -> MonsterParty
        self.next_nest_id = 0
        self.next_party_id = 0

    def process_turn(
        self,
        current_turn: int,
        territories: dict[str, Territory]
    ) -> list[dict]:
        """
        Process monster spawning and behavior for this turn.

        Args:
            current_turn: Current game turn
            territories: All territories in game

        Returns:
            List of events that occurred (spawns, movements, etc.)
        """
        events = []

        # Spawn new nests in wilderness (low chance)
        if random.random() < 0.05:  # 5% chance per turn
            event = self._try_spawn_nest(current_turn, territories)
            if event:
                events.append(event)

        # Update existing nests
        for nest in list(self.nests.values()):
            nest.turns_active += 1

            # Spawn monsters at nests
            if nest.should_spawn(current_turn):
                if nest.spawn_monster(current_turn):
                    events.append({
                        "type": "monster_spawn",
                        "nest_id": nest.nest_id,
                        "territory_id": nest.territory_id,
                        "monster_type": nest.monster_type_id,
                    })

            # Nests grow over time
            if nest.turns_active % 20 == 0:  # Every 20 turns
                nest.grow_nest()
                events.append({
                    "type": "nest_growth",
                    "nest_id": nest.nest_id,
                    "territory_id": nest.territory_id,
                    "new_level": nest.nest_level,
                })

        # Move roaming monster parties
        for party in self.monster_parties.values():
            if party.is_roaming and random.random() < 0.3:  # 30% chance to move
                event = self._move_monster_party(party, territories)
                if event:
                    events.append(event)

        return events

    def _try_spawn_nest(
        self,
        current_turn: int,
        territories: dict[str, Territory]
    ) -> Optional[dict]:
        """
        Try to spawn a new monster nest in wilderness.

        Returns:
            Event dict if nest spawned, None otherwise
        """
        # Find unowned territories
        wilderness = [
            t for t in territories.values()
            if not t.is_owned()
        ]

        if not wilderness:
            return None

        # Select random territory
        territory = random.choice(wilderness)

        # Select monster type suitable for biome
        monster_type = select_random_monster_type(territory.biome.biome_id, current_turn)

        if not monster_type:
            return None

        # Create nest
        nest_id = f"nest_{self.next_nest_id}"
        self.next_nest_id += 1

        nest = MonsterNest(
            nest_id=nest_id,
            territory_id=territory.territory_id,
            monster_type_id=monster_type.monster_type_id,
            last_spawn_turn=current_turn,
        )

        self.nests[nest_id] = nest

        # Create initial monster party at nest
        self._create_monster_party(
            territory.territory_id,
            monster_type.monster_type_id,
            monster_count=1,
            guarding_nest=True,
        )

        return {
            "type": "nest_created",
            "nest_id": nest_id,
            "territory_id": territory.territory_id,
            "monster_type": monster_type.name,
        }

    def _create_monster_party(
        self,
        territory_id: str,
        monster_type_id: str,
        monster_count: int = 3,
        party_level: int = 1,
        guarding_nest: bool = False,
        roaming: bool = False,
    ) -> MonsterParty:
        """Create a new monster party."""
        party_id = f"party_{self.next_party_id}"
        self.next_party_id += 1

        party = MonsterParty(
            party_id=party_id,
            territory_id=territory_id,
            monster_type_id=monster_type_id,
            monster_count=monster_count,
            party_level=party_level,
            is_roaming=roaming,
            is_guarding_nest=guarding_nest,
        )

        party.calculate_strength()
        self.monster_parties[party_id] = party

        return party

    def _move_monster_party(
        self,
        party: MonsterParty,
        territories: dict[str, Territory]
    ) -> Optional[dict]:
        """
        Move a roaming monster party to adjacent territory.

        Returns:
            Event dict if party moved
        """
        current_territory = territories.get(party.territory_id)
        if not current_territory:
            return None

        # Get adjacent territories
        neighbors = current_territory.get_neighbors(40, 30)  # World dimensions

        if not neighbors:
            return None

        # Select random neighbor
        next_x, next_y = random.choice(neighbors)
        next_territory_id = f"hex_{next_x}_{next_y}"

        # Move party
        party.move_to_territory(next_territory_id)

        return {
            "type": "monster_movement",
            "party_id": party.party_id,
            "from_territory": current_territory.territory_id,
            "to_territory": next_territory_id,
        }

    def get_monsters_in_territory(self, territory_id: str) -> list[MonsterParty]:
        """Get all monster parties in a specific territory."""
        return [
            party for party in self.monster_parties.values()
            if party.territory_id == territory_id
        ]

    def get_nest_in_territory(self, territory_id: str) -> Optional[MonsterNest]:
        """Get monster nest in a specific territory, if any."""
        for nest in self.nests.values():
            if nest.territory_id == territory_id:
                return nest
        return None

    def defeat_monster_party(self, party_id: str) -> Optional[dict]:
        """
        Remove a defeated monster party.

        Returns:
            Loot rewards for defeating the party
        """
        party = self.monster_parties.get(party_id)
        if not party:
            return None

        monster_type = party.get_monster_type()
        if not monster_type:
            return None

        # Calculate rewards
        gold_min, gold_max = monster_type.gold_reward
        total_gold = random.randint(gold_min, gold_max) * party.monster_count
        total_exp = monster_type.exp_reward * party.monster_count

        # Remove party
        del self.monster_parties[party_id]

        # If guarding nest, reduce nest monster count
        if party.is_guarding_nest:
            nest = self.get_nest_in_territory(party.territory_id)
            if nest:
                nest.remove_monster()

        return {
            "gold": total_gold,
            "exp": total_exp,
            "monster_type": monster_type.name,
            "count": party.monster_count,
        }

    def destroy_nest(self, nest_id: str) -> bool:
        """
        Destroy a monster nest.

        Returns:
            True if nest destroyed
        """
        if nest_id not in self.nests:
            return False

        nest = self.nests[nest_id]

        # Remove all parties guarding this nest
        parties_to_remove = [
            pid for pid, party in self.monster_parties.items()
            if party.is_guarding_nest and party.territory_id == nest.territory_id
        ]

        for pid in parties_to_remove:
            del self.monster_parties[pid]

        # Remove nest
        del self.nests[nest_id]

        return True

    def get_threat_assessment(self, territory_id: str) -> dict:
        """
        Assess monster threat level in a territory.

        Returns:
            Dictionary with threat information
        """
        nest = self.get_nest_in_territory(territory_id)
        parties = self.get_monsters_in_territory(territory_id)

        total_monsters = sum(p.monster_count for p in parties)
        total_strength = sum(p.total_strength for p in parties)

        threat_level = "None"
        if total_strength > 0:
            if total_strength < 100:
                threat_level = "Low"
            elif total_strength < 300:
                threat_level = "Medium"
            elif total_strength < 600:
                threat_level = "High"
            else:
                threat_level = "Extreme"

        return {
            "has_nest": nest is not None,
            "nest_level": nest.nest_level if nest else 0,
            "nest_threat": nest.get_threat_level() if nest else "None",
            "party_count": len(parties),
            "total_monsters": total_monsters,
            "total_strength": total_strength,
            "threat_level": threat_level,
        }

    def spawn_boss_monster(
        self,
        territory_id: str,
        monster_type_id: str,
        level: int = 3
    ) -> MonsterParty:
        """
        Spawn a special boss monster party.

        Used for events or quests.
        """
        return self._create_monster_party(
            territory_id=territory_id,
            monster_type_id=monster_type_id,
            monster_count=1,
            party_level=level,
            roaming=False,
            guarding_nest=False,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "nests": {
                nest_id: nest.to_dict()
                for nest_id, nest in self.nests.items()
            },
            "monster_parties": {
                party_id: party.to_dict()
                for party_id, party in self.monster_parties.items()
            },
            "next_nest_id": self.next_nest_id,
            "next_party_id": self.next_party_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterSpawner":
        """Load from dictionary."""
        spawner = cls()

        # Load nests
        if "nests" in data:
            for nest_id, nest_data in data["nests"].items():
                spawner.nests[nest_id] = MonsterNest.from_dict(nest_data)

        # Load parties
        if "monster_parties" in data:
            for party_id, party_data in data["monster_parties"].items():
                spawner.monster_parties[party_id] = MonsterParty.from_dict(party_data)

        spawner.next_nest_id = data.get("next_nest_id", 0)
        spawner.next_party_id = data.get("next_party_id", 0)

        return spawner
