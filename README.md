# Chronicles of Aethermoor

A text-based tactical JRPG combining Final Fantasy Tactics' job system, Brigandine's strategic conquest, and Age of Wonders' elemental magic.

## Project Status

**Phase 3: Tactical Combat ✅ COMPLETE**
- ✅ 12×18 hex battlefield system
- ✅ A* pathfinding for movement
- ✅ Complete damage calculation (physical/magical)
- ✅ Elemental advantage system
- ✅ Critical hits and terrain bonuses
- ✅ Speed-based turn order
- ✅ AI opponent logic
- ✅ Interactive battle UI
- ✅ Status effects system

**Phase 2: World Layer ✅ COMPLETE**
- ✅ Procedural world map generator (40×30 hex grid)
- ✅ Territory system with 6 biome types
- ✅ Nation system with AI personalities
- ✅ Resource generation and economy
- ✅ Diplomacy framework
- ✅ World map visualization
- ✅ Complete save/load integration

**Phase 1: Foundation ✅ COMPLETE**
- ✅ Core data structures
- ✅ Game engine foundation
- ✅ Save/load system with compression
- ✅ Basic UI framework
- ✅ Turn-based time progression

**Next: Phase 4 - AI Nations & Monster System**

## Tech Stack

- **Language:** Python 3.10+
- **UI Framework:** Textual (Terminal UI)
- **Data Format:** JSON + zlib compression
- **Testing:** pytest

## Project Structure

```
chronicles-of-aethermoor/
├── src/
│   ├── core/          # Game engine, state management
│   ├── models/        # Data models (units, territories, etc.)
│   ├── ui/            # Terminal UI components
│   ├── systems/       # Game systems (combat, diplomacy, etc.)
│   ├── data/          # Game data and constants
│   └── utils/         # Utilities and helpers
├── tests/             # Unit tests
├── assets/            # Game assets (audio, data files)
├── docs/              # Documentation
├── saves/             # Save game files
└── config/            # Configuration files
```

## Features

### World Map System
- **Procedural generation**: Every game creates a unique 40×30 hex world
- **6 biome types**: Plains, Forest, Mountain, Volcano, Ocean, Swamp
- **Elemental affinities**: Territories generate element-specific mana
- **Special features**: Ancient ruins, elemental shrines
- **Strategic starts**: AI nations placed at balanced distances

### Nation Management
- **Player + 3 AI nations** with distinct personalities
- **Resource economy**: Gold, Food, Timber, Iron, Leather, Herbs, Gems, Mithril
- **Mana system**: 6 elemental crystals (Fire, Water, Earth, Air, Life, Death)
- **Territory control**: Build your empire across the map
- **Diplomacy**: Track relationships, wars, alliances

### Tactical Combat
- **12×18 hex battlefield**: Strategic positioning matters
- **A* pathfinding**: Intelligent movement around obstacles
- **Damage system**: Physical and magical attacks with elemental bonuses
- **Critical hits**: 10% chance for 1.5× damage
- **Terrain effects**: Forests +15% defense, Hills +20% defense + height advantage
- **Status effects**: Poison, Burn, Freeze, Stun, Haste, Slow, and more
- **AI opponents**: Smart enemy units with tactical positioning
- **Turn order**: Speed-based queue, fastest units act first
- **Interactive battles**: Player controls units with move/attack commands

### Gameplay
- **Turn-based strategy**: Resources generate each turn on world map
- **Tactical battles**: Fight on hex grids with positioning and terrain
- **Territory inspection**: View detailed stats for any hex
- **Nation overview**: Track population, happiness, military strength
- **World exploration**: Interactive map with ASCII visualization
- **Battle demo**: Test the combat system with procedural encounters
- **Multiple difficulty levels**: Easy, Normal, Hard, Legendary

### Save System
- **10 manual save slots**
- **Rotating autosaves** (every 5 turns)
- **Quicksave** for convenience
- **Compressed saves**: ~50KB per file
- **Full state preservation**: Everything saves and loads perfectly

## Setup

```bash
# Navigate to project directory
cd ~/chronicles-of-aethermoor

# Activate virtual environment (already created)
source venv/bin/activate

# Run game
python -m src.main

# Or use the quick start guide
cat QUICKSTART.md
```

## Development

```bash
# Run tests
pytest

# Run with debug mode
python -m src.main --debug
```

## Design Documents

See `/home/schade/Documents/` for:
- `JRPG_Masterwork_Design.md` - Complete game design
- `JRPG_Implementation_Roadmap.md` - Development roadmap
- `JRPG_Class_Monster_Reference.md` - Game data reference

## License

Copyright 2025. All rights reserved.
