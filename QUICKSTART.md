# Chronicles of Aethermoor - Quick Start Guide

## Installation

```bash
cd ~/chronicles-of-aethermoor
source venv/bin/activate  # Activate virtual environment
```

## Running the Game

```bash
python -m src.main
```

## Playing the Game

### Main Menu
1. **New Game** - Start a new campaign
2. **Load Game** - Load from save slots
3. **Settings** - (Coming in Phase 2)
4. **Credits** - View game credits
5. **Exit** - Quit game

### Starting a New Game

1. Enter your player name
2. Enter your nation name
3. Select difficulty:
   - **Easy** - For newcomers
   - **Normal** - Balanced (recommended)
   - **Hard** - For JRPG veterans
   - **Legendary** - Ultimate challenge

### In-Game Controls

During gameplay you can:
- **View Status** - See current game information
- **View World Map** - Explore the world, view territories and nations
- **Advance Turn** - Progress to next turn (generates resources)
- **Save Game** - Save to manual slot or quicksave
- **Return to Menu** - End session and return to main menu

### Saving Your Game

The game features multiple save systems:

1. **Manual Saves** - 10 slots for named saves
2. **Autosave** - Automatically saves every 5 turns
3. **Quicksave** - Single slot for quick saves
4. **Checkpoint** - Story checkpoints (Phase 2+)

**To save manually:**
1. In game menu, select "Save Game"
2. Choose slot 1, 2, or 3 (more available)
3. Or select Quicksave for instant save

### Loading a Game

1. From main menu, select "Load Game"
2. View list of available saves
3. Select save number to load
4. Continue your adventure!

### Exploring the World Map

1. In game menu, select "View World Map"
2. Choose from map options:
   - **View World Map** - See the hex grid with biomes and nations
   - **View Your Nation** - See resources, population, territories
   - **View Territory Details** - Inspect any hex by coordinates
   - **Territory List** - Browse all territories
   - **Map Statistics** - See biome distribution and world stats

**Map Symbols:**
- `~` Ocean
- `.` Plains
- `T` Forest
- `^` Mountain
- `V` Volcano
- `m` Swamp
- `R` Ruins (special feature)
- `S` Shrine (elemental power)
- Letters = Nation-owned territories

## Save File Locations

All saves are stored in: `~/chronicles-of-aethermoor/saves/`

- `saves/manual/` - Manual save slots
- `saves/auto/` - Autosaves (rotating)
- `saves/quick/` - Quicksave
- `saves/checkpoint/` - Checkpoints

## Tips

- **Save often!** Use quicksave (option 4) for convenience
- **Autosave happens every 5 turns** - but manual saving is recommended
- **Try different difficulties** - Easy is great for learning, Normal for regular play
- **Watch your playtime** - Displayed in status screen

## Phase 2 Features

Currently available:
- ✅ Create custom nations
- ✅ Turn-based time progression
- ✅ Multiple save slots
- ✅ Difficulty selection
- ✅ Playtime tracking
- ✅ Season/year system
- ✅ **Procedural world map generation (40×30 hexes)**
- ✅ **6 biome types with unique resources**
- ✅ **AI nations with distinct personalities**
- ✅ **Territory management and inspection**
- ✅ **Resource generation each turn**
- ✅ **Mana crystal production**
- ✅ **Buildings and workers**
- ✅ **Diplomacy system**
- ✅ **World map visualization**

Coming in Phase 3+:
- Tactical combat (12×18 hex battles)
- Unit recruitment
- Territory conquest
- AI opponents and actions
- Monster encounters
- Quests and narrative

## Keyboard Shortcuts

- **Numbers (1-9)** - Select menu options
- **Enter** - Confirm selection
- **Ctrl+C** - Emergency quit (saves before exit)

## Troubleshooting

**Game won't start?**
```bash
cd ~/chronicles-of-aethermoor
source venv/bin/activate
python -m src.main
```

**Save file issues?**
- Check `~/chronicles-of-aethermoor/saves/` directory exists
- Ensure you have write permissions
- Backup saves are created as `.bak` files

**Lost progress?**
- Check autosaves in Load Game menu
- Autosaves rotate every 5 turns
- Up to 3 autosaves are kept

## Getting Help

For issues or questions:
1. Check `README.md` for technical details
2. Review `PHASE1_COMPLETE.md` for features
3. See design docs in `/home/schade/Documents/`

## What's Next?

This is Phase 1 - the foundation. Future phases will add:
- **Phase 2:** World map, territories, nations
- **Phase 3:** Tactical combat system
- **Phase 4:** AI opponents, monsters
- **Phase 5:** Economy and crafting
- **Phase 6:** Narrative and quests

Stay tuned for updates! 🎮

---

**Enjoy Chronicles of Aethermoor!**
