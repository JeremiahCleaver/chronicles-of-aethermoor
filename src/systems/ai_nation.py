"""
AI Nation System - strategic decision-making for AI-controlled nations.

This system handles:
- Territory expansion decisions
- Diplomatic actions
- Military strategy
- Economic management
- War and peace declarations
"""

from typing import Optional
import random
from src.models.nation import Nation, AIPersonality, DiplomaticRelation
from src.models.territory import Territory
from src.systems.monster_spawner import MonsterSpawner
from src.data.constants import ResourceType, Element


class AIDecision:
    """Represents a decision made by AI nation."""
    def __init__(self, decision_type: str, priority: float = 0.5, **params):
        self.decision_type = decision_type
        self.priority = priority  # 0.0-1.0, higher = more important
        self.params = params

    def __repr__(self):
        return f"AIDecision({self.decision_type}, priority={self.priority:.2f})"


class AINationController:
    """
    Controls AI nation strategic behavior.

    Each AI nation evaluates:
    - Expansion opportunities (conquer territory)
    - Diplomatic relations (war, peace, alliances)
    - Economic development (buildings, workers)
    - Military buildup (recruit units)
    - Monster threats (clear nests, defend)
    """

    def __init__(self):
        """Initialize AI controller."""
        pass

    def execute_ai_turn(
        self,
        nation: Nation,
        all_nations: dict[str, Nation],
        all_territories: dict[str, Territory],
        monster_spawner: MonsterSpawner,
        current_turn: int,
    ) -> list[dict]:
        """
        Execute one AI nation's turn.

        Args:
            nation: The AI nation
            all_nations: All nations in game
            all_territories: All territories
            monster_spawner: Monster system
            current_turn: Current game turn

        Returns:
            List of actions/events that occurred
        """
        if not nation.is_ai or not nation.is_active:
            return []

        events = []

        # Evaluate possible decisions
        decisions = self._evaluate_decisions(
            nation,
            all_nations,
            all_territories,
            monster_spawner,
            current_turn,
        )

        # Sort by priority and execute top decisions
        decisions.sort(key=lambda d: d.priority, reverse=True)

        # Execute decisions (limit to prevent AI from doing too much per turn)
        max_actions = 3
        actions_taken = 0

        for decision in decisions:
            if actions_taken >= max_actions:
                break

            event = self._execute_decision(
                decision,
                nation,
                all_nations,
                all_territories,
                monster_spawner,
            )

            if event:
                events.append(event)
                actions_taken += 1

        return events

    def _evaluate_decisions(
        self,
        nation: Nation,
        all_nations: dict[str, Nation],
        all_territories: dict[str, Territory],
        monster_spawner: MonsterSpawner,
        current_turn: int,
    ) -> list[AIDecision]:
        """
        Evaluate all possible decisions for an AI nation.

        Returns:
            List of possible decisions with priority scores
        """
        decisions = []
        personality = nation.ai_personality

        if not personality:
            personality = AIPersonality.create_balanced()

        # 1. Territory Expansion
        expansion_decisions = self._evaluate_expansion(
            nation, all_territories, monster_spawner, personality
        )
        decisions.extend(expansion_decisions)

        # 2. Diplomacy
        diplomacy_decisions = self._evaluate_diplomacy(
            nation, all_nations, personality, current_turn
        )
        decisions.extend(diplomacy_decisions)

        # 3. Military Buildup
        military_decisions = self._evaluate_military(
            nation, all_nations, personality
        )
        decisions.extend(military_decisions)

        # 4. Economic Development
        economic_decisions = self._evaluate_economy(
            nation, all_territories, personality
        )
        decisions.extend(economic_decisions)

        # 5. Monster Threats
        monster_decisions = self._evaluate_monster_threats(
            nation, all_territories, monster_spawner, personality
        )
        decisions.extend(monster_decisions)

        return decisions

    def _evaluate_expansion(
        self,
        nation: Nation,
        all_territories: dict[str, Territory],
        monster_spawner: MonsterSpawner,
        personality: AIPersonality,
    ) -> list[AIDecision]:
        """Evaluate territory expansion opportunities."""
        decisions = []

        # Find adjacent territories to conquer
        adjacent_targets = self._find_expansion_targets(nation, all_territories)

        for territory_id, territory in adjacent_targets:
            priority = 0.3 * personality.expansion_desire

            # Increase priority for valuable territories
            if territory.biome.base_resources:
                resource_value = sum(territory.biome.base_resources.values())
                priority += min(0.3, resource_value / 200)

            # Reduce priority if territory has monsters
            threat = monster_spawner.get_threat_assessment(territory_id)
            if threat["total_strength"] > 0:
                priority -= 0.2

            # Reduce priority if owned by another nation (war required)
            if territory.is_owned():
                owner = territory.owner_id
                if owner and owner != nation.nation_id:
                    # Check if at war
                    relation = nation.get_relationship(owner)
                    if not relation or not relation.at_war:
                        priority *= 0.5  # Harder without war

            decisions.append(AIDecision(
                "conquer_territory",
                priority=priority,
                territory_id=territory_id,
            ))

        return decisions

    def _evaluate_diplomacy(
        self,
        nation: Nation,
        all_nations: dict[str, Nation],
        personality: AIPersonality,
        current_turn: int,
    ) -> list[AIDecision]:
        """Evaluate diplomatic actions."""
        decisions = []

        for other_nation in all_nations.values():
            if other_nation.nation_id == nation.nation_id:
                continue

            if not other_nation.is_active:
                continue

            relation = nation.get_relationship(other_nation.nation_id)

            if not relation:
                # Initialize relationship
                relation = DiplomaticRelation(
                    nation_id=other_nation.nation_id,
                    relationship=0,
                )
                nation.set_relationship(other_nation.nation_id, relation)

            # Consider declaring war
            if not relation.at_war:
                # Aggressive AI more likely to declare war
                war_priority = personality.aggression * 0.4

                # Consider relative strength
                if other_nation.total_military_strength < nation.total_military_strength * 0.7:
                    war_priority += 0.2  # Target weaker nations

                # Reduce priority if good relations
                if relation.relationship > 25:
                    war_priority *= 0.3

                # Expansionist AI wants more territory
                if other_nation.get_territory_count() > 3:
                    war_priority += 0.1 * personality.expansion_desire

                if war_priority > 0.3:
                    decisions.append(AIDecision(
                        "declare_war",
                        priority=war_priority,
                        target_nation_id=other_nation.nation_id,
                    ))

            # Consider making peace
            if relation.at_war:
                peace_priority = 0.2

                # Want peace if losing badly
                if other_nation.total_military_strength > nation.total_military_strength * 1.5:
                    peace_priority += 0.4

                # Diplomatic AI prefers peace
                peace_priority += personality.diplomacy_preference * 0.3

                # War has gone on long enough
                if relation.turns_at_current_state > 20:
                    peace_priority += 0.2

                if peace_priority > 0.4:
                    decisions.append(AIDecision(
                        "make_peace",
                        priority=peace_priority,
                        target_nation_id=other_nation.nation_id,
                    ))

            # Consider alliance
            if not relation.has_alliance and not relation.at_war:
                alliance_priority = personality.diplomacy_preference * 0.3

                # Good relations make alliance more likely
                if relation.relationship > 50:
                    alliance_priority += 0.3

                # Common enemy (both at war with same nation)
                if self._have_common_enemy(nation, other_nation, all_nations):
                    alliance_priority += 0.2

                if alliance_priority > 0.5:
                    decisions.append(AIDecision(
                        "form_alliance",
                        priority=alliance_priority,
                        target_nation_id=other_nation.nation_id,
                    ))

        return decisions

    def _evaluate_military(
        self,
        nation: Nation,
        all_nations: dict[str, Nation],
        personality: AIPersonality,
    ) -> list[AIDecision]:
        """Evaluate military buildup needs."""
        decisions = []

        # Check if military is weak compared to neighbors
        neighbor_strength = 0
        neighbor_count = 0

        for other_nation in all_nations.values():
            if other_nation.nation_id == nation.nation_id:
                continue
            if not other_nation.is_active:
                continue

            neighbor_strength += other_nation.total_military_strength
            neighbor_count += 1

        avg_neighbor_strength = neighbor_strength / max(1, neighbor_count)

        # Need military if weaker than neighbors
        if nation.total_military_strength < avg_neighbor_strength * 0.8:
            priority = 0.6 * personality.military_focus

            decisions.append(AIDecision(
                "recruit_units",
                priority=priority,
                unit_count=2,
            ))

        # Always maintain some military
        if len(nation.generals) < 2:
            priority = 0.4 * personality.military_focus

            decisions.append(AIDecision(
                "recruit_units",
                priority=priority,
                unit_count=1,
            ))

        return decisions

    def _evaluate_economy(
        self,
        nation: Nation,
        all_territories: dict[str, Territory],
        personality: AIPersonality,
    ) -> list[AIDecision]:
        """Evaluate economic development opportunities."""
        decisions = []

        # Check resources
        low_on_resources = False
        for resource, amount in nation.resources.items():
            if amount < 100 and resource != ResourceType.GEMS and resource != ResourceType.MITHRIL:
                low_on_resources = True
                break

        if low_on_resources:
            priority = 0.5 * personality.economic_focus

            decisions.append(AIDecision(
                "develop_economy",
                priority=priority,
            ))

        return decisions

    def _evaluate_monster_threats(
        self,
        nation: Nation,
        all_territories: dict[str, Territory],
        monster_spawner: MonsterSpawner,
        personality: AIPersonality,
    ) -> list[AIDecision]:
        """Evaluate monster threats to nation."""
        decisions = []

        # Check for monsters near controlled territories
        for territory_id in nation.controlled_territories:
            territory = all_territories.get(territory_id)
            if not territory:
                continue

            threat = monster_spawner.get_threat_assessment(territory_id)

            if threat["total_strength"] > 50:
                priority = 0.5 + min(0.4, threat["total_strength"] / 1000)

                decisions.append(AIDecision(
                    "clear_monsters",
                    priority=priority,
                    territory_id=territory_id,
                ))

        return decisions

    def _execute_decision(
        self,
        decision: AIDecision,
        nation: Nation,
        all_nations: dict[str, Nation],
        all_territories: dict[str, Territory],
        monster_spawner: MonsterSpawner,
    ) -> Optional[dict]:
        """
        Execute an AI decision.

        Returns:
            Event dict describing what happened
        """
        if decision.decision_type == "conquer_territory":
            return self._execute_conquest(
                nation,
                decision.params["territory_id"],
                all_territories,
                all_nations,
            )

        elif decision.decision_type == "declare_war":
            return self._execute_declare_war(
                nation,
                decision.params["target_nation_id"],
                all_nations,
            )

        elif decision.decision_type == "make_peace":
            return self._execute_make_peace(
                nation,
                decision.params["target_nation_id"],
                all_nations,
            )

        elif decision.decision_type == "form_alliance":
            return self._execute_form_alliance(
                nation,
                decision.params["target_nation_id"],
                all_nations,
            )

        elif decision.decision_type == "recruit_units":
            return self._execute_recruit_units(
                nation,
                decision.params.get("unit_count", 1),
            )

        elif decision.decision_type == "clear_monsters":
            return self._execute_clear_monsters(
                nation,
                decision.params["territory_id"],
                monster_spawner,
            )

        return None

    def _execute_conquest(
        self,
        nation: Nation,
        territory_id: str,
        all_territories: dict[str, Territory],
        all_nations: dict[str, Nation],
    ) -> Optional[dict]:
        """Execute territory conquest."""
        territory = all_territories.get(territory_id)
        if not territory:
            return None

        # Check if can afford conquest (simplified for now)
        cost = {ResourceType.GOLD: 100, ResourceType.FOOD: 50}

        if not nation.has_resources(cost):
            return None

        nation.consume_resources(cost)

        # If owned by another nation, they lose it
        if territory.is_owned():
            old_owner_id = territory.owner_id
            old_owner = all_nations.get(old_owner_id)
            if old_owner:
                old_owner.remove_territory(territory_id)

        # Nation gains territory
        territory.owner_id = nation.nation_id
        nation.add_territory(territory_id)

        return {
            "type": "territory_conquered",
            "nation_id": nation.nation_id,
            "nation_name": nation.name,
            "territory_id": territory_id,
            "territory_name": territory.name,
        }

    def _execute_declare_war(
        self,
        nation: Nation,
        target_nation_id: str,
        all_nations: dict[str, Nation],
    ) -> Optional[dict]:
        """Execute war declaration."""
        target = all_nations.get(target_nation_id)
        if not target:
            return None

        nation.declare_war(target_nation_id)
        target.declare_war(nation.nation_id)  # Mutual war

        return {
            "type": "war_declared",
            "aggressor_id": nation.nation_id,
            "aggressor_name": nation.name,
            "target_id": target.nation_id,
            "target_name": target.name,
        }

    def _execute_make_peace(
        self,
        nation: Nation,
        target_nation_id: str,
        all_nations: dict[str, Nation],
    ) -> Optional[dict]:
        """Execute peace treaty."""
        target = all_nations.get(target_nation_id)
        if not target:
            return None

        nation.make_peace(target_nation_id)
        target.make_peace(nation.nation_id)

        return {
            "type": "peace_made",
            "nation1_id": nation.nation_id,
            "nation1_name": nation.name,
            "nation2_id": target.nation_id,
            "nation2_name": target.name,
        }

    def _execute_form_alliance(
        self,
        nation: Nation,
        target_nation_id: str,
        all_nations: dict[str, Nation],
    ) -> Optional[dict]:
        """Execute alliance formation."""
        target = all_nations.get(target_nation_id)
        if not target:
            return None

        nation.form_alliance(target_nation_id)
        target.form_alliance(nation.nation_id)

        return {
            "type": "alliance_formed",
            "nation1_id": nation.nation_id,
            "nation1_name": nation.name,
            "nation2_id": target.nation_id,
            "nation2_name": target.name,
        }

    def _execute_recruit_units(
        self,
        nation: Nation,
        unit_count: int,
    ) -> Optional[dict]:
        """Execute unit recruitment."""
        # Cost per unit
        cost_per_unit = {
            ResourceType.GOLD: 200,
            ResourceType.FOOD: 50,
            ResourceType.IRON: 25,
        }

        total_cost = {
            resource: amount * unit_count
            for resource, amount in cost_per_unit.items()
        }

        if not nation.has_resources(total_cost):
            return None

        nation.consume_resources(total_cost)

        # Add units (simplified - will integrate with actual unit system later)
        for i in range(unit_count):
            unit_id = f"unit_{nation.nation_id}_{len(nation.generals)}"
            nation.generals.append(unit_id)

        nation.total_military_strength += 100 * unit_count  # Simplified

        return {
            "type": "units_recruited",
            "nation_id": nation.nation_id,
            "nation_name": nation.name,
            "unit_count": unit_count,
        }

    def _execute_clear_monsters(
        self,
        nation: Nation,
        territory_id: str,
        monster_spawner: MonsterSpawner,
    ) -> Optional[dict]:
        """Execute monster clearing operation."""
        # Get monster parties in territory
        parties = monster_spawner.get_monsters_in_territory(territory_id)

        if not parties:
            return None

        # Fight weakest party
        parties.sort(key=lambda p: p.total_strength)
        target_party = parties[0]

        # Simulate combat (simplified)
        if nation.total_military_strength > target_party.total_strength:
            # Victory
            rewards = monster_spawner.defeat_monster_party(target_party.party_id)

            if rewards:
                nation.add_resources({ResourceType.GOLD: rewards["gold"]})

            return {
                "type": "monsters_defeated",
                "nation_id": nation.nation_id,
                "nation_name": nation.name,
                "territory_id": territory_id,
                "rewards": rewards,
            }

        return None

    def _find_expansion_targets(
        self,
        nation: Nation,
        all_territories: dict[str, Territory],
    ) -> list[tuple[str, Territory]]:
        """Find territories adjacent to nation that could be conquered."""
        targets = []

        for territory_id in nation.controlled_territories:
            territory = all_territories.get(territory_id)
            if not territory:
                continue

            # Get neighbors
            neighbors = territory.get_neighbors(40, 30)

            for nx, ny in neighbors:
                neighbor_id = f"hex_{nx}_{ny}"
                neighbor = all_territories.get(neighbor_id)

                if not neighbor:
                    continue

                # Can target unowned or enemy territories
                if not neighbor.is_owned():
                    targets.append((neighbor_id, neighbor))
                elif neighbor.owner_id != nation.nation_id:
                    # Enemy territory
                    relation = nation.get_relationship(neighbor.owner_id)
                    if relation and relation.at_war:
                        targets.append((neighbor_id, neighbor))

        return targets

    def _have_common_enemy(
        self,
        nation1: Nation,
        nation2: Nation,
        all_nations: dict[str, Nation],
    ) -> bool:
        """Check if two nations have a common enemy."""
        for other_nation in all_nations.values():
            if other_nation.nation_id in [nation1.nation_id, nation2.nation_id]:
                continue

            if nation1.is_at_war_with(other_nation.nation_id) and \
               nation2.is_at_war_with(other_nation.nation_id):
                return True

        return False
